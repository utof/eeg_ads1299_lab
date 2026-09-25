"""An optional unmeasured amplifier pole must stay consistent across both solvers."""

from dataclasses import fields, replace
from pathlib import Path

import numpy as np
import pytest

from lab.analog import run_ngspice
from lab.rev_a_bias import closed_poles, export_bias_spice, load_bias_model, response


def test_optional_extra_pole_preserves_dc_and_adds_one_state() -> None:
    original = load_bias_model()
    extra = replace(original, extra_pole_hz=1000.0)
    first = response(np.array([0.0]), original)
    second = response(np.array([0.0]), extra)
    np.testing.assert_allclose(first.common_impedance_ohm, second.common_impedance_ohm)
    assert closed_poles(original).size == 12
    assert closed_poles(extra).size == 13


@pytest.mark.parametrize("pole", [0.0, -1.0, float("nan"), float("inf"), True])
def test_invalid_extra_poles_rejected(pole: float) -> None:
    with pytest.raises(ValueError):
        replace(load_bias_model(), extra_pole_hz=pole)


def test_remote_extra_pole_tends_to_original_model() -> None:
    original = load_bias_model()
    high = replace(original, extra_pole_hz=1e12)
    frequencies = np.geomspace(0.1, 1e5, 241)
    first, second = response(frequencies, original), response(frequencies, high)
    np.testing.assert_allclose(first.loop_gain, second.loop_gain, rtol=1e-6, atol=1e-10)


@pytest.mark.native
@pytest.mark.parametrize("pole", [100.0, 1000.0, 100000.0])
@pytest.mark.parametrize("mode", ["loop", "closed"])
def test_two_pole_native_matches_equations(tmp_path: Path, pole: float, mode: str) -> None:
    model = replace(load_bias_model(), extra_pole_hz=pole)
    path = export_bias_spice(tmp_path / "network.cir", model, mode=mode)
    frequency, actual = run_ngspice(path, tmp_path)
    numerical = response(frequency, model)
    expected = numerical.loop_gain if mode == "loop" else numerical.common_impedance_ohm
    np.testing.assert_allclose(actual, expected, rtol=1e-5, atol=1e-6)


def test_optional_extra_pole_is_an_explicit_model_parameter() -> None:
    assert "extra_pole_hz" in {field.name for field in fields(load_bias_model())}


def test_two_pole_step_converges_to_same_dc() -> None:
    from lab.rev_a_bias import step_response

    model = replace(load_bias_model(), extra_pole_hz=100.0)
    times = np.linspace(0, 0.3, 151)
    samples = step_response(times, model, current_a=1e-9)
    steady = complex(response(np.array([0.0]), model).common_impedance_ohm[0]).real * 1e-9
    assert samples[0] == pytest.approx(0, abs=1e-12)
    assert samples[-1] == pytest.approx(steady, rel=1e-7)


def test_assumed_extra_pole_changes_damping_without_changing_dc() -> None:
    original = load_bias_model()
    extra = replace(original, extra_pole_hz=100.0)
    nominal = float(np.max(closed_poles(original).real))
    varied = float(np.max(closed_poles(extra).real))
    assert nominal < -700
    assert -100 < varied < 0
