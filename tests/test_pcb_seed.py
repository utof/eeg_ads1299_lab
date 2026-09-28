"""A board import is not a routed board or a fabrication release."""

import gzip
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from hardware.rev_a import load_documents, make_pcb_seed, parse_schematic_xml
from tests.footprint_fixtures import footprint_sources

ROOT = Path(__file__).resolve().parents[1]
CAD = ROOT / "hardware/rev_a/kicad"
XML = gzip.decompress((ROOT / "tests/fixtures/rev_a_netlist.xml.gz").read_bytes()).decode()


def _libraries() -> dict[str, str]:
    selected = {part.footprint for part in parse_schematic_xml(XML).parts.values()} - {""}
    sources = footprint_sources()
    for path in (CAD / "RevA_Passives.pretty").glob("*.kicad_mod"):
        sources["RevA_Passives:" + path.stem] = path.read_text()
    return {name: sources[name] for name in selected}


def _seed(xml: str = XML, libraries: dict[str, str] | None = None) -> str:
    profile, bom, _ = load_documents()
    return make_pcb_seed(
        xml,
        (CAD / "rev_a.kicad_sch").read_text(),
        _libraries() if libraries is None else libraries,
        profile,
        bom,
    )


def test_seed_contains_all_board_instances_and_no_invented_routes_or_outline() -> None:
    board = _seed()
    assert board.startswith("(kicad_pcb ")
    assert board.count('(footprint "') == 68
    assert board.count('(pad "') == 245  # 256 terminals minus 11 off-board MOD1 pins.
    assert board.count(" dnp)") == 8
    assert '"MOD1"' not in board
    assert '(property "Reference" "U1"' in board
    assert '(property "ContractRef" "C_REF"' in board
    assert "RevA_Passives:T491B_3528_DensityB" in board
    assert "(segment " not in board and "(zone " not in board and "(gr_rect " not in board
    assert "UNROUTED IMPORT - NOT FOR FABRICATION" in board


def test_seed_is_deterministic_and_does_not_mutate_footprint_sources() -> None:
    sources = _libraries()
    before = dict(sources)
    board = _seed(libraries=sources)
    assert board == _seed(libraries=dict(reversed(list(sources.items()))))
    assert sources == before


@pytest.mark.parametrize("fault", ["missing", "extra", "wrong-pad", "wrong-value", "missing-path"])
def test_invalid_import_inputs_are_rejected(fault: str) -> None:
    sources, xml = _libraries(), XML
    if fault == "missing":
        sources.pop("Package_TO_SOT_SMD:SOT-23-5")
    elif fault == "extra":
        sources["Unreviewed:Spare"] = "(footprint)"
    elif fault == "wrong-pad":
        key = "Package_QFP:TQFP-64_10x10mm_P0.5mm"
        sources[key] = sources[key].replace('(pad "1"', '(pad "99"', 1)
    elif fault == "wrong-value":
        xml = xml.replace("<value>4.7n</value>", "<value>4.7u</value>", 1)
    else:
        xml = xml.replace("<tstamps>2bb2d28c-3364-549d-bcb5-2081e2c5ec77</tstamps>", "")
    with pytest.raises(ValueError):
        _seed(xml, sources)


def test_every_imported_component_keeps_identity_population_and_pad_count() -> None:
    graph = parse_schematic_xml(XML)
    lines = _seed().splitlines()
    for ref, part in graph.parts.items():
        matches = [line for line in lines if f'(property "Reference" "{part.native_ref}"' in line]
        if "exclude_from_board" in part.properties:
            assert matches == []
            continue
        assert len(matches) == 1
        line = matches[0]
        assert f'(footprint "{part.footprint}"' in line
        assert f'(property "Value" {json.dumps(part.value)}' in line
        for key in ("ContractRef", "MPN", "BOM_ID", "Population", "Tolerance"):
            if key in part.properties:
                assert f'(property "{key}" {json.dumps(part.properties[key])}' in line
        assert (" dnp)" in line) is ("dnp" in part.properties)
        assert line.count('(pad "') == sum(pin[0] == ref for pin in graph.nets)
        assert line.count('(path "') == 1


@pytest.mark.parametrize("code", ["0", "01", "-1", "one", "\u0661"])
def test_native_net_codes_cannot_alias_or_be_nonintegers(code: str) -> None:
    with pytest.raises(ValueError, match="net codes"):
        _seed(XML.replace('<net code="1"', f'<net code="{code}"'))


def test_unknown_root_uuid_is_not_silently_invented() -> None:
    profile, bom, _ = load_documents()
    with pytest.raises(ValueError, match="root schematic UUID"):
        make_pcb_seed(XML, "(kicad_sch)", _libraries(), profile, bom)


def _drc(cad: Path) -> dict[str, object]:
    cli = shutil.which("kicad-cli")
    assert cli is not None, "PCB import requires actual KiCad"
    output = cad / "board-drc.json"
    command = [
        cli,
        "pcb",
        "drc",
        "--format",
        "json",
        "--schematic-parity",
        "--severity-all",
        "--exit-code-violations",
        "-o",
        str(output),
        str(cad / "rev_a.kicad_pcb"),
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=45,
        env=dict(os.environ, KICAD_CONFIG_HOME=str(cad / "config")),
    )
    (cad / "board-drc.log").write_text(result.stdout + result.stderr)
    assert result.returncode == 5, "An unrouted import must not appear DRC-clean: " + result.stderr
    report = json.loads(output.read_text())
    assert isinstance(report, dict)
    return report


@pytest.mark.schematic
@pytest.mark.parametrize("fault", ["none", "wrong-reference", "missing-component", "wrong-net"])
def test_actual_pcb_import_parity_and_faults(tmp_path: Path, fault: str) -> None:
    from tests.test_schematic_native import _export

    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    xml = _export(cad, tmp_path)  # Fresh native export; no fixture is substituted.
    libraries = _libraries()
    installed = Path(os.environ.get("KICAD9_FOOTPRINT_DIR", "/usr/share/kicad/footprints"))
    for name in libraries:
        lib, base = name.split(":")
        directory = cad if lib == "RevA_Passives" else installed
        libraries[name] = (directory / (lib + ".pretty") / (base + ".kicad_mod")).read_text()
    board = _seed(xml, libraries)
    lines = board.splitlines()
    target = next(line for line in lines if '(property "Reference" "C7"' in line)
    if fault == "wrong-reference":
        board = board.replace('(property "Reference" "C7"', '(property "Reference" "C999"', 1)
    elif fault == "missing-component":
        board = board.replace(target, "", 1)
    elif fault == "wrong-net":
        import re

        # Change ONLY C_REF's positive pad assignment to the already-declared ground net.
        ground = next(re.finditer(r'\(net (\d+) "GND"\)', board)).group(0)
        changed = re.sub(r'\(net \d+ "VREFP"\)', ground, target, count=1)
        assert changed != target
        board = board.replace(target, changed, 1)
    (cad / "rev_a.kicad_pcb").write_text(board)
    report = _drc(cad)
    assert bool(report["schematic_parity"]) is (fault != "none")
    assert report["unconnected_items"], "Zero parity issues must not imply completed routing"
