"""A timing hypothesis is explicit, not a hidden ADS startup specification."""

import json
import math
import shutil
import sys
from dataclasses import FrozenInstanceError, asdict, replace
from pathlib import Path
from typing import cast

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from lab.analog import run_ngspice_transient
from lab.rev_a_supply import (
    SupplyCase,
    SupplyTiming,
    main,
    rail_response,
    source_voltage_window,
    supply_netlist,
)
from lab.validation import float_array, read_object

LIMITS = (4.75, 5.25)


def test_default_schedule_preserves_existing_public_calculations() -> None:
    timing = SupplyTiming()
    assert asdict(timing) == {
        "source_on_s": 0.001,
        "burst_on_s": 0.008,
        "burst_off_s": 0.012,
        "stop_s": 0.02,
        "observation_s": (0.004, 0.02),
    }
    case = SupplyCase()
    times = np.linspace(0, 0.02, 1001)
    np.testing.assert_array_equal(
        rail_response(case, times), rail_response(case, times, timing=timing)
    )
    assert supply_netlist(case) == supply_netlist(case, timing=timing)
    assert source_voltage_window(case, LIMITS) == source_voltage_window(case, LIMITS, timing=timing)
    with pytest.raises(FrozenInstanceError):
        field = "stop_s"
        setattr(timing, field, 1.0)


def test_observation_change_does_not_change_the_physical_trajectory() -> None:
    case = replace(SupplyCase(), shared_r_ohm=0.0, analog_g_s=0.0, capacitance_f=100e-6)
    early = SupplyTiming(observation_s=(0.002, 0.003))
    late = replace(early, observation_s=(0.006, 0.007))
    times = np.linspace(0, 0.02, 1001)
    np.testing.assert_array_equal(
        rail_response(case, times, timing=early), rail_response(case, times, timing=late)
    )
    assert supply_netlist(case, timing=early) == supply_netlist(case, timing=late)
    for timing in (early, late):
        begin, end = timing.observation_s
        # Independent unloaded RC, no upstream attenuation or MCU influence.
        expected = (
            4.75 / -math.expm1(-(begin - 0.001) / 0.001),
            5.25 / -math.expm1(-(end - 0.001) / 0.001),
        )
        assert source_voltage_window(case, LIMITS, timing=timing) == pytest.approx(
            expected, rel=1e-13
        )


@pytest.mark.parametrize("window", [(0.004, 0.006), (0.009, 0.010), (0.014, 0.018), (0.007, 0.014)])
def test_only_events_inside_the_requested_window_constrain_the_source(
    window: tuple[float, float],
) -> None:
    timing = SupplyTiming(observation_s=window)
    case = replace(SupplyCase(), shared_r_ohm=1.0, capacitance_f=100e-6)
    times = np.unique(
        np.concatenate(
            (np.linspace(*window, 1001), [x for x in (0.008, 0.012) if window[0] < x < window[1]])
        )
    )
    unit = rail_response(replace(case, source_v=1.0), times, timing=timing)
    expected = (4.75 / float(unit.min()), 5.25 / float(unit.max()))
    assert source_voltage_window(case, LIMITS, timing=timing) == pytest.approx(expected, rel=1e-13)


def test_discarding_the_pulse_minimum_would_falsely_accept_a_source() -> None:
    case = replace(SupplyCase(), shared_r_ohm=1.0, capacitance_f=100e-6)
    timing = SupplyTiming(
        burst_on_s=0.01, burst_off_s=0.017, stop_s=0.03, observation_s=(0.007, 0.028)
    )
    endpoints = rail_response(case, np.array(timing.observation_s), timing=timing)
    minimum = float(rail_response(case, np.array([0.017]), timing=timing)[0])
    assert minimum < endpoints.min() - 0.1
    required, _ = source_voltage_window(case, LIMITS, timing=timing)
    assert required == pytest.approx(case.source_v * 4.75 / minimum, abs=1e-12)


def test_larger_capacitor_failure_at_four_ms_is_not_a_universal_capacitor_failure() -> None:
    case = replace(SupplyCase(), capacitance_f=100e-6)
    early = source_voltage_window(case, LIMITS)
    late = source_voltage_window(case, LIMITS, timing=SupplyTiming(observation_s=(0.006, 0.02)))
    assert early[0] > 5.05
    assert late[0] <= 4.95 <= 5.05 <= late[1]
    # A later observation window cannot fix a sustained large shared-resistance loss.
    soft = replace(case, shared_r_ohm=1.0)
    assert (
        source_voltage_window(soft, LIMITS, timing=SupplyTiming(observation_s=(0.006, 0.02)))[0]
        > 5.05
    )


@settings(max_examples=30, derandomize=True, deadline=None)
@given(scale=st.floats(0.5, 5), shift=st.floats(0, 0.02))
def test_time_translation_and_rc_scaling_preserve_the_entire_response(
    scale: float, shift: float
) -> None:
    case = replace(SupplyCase(), shared_r_ohm=0.5, capacitance_f=100e-6)
    timing = SupplyTiming(
        source_on_s=0.001 * scale + shift,
        burst_on_s=0.008 * scale + shift,
        burst_off_s=0.012 * scale + shift,
        stop_s=0.02 * scale + shift,
        observation_s=(0.004 * scale + shift, 0.02 * scale + shift),
    )
    times = np.array([0.002, 0.004, 0.006, 0.01, 0.014, 0.02])
    scaled = replace(case, capacitance_f=case.capacitance_f * scale)
    np.testing.assert_allclose(
        rail_response(scaled, times * scale + shift, timing=timing),
        rail_response(case, times),
        atol=1e-12,
        rtol=1e-12,
    )
    assert source_voltage_window(scaled, LIMITS, timing=timing) == pytest.approx(
        source_voltage_window(case, LIMITS), abs=1e-11
    )


def _invalid_timing(changes: dict[str, object]) -> SupplyTiming:
    # Casts intentionally deliver invalid runtime values to the constructor.
    return SupplyTiming(
        source_on_s=cast(float, changes.get("source_on_s", 0.001)),
        burst_on_s=cast(float, changes.get("burst_on_s", 0.008)),
        burst_off_s=cast(float, changes.get("burst_off_s", 0.012)),
        stop_s=cast(float, changes.get("stop_s", 0.02)),
        observation_s=cast(tuple[float, float], changes.get("observation_s", (0.004, 0.02))),
    )


@pytest.mark.parametrize("field", ["source_on_s", "burst_on_s", "burst_off_s", "stop_s"])
@pytest.mark.parametrize("bad", [True, float("nan"), float("inf"), -1.0])
def test_invalid_timing_numbers_fail_before_solving(field: str, bad: float) -> None:
    with pytest.raises(ValueError):
        _invalid_timing({field: bad})


@pytest.mark.parametrize(
    "changes",
    [
        {"source_on_s": 0.008},
        {"burst_on_s": 0.012},
        {"burst_off_s": 0.02},
        {"burst_on_s": 0.001 + 1e-10},
        {"observation_s": (0.0, 0.02)},
        {"observation_s": (0.02, 0.004)},
        {"observation_s": (0.004, 0.021)},
        {"observation_s": (0.004,)},
        {"observation_s": [0.004, 0.02]},
        {"observation_s": (True, 0.02)},
        {"observation_s": (0.004, float("nan"))},
    ],
)
def test_invalid_order_or_observation_window_is_rejected(changes: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        _invalid_timing(changes)


def test_nondefault_timing_rejects_queries_past_its_stop() -> None:
    timing = SupplyTiming(
        burst_on_s=0.003, burst_off_s=0.005, stop_s=0.01, observation_s=(0.004, 0.01)
    )
    with pytest.raises(ValueError, match="times"):
        rail_response(SupplyCase(), np.array([0.009, 0.011]), timing=timing)


@pytest.mark.native
@pytest.mark.parametrize("window", [(0.004, 0.006), (0.013, 0.015), (0.024, 0.029)])
def test_nondefault_native_pulse_and_both_source_boundaries(
    tmp_path: Path, window: tuple[float, float]
) -> None:
    assert shutil.which("ngspice"), "native gate requires an actual simulator"
    timing = SupplyTiming(
        source_on_s=0.002, burst_on_s=0.011, burst_off_s=0.019, stop_s=0.03, observation_s=window
    )
    case = replace(SupplyCase(), shared_r_ohm=0.5, capacitance_f=100e-6)
    bounds = source_voltage_window(case, LIMITS, timing=timing)
    grid = np.unique(
        np.concatenate(
            (np.linspace(*window, 101), [x for x in (0.011, 0.019) if window[0] < x < window[1]])
        )
    )
    for i, source in enumerate(bounds):
        out = tmp_path / str(i)
        out.mkdir()
        text = supply_netlist(replace(case, source_v=source), timing=timing)
        netlist = out / "network.cir"
        netlist.write_text(text)
        times, volts = run_ngspice_transient(
            netlist, out, columns=1, expected_stop_s=0.03, expected_vectors=("v(avdd)",)
        )
        expected = rail_response(replace(case, source_v=source), times, timing=timing)
        np.testing.assert_allclose(volts[:, 0], expected, atol=1e-4, rtol=0)
        raw: object = np.interp(grid, times, volts[:, 0])
        observed = float_array(raw)
        assert (observed.min() if i == 0 else observed.max()) == pytest.approx(LIMITS[i], abs=1e-4)


@pytest.mark.native
def test_cli_carries_timing_and_full_source_band_into_fresh_native_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert shutil.which("ngspice"), "native gate requires an actual simulator"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "supply",
            "--out",
            str(tmp_path),
            "--source-on-ms",
            "2",
            "--burst-on-ms",
            "11",
            "--burst-off-ms",
            "19",
            "--stop-ms",
            "30",
            "--observe-ms",
            "7",
            "28",
        ],
    )
    assert main() == 0
    report = read_object(json.loads(next(tmp_path.glob("*/study.json")).read_text()), "report")
    assert report["timing"] == {
        "source_on_s": 0.002,
        "burst_on_s": 0.011,
        "burst_off_s": 0.019,
        "stop_s": 0.03,
        "observation_s": [0.007, 0.028],
    }
    assert report["margin_window_s"] == [0.007, 0.028]
    assert report["configured_source_range_v"] == [4.95, 5.05]
    assert report["hardware_validated"] is False
    cases = cast(list[dict[str, object]], report["cases"])
    assert len(cases) == 5
    for row in cases:
        low, high = cast(list[float], row["model_source_window_v"])
        assert row["model_source_range_covered"] is (low <= 4.95 and high >= 5.05)
        assert row["native_comparison_passed"] is True


def test_invalid_cli_timing_cannot_create_a_new_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys, "argv", ["supply", "--out", str(tmp_path), "--observe-ms", "19", "5"])
    assert main() == 1
    assert not list(tmp_path.iterdir())


def test_a_feasible_source_and_low_endpoint_pass_do_not_cover_the_full_source_band(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from lab.rev_a_supply import run_supply_study

    def constrained_window(
        _case: SupplyCase, _limits: tuple[float, float], *, timing: SupplyTiming
    ) -> tuple[float, float]:
        return 4.8, 5.0

    def rejected(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("software-only publication double; no simulator")

    monkeypatch.setattr("lab.rev_a_supply.source_voltage_window", constrained_window)
    monkeypatch.setattr("lab.rev_a_supply.run_ngspice_transient", rejected)
    with pytest.raises(RuntimeError, match="retained"):
        run_supply_study(tmp_path)
    report = read_object(json.loads(next(tmp_path.glob("*/study.json")).read_text()), "report")
    cases = cast(list[dict[str, object]], report["cases"])
    stiff = cases[0]
    assert stiff["model_margin_ok"] is True  # Actual model at source=4.95 V passes.
    assert stiff["model_source_window_feasible"] is True
    assert stiff["model_source_range_covered"] is False  # The 5.05 V end was NOT covered.
    assert stiff["native_comparison_passed"] is False  # Never call the double native evidence.
