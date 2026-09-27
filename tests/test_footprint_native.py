"""Native KiCad footprint loading/export; not physical pad or assembly measurement."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from hardware.rev_a import read_schematic_file, validate_footprint
from tests.footprint_fixtures import footprint_sources

SOURCES = footprint_sources()
NAMES = list(SOURCES)


@pytest.mark.schematic
@pytest.mark.parametrize("footprint", NAMES)
def test_native_library_loads_and_exports_inspected_pads(tmp_path: Path, footprint: str) -> None:
    _inspect_and_export(tmp_path, footprint)


def _inspect_and_export(tmp_path: Path, footprint: str) -> None:
    cli = shutil.which("kicad-cli")
    assert cli is not None, "actual footprint export requires KiCad"
    root = Path(os.environ.get("KICAD9_FOOTPRINT_DIR", "/usr/share/kicad/footprints"))
    library, name = footprint.split(":")
    path = root / (library + ".pretty") / (name + ".kicad_mod")
    # The geometry contract permits nonpolar swaps and representation tolerance.
    # A literal dataclass comparison to the fixture would impose a second,
    # stricter rule and reject those benign changes before native export.
    validate_footprint(footprint, read_schematic_file(path))
    command = [
        cli,
        "fp",
        "export",
        "svg",
        "--layers",
        "F.Cu,F.Fab,F.SilkS",
        "--sketch-pads-on-fab-layers",
        "--black-and-white",
        "--footprint",
        name,
        "-o",
        str(tmp_path),
        str(path.parent),
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=45,
        env=dict(os.environ, KICAD_CONFIG_HOME=str(tmp_path / "config"), LC_ALL="C", LANG="C"),
    )
    (tmp_path / "native.log").write_text(result.stdout + result.stderr)
    assert result.returncode == 0, result.stdout + result.stderr
    output = tmp_path / (name + ".svg")
    assert output.is_file() and "<svg" in output.read_text()


@pytest.mark.schematic
@pytest.mark.parametrize(
    ("footprint", "before", "after"),
    [
        (
            "Capacitor_Tantalum_SMD:CP_EIA-7343-31_Kemet-D",
            "(size 2.07 2.59)",
            "(size 0.2 0.2)",
        ),
        (
            "Connector_PinHeader_2.54mm:PinHeader_2x10_P2.54mm_Vertical",
            "(drill 1)",
            "(drill 0.5)",
        ),
    ],
    ids=["collapsed-vcap-land", "undersized-header-hole"],
)
def test_native_erc_and_netlist_do_not_qualify_pad_geometry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, footprint: str, before: str, after: str
) -> None:
    from hardware.rev_a import (
        load_documents,
        parse_schematic_xml,
        schematic_source_snapshot,
        validate_erc,
        validate_schematic,
    )
    from tests.test_schematic_native import CAD, _export, _run

    installed = Path(os.environ.get("KICAD9_FOOTPRINT_DIR", "/usr/share/kicad/footprints"))
    copies = tmp_path / "footprints"
    for identifier in NAMES:
        library, name = identifier.split(":")
        relative = Path(library + ".pretty") / (name + ".kicad_mod")
        target = copies / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(installed / relative, target)
    library, name = footprint.split(":")
    path = copies / (library + ".pretty") / (name + ".kicad_mod")
    content = path.read_text()
    assert before in content
    path.write_text(content.replace(before, after, 1))
    monkeypatch.setenv("KICAD9_FOOTPRINT_DIR", str(copies))
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
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
    with pytest.raises(ValueError, match=r"footprint.*geometry differs"):
        schematic_source_snapshot(cad, copies)
