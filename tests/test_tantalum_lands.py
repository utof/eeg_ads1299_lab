"""Two selected T491 cases use explicit manufacturer nominal reflow lands.

Independent dimensions are from KEMET T2005_T491 Table 2, density B. This is
source geometry, not a fabricated board, solder-process or electrical approval.
"""

import gzip
import shutil
from pathlib import Path

import pytest

from hardware.rev_a import parse_schematic_xml, schematic_source_snapshot, validate_footprint

ROOT = Path(__file__).resolve().parents[1]
CAD = ROOT / "hardware/rev_a/kicad"
CASES = [
    ("C_REF", "T491B_3528_DensityB", 1.46, 1.80, 2.23, 5.22, 3.50),
    ("C_VCAP1", "T491D_7343_DensityB", 3.12, 2.37, 2.43, 9.12, 5.10),
]


@pytest.mark.parametrize(("ref", "name", "x", "length", "width", "v1", "v2"), CASES)
def test_selected_graph_points_at_the_explicit_local_pattern(
    ref: str, name: str, x: float, length: float, width: float, v1: float, v2: float
) -> None:
    xml = gzip.decompress((ROOT / "tests/fixtures/rev_a_netlist.xml.gz").read_bytes()).decode()
    part = parse_schematic_xml(xml).parts[ref]
    assert part.footprint == "RevA_Passives:" + name


@pytest.mark.parametrize(("ref", "name", "x", "length", "width", "v1", "v2"), CASES)
def test_manufacturer_land_and_courtyard_dimensions_are_present(
    ref: str, name: str, x: float, length: float, width: float, v1: float, v2: float
) -> None:
    path = CAD / "RevA_Passives.pretty" / (name + ".kicad_mod")
    assert path.is_file(), "missing editable project-local tantalum footprint"
    content = path.read_text()
    pads = validate_footprint("RevA_Passives:" + name, content)
    assert [(p.number, p.x_mm, p.y_mm, p.width_mm, p.height_mm, p.shape) for p in pads] == [
        ("1", -x, 0, length, width, "rect"),
        ("2", x, 0, length, width, "rect"),
    ]
    # Courtyard envelope is a separate manufacturer quantity, not the copper gap.
    assert f"(start {-v1 / 2:g} {-v2 / 2:g}) (end {v1 / 2:g} {v2 / 2:g})" in content
    assert '(fp_text user "+"' in content


@pytest.mark.parametrize(
    ("before", "after"),
    [
        ('(pad "1"', '(pad "9"'),
        ("(at -1.46 0)", "(at 1.46 0)"),
        ("(size 1.8 2.23)", "(size 1.34 2.39)"),
        ("(start -2.61 -1.75) (end 2.61 1.75)", "(start -2.36 -1.4) (end 2.36 1.4)"),
        ('(layer "F.CrtYd")', '(layer "F.Fab")'),
        ('(layer "F.CrtYd")', '(layer "F.Cu")'),
    ],
    ids=[
        "pad-id",
        "polarity",
        "old-generic-land",
        "small-courtyard",
        "missing-courtyard",
        "copper-rectangle",
    ],
)
def test_wrong_local_land_or_courtyard_fails(before: str, after: str) -> None:
    path = CAD / "RevA_Passives.pretty/T491B_3528_DensityB.kicad_mod"
    content = path.read_text()
    assert before in content
    with pytest.raises(ValueError, match="footprint"):
        validate_footprint("RevA_Passives:T491B_3528_DensityB", content.replace(before, after, 1))


@pytest.mark.parametrize(
    "fault", ["missing", "file-link", "directory-link", "extra", "global-fallback"]
)
def test_local_library_is_a_closed_snapshotted_dependency(tmp_path: Path, fault: str) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    library = cad / "RevA_Passives.pretty"
    path = library / "T491B_3528_DensityB.kicad_mod"
    if fault == "missing":
        path.unlink()
    elif fault == "file-link":
        target = tmp_path / "borrowed.kicad_mod"
        path.rename(target)
        path.symlink_to(target)
    elif fault == "directory-link":
        target = tmp_path / "borrowed.pretty"
        library.rename(target)
        library.symlink_to(target, target_is_directory=True)
    elif fault == "extra":
        (library / "unreviewed.kicad_mod").write_text("unexpected")
    else:
        table = cad / "fp-lib-table"
        table.write_text(
            table.read_text().replace(
                "${KIPRJMOD}/RevA_Passives.pretty", "${KICAD9_FOOTPRINT_DIR}/RevA_Passives.pretty"
            )
        )
    with pytest.raises(ValueError):
        schematic_source_snapshot(cad)


def test_both_local_files_are_hashed_without_an_installed_library() -> None:
    hashes = schematic_source_snapshot(CAD)
    assert len(hashes) == 9
    for _, name, *_ in CASES:
        assert "footprints/RevA_Passives.pretty/" + name + ".kicad_mod" in hashes
