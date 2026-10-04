"""S2 mean-load and two-node return arithmetic, not hardware qualification."""

import math
from pathlib import Path

import pytest

from tools import dc_budget

ROOT = Path(__file__).resolve().parents[1]


def test_resistive_and_capacitive_loads_are_separate() -> None:
    # 3V/10kohm * 0.015 = 4.5uA; 100pF*3V*30000 rising edges/s = 9uA.
    pull, charging = dc_budget.switched_load(3.0, 10000.0, 0.015, 100e-12, 30000.0)
    assert (pull, charging) == pytest.approx((4.5e-6, 9e-6))
    # No factor of two: falling edges dissipate already stored charge.
    assert dc_budget.switched_load(3.0, 10000.0, 0.5, 100e-12, 1e6) == pytest.approx(
        (150e-6, 300e-6)
    )


def test_static_high_still_loads_supply_without_clock_activity() -> None:
    assert dc_budget.switched_load(3.3, 33000.0, 1.0, 100e-12, 0.0) == pytest.approx((100e-6, 0.0))
    assert dc_budget.switched_load(3.3, 33000.0, 0.0, 0.0, 0.0) == (0.0, 0.0)


def test_parallel_returns_use_conductance_not_wire_count() -> None:
    # Ten 0.2ohm paths + two 0.1ohm paths => 70S, 14mA/70S = 0.2mV.
    resistances = {**{f"K1-{i}": 0.2 for i in range(10)}, "C4-1": 0.1, "C4-5": 0.1}
    shift, currents = dc_budget.parallel_returns(resistances, 0.014)
    assert shift == pytest.approx(0.0002)
    assert currents["K1-0"] == pytest.approx(0.001)
    assert currents["C4-1"] == pytest.approx(0.002)
    assert sum(currents.values()) == pytest.approx(0.014)
    assert dc_budget.parallel_returns({"combined": 1 / 70}, 0.014)[0] == pytest.approx(shift)
    opposite, reverse = dc_budget.parallel_returns(resistances, -0.014)
    assert opposite == pytest.approx(-shift)
    assert reverse == pytest.approx({k: -v for k, v in currents.items()})


@pytest.mark.parametrize("bad", [math.nan, math.inf, -1.0, True])
def test_nonphysical_switched_load_parameters_rejected(bad: float) -> None:
    for index in range(5):
        args = [3.3, 42200.0, 0.5, 100e-12, 30000.0]
        args[index] = bad
        with pytest.raises(ValueError):
            dc_budget.switched_load(*args)
    with pytest.raises(ValueError):
        dc_budget.parallel_returns({"wire": bad}, 0.001)


def test_impossible_fraction_zero_resistance_empty_paths_and_overflow_rejected() -> None:
    for args in [(3.3, 0.0, 0.5, 0.0, 0.0), (3.3, 1.0, 1.01, 0.0, 0.0)]:
        with pytest.raises(ValueError):
            dc_budget.switched_load(*args)
    for resistances in ({}, {"wire": 0.0}):
        with pytest.raises(ValueError):
            dc_budget.parallel_returns(resistances, 0.0)
    for current in (math.nan, math.inf, True):
        with pytest.raises(ValueError):
            dc_budget.parallel_returns({"wire": 1.0}, current)
    with pytest.raises(ValueError):
        dc_budget.switched_load(1e300, 1.0, 1.0, 1e300, 1.0)
    with pytest.raises(ValueError):
        dc_budget.parallel_returns({"wire": 1e300}, 1e300)


def test_documented_s2_calculation_executes() -> None:
    import re

    path = ROOT / "docs/REV_A_CURRENT_RETURN_S2.md"
    assert path.is_file(), "missing executable mode/current/return study"
    assert len(re.findall(r"```python\n(.*?)\n```", path.read_text(), re.DOTALL)) == 1
