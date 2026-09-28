"""Native differential tests for the assumed projection, not actual chip behavior."""

from pathlib import Path

import numpy as np
import pytest

from lab.analog import run_ngspice_transient
from lab.rev_a_bias import load_bias_model, scenarios
from lab.rev_a_bias_overload import (
    InterferencePulse,
    OutputLimits,
    export_overload_spice,
    overload_response,
)


@pytest.mark.native
@pytest.mark.parametrize("name", ["balanced", "asymmetric", "open_input", "open_bias", "slow_slew"])
def test_native_overload_matches_hybrid_circuit(tmp_path: Path, name: str) -> None:
    model = scenarios(load_bias_model()).get(name, load_bias_model())
    limits = OutputLimits(slew_v_per_s=100) if name == "slow_slew" else OutputLimits()
    pulse = InterferencePulse()
    path = export_overload_spice(tmp_path / "network.cir", model, pulse, limits)
    times, actual = run_ngspice_transient(path, tmp_path, columns=3, expected_stop_s=0.035)
    assert times[0] == 0
    assert times[-1] == pytest.approx(0.035, abs=1e-12)
    reference = overload_response(times, model, pulse, limits).state_v[:, [1, 11, 10]]
    np.testing.assert_allclose(actual, reference, rtol=2e-4, atol=1e-4)
    assert np.max(actual[:, 1]) <= limits.upper_v + 1e-4
    assert np.min(actual[:, 1]) >= limits.lower_v - 1e-4


@pytest.mark.native
def test_nominal_overload_is_insensitive_to_finer_native_timestep(tmp_path: Path) -> None:
    model, pulse = load_bias_model(), InterferencePulse()
    coarse_path = export_overload_spice(tmp_path / "coarse" / "network.cir", model, pulse)
    fine_path = export_overload_spice(
        tmp_path / "fine" / "network.cir", model, pulse, max_step_s=50e-9
    )
    times, coarse = run_ngspice_transient(
        coarse_path, coarse_path.parent, columns=3, expected_stop_s=0.035
    )
    fine_times, fine = run_ngspice_transient(
        fine_path, fine_path.parent, columns=3, expected_stop_s=0.035
    )
    np.testing.assert_array_equal(times, fine_times)
    expected = overload_response(times, model, pulse).state_v[:, [1, 11, 10]]
    # A stronger nominal-case accuracy check than the broad seven-case gate.
    np.testing.assert_allclose(coarse, expected, rtol=0, atol=2e-6)
    np.testing.assert_allclose(fine, expected, rtol=0, atol=2e-6)
    np.testing.assert_allclose(coarse, fine, rtol=0, atol=2e-6)
