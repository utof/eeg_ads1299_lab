"""Electrical limits for C3 are conditional calculations, not hardware approval."""

from pathlib import Path

import pytest

from hardware.rev_a import load_documents

ROOT = Path(__file__).resolve().parents[1]
BUS_PULLS = (
    "R_CS_DN",
    "R_CLKSEL_DN",
    "R_RESET_DN",
    "R_PWDN_DN",
    "R_START_DN",
    "R_SCLK_DN",
    "R_DIN_DN",
)


@pytest.mark.parametrize("reference", BUS_PULLS)
def test_bus_pull_fits_both_loaded_high_and_disabled_low(reference: str) -> None:
    """TI 100-uA VOH row and ADC leakage must both work; bigger R is not free."""
    _, bom, _ = load_documents(ROOT / "hardware/rev_a")
    item = next(row for row in bom["line_items"] if reference in row["references"])
    resistance = item["spec"]["resistance_ohm"]
    # 1% initial + 100 ppm/K * 5 K for the declared 20--30 C bench target.
    r_min, r_max = resistance * 0.9895, resistance * 1.0105
    # ADS input: 10 uA max. Additional board leakage <=1 uA is a REQUIREMENT.
    enabled_current = 3.6 / r_min + 11e-6
    assert enabled_current <= 100e-6, "outside the cited TXU near-rail VOH load row"
    # 2.5 uA is the conservative TXU off-state current; not a ramp guarantee.
    assert (10e-6 + 2.5e-6 + 1e-6) * r_max < 0.2 * 3.0
    assert item["population"] == "fit"


def test_auxiliary_native_source_exists_separately_from_the_afe() -> None:
    assert (ROOT / "hardware/rev_a/auxiliary/auxiliary.kicad_sch").is_file()
