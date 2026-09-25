"""Regression cases from the independent PR review, not physical model evidence."""

from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from lab.data_types import FloatArray
from lab.rev_a_bias import load_bias_model
from lab.rev_a_bias_overload import (
    InterferencePulse,
    OutputLimits,
    overload_response,
    run_overload_study,
)


@pytest.mark.parametrize("fault", ["sparse", "missing_interior", "irregular"])
def test_sparse_native_endpoints_cannot_publish_comparison(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    def endpoints(
        _netlist: Path, _out: Path, *, columns: int, expected_stop_s: float
    ) -> tuple[FloatArray, FloatArray]:
        assert expected_stop_s == 0.035
        times = np.linspace(0.0, 0.035, 17501)
        if fault == "sparse":
            times = times[[0, -1]]
        elif fault == "missing_interior":
            times = np.delete(times, 501)
        else:
            times[501] = float(times[501]) + 0.1e-6
        return times, np.zeros((len(times), columns), dtype=np.float64)

    monkeypatch.setattr("lab.rev_a_bias_overload.run_ngspice_transient", endpoints)
    with pytest.raises(RuntimeError, match="grid"):
        run_overload_study(tmp_path, require_ngspice=True, run_id="e" * 32)
    assert not (tmp_path / ("e" * 32) / "manifest.json").exists()


@pytest.mark.parametrize("rail", [1e-12, 1e-9, 1e-6])
def test_unresolvable_rail_scale_is_rejected(rail: float) -> None:
    with pytest.raises(ValueError, match="millivolt"):
        OutputLimits(lower_v=-rail, upper_v=rail)


def test_endpoint_event_is_recorded_and_snap_preserves_feedback_charge(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    received: list[FloatArray] = []

    def solver(
        _fun: object, span: tuple[float, float], initial: FloatArray, **_kwargs: object
    ) -> SimpleNamespace:
        received.append(initial.copy())
        state = initial.copy()
        first = len(received) == 1
        if first:
            state[10], state[11] = 0.1, -2.0 - 1e-9

        def sample(times: FloatArray) -> FloatArray:
            return np.repeat(state[:, None], len(times), axis=1)

        return SimpleNamespace(
            success=True,
            message="synthetic endpoint event",
            status=1 if first else 0,
            t=np.array([span[0], span[1]]),
            y=np.column_stack((initial, state)),
            sol=sample,
        )

    monkeypatch.setattr("lab.rev_a_bias_overload.solve_ivp", solver)
    trace = overload_response(np.array([0.0, 0.035]), load_bias_model(), InterferencePulse())
    assert trace.rail_events[0] == (0.001, "lower")
    assert received[1][10] - received[1][11] == pytest.approx(0.1 - (-2.0 - 1e-9), abs=1e-14)
