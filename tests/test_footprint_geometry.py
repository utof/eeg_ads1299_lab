"""Pad geometry must be checked, not merely hashed under a plausible filename."""

from pathlib import Path

import pytest

from hardware.rev_a import schematic_source_snapshot
from tests.footprint_fixtures import write_footprint_library

ROOT = Path(__file__).resolve().parents[1]
CAD = ROOT / "hardware/rev_a/kicad"
FIXTURES = ROOT / "tests/fixtures/footprints"


@pytest.mark.parametrize(
    ("relative", "before", "after"),
    [
        ("Package_QFP.pretty/TQFP-64_10x10mm_P0.5mm.kicad_mod", '(pad "1"', '(pad "65"'),
        ("Package_TO_SOT_SMD.pretty/SOT-23-5.kicad_mod", '(pad "5"', '(pad "6"'),
        ("Package_TO_SOT_SMD.pretty/SOT-23.kicad_mod", '(pad "3"', '(pad "4"'),
        (
            "Capacitor_Tantalum_SMD.pretty/CP_EIA-3528-21_Kemet-B.kicad_mod",
            "(at -1.54 0)",
            "(at 1.54 0)",
        ),
        (
            "Capacitor_Tantalum_SMD.pretty/CP_EIA-7343-31_Kemet-D.kicad_mod",
            "(size 2.07 2.59)",
            "(size 0.2 0.2)",
        ),
        (
            "Connector_PinHeader_2.54mm.pretty/PinHeader_2x10_P2.54mm_Vertical.kicad_mod",
            "(drill 1)",
            "(drill 0.5)",
        ),
        (
            "Capacitor_SMD.pretty/C_0603_1608Metric.kicad_mod",
            "(size 0.9 0.95)",
            "(size 0.09 0.095)",
        ),
        (
            "Capacitor_SMD.pretty/C_0805_2012Metric.kicad_mod",
            '"F.Cu" "F.Mask" "F.Paste"',
            '"B.Cu" "B.Mask" "B.Paste"',
        ),
        ("Resistor_SMD.pretty/R_0603_1608Metric.kicad_mod", "(at -0.825 0)", "(at -0.0825 0)"),
    ],
    ids=[
        "ads-pad",
        "ldo-pad",
        "diode-pad",
        "ref-polarity",
        "vcap-land",
        "header-hole",
        "0603-land",
        "0805-layer",
        "resistor-spacing",
    ],
)
def test_snapshot_rejects_same_name_but_wrong_pad_geometry(
    tmp_path: Path, relative: str, before: str, after: str
) -> None:
    library = write_footprint_library(tmp_path / "footprints")
    path = library / relative
    text = path.read_text()
    assert before in text
    path.write_text(text.replace(before, after, 1))
    with pytest.raises(ValueError, match="footprint"):
        schematic_source_snapshot(CAD, library)


def test_canonical_footprints_remain_readable(tmp_path: Path) -> None:
    assert len(schematic_source_snapshot(CAD, write_footprint_library(tmp_path))) == 16
