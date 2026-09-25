"""Focused regressions from the independent review; fixtures are not native evidence."""

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Literal

import numpy as np
import pytest
from scipy.integrate import solve_ivp

from lab.data_types import FloatArray
from lab.rev_a_bias import load_bias_model
from lab.rev_a_bias_overload import (
    InterferencePulse,
    OutputLimits,
    overload_response,
    run_overload_study,
)


@pytest.mark.parametrize("rail", [1e-12, 1e-10, 1e-8])
def test_rails_below_supported_numerical_scale_are_rejected(rail: float) -> None:
    with pytest.raises(ValueError, match="numerical"):
        OutputLimits(lower_v=-rail, upper_v=rail)


@pytest.mark.parametrize("grid", ["endpoints", "missing_interval", "shifted"])
def test_native_grid_cannot_omit_pulse_or_switching_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, grid: str
) -> None:
    def incomplete(
        netlist: Path,
        _out: Path,
        *,
        columns: int,
        expected_stop_s: float | None = None,
    ) -> tuple[FloatArray, FloatArray]:
        assert columns == 3 and expected_stop_s in (None, 0.035)
        # Values match the requested model exactly, but the sampling contract is wrong.
        times = np.linspace(0, 0.035, 17501)
        if grid == "endpoints":
            times = times[[0, -1]]
        elif grid == "missing_interval":
            times = times[(times < 0.001) | (times > 0.008)]
        else:
            times[100] = float(times[100]) + 1e-7
        model = load_bias_model()
        pulse = InterferencePulse(amplitude_a=1e-9)
        values = overload_response(times, model, pulse).state_v[:, [1, 11, 10]]
        assert netlist.parent.parent.name == "small_signal", "incomplete first trace was accepted"
        return times, values

    monkeypatch.setattr("lab.rev_a_bias_overload.run_ngspice_transient", incomplete)
    with pytest.raises(RuntimeError, match="observation grid"):
        run_overload_study(tmp_path, require_ngspice=True, run_id="d" * 32)
    assert not (tmp_path / ("d" * 32) / "manifest.json").exists()


@pytest.mark.parametrize("boundary", ["hit", "release"])
def test_event_at_segment_endpoint_is_not_dropped(
    monkeypatch: pytest.MonkeyPatch, boundary: str
) -> None:
    model = load_bias_model()
    original = overload_response(np.array([0.0, 0.035]), model, InterferencePulse())
    pulse = (
        InterferencePulse(off_s=original.rail_events[0][0])
        if boundary == "hit"
        else InterferencePulse()
    )
    stop = 0.035 if boundary == "hit" else original.rail_events[1][0]
    rounded = False

    def integrate(
        fun: Callable[[float, FloatArray], FloatArray],
        span: tuple[float, float],
        initial: FloatArray,
        *,
        method: Literal["Radau"],
        rtol: float,
        atol: float,
        max_step: float,
        events: Sequence[Callable[[float, FloatArray], float]],
        dense_output: bool,
    ) -> object:
        nonlocal rounded
        result = solve_ivp(
            fun,
            span,
            initial,
            method=method,
            rtol=rtol,
            atol=atol,
            max_step=max_step,
            events=events,
            dense_output=dense_output,
        )
        if result.status == 1 and abs(float(result.t[-1]) - span[1]) < 2e-12:
            # Exercise the valid solver case event_time == segment_end. This rounds
            # a sub-picosecond endpoint residual, not a different physical trajectory.
            result.t[-1] = span[1]
            rounded = True
        return result

    monkeypatch.setattr("lab.rev_a_bias_overload.solve_ivp", integrate)
    trace = overload_response(np.array([0.0, stop]), model, pulse)
    assert rounded
    assert [event[1] for event in trace.rail_events] == ["lower", "release"]
    if boundary == "hit":
        assert trace.rail_events[0][0] == pulse.off_s
    else:
        assert trace.rail_events[-1][0] == stop


def test_rail_snap_preserves_the_returned_capacitor_charge(monkeypatch: pytest.MonkeyPatch) -> None:
    previous_charge: float | None = None
    snaps = 0

    def integrate(
        fun: Callable[[float, FloatArray], FloatArray],
        span: tuple[float, float],
        initial: FloatArray,
        *,
        method: Literal["Radau"],
        rtol: float,
        atol: float,
        max_step: float,
        events: Sequence[Callable[[float, FloatArray], float]],
        dense_output: bool,
    ) -> object:
        nonlocal previous_charge, snaps
        if previous_charge is not None:
            assert float(initial[10]) - float(initial[11]) == pytest.approx(
                previous_charge, abs=1e-15
            )
            snaps += 1
        result = solve_ivp(
            fun,
            span,
            initial,
            method=method,
            rtol=rtol,
            atol=atol,
            max_step=max_step,
            events=events,
            dense_output=dense_output,
        )
        previous_charge = None
        if result.status == 1 and abs(abs(float(result.y[11, -1])) - 2.0) < 1e-10:
            # Inject a small root-state residual. The state snap must not change
            # the feedback charge represented by that returned numerical state.
            result.y[11, -1] = float(result.y[11, -1]) + 1e-8
            previous_charge = float(result.y[10, -1]) - float(result.y[11, -1])
        return result

    monkeypatch.setattr("lab.rev_a_bias_overload.solve_ivp", integrate)
    overload_response(np.array([0.0, 0.035]), load_bias_model(), InterferencePulse())
    assert snaps >= 1
