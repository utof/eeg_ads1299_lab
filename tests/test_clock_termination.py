"""Passive ADS clock termination is a schematic contract, not GPIO evidence."""

import copy

import pytest

from hardware.rev_a import load_documents, validate


def test_external_clock_pin_has_declared_low_termination() -> None:
    profile, bom, _sources = load_documents()
    # Deliberately use independent datasheet pin expectations, not a GPIO map.
    assert profile["afe"].get("clock_input_pull") == {
        "ads_pin": 37,
        "reference": "R_CLK_DN",
        "return_net": "DGND",
    }
    straps = next(row for row in bom["line_items"] if row["id"] == "straps")
    assert straps["quantity"] == 13
    assert "R_CLK_DN" in straps["references"]
    assert straps["spec"]["resistance_ohm"] == 10000
    assert straps["population"] == "fit"


@pytest.mark.parametrize(
    "fault", ["missing-resistor", "pull-up", "dnp", "wrong-value", "clock-output"]
)
def test_passive_clock_faults_rejected(fault: str) -> None:
    profile, bom, sources = copy.deepcopy(load_documents())
    straps = next(row for row in bom["line_items"] if row["id"] == "straps")
    if fault in {"missing-resistor", "pull-up"}:
        refs = straps["references"]
        assert "R_CLK_DN" in refs, "clock termination not implemented"
        refs[refs.index("R_CLK_DN")] = "R_SPARE" if fault == "missing-resistor" else "R_CLK_UP"
    elif fault == "dnp":
        straps["population"] = "dnp"
    elif fault == "wrong-value":
        straps["spec"]["resistance_ohm"] = 0
    else:
        profile["afe"]["clock_output_enabled"] = True
    assert any("clock" in message.lower() for message in validate(profile, bom, sources))
