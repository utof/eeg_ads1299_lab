"""Actual C3 exports; mutations are disposable CAD copies, not physical faults."""

import csv
import gzip
import io
import os
import re
import shutil
import subprocess
import uuid
from pathlib import Path

import pytest

from hardware.rev_a import (
    parse_auxiliary_contract,
    parse_schematic_xml,
    read_schematic_file,
    validate_auxiliary,
    validate_auxiliary_erc,
)

ROOT = Path(__file__).resolve().parents[1]
CAD = ROOT / "hardware/rev_a/auxiliary"
pytestmark = pytest.mark.schematic


def _run(cad: Path, out: Path, command: list[str]) -> None:
    cli = shutil.which("kicad-cli")
    assert cli is not None, "native auxiliary checks require KiCad"
    env = dict(os.environ, KICAD_CONFIG_HOME=str(out / "config"), LANG="C", LC_ALL="C")
    log = out / ("-".join(command[:3]) + ".log")
    with log.open("w") as stream:
        result = subprocess.run(
            [cli, *command, str(cad / "auxiliary.kicad_sch")],
            stdout=stream,
            stderr=subprocess.STDOUT,
            timeout=45,
            env=env,
        )
    assert result.returncode == 0, log.read_text()


def _export(cad: Path, out: Path) -> str:
    _run(cad, out, ["sch", "export", "netlist", "--format", "kicadxml", "-o", str(out / "aux.xml")])
    return read_schematic_file(out / "aux.xml")


def _erc(cad: Path, out: Path) -> None:
    _run(
        cad,
        out,
        [
            "sch",
            "erc",
            "--format",
            "json",
            "--severity-all",
            "--exit-code-violations",
            "-o",
            str(out / "erc.json"),
        ],
    )
    validate_auxiliary_erc(read_schematic_file(out / "erc.json"))


def test_auxiliary_native_erc_netlist_pdf_and_bom(tmp_path: Path) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    _erc(cad, tmp_path)
    graph = parse_schematic_xml(_export(cad, tmp_path))
    contract = parse_auxiliary_contract(read_schematic_file(CAD / "contract.json"))
    assert validate_auxiliary(graph, contract) == []
    frozen = gzip.decompress(
        (ROOT / "tests/fixtures/auxiliary_c3_netlist.xml.gz").read_bytes()
    ).decode()
    assert graph == parse_schematic_xml(frozen)
    _run(cad, tmp_path, ["sch", "export", "pdf", "-o", str(tmp_path / "auxiliary.pdf")])
    assert (tmp_path / "auxiliary.pdf").read_bytes().startswith(b"%PDF-")
    _run(
        cad,
        tmp_path,
        [
            "sch",
            "export",
            "bom",
            "--fields",
            "Reference,ContractRef,Value,MPN,Footprint",
            "--labels",
            "Reference,ContractRef,Value,MPN,Footprint",
            "-o",
            str(tmp_path / "bom.csv"),
        ],
    )
    rows = list(csv.DictReader(io.StringIO(read_schematic_file(tmp_path / "bom.csv"))))
    assert len(rows) == 43
    assert {r["ContractRef"] for r in rows} == {r for r, p in contract.parts.items() if p.in_bom}
    for row in rows:
        part = contract.parts[row["ContractRef"]]
        assert (row["Reference"], row["Value"], row["MPN"], row["Footprint"]) == (
            part.reference,
            part.value,
            part.mpn,
            part.footprint,
        )


def _label(cad: Path, sheet: str, reference: str, number: int, value: str) -> None:
    # This UUID locates a mutation target, never an acceptance/geometry oracle.
    key = uuid.uuid5(
        uuid.UUID("23b8be8c-a771-45f2-a7b0-74a8245c5075"), reference + str(number) + "label"
    )
    path = cad / (sheet + ".kicad_sch")
    text = path.read_text()
    lines = text.splitlines(keepends=True)
    targets = [i for i, line in enumerate(lines) if f'(uuid "{key}")' in line]
    assert len(targets) == 1, "native fault no longer locates the intended pin label"
    i = targets[0]
    assert lines[i].startswith('(global_label "')
    lines[i] = re.sub(r'^\(global_label "[^"]+"', f'(global_label "{value}"', lines[i], count=1)
    changed = "".join(lines)
    assert changed != text
    path.write_text(changed)


@pytest.mark.parametrize(
    "sheet,ref,pin,target",
    [
        ("bus", "U102", 14, "MCU_3V3"),
        ("supervision", "U106", 1, "AFE_DVDD"),
        ("supervision", "U108", 2, "TARGET_VIN5"),
        ("arming", "U110", 6, "CLR_N"),
        ("auxiliary", "C101", 2, "TARGET_GND"),
        ("bus", "U104", 3, "MCU_SCLK"),
    ],
)
def test_auxiliary_wrong_connections_export_but_fail_contract(
    tmp_path: Path, sheet: str, ref: str, pin: int, target: str
) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    _label(cad, sheet, ref, pin, target)
    # Deliberately wrong supply/input choices and coupling through a bypass can
    # be perfectly ERC-clean. The independent terminal contract must catch them.
    _erc(cad, tmp_path)
    graph = parse_schematic_xml(_export(cad, tmp_path))
    errors = validate_auxiliary(
        graph, parse_auxiliary_contract(read_schematic_file(CAD / "contract.json"))
    )
    (tmp_path / "contract-errors.txt").write_text("\n".join(errors))
    assert errors


@pytest.mark.parametrize("kind", ["rename", "passive-reverse"])
def test_auxiliary_benign_native_edits(tmp_path: Path, kind: str) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    if kind == "rename":
        for path in cad.glob("*.kicad_sch"):
            path.write_text(
                path.read_text().replace(
                    '(global_label "MCU_3V3"', '(global_label "LOGIC_SUPPLY_RENAMED"'
                )
            )
    else:
        _label(cad, "auxiliary", "C101", 1, "HOST_GND")
        _label(cad, "auxiliary", "C101", 2, "HOST_3V3")
    _erc(cad, tmp_path)
    graph = parse_schematic_xml(_export(cad, tmp_path))
    assert (
        validate_auxiliary(
            graph, parse_auxiliary_contract(read_schematic_file(CAD / "contract.json"))
        )
        == []
    )


_FOOTPRINT_SCRIPT = """
import json,sys
from pathlib import Path
import pcbnew as p
assert p.Version() == '9.0.2'
cad, libraries = map(Path, sys.argv[1:])
parts=json.loads((cad/'contract.json').read_text())['parts']
seen=set()
for item in parts:
    identifier=item['footprint']
    if identifier in seen:
        continue
    seen.add(identifier)
    lib,name=identifier.split(':')
    base=cad if lib=='Aux_Lands' else libraries
    fp=p.FootprintLoad(str(base/(lib+'.pretty')),name)
    assert fp is not None, identifier
    pads=list(fp.Pads())
    assert {x.GetNumber() for x in pads}==set(item['pins']), identifier
    assert len(pads)==len(item['pins']), identifier
    if lib=='Aux_Lands':
        for pad in pads:
            assert pad.GetAttribute()==p.PAD_ATTRIB_PTH
            assert pad.GetDrillSize()==p.VECTOR2I(p.FromMM(1),p.FromMM(1))
            assert pad.GetSize()==p.VECTOR2I(p.FromMM(2),p.FromMM(2))
            assert pad.GetPosition()==p.VECTOR2I(p.FromMM((int(pad.GetNumber())-1)*2.54),0)
print(json.dumps({'kicad':p.Version(),'unique_footprints':len(seen),'parts':len(parts)}))
"""


@pytest.mark.parametrize("bad_tail_drill", [False, True])
def test_auxiliary_native_footprint_pin_sets_and_solder_land_dimensions(
    tmp_path: Path, bad_tail_drill: bool
) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    if bad_tail_drill:
        path = cad / "Aux_Lands.pretty/SolderTails_20.kicad_mod"
        text = path.read_text()
        assert "(drill 1)" in text
        path.write_text(text.replace("(drill 1)", "(drill 0.7)", 1))
    libraries = os.environ.get("KICAD9_FOOTPRINT_DIR")
    assert libraries, "native library path must be explicit"
    log = tmp_path / "native-footprints.log"
    with log.open("w") as stream:
        result = subprocess.run(
            [
                os.environ.get("KICAD_PYTHON", "/usr/bin/python3"),
                "-c",
                _FOOTPRINT_SCRIPT,
                str(cad),
                libraries,
            ],
            stdout=stream,
            stderr=subprocess.STDOUT,
            timeout=45,
        )
    if bad_tail_drill:
        assert result.returncode != 0 and "AssertionError" in log.read_text()
    else:
        assert result.returncode == 0, log.read_text()
