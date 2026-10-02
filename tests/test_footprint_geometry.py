"""Pad geometry must be checked, not merely hashed under a plausible filename."""

import shutil
from pathlib import Path

import pytest

from hardware.rev_a import schematic_source_snapshot
from tests.footprint_fixtures import footprint_sources, write_footprint_library

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
            "RevA_Passives.pretty/T491B_3528_DensityB.kicad_mod",
            "(at -1.46 0)",
            "(at 1.46 0)",
        ),
        (
            "RevA_Passives.pretty/T491D_7343_DensityB.kicad_mod",
            "(size 2.37 2.43)",
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
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    path = (cad if relative.startswith("RevA_Passives.pretty/") else library) / relative
    text = path.read_text()
    assert before in text
    path.write_text(text.replace(before, after, 1))
    with pytest.raises(ValueError, match="footprint"):
        schematic_source_snapshot(cad, library)


def test_canonical_footprints_remain_readable(tmp_path: Path) -> None:
    assert len(schematic_source_snapshot(CAD, write_footprint_library(tmp_path))) == 17


def _footprints() -> list[tuple[str, str]]:
    return list(footprint_sources().items())


@pytest.mark.parametrize(("footprint", "content"), _footprints(), ids=[p[0] for p in _footprints()])
def test_every_numbered_pad_is_independently_required(footprint: str, content: str) -> None:
    from hardware.rev_a import validate_footprint

    pads = validate_footprint(footprint, content)
    for pad in pads:
        changed = content.replace(f'(pad "{pad.number}"', '(pad "999"', 1)
        assert changed != content
        with pytest.raises(ValueError, match="footprint pad numbers"):
            validate_footprint(footprint, changed)


@pytest.mark.parametrize(("footprint", "content"), _footprints(), ids=[p[0] for p in _footprints()])
def test_geometry_is_not_a_text_hash_allowlist(footprint: str, content: str) -> None:
    from hardware.rev_a import validate_footprint

    original = validate_footprint(footprint, content)
    # Formatting, equivalent numbers and display labels are not copper geometry.
    changed = content.replace("\t", "  ").replace('"REF**"', '"READ_ONLY_REVIEW"')
    changed = changed.replace("(size 0.9 0.95)", "(size 9e-1 0.9500)")
    assert validate_footprint(footprint, changed) == original


@pytest.mark.parametrize(("footprint", "content"), _footprints(), ids=[p[0] for p in _footprints()])
def test_only_nonpolar_components_accept_pad_one_two_swap(footprint: str, content: str) -> None:
    from hardware.rev_a import validate_footprint

    changed = content.replace('(pad "1"', '(pad "temporary"').replace('(pad "2"', '(pad "1"')
    changed = changed.replace('(pad "temporary"', '(pad "2"')
    nonpolar = footprint.startswith(("Capacitor_SMD:", "Resistor_SMD:"))
    if nonpolar:
        assert len(validate_footprint(footprint, changed)) == 2
    else:
        with pytest.raises(ValueError, match="geometry differs"):
            validate_footprint(footprint, changed)


@pytest.mark.parametrize(
    ("before", "after"),
    [
        ('(footprint "C_0603_1608Metric"', '(footprint "wrong"'),
        ('(layer "F.Cu")', '(layer "B.Cu")'),
        ("(attr smd)", "(attr through_hole)"),
        ("(attr smd)", "(attr smd) (attr smd)"),
        ("(at -0.775 0)", "(at nan 0)"),
        ("(at -0.775 0)", "(at inf 0)"),
        ("(at -0.775 0)", "(at not-a-number 0)"),
        ("(at -0.775 0)", "(at -0.775)"),
        ("(at -0.775 0)", "(at -0.775 0 45)"),
        ("(at -0.775 0)", "(at -0.775 0) (at -0.775 0)"),
        ("(size 0.9 0.95)", "(size -0.9 0.95)"),
        ("(size 0.9 0.95)", "(size 0 0.95)"),
        ("(size 0.9 0.95)", "(size (hidden 0.9) 0.95)"),
        ("(size 0.9 0.95)", "(size 0.9 0.95) (offset 2 0)"),
        ("(roundrect_rratio 0.25)", "(roundrect_rratio 0.5)"),
        ("smd roundrect", "smd custom"),
        ("(attr smd)", "(attr smd) (solder_mask_margin -1)"),
        ('(layers "F.Cu" "F.Mask" "F.Paste")', '(layers "F.Cu" "F.Mask" "F.Mask")'),
        ('(layer "F.SilkS")', '(layer "F.Cu")'),
    ],
)
def test_unsupported_or_wrong_copper_definition_fails_closed(before: str, after: str) -> None:
    from hardware.rev_a import validate_footprint

    footprint, content = _footprints()[0]
    assert before in content
    with pytest.raises(ValueError, match="footprint"):
        validate_footprint(footprint, content.replace(before, after, 1))


def test_rotated_rectangle_with_swapped_size_preserves_copper() -> None:
    from hardware.rev_a import validate_footprint

    footprint, content = _footprints()[0]
    changed = content.replace("(at -0.775 0)", "(at -0.775 0 90)", 1)
    changed = changed.replace("(size 0.9 0.95)", "(size 0.95 0.9)", 1)
    assert validate_footprint(footprint, changed) == validate_footprint(footprint, content)


@pytest.mark.parametrize("content", ["", "plain", "()", "(footprint", '"unterminated', "(" * 65])
def test_malformed_structure_is_not_accepted(content: str) -> None:
    from hardware.rev_a import validate_footprint

    with pytest.raises(ValueError, match="footprint"):
        validate_footprint("Capacitor_SMD:C_0603_1608Metric", content)


def test_unknown_library_id_cannot_select_a_reviewed_pad_shape() -> None:
    from hardware.rev_a import validate_footprint

    with pytest.raises(ValueError, match="outside"):
        validate_footprint("Unknown:C_0603_1608Metric", _footprints()[0][1])
