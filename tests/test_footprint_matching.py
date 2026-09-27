"""Each actual copper land needs a distinct expected partner, including near duplicates."""

from pathlib import Path

import pytest

from hardware.rev_a import schematic_source_snapshot, validate_footprint
from tests.footprint_fixtures import footprint_sources, write_footprint_library

NONPOLAR = [
    "Capacitor_SMD:C_0603_1608Metric",
    "Capacitor_SMD:C_0805_2012Metric",
    "Resistor_SMD:R_0603_1608Metric",
]
CAD = Path(__file__).resolve().parents[1] / "hardware/rev_a/kicad"


def _move_second_land(footprint: str, collapse: bool) -> str:
    content = footprint_sources()[footprint]
    left, right = validate_footprint(footprint, content)
    before = f"(at {right.x_mm:g} 0)"
    # Half a nanometre breaks an exact-coordinate duplicate test, but remains
    # inside the documented representation tolerance. The WRONG move is about
    # 1.5-1.9 mm: the second land has jumped to the first land's side.
    position = left.x_mm if collapse else right.x_mm
    after = f"(at {position + 0.0000005:.7f} 0)"
    assert content.count(before) == 1
    return content.replace(before, after)


@pytest.mark.parametrize("footprint", NONPOLAR)
def test_two_actual_lands_cannot_reuse_one_expected_partner(footprint: str) -> None:
    with pytest.raises(ValueError, match="footprint"):
        validate_footprint(footprint, _move_second_land(footprint, collapse=True))


@pytest.mark.parametrize("footprint", NONPOLAR)
def test_distinct_lands_keep_representation_tolerance(footprint: str) -> None:
    pads = validate_footprint(footprint, _move_second_land(footprint, collapse=False))
    assert len(pads) == 2 and pads[0].x_mm < 0 < pads[1].x_mm


def test_source_snapshot_rejects_a_near_duplicate_copper_pair(tmp_path: Path) -> None:
    root = write_footprint_library(tmp_path / "footprints")
    footprint = NONPOLAR[0]
    path = root / "Capacitor_SMD.pretty/C_0603_1608Metric.kicad_mod"
    path.write_text(_move_second_land(footprint, collapse=True))
    with pytest.raises(ValueError, match="footprint"):
        schematic_source_snapshot(CAD, root)


@pytest.mark.schematic
@pytest.mark.parametrize("footprint", NONPOLAR)
def test_benign_nonpolar_swap_reaches_the_existing_native_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, footprint: str
) -> None:
    from tests.test_footprint_native import _inspect_and_export

    root = write_footprint_library(tmp_path / "footprints")
    library, name = footprint.split(":")
    path = root / (library + ".pretty") / (name + ".kicad_mod")
    text = path.read_text().replace('(pad "1"', '(pad "temporary"')
    text = text.replace('(pad "2"', '(pad "1"').replace('(pad "temporary"', '(pad "2"')
    path.write_text(text)
    monkeypatch.setenv("KICAD9_FOOTPRINT_DIR", str(root))
    # Exercise the exact existing native path: accepting this only in the pure
    # validator is insufficient if its subsequent fixture comparison rejects it.
    _inspect_and_export(tmp_path, footprint)


@pytest.mark.schematic
def test_near_duplicate_pair_is_native_loadable_but_rejected(tmp_path: Path) -> None:
    import os
    import shutil
    import subprocess

    footprint = NONPOLAR[0]
    root = write_footprint_library(tmp_path / "footprints")
    library, name = footprint.split(":")
    content = _move_second_land(footprint, collapse=True)
    (root / (library + ".pretty") / (name + ".kicad_mod")).write_text(content)
    cli = shutil.which("kicad-cli")
    assert cli is not None, "actual footprint regression requires KiCad"
    command = [
        cli,
        "fp",
        "export",
        "svg",
        "--layers",
        "F.Cu",
        "--black-and-white",
        "--footprint",
        name,
        "-o",
        str(tmp_path),
        str(root / (library + ".pretty")),
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=45,
        env=dict(os.environ, KICAD_CONFIG_HOME=str(tmp_path / "config"), LC_ALL="C", LANG="C"),
    )
    (tmp_path / "near-duplicate-native.log").write_text(result.stdout + result.stderr)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "<svg" in (tmp_path / (name + ".svg")).read_text()
    with pytest.raises(ValueError, match="footprint"):
        validate_footprint(footprint, content)
