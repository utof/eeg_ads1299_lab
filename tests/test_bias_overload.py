"""Behavioral limits are hypotheses, not qualified ADS1299 output specifications."""

from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
from scipy.linalg import expm

from lab.data_types import FloatArray
from lab.rev_a_bias import load_bias_model, state_matrices
from lab.rev_a_bias_overload import (
    InterferencePulse,
    OutputLimits,
    export_overload_spice,
    overload_response,
    run_overload_study,
)


@pytest.mark.parametrize("field", ["lower_v", "upper_v", "slew_v_per_s"])
@pytest.mark.parametrize("value", [float("nan"), float("inf"), True])
def test_limits_reject_nonfinite_and_boolean(field: str, value: float) -> None:
    with pytest.raises(ValueError):
        replace(OutputLimits(), **{field: value})


@pytest.mark.parametrize("kwargs", [{"lower_v": 0.0}, {"upper_v": -1.0}, {"slew_v_per_s": 0.0}])
def test_limits_must_contain_zero_and_have_positive_slew(kwargs: dict[str, float]) -> None:
    with pytest.raises(ValueError):
        OutputLimits(**kwargs)


def test_no_invented_extra_pole_saturation_topology() -> None:
    with pytest.raises(ValueError, match="one-pole"):
        overload_response(
            np.linspace(0, 0.035, 101),
            replace(load_bias_model(), extra_pole_hz=1000),
            InterferencePulse(),
        )


def test_small_pulse_matches_independent_linear_matrix_exponential() -> None:
    model = load_bias_model()
    pulse = InterferencePulse(amplitude_a=1e-9, rise_s=10e-6)
    times = np.linspace(0, 0.035, 3501)
    actual = overload_response(times, model, pulse)
    a, b = state_matrices(model)
    expected = _linear_pulse_reference(a, b, times, pulse.current(times))
    np.testing.assert_allclose(actual.state_v, expected, rtol=2e-5, atol=2e-10)
    assert actual.rail_events == ()
    assert not actual.state_v.flags.writeable


def test_overload_is_symmetric_and_retains_feedback_capacitor_memory() -> None:
    model = load_bias_model()
    times = np.linspace(0, 0.035, 3501)
    positive = overload_response(times, model, InterferencePulse())
    negative = overload_response(times, model, InterferencePulse(amplitude_a=-5e-6))
    np.testing.assert_allclose(positive.state_v, -negative.state_v, atol=2e-8, rtol=1e-7)
    assert np.min(positive.state_v[:, 11]) == pytest.approx(-2.0, abs=1e-9)
    assert positive.rail_events[0][1] == "lower"
    release = positive.rail_events[1]
    assert release[1] == "release"
    assert release[0] > 0.006001  # saturation persists after the interference is removed
    assert abs(positive.state_v[-1, 11]) < 1e-6
    sample = int(np.searchsorted(times, 0.006))
    assert abs(float(positive.state_v[sample, 10]) - float(positive.state_v[sample, 11])) > 0.1


def test_slew_is_applied_to_dynamics_not_to_a_finished_plot() -> None:
    times = np.linspace(0, 0.035, 3501)
    limits = OutputLimits(slew_v_per_s=100.0)
    actual = overload_response(times, load_bias_model(), InterferencePulse(), limits)
    slopes = np.diff(actual.state_v[:, 11]) / np.diff(times)
    assert np.max(np.abs(slopes)) <= 100.0 + 1e-5
    assert np.max(np.abs(slopes)) > 99.0


@pytest.mark.parametrize(
    "times",
    [
        np.array([]),
        np.array([0.0]),
        np.array([0.1, 0.0]),
        np.array([0.0, np.nan]),
        np.array([0.001, 0.035]),
    ],
)
def test_invalid_times_rejected(times: np.ndarray[tuple[int, ...], np.dtype[np.float64]]) -> None:
    with pytest.raises(ValueError):
        overload_response(times, load_bias_model(), InterferencePulse())


def test_run_is_unique_and_manifest_is_published_last(tmp_path: Path) -> None:
    root = run_overload_study(tmp_path, run_id="a" * 32)
    assert (root / "manifest.json").is_file()
    assert (root / "positive_overload" / "response.csv").is_file()
    with pytest.raises(FileExistsError):
        run_overload_study(tmp_path, run_id="a" * 32)


def test_native_export_keeps_real_feedback_capacitor(tmp_path: Path) -> None:
    netlist = export_overload_spice(tmp_path / "test.cir", load_bias_model(), InterferencePulse())
    text = netlist.read_text()
    assert "Cf vm out" in text
    assert "Bproject" in text
    assert "uic" in text
    assert "min(max(" in text  # native ngspice limit() is not a portable clipping primitive


def _linear_pulse_reference(
    a: FloatArray, b: FloatArray, times: FloatArray, current: FloatArray
) -> FloatArray:
    # Exact piecewise-linear forcing through an augmented matrix exponential;
    # algorithmically independent of Radau and of the rail-event integrator.
    dt = float(times[1]) - float(times[0])
    augmented = np.zeros((14, 14), dtype=np.float64)
    augmented[:12, :12] = a
    augmented[:12, 12] = b
    augmented[12, 13] = 1
    transition: FloatArray = np.asarray(expm(augmented * dt), dtype=np.float64)
    states = np.zeros((len(times), 12), dtype=np.float64)
    for index in range(1, len(times)):
        packed: FloatArray = np.concatenate(
            (states[index - 1], [current[index - 1], (current[index] - current[index - 1]) / dt])
        )
        advanced: FloatArray = transition @ packed
        states[index] = advanced[:12]
    return states


def test_sparse_observation_grid_does_not_skip_capacitor_evolution() -> None:
    times = np.array([0.0, 0.035])
    result = overload_response(times, load_bias_model(), InterferencePulse())
    assert result.state_v.shape == (2, 12)
    assert len(result.rail_events) == 2
    assert abs(float(result.state_v[-1, 11])) < 1e-6


@pytest.mark.parametrize(
    "kwargs",
    [
        {"amplitude_a": float("nan")},
        {"amplitude_a": True},
        {"on_s": -1.0},
        {"rise_s": 0.0},
        {"off_s": 0.001001},
    ],
)
def test_pulse_rejects_invalid_parameters(kwargs: dict[str, float]) -> None:
    with pytest.raises(ValueError):
        InterferencePulse(**kwargs)


def test_feedback_charge_obeys_resistor_kcl_during_saturation() -> None:
    model = load_bias_model()
    trace = overload_response(np.linspace(0, 0.035, 35001), model, InterferencePulse())
    state = trace.state_v
    difference: FloatArray = state[:, 10] - state[:, 11]
    into_capacitor: FloatArray = (
        np.sum((state[:, 2:10] - state[:, 10, None]) / model.summing_r_ohm, axis=1)
        - difference / model.feedback_r_ohm
    )
    integral = np.cumsum(0.5 * (into_capacitor[1:] + into_capacitor[:-1]) * np.diff(trace.time_s))
    # Independent integrated KCL, including the interval where output is stuck
    # at its rail. 50 uV allows the stated 1 us trapezoidal quadrature error.
    np.testing.assert_allclose(integral / model.feedback_c_f, difference[1:], rtol=0, atol=50e-6)


@pytest.mark.parametrize("fault", ["early_stop", "late_start", "disagreement"])
def test_failed_native_cannot_publish_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    def bad_trace(_netlist: Path, _out: Path, *, columns: int) -> tuple[FloatArray, FloatArray]:
        assert columns == 3
        times = np.array([0.0, 0.01, 0.035])
        if fault == "early_stop":
            times[-1] = 0.02
        elif fault == "late_start":
            times[0] = 1e-3
        return times, np.zeros((3, 3), dtype=np.float64)

    monkeypatch.setattr("lab.rev_a_bias_overload.run_ngspice_transient", bad_trace)
    with pytest.raises(RuntimeError, match=r"transient|disagree"):
        run_overload_study(tmp_path, require_ngspice=True, run_id="f" * 32)
    root = tmp_path / ("f" * 32)
    assert (root / "small_signal" / "native" / "network.cir").is_file()
    assert not (root / "manifest.json").exists()
    assert not (root / "study.json").exists()


def test_event_records_are_defensively_copied_and_validated() -> None:
    from lab.rev_a_bias_overload import OverloadTrace

    times = np.array([0.0, 0.01])
    state = np.zeros((2, 12), dtype=np.float64)
    trace = OverloadTrace(times, state, OutputLimits(), ())
    times[1] = 100
    state[0, 11] = 100
    assert trace.time_s[-1] == 0.01
    assert trace.state_v[0, 11] == 0
    with pytest.raises(ValueError, match="rails"):
        OverloadTrace(np.array([0.0, 0.01]), state, OutputLimits(), ())
