"""Independent time-domain check of the stated linear circuit, not hardware."""

from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from lab.analog import run_ngspice_transient
from lab.rev_a_bias import (
    export_bias_spice,
    load_bias_model,
    response,
    scenarios,
    step_response,
    step_voltages,
)


def test_step_voltage_columns_have_independent_dc_limits() -> None:
    model = load_bias_model()
    times = np.array([0.0, 0.001, 0.1])
    volts = step_voltages(times, model, current_a=1e-9)
    assert volts.shape == (3, 2)
    np.testing.assert_array_equal(volts[0], [0.0, 0.0])
    dc = response(np.array([0.0]), model)
    assert volts[-1, 0] == pytest.approx(complex(dc.common_impedance_ohm[0]).real * 1e-9)
    assert volts[-1, 1] == pytest.approx(complex(dc.output_impedance_ohm[0]).real * 1e-9)
    np.testing.assert_array_equal(volts[:, 0], step_response(times, model, current_a=1e-9))


@pytest.mark.native
@pytest.mark.parametrize(
    ("case", "extra_pole"),
    [
        ("balanced", None),
        ("asymmetric", None),
        ("open_input", None),
        ("open_bias", None),
        ("balanced", 100.0),
        ("balanced", 1000.0),
        ("balanced", 100000.0),
    ],
)
def test_native_bias_step_matches_matrix_exponential(
    tmp_path: Path, case: str, extra_pole: float | None
) -> None:
    model = replace(scenarios(load_bias_model())[case], extra_pole_hz=extra_pole)
    path = export_bias_spice(tmp_path / "network.cir", model, mode="step")
    times, actual = run_ngspice_transient(path, tmp_path, columns=2)
    assert times[0] <= 1e-6
    assert times[-1] == pytest.approx(0.1, abs=1e-12)
    # Test early samples and the entire window; retain the complete native table.
    indexes = np.unique(
        np.concatenate((np.arange(20), np.linspace(0, len(times) - 1, 301, dtype=int)))
    )
    expected = step_voltages(times[indexes], model, current_a=1e-9)
    np.testing.assert_allclose(actual[indexes], expected, rtol=1e-4, atol=1e-9)


@pytest.mark.native
def test_slow_extra_pole_step_converges_under_timestep_refinement(tmp_path: Path) -> None:
    model = replace(load_bias_model(), extra_pole_hz=100.0)
    coarse_path = export_bias_spice(tmp_path / "coarse" / "network.cir", model, mode="step")
    fine_path = export_bias_spice(tmp_path / "fine" / "network.cir", model, mode="step")
    fine_path.write_text(fine_path.read_text().replace("0 200n uic", "0 100n uic"))
    times, coarse = run_ngspice_transient(coarse_path, coarse_path.parent, columns=2)
    fine_times, fine = run_ngspice_transient(fine_path, fine_path.parent, columns=2)
    np.testing.assert_array_equal(times, fine_times)
    indexes = np.linspace(0, len(times) - 1, 701, dtype=np.int64)
    reference = step_voltages(times[indexes], model, current_a=1e-9)
    coarse_error = float(np.max(np.abs(coarse[indexes] - reference)))
    fine_error = float(np.max(np.abs(fine[indexes] - reference)))
    # A real convergence experiment, not relaxing a failed comparison threshold.
    assert coarse_error > 2 * fine_error
    np.testing.assert_allclose(fine[indexes], reference, rtol=1e-4, atol=1e-9)
