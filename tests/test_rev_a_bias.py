"""Reference equations and independent circuit checks for bounded BIAS analysis."""

from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from lab.analog import run_ngspice
from lab.data_types import FloatArray
from lab.rev_a_bias import (
    closed_poles,
    export_bias_spice,
    ideal_controller,
    load_bias_model,
    response,
    step_response,
)


def test_sbaa188_two_input_reference_gain_and_pole() -> None:
    model = load_bias_model()
    pole = 1 / (2 * np.pi * 1e6 * 1.5e-9)
    frequency = np.array([0.0, pole])
    gain = ideal_controller(frequency, model, selected_outputs=2)
    assert pole == pytest.approx(106.1032953945969)
    assert gain[0] == pytest.approx(2e6 / 220e3)
    assert gain[1] == pytest.approx((2e6 / 220e3) / (1 + 1j))


def test_selected_baseline_and_typical_value_are_not_new_hardware_choices() -> None:
    model = load_bias_model()
    assert model.feedback_r_ohm == 1e6
    assert model.feedback_c_f == 1.5e-9
    assert model.drive_r_ohm == 1e6
    assert model.input_r_ohm == 4990
    assert model.differential_c_f == 4.7e-9
    assert model.summing_r_ohm == 220e3
    assert model.gbw_hz == 100e3


def test_balanced_dc_matches_resistor_only_equation() -> None:
    model = load_bias_model()
    values = response(np.array([0.0]), model)
    contact = model.contacts_ohm[0]
    assert contact is not None
    branch_r = contact + model.input_r_ohm + model.input_load_ohm
    body_load = 1 / (1 / model.environment_r_ohm + 8 / branch_r)
    assert model.bias_contact_ohm is not None
    drive_r = model.drive_r_ohm + model.bias_contact_ohm
    sensing = model.input_load_ohm / branch_r
    controller = (model.open_loop_gain / model.summing_r_ohm) / (
        8 / model.summing_r_ohm + (1 + model.open_loop_gain) / model.feedback_r_ohm
    )
    loop = controller * 8 * sensing * body_load / (drive_r + body_load)
    open_z = 1 / (1 / body_load + 1 / drive_r)
    assert values.loop_gain[0] == pytest.approx(loop, rel=1e-11)
    assert values.common_impedance_ohm[0] == pytest.approx(open_z / (1 + loop), rel=1e-11)


def test_disconnected_drive_has_no_feedback_loop() -> None:
    model = replace(load_bias_model(), bias_contact_ohm=None)
    values = response(np.array([0.0, 50.0, 1000.0]), model)
    np.testing.assert_array_equal(values.loop_gain, np.zeros(3))
    assert np.all(np.isfinite(values.common_impedance_ohm))


def test_eight_input_symmetry_and_open_contact_differ() -> None:
    model = load_bias_model()
    frequency = np.array([50.0, 60.0, 1000.0])
    balanced = response(frequency, model)
    np.testing.assert_allclose(balanced.differential_impedance_ohm, 0, atol=1e-6)
    contacts = (None, *model.contacts_ohm[1:])
    opened = response(frequency, replace(model, contacts_ohm=contacts))
    assert np.max(np.abs(opened.differential_impedance_ohm)) > 1


def test_linear_step_converges_to_dc_and_poles_are_finite() -> None:
    model = load_bias_model()
    poles = closed_poles(model)
    assert np.all(np.isfinite(poles))
    assert np.max(poles.real) < 0
    time = np.linspace(0, 0.1, 201)
    actual = step_response(time, model, current_a=1e-9)
    target = complex(response(np.array([0.0]), model).common_impedance_ohm[0]).real * 1e-9
    assert actual[0] == pytest.approx(0, abs=1e-12)
    assert actual[-1] == pytest.approx(target, rel=1e-5)


@pytest.mark.parametrize("value", [-1, 0, float("nan"), float("inf"), True])
def test_invalid_dynamics_rejected(value: float) -> None:
    with pytest.raises(ValueError):
        replace(load_bias_model(), gbw_hz=value)


@pytest.mark.parametrize(
    "frequency", [np.array([-1.0]), np.array([float("nan")]), np.zeros((2, 2))]
)
def test_invalid_frequency_rejected(frequency: FloatArray) -> None:
    with pytest.raises(ValueError):
        response(frequency, load_bias_model())


@pytest.mark.native
@pytest.mark.parametrize("mode", ["loop", "closed"])
def test_native_bias_matches_independent_equations(tmp_path: Path, mode: str) -> None:
    model = load_bias_model()
    netlist = export_bias_spice(tmp_path / "network.cir", model, mode=mode)
    frequency, actual = run_ngspice(netlist, tmp_path)
    result = response(frequency, model)
    expected = result.loop_gain if mode == "loop" else result.common_impedance_ohm
    np.testing.assert_allclose(actual, expected, rtol=1e-5, atol=1e-6)


def test_stress_case_is_not_misreported_as_settling() -> None:
    model = replace(load_bias_model(), contacts_ohm=(10e6,) * 8)
    assert np.max(closed_poles(model).real) > 0
    with pytest.raises(ValueError, match="unstable"):
        step_response(np.array([0.0, 0.01]), model, current_a=1e-9)


@pytest.mark.parametrize("contacts", [(1e4,) * 7, (1e4,) * 9, (0.0,) * 8, (-1.0,) * 8])
def test_contact_shape_and_values_are_validated(contacts: tuple[float, ...]) -> None:
    with pytest.raises(ValueError):
        replace(load_bias_model(), contacts_ohm=contacts)


def test_model_defensively_snapshots_contact_sequence() -> None:
    from collections.abc import Callable
    from typing import cast

    model = load_bias_model()
    contacts = [1e4] * 8
    operation = cast(Callable[..., object], replace)
    copied = operation(model, contacts_ohm=contacts)
    contacts[0] = 1e6
    assert isinstance(copied, type(model))
    assert copied.contacts_ohm[0] == 1e4


@pytest.mark.parametrize("time", [np.array([0.1, 0.0]), np.array([0.0, 0.0]), np.array([])])
def test_invalid_time_rejected(time: FloatArray) -> None:
    with pytest.raises(ValueError):
        step_response(time, load_bias_model(), current_a=1e-9)


@pytest.mark.parametrize("selected", [0, 9, True, 2.5])
def test_summing_count_requires_an_integer(selected: int) -> None:
    with pytest.raises(ValueError):
        ideal_controller(np.array([0.0]), load_bias_model(), selected_outputs=selected)


def test_linear_step_scales_with_amplitude_and_sign() -> None:
    time = np.linspace(0, 0.01, 21)
    model = load_bias_model()
    first = step_response(time, model, current_a=1e-9)
    second = step_response(time, model, current_a=-2e-9)
    np.testing.assert_allclose(second, -2 * first, rtol=1e-12, atol=1e-15)


def test_passive_loading_and_buffer_placement_are_explicit_in_netlist(tmp_path: Path) -> None:
    path = export_bias_spice(tmp_path / "circuit.cir", load_bias_model())
    netlist = path.read_text()
    assert "Rsum0 buf0 vm 220000" in netlist
    assert "Ebuffer0 buf0 0 i0 0 1" in netlist
    assert "Cdiff0 i0 i1 4.7e-09" in netlist
    assert "Rdrive drive lead 1000000" in netlist
    assert "Rsum0 i0" not in netlist


@pytest.mark.native
@pytest.mark.parametrize(
    "scenario", ["asymmetric", "open_input", "open_bias", "high_impedance_stress"]
)
@pytest.mark.parametrize("mode", ["loop", "closed"])
def test_native_bad_contacts_match_formal_transfer(
    tmp_path: Path, scenario: str, mode: str
) -> None:
    from lab.rev_a_bias import scenarios

    model = scenarios(load_bias_model())[scenario]
    netlist = export_bias_spice(tmp_path / "network.cir", model, mode=mode)
    frequency, actual = run_ngspice(netlist, tmp_path)
    values = response(frequency, model)
    reference = values.loop_gain if mode == "loop" else values.common_impedance_ohm
    # The stress case can agree in AC while being dynamically unstable.
    np.testing.assert_allclose(actual, reference, rtol=1e-5, atol=1e-6)
