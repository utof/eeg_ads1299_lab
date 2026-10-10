"""Actual KiCad execution; deliberate CAD faults are not approved hardware designs."""

import gzip
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from hardware.rev_a import (
    load_documents,
    parse_schematic_xml,
    read_schematic_file,
    schematic_source_snapshot,
    validate_erc,
    validate_schematic,
    validate_schematic_bom,
)

ROOT = Path(__file__).resolve().parents[1]
CAD = ROOT / "hardware/rev_a/kicad"
pytestmark = pytest.mark.schematic


def _run(cad: Path, out: Path, command: list[str]) -> None:
    cli = shutil.which("kicad-cli")
    assert cli is not None, "native schematic test requires kicad-cli"
    env = dict(os.environ, KICAD_CONFIG_HOME=str(out / "native-config"), LC_ALL="C", LANG="C")
    log = out / ("-".join(command[:3]) + ".log")
    with log.open("w") as stream:
        result = subprocess.run(
            [cli, *command, str(cad / "rev_a.kicad_sch")],
            stdout=stream,
            stderr=subprocess.STDOUT,
            timeout=45,
            env=env,
        )
    assert result.returncode == 0, log.read_text()


def _export(cad: Path, out: Path) -> str:
    _run(
        cad,
        out,
        ["sch", "export", "netlist", "--format", "kicadxml", "-o", str(out / "native.xml")],
    )
    return read_schematic_file(out / "native.xml")


def test_actual_native_erc_and_export_match_frozen_graph(tmp_path: Path) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    before = schematic_source_snapshot(cad)
    _run(
        cad,
        tmp_path,
        [
            "sch",
            "erc",
            "--format",
            "json",
            "--severity-all",
            "--exit-code-violations",
            "-o",
            str(tmp_path / "erc.json"),
        ],
    )
    validate_erc(read_schematic_file(tmp_path / "erc.json"))
    netlist = parse_schematic_xml(_export(cad, tmp_path))
    profile, bom, _ = load_documents()
    assert validate_schematic(netlist, profile, bom) == []
    fixture = gzip.decompress((ROOT / "tests/fixtures/rev_a_netlist.xml.gz").read_bytes()).decode()
    assert netlist == parse_schematic_xml(fixture)
    validate_schematic_bom(_export_bom(cad, tmp_path), netlist)
    assert schematic_source_snapshot(cad) == before


@pytest.mark.parametrize(
    "fault",
    [
        "reference-to-dvdd",
        "input-pair-swap",
        "wrong-resistor-value",
        "clamp-fitted",
        "clock-unheld",
        "daisy-not-ground",
    ],
)
def test_actual_cad_faults_reach_native_export_then_fail_contract(
    tmp_path: Path, fault: str
) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    _break_cad(cad, fault)
    # Value/population errors are intentionally invisible to general ERC.
    if fault in {"wrong-resistor-value", "clamp-fitted"}:
        _run(
            cad,
            tmp_path,
            [
                "sch",
                "erc",
                "--format",
                "json",
                "--severity-all",
                "--exit-code-violations",
                "-o",
                str(tmp_path / "erc.json"),
            ],
        )
        validate_erc(read_schematic_file(tmp_path / "erc.json"))
    netlist = parse_schematic_xml(_export(cad, tmp_path))
    profile, bom, _ = load_documents()
    errors = validate_schematic(netlist, profile, bom)
    (tmp_path / "contract-errors.txt").write_text("\n".join(errors))
    assert errors, fault


def _break_cad(cad: Path, fault: str) -> None:
    name = (
        "power"
        if fault == "reference-to-dvdd"
        else "digital"
        if fault in {"clock-unheld", "daisy-not-ground"}
        else "rev_a"
    )
    path = cad / (name + ".kicad_sch")
    text = path.read_text()
    if fault == "input-pair-swap":
        text = text.replace('(global_label "IN1P"', '(global_label "TEMPORARY"', 1)
        text = text.replace('(global_label "IN1N"', '(global_label "IN1P"', 1)
        text = text.replace('(global_label "TEMPORARY"', '(global_label "IN1N"', 1)
    else:
        changes = {
            "reference-to-dvdd": ('(global_label "VREFP"', '(global_label "DVDD"'),
            "wrong-resistor-value": ('(property "Value" "4.99k"', '(property "Value" "4.99m"'),
            "clamp-fitted": ("(dnp yes)", "(dnp no)"),
            "clock-unheld": ('(global_label "CLK"', '(global_label "FLOATING_CLK"'),
            "daisy-not-ground": ('(global_label "GND"', '(global_label "FLOATING_DAISY"'),
        }
        before, after = changes[fault]
        assert before in text
        text = text.replace(before, after, 1)
    assert text != path.read_text(), "native fault no longer hits a CAD source operation"
    path.write_text(text)


def test_native_net_label_rename_does_not_change_connectivity(tmp_path: Path) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    for path in cad.glob("*.kicad_sch"):
        path.write_text(
            path.read_text().replace('(global_label "AVDD"', '(global_label "ANALOG_SUPPLY"')
        )
    netlist = parse_schematic_xml(_export(cad, tmp_path))
    profile, bom, _ = load_documents()
    assert validate_schematic(netlist, profile, bom) == []


def _export_bom(cad: Path, out: Path) -> str:
    _run(
        cad,
        out,
        [
            "sch",
            "export",
            "bom",
            "--fields",
            "Reference,ContractRef,Value,MPN,Footprint,Population,${DNP},${EXCLUDE_FROM_BOARD}",
            "--labels",
            "Reference,ContractRef,Value,MPN,Footprint,Population,DNP,OffBoard",
            "-o",
            str(out / "bom.csv"),
        ],
    )
    return read_schematic_file(out / "bom.csv")


@pytest.mark.parametrize("fault", ["excluded-from-bom", "library-only-pin-change"])
def test_native_erc_and_graph_do_not_hide_review_artifact_faults(
    tmp_path: Path, fault: str
) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    if fault == "excluded-from-bom":
        path = cad / "rev_a.kicad_sch"
        text = path.read_text()
        start = text.index('(symbol (lib_id "RevA:R")')
        path.write_text(text[:start] + text[start:].replace("(in_bom yes)", "(in_bom no)", 1))
    else:
        path = cad / "RevA.kicad_sym"
        text = path.read_text()
        assert text.count('(name "IN1P"') == 1
        path.write_text(text.replace('(name "IN1P"', '(name "LIBRARY_ONLY_CHANGED"', 1))
    _run(
        cad,
        tmp_path,
        [
            "sch",
            "erc",
            "--format",
            "json",
            "--severity-all",
            "--exit-code-violations",
            "-o",
            str(tmp_path / "erc.json"),
        ],
    )
    validate_erc(read_schematic_file(tmp_path / "erc.json"))
    netlist = parse_schematic_xml(_export(cad, tmp_path))
    profile, bom, _ = load_documents()
    assert validate_schematic(netlist, profile, bom) == []
    assert len(netlist.parts) == 71
    if fault == "excluded-from-bom":
        content = _export_bom(cad, tmp_path)
        with pytest.raises(ValueError, match="BOM CSV component inventory is incomplete"):
            validate_schematic_bom(content, netlist)
    else:
        with pytest.raises(ValueError, match="embedded symbol ADS1299_4 differs"):
            schematic_source_snapshot(cad)
