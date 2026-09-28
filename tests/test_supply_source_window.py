"""Invert the existing rail hypothesis, without approving a supply or capacitor."""

import math
import shutil
from dataclasses import replace
from pathlib import Path
from typing import cast

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from lab.analog import run_ngspice_transient
from lab.rev_a_supply import SupplyCase, rail_response, source_voltage_window, supply_netlist
from lab.validation import float_array

LIMITS = (4.75, 5.25)


def test_stiff_unloaded_rc_has_an_independent_closed_form_window() -> None:
    case = SupplyCase(
        shared_r_ohm=0.0, analog_g_s=0.0, idle_g_s=0.0, burst_g_s=0.0, capacitance_f=100e-6
    )
    # Source turns on at 1 ms. The margin interval is 4..20 ms, not from time zero.
    low, high = source_voltage_window(case, LIMITS)
    assert low == pytest.approx(4.75 / -math.expm1(-0.003 / 0.001), rel=1e-13)
    assert high == pytest.approx(5.25 / -math.expm1(-0.019 / 0.001), rel=1e-13)


def test_slow_start_can_make_the_entire_source_window_empty() -> None:
    case = SupplyCase(
        shared_r_ohm=0.0, analog_g_s=0.0, idle_g_s=0.0, burst_g_s=0.0, capacitance_f=1e-3
    )
    low, high = source_voltage_window(case, LIMITS)
    assert low > high  # Not sorted into a false feasible interval.
    assert low == pytest.approx(4.75 / -math.expm1(-0.3))
    assert high == pytest.approx(5.25 / -math.expm1(-1.9))


@pytest.mark.parametrize("source", [0.1, 4.95, 100.0])
def test_inverse_window_does_not_depend_on_the_forward_source_setting(source: float) -> None:
    case = replace(SupplyCase(), source_v=source)
    assert source_voltage_window(case, LIMITS) == source_voltage_window(SupplyCase(), LIMITS)


@pytest.mark.parametrize("shared", [0.0, 0.1, 0.5, 1.0])
def test_fast_settled_case_matches_direct_two_node_dc_dividers(shared: float) -> None:
    case = replace(SupplyCase(), shared_r_ohm=shared, capacitance_f=1e-6)
    # Direct two-node KCL denominator: Vs/Vrail = (1+Rf*Ga)*(1+Rs*Gm)+Rs*Ga.
    idle_den = (1 + 10 * 0.002) * (1 + shared * 0.02) + shared * 0.002
    burst_den = (1 + 10 * 0.002) * (1 + shared * 0.10) + shared * 0.002
    low, high = source_voltage_window(case, LIMITS)
    assert low == pytest.approx(4.75 * burst_den, abs=1e-11)
    assert high == pytest.approx(5.25 * idle_den, abs=1e-11)


@pytest.mark.parametrize(
    "bad",
    [
        (),
        (4.75,),
        (4.75, 5.25, 6.0),
        [4.75, 5.25],
        (0, 5),
        (-1, 5),
        (5.25, 4.75),
        (True, 5.25),
        (4.75, float("nan")),
        (float("inf"), 5.25),
    ],
)
def test_invalid_limits_cannot_return_a_source_requirement(bad: object) -> None:
    with pytest.raises(ValueError):
        source_voltage_window(SupplyCase(), cast(tuple[float, float], bad))


def test_underflowed_response_cannot_publish_infinite_or_zero_requirements() -> None:
    with pytest.raises(ValueError, match="numerical"):
        source_voltage_window(replace(SupplyCase(), capacitance_f=1e308), LIMITS)


def test_finite_forward_response_but_unrepresentable_inverse_is_rejected() -> None:
    with pytest.raises(ValueError, match="numerical"):
        source_voltage_window(replace(SupplyCase(), capacitance_f=1e300), (1e307, 1e308))


@settings(max_examples=40, derandomize=True, deadline=None)
@given(shared=st.floats(0, 1.0), cap=st.floats(1e-6, 200e-6))
def test_window_is_necessary_and_sufficient_for_the_continuous_model(
    shared: float, cap: float
) -> None:
    case = replace(SupplyCase(), shared_r_ohm=shared, capacitance_f=cap)
    low, high = source_voltage_window(case, LIMITS)
    # Dense observations plus exact switching/window edges: not just final/DC state.
    times = np.unique(np.concatenate((np.linspace(0.004, 0.02, 1001), [0.008, 0.012])))
    for source in (low, high, (low + high) / 2, low * 0.99, high * 1.01):
        trace = rail_response(replace(case, source_v=source), times)
        actual = np.min(trace) >= 4.75 - 1e-12 and np.max(trace) <= 5.25 + 1e-12
        assert bool(actual) == (low <= source <= high)


@pytest.mark.native
@pytest.mark.parametrize("bound", ["low", "high"])
@pytest.mark.parametrize("shared,cap", [(0.1, 10e-6), (0.5, 100e-6)])
def test_source_bound_agrees_with_unreduced_native_network(
    tmp_path: Path, bound: str, shared: float, cap: float
) -> None:
    if shutil.which("ngspice") is None:
        pytest.skip("ngspice unavailable; --native rejects absence")
    case = replace(SupplyCase(), shared_r_ohm=shared, capacitance_f=cap)
    limits = source_voltage_window(case, LIMITS)
    chosen = limits[0 if bound == "low" else 1]
    # Center and outward 20 mV perturbation prove the limiting endpoint is active.
    for name, delta in [("boundary", 0.0), ("outside", -0.02 if bound == "low" else 0.02)]:
        out = tmp_path / name
        out.mkdir()
        netlist = out / "network.cir"
        netlist.write_text(supply_netlist(replace(case, source_v=chosen + delta)))
        times, volts = run_ngspice_transient(
            netlist, out, columns=1, expected_stop_s=0.02, expected_vectors=("v(avdd)",)
        )
        grid = np.array([0.004, 0.008, 0.012, 0.02])
        raw: object = np.interp(grid, times, volts[:, 0])
        measured = float_array(raw)
        limiting = float(np.min(measured) if bound == "low" else np.max(measured))
        target = LIMITS[0 if bound == "low" else 1]
        if name == "boundary":
            assert limiting == pytest.approx(target, abs=1e-4)
        elif bound == "low":
            assert limiting < target - 0.005
        else:
            assert limiting > target + 0.005
