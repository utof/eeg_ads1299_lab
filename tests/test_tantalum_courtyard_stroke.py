"""The local courtyard's rendered outline is part of its closed design contract."""

from pathlib import Path

import pytest

from hardware.rev_a import validate_footprint

CAD = Path(__file__).resolve().parents[1] / "hardware/rev_a/kicad/RevA_Passives.pretty"
STROKE = "(stroke (width 0.05) (type default))"


@pytest.mark.parametrize("name", ["T491B_3528_DensityB", "T491D_7343_DensityB"])
@pytest.mark.parametrize(
    "replacement",
    [
        "(stroke (width 10) (type default))",
        "",
        STROKE + " " + STROKE,
        "(stroke (width 0.05) (type dash))",
        "(stroke (width 0.05) (width 10) (type default))",
        "(stroke (width 0.05) (type default) (unreviewed 1))",
    ],
    ids=["wide", "absent", "duplicate", "dashed", "duplicate-width", "extra-field"],
)
def test_local_courtyard_rejects_wrong_stroke(name: str, replacement: str) -> None:
    content = (CAD / (name + ".kicad_mod")).read_text()
    assert content.count(STROKE) == 1
    with pytest.raises(ValueError, match="footprint"):
        validate_footprint("RevA_Passives:" + name, content.replace(STROKE, replacement, 1))


@pytest.mark.parametrize("name", ["T491B_3528_DensityB", "T491D_7343_DensityB"])
def test_equivalent_stroke_order_and_numeric_spelling_remain_acceptable(name: str) -> None:
    content = (CAD / (name + ".kicad_mod")).read_text()
    changed = content.replace(STROKE, "(stroke (type default) (width 5e-2))", 1)
    assert validate_footprint("RevA_Passives:" + name, changed) == validate_footprint(
        "RevA_Passives:" + name, content
    )
