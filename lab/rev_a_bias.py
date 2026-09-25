"""Bounded linear BIAS feedback study; prospective electrical dummy loads only.

TI SBAA188 topology/equation, not imported TINA or a silicon model. All voltages
are small deviations from the analog midpoint. No firmware excitation is enabled.
"""

import argparse
import hashlib
import json
import math
import platform
import re
import shutil
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass, fields, replace
from pathlib import Path
from uuid import uuid4

import numpy as np
import scipy
from scipy.linalg import expm

from hardware.rev_a import load_documents, validate

from .analog import run_ngspice, run_ngspice_transient
from .data_types import ComplexArray, FloatArray


@dataclass(frozen=True, slots=True)
class BiasModel:
    baseline_sha256: str
    feedback_r_ohm: float
    feedback_c_f: float
    drive_r_ohm: float
    input_r_ohm: float
    differential_c_f: float
    # TI corrected the 330 kohm typo to 220 kohm; see source record.
    summing_r_ohm: float = 220e3
    # 100 kHz is a typical datasheet value, not a guaranteed tolerance band.
    gbw_hz: float = 100e3
    # Remaining values are explicit, unmeasured engineering assumptions.
    open_loop_gain: float = 1e5
    extra_pole_hz: float | None = None
    contacts_ohm: tuple[float | None, ...] = (10e3,) * 8
    bias_contact_ohm: float | None = 10e3
    lead_c_f: float = 100e-12
    environment_r_ohm: float = 100e6
    environment_c_f: float = 200e-12
    input_load_ohm: float = 1e9
    input_c_f: float = 100e-12

    def __post_init__(self) -> None:
        if re.fullmatch(r"[0-9a-f]{64}", self.baseline_sha256) is None:
            raise ValueError("baseline digest must be SHA-256")
        for field in fields(self):
            if field.name not in (
                "baseline_sha256",
                "contacts_ohm",
                "bias_contact_ohm",
                "extra_pole_hz",
            ):
                _positive(getattr(self, field.name), field.name)
        if self.extra_pole_hz is not None:
            _positive(self.extra_pole_hz, "extra amplifier pole")
        contacts = tuple(self.contacts_ohm)
        if len(contacts) != 8:
            raise ValueError("exactly eight input contacts are required")
        for contact in (*contacts, self.bias_contact_ohm):
            if contact is not None:
                _positive(contact, "contact")
        object.__setattr__(self, "contacts_ohm", contacts)


def _positive(value: float, name: str) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value <= 0
    ):
        raise ValueError(f"{name} must be finite and positive")


def _frequencies(frequency_hz: FloatArray) -> FloatArray:
    values = np.asarray(frequency_hz, dtype=np.float64)
    if values.ndim != 1 or values.size == 0 or not np.all(np.isfinite(values)):
        raise ValueError("frequency must be a nonempty finite one-dimensional array")
    if np.any(values < 0):
        raise ValueError("frequency cannot be negative")
    return values


def load_bias_model() -> BiasModel:
    """Derive selected external components only after validating the hardware contract."""
    profile, bom, sources = load_documents()
    errors = validate(profile, bom, sources)
    if errors:
        raise ValueError("Rev A baseline rejected: " + "; ".join(errors))
    network = profile["input_network"]
    digest = hashlib.sha256(
        json.dumps([profile, bom, sources], sort_keys=True, allow_nan=False).encode("utf-8")
    ).hexdigest()
    return BiasModel(
        baseline_sha256=digest,
        feedback_r_ohm=network["bias_feedback_resistance_ohm"],
        feedback_c_f=network["bias_feedback_capacitance_f"],
        drive_r_ohm=network["bias_output_series_resistance_ohm"],
        input_r_ohm=network["series_resistance_each_ohm"],
        differential_c_f=network["differential_capacitance_f"],
    )


def ideal_controller(
    frequency_hz: FloatArray, model: BiasModel, *, selected_outputs: int = 8
) -> ComplexArray:
    """Positive gain magnitude/sign convention: actual summing stage is inverting.

    SBAA188 equation 3 is the two-selected-output, infinite-amplifier-gain limit.
    This function excludes the output/load path and cannot establish loop stability.
    """
    if (
        isinstance(selected_outputs, bool)
        or not isinstance(selected_outputs, int)
        or not 1 <= selected_outputs <= 8
    ):
        raise ValueError("selected outputs must be an integer from one to eight")
    frequency = _frequencies(frequency_hz)
    return np.asarray(
        selected_outputs
        * model.feedback_r_ohm
        / model.summing_r_ohm
        / (1 + 2j * np.pi * frequency * model.feedback_r_ohm * model.feedback_c_f),
        dtype=np.complex128,
    )


def _stamp(matrix: FloatArray, a: int, b: int | None, value: float) -> None:
    matrix[a, a] = float(matrix[a, a]) + value
    if b is not None:
        matrix[b, b] = float(matrix[b, b]) + value
        matrix[a, b] = float(matrix[a, b]) - value
        matrix[b, a] = float(matrix[b, a]) - value


def _plant(model: BiasModel) -> tuple[FloatArray, FloatArray, FloatArray]:
    """Nodes: driven lead, common dummy, then eight ADC input nodes.

    Buffers isolate the 220 kohm summing resistors from these input nodes.
    Pairwise selected differential capacitors remain in the plant.
    """
    conductance = np.zeros((10, 10), dtype=np.float64)
    capacitance = np.zeros((10, 10), dtype=np.float64)
    sources = np.zeros((10, 2), dtype=np.float64)
    _stamp(conductance, 0, None, 1 / model.drive_r_ohm)
    sources[0, 0] = 1 / model.drive_r_ohm
    sources[1, 1] = 1  # one ampere for a transimpedance response, not physical excitation
    _stamp(capacitance, 0, None, model.lead_c_f)
    _stamp(conductance, 1, None, 1 / model.environment_r_ohm)
    _stamp(capacitance, 1, None, model.environment_c_f)
    if model.bias_contact_ohm is not None:
        _stamp(conductance, 0, 1, 1 / model.bias_contact_ohm)
    for index, contact in enumerate(model.contacts_ohm, start=2):
        if contact is not None:
            _stamp(conductance, 1, index, 1 / (contact + model.input_r_ohm))
        _stamp(conductance, index, None, 1 / model.input_load_ohm)
        _stamp(capacitance, index, None, model.input_c_f)
    for index in range(2, 10, 2):
        _stamp(capacitance, index, index + 1, model.differential_c_f)
    return conductance, capacitance, sources


@dataclass(frozen=True, slots=True)
class BiasResponse:
    loop_gain: ComplexArray
    common_impedance_ohm: ComplexArray
    differential_impedance_ohm: ComplexArray
    output_impedance_ohm: ComplexArray

    def __post_init__(self) -> None:
        for field in fields(self):
            value = np.array(getattr(self, field.name), dtype=np.complex128, copy=True)
            if not np.all(np.isfinite(value)):
                raise ValueError("BIAS response is nonfinite")
            value.flags.writeable = False
            object.__setattr__(self, field.name, value)
        length = self.loop_gain.size
        if length == 0 or self.loop_gain.shape != (length,):
            raise ValueError("loop response must be nonempty and one-dimensional")
        if self.common_impedance_ohm.shape != (length,) or self.output_impedance_ohm.shape != (
            length,
        ):
            raise ValueError("response lengths must match")
        if self.differential_impedance_ohm.shape != (length, 4):
            raise ValueError("differential response must contain four channels")


def response(frequency_hz: FloatArray, model: BiasModel) -> BiasResponse:
    """Return ratio L for negative feedback, and closed V/A responses.

    A(s)=A0/(1+s*A0/(2*pi*GBW)), optionally divided by (1+s/(2*pi*extra_pole)).
    With an extra pole GBW remains a dominant gain product, not total unity bandwidth.
    Controller output = -K(s)*sum(sensed input voltages); L=K*sum(plant gains).
    """
    frequency = _frequencies(frequency_hz)
    s: ComplexArray = np.asarray(2j * np.pi * frequency, dtype=np.complex128)
    conductance, capacitance, sources = _plant(model)
    admittance: ComplexArray = np.asarray(
        conductance + s[:, None, None] * capacitance, dtype=np.complex128
    )
    plant: ComplexArray = np.asarray(
        np.linalg.solve(admittance, np.broadcast_to(sources, (len(s), 10, 2))), dtype=np.complex128
    )
    amplifier: ComplexArray = model.open_loop_gain / (
        1 + s * model.open_loop_gain / (2 * np.pi * model.gbw_hz)
    )
    if model.extra_pole_hz is not None:
        amplifier = amplifier / (1 + s / (2 * np.pi * model.extra_pole_hz))
    feedback: ComplexArray = 1 / model.feedback_r_ohm + s * model.feedback_c_f
    controller: ComplexArray = (
        amplifier / model.summing_r_ohm / (8 / model.summing_r_ohm + (1 + amplifier) * feedback)
    )
    loop: ComplexArray = controller * np.sum(plant[:, 2:, 0], axis=1)
    output: ComplexArray = -controller * np.sum(plant[:, 2:, 1], axis=1) / (1 + loop)
    nodes: ComplexArray = plant[:, :, 1] + plant[:, :, 0] * output[:, None]
    return BiasResponse(
        loop_gain=loop,
        common_impedance_ohm=nodes[:, 1],
        differential_impedance_ohm=nodes[:, 2::2] - nodes[:, 3::2],
        output_impedance_ohm=output,
    )


def _closed_system(model: BiasModel) -> tuple[FloatArray, FloatArray]:
    """Independent full circuit descriptor: passive nodes, summing node, amplifier output."""
    plant_g, plant_c, sources = _plant(model)
    size = 12 if model.extra_pole_hz is None else 13
    conductance = np.zeros((size, size), dtype=np.float64)
    capacitance = np.zeros((size, size), dtype=np.float64)
    conductance[:10, :10], capacitance[:10, :10] = plant_g, plant_c
    conductance[:10, 11] = -sources[:, 0]
    # Summing-node KCL, with ideal unity buffers supplying the eight resistor paths.
    conductance[10, 2:10] = -1 / model.summing_r_ohm
    conductance[10, 10] = 8 / model.summing_r_ohm + 1 / model.feedback_r_ohm
    conductance[10, 11] = -1 / model.feedback_r_ohm
    capacitance[10, 10], capacitance[10, 11] = model.feedback_c_f, -model.feedback_c_f
    dominant = 11 if model.extra_pole_hz is None else 12
    conductance[dominant, 10], conductance[dominant, dominant] = model.open_loop_gain, 1
    capacitance[dominant, dominant] = model.open_loop_gain / (2 * np.pi * model.gbw_hz)
    if model.extra_pole_hz is not None:
        conductance[11, 11], conductance[11, 12] = 1, -1
        capacitance[11, 11] = 1 / (2 * np.pi * model.extra_pole_hz)
    injected = np.zeros(size, dtype=np.float64)
    injected[1] = 1
    return np.asarray(-np.linalg.solve(capacitance, conductance), dtype=np.float64), np.asarray(
        np.linalg.solve(capacitance, injected), dtype=np.float64
    )


def closed_poles(model: BiasModel) -> ComplexArray:
    """Poles of this linear model, NOT proof that physical ADS1299 hardware is stable."""
    state, _ = _closed_system(model)
    return np.asarray(np.linalg.eigvals(state), dtype=np.complex128)


def step_voltages(time_s: FloatArray, model: BiasModel, *, current_a: float) -> FloatArray:
    """Zero-state linear [dummy common, amplifier output] volts for a current step.

    No rails, slew limiting, current limiting, power-up or saturation recovery.
    Reject unstable models rather than presenting a settling result for them.
    """
    times = _frequencies(time_s)
    if np.any(np.diff(times) <= 0) or isinstance(current_a, bool) or not math.isfinite(current_a):
        raise ValueError("time must increase strictly and current must be finite")
    state, drive = _closed_system(model)
    if np.max(np.linalg.eigvals(state).real) >= 0:
        raise ValueError("unstable linear model has no settling response")
    steady = -np.linalg.solve(state, drive) * current_a
    return np.array(
        [(steady - expm(state * float(time)) @ steady)[[1, 11]] for time in times], dtype=np.float64
    )


def step_response(time_s: FloatArray, model: BiasModel, *, current_a: float) -> FloatArray:
    """Compatibility view of the zero-state linear dummy-common step voltage."""
    return step_voltages(time_s, model, current_a=current_a)[:, 0]


def export_bias_spice(path: str | Path, model: BiasModel, *, mode: str = "loop") -> Path:
    """Generate only this bounded circuit; execution reuses lab.analog.run_ngspice."""
    if mode not in ("loop", "closed", "step"):
        raise ValueError("mode must be loop, closed or step")
    stimulus = "Iinterference 0 common DC 1n" if mode == "step" else "Iinterference 0 common AC 1n"
    lines = [
        "Bounded BIAS dummy-load model -- NOT A HUMAN-USE SCHEMATIC",
        "* Midpoint small-signal reference; unmeasured loads and assumed amplifier dynamics.",
        "* No imported TINA/silicon model, rails, slew, current limit or recovery model.",
        "Vdrive drive 0 AC 1" if mode == "loop" else stimulus,
        f"Rdrive {'drive' if mode == 'loop' else 'out'} lead {model.drive_r_ohm:.15g}",
        f"Clead lead 0 {model.lead_c_f:.15g}",
        f"Renv common 0 {model.environment_r_ohm:.15g}",
        f"Cenv common 0 {model.environment_c_f:.15g}",
        f"Rf vm out {model.feedback_r_ohm:.15g}",
        f"Cf vm out {model.feedback_c_f:.15g}",
        f"Eamp raw 0 vm 0 {-model.open_loop_gain:.15g}",
        "Rdominant raw dom 1000",
        f"Cdominant dom 0 {model.open_loop_gain / (2 * np.pi * model.gbw_hz) / 1000:.15g}",
    ]
    if model.extra_pole_hz is None:
        lines.append("Eoutput out 0 dom 0 1")
    else:
        lines.extend(
            [
                "Eisolate buffer 0 dom 0 1",
                "Rextra buffer extra 1000",
                f"Cextra extra 0 {1 / (2 * np.pi * model.extra_pole_hz * 1000):.15g}",
                "Eoutput out 0 extra 0 1",
            ]
        )
    if model.bias_contact_ohm is not None:
        lines.append(f"Rbias lead common {model.bias_contact_ohm:.15g}")
    for index, contact in enumerate(model.contacts_ohm):
        if contact is not None:
            lines.append(f"Rcontact{index} common i{index} {contact + model.input_r_ohm:.15g}")
        lines.extend(
            [
                f"Rinput{index} i{index} 0 {model.input_load_ohm:.15g}",
                f"Cinput{index} i{index} 0 {model.input_c_f:.15g}",
                f"Ebuffer{index} buf{index} 0 i{index} 0 1",
                f"Rsum{index} buf{index} vm {model.summing_r_ohm:.15g}",
            ]
        )
    for index in range(0, 8, 2):
        lines.append(f"Cdiff{index} i{index} i{index + 1} {model.differential_c_f:.15g}")
    if mode == "step":
        lines.extend(
            [".save v(common) v(out)", ".options reltol=1e-7 vntol=1e-10 abstol=1e-14 method=trap"]
        )
    lines.extend([".control", "set wr_singlescale", "set wr_vecnames", "set numdgt=15"])
    lines.extend(_analysis_commands(mode))
    lines.extend(["quit", ".endc", ".end", ""])
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines), encoding="utf-8")
    return target


def _analysis_commands(mode: str) -> list[str]:
    if mode == "step":
        # All capacitors start at zero. DC operating-point initialization would
        # incorrectly start at the final steady state, so uic is essential.
        return [
            "tran 1n 0.1 0 200n uic",
            "let lin-tstart = 0",
            "let lin-tstop = 0.1",
            "let lin-tstep = 2u",
            "linearize v(common) v(out)",
            "wrdata transient.txt v(common) v(out)",
        ]
    output = "-v(out)" if mode == "loop" else "v(common)/1e-9"
    return [
        "ac dec 40 0.1 100000",
        f"let h = {output}",
        "let hr = real(h)",
        "let hi = imag(h)",
        "wrdata ac.txt hr hi",
    ]


def scenarios(model: BiasModel) -> dict[str, BiasModel]:
    """Five electrical dummy cases for the same four-channel topology, not electrode brands."""
    return {
        "balanced": model,
        "asymmetric": replace(model, contacts_ohm=(50e3, *model.contacts_ohm[1:])),
        "open_input": replace(model, contacts_ohm=(None, *model.contacts_ohm[1:])),
        "open_bias": replace(model, bias_contact_ohm=None),
        "high_impedance_stress": replace(model, contacts_ohm=(10e6,) * 8),
    }


def _crossings(frequency: FloatArray, loop: ComplexArray) -> list[dict[str, float]]:
    # This is an explicitly sampled crossover estimate, NOT a proof of stability.
    magnitude: FloatArray = np.abs(loop)
    phase: FloatArray = np.rad2deg(np.unwrap(np.angle(loop)))
    crossings: list[dict[str, float]] = []
    for index in range(len(frequency) - 1):
        left, right = float(magnitude[index]), float(magnitude[index + 1])
        if min(left, right) <= 0 or (left - 1) * (right - 1) > 0 or left == right:
            continue
        fraction = -math.log(left) / (math.log(right) - math.log(left))
        hz = math.exp(
            math.log(float(frequency[index]))
            + fraction * math.log(float(frequency[index + 1]) / float(frequency[index]))
        )
        degrees = (
            180 + float(phase[index]) + fraction * (float(phase[index + 1]) - float(phase[index]))
        )
        crossings.append({"frequency_hz": hz, "phase_margin_deg": degrees})
    return crossings


def _metrics(model: BiasModel) -> dict[str, object]:
    frequency: FloatArray = np.geomspace(0.1, 100000, 1201)
    values = response(frequency, model)
    poles = closed_poles(model)
    rightmost = float(np.max(poles.real))
    line = response(np.array([50.0, 60.0]), model)
    return {
        "model": asdict(model),
        "rightmost_pole_real_per_s": rightmost,
        "linear_model_stable": rightmost < 0,
        "poles_per_s": [[complex(pole).real, complex(pole).imag] for pole in poles],
        "sampled_unity_crossings": _crossings(frequency, values.loop_gain),
        "common_impedance_50_60hz_ohm": np.abs(line.common_impedance_ohm).tolist(),
        "differential_impedance_50_60hz_ohm": np.abs(line.differential_impedance_ohm).tolist(),
        "frequency_response_interpretation": "sinusoidal_steady_state_of_linear_model"
        if rightmost < 0
        else "formal_transfer_only_unstable_model",
    }


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )


def _case_artifacts(root: Path, model: BiasModel, required: bool) -> dict[str, object]:
    root.mkdir()
    summary = _metrics(model)
    frequency: FloatArray = np.geomspace(0.1, 100000, 241)
    values = response(frequency, model)
    np.savetxt(
        root / "response.csv",
        np.column_stack(
            (
                frequency,
                values.loop_gain.real,
                values.loop_gain.imag,
                values.common_impedance_ohm.real,
                values.common_impedance_ohm.imag,
            )
        ),
        delimiter=",",
        header="frequency_hz,loop_real,loop_imag,common_ohm_real,common_ohm_imag",
        comments="",
    )
    errors: dict[str, float] = {}
    for mode in ("loop", "closed"):
        netlist = export_bias_spice(root / mode / "network.cir", model, mode=mode)
        if required:
            frequencies, actual = run_ngspice(netlist, netlist.parent)
            expected = response(frequencies, model)
            reference = expected.loop_gain if mode == "loop" else expected.common_impedance_ohm
            if not np.allclose(actual, reference, rtol=1e-5, atol=1e-6):
                raise RuntimeError(f"BIAS ngspice disagreement in {root.name}/{mode}")
            errors[mode] = float(np.max(np.abs(actual - reference)))
    summary["native_comparison"] = (
        {"loop_max_abs_error_v_per_v": errors["loop"], "closed_max_abs_error_ohm": errors["closed"]}
        if required
        else None
    )
    summary["native_step_comparison"] = None
    if summary["linear_model_stable"]:
        times: FloatArray = np.linspace(0, 0.1, 201)
        samples = step_response(times, model, current_a=1e-9)
        np.savetxt(
            root / "linear_step.csv",
            np.column_stack((times, samples)),
            delimiter=",",
            header="time_s,dummy_common_v_for_1na_step",
            comments="",
        )
        netlist = export_bias_spice(root / "step" / "network.cir", model, mode="step")
        if required:
            summary["native_step_comparison"] = _compare_bias_step(netlist, model)
    return summary


def _compare_bias_step(netlist: Path, model: BiasModel) -> dict[str, float | int]:
    """Compare a native zero-state trace against sampled matrix exponentials.

    Both a logarithmic early-time selection and a uniform whole-trace selection
    are checked; the uniform interpolated native table is retained. Not all rows are checked.
    """
    times, actual = run_ngspice_transient(netlist, netlist.parent, columns=2)
    if times[0] > 1e-6 or abs(float(times[-1]) - 0.1) > 1e-12:
        raise RuntimeError("BIAS transient does not cover the requested time window")
    indexes = np.unique(
        np.concatenate(
            (
                np.linspace(0, len(times) - 1, 256, dtype=np.int64),
                np.geomspace(1, len(times), 128).astype(np.int64) - 1,
            )
        )
    )
    expected = step_voltages(times[indexes], model, current_a=1e-9)
    if not np.allclose(actual[indexes], expected, rtol=1e-4, atol=1e-9):
        raise RuntimeError("BIAS transient and matrix-exponential step disagree")
    errors: FloatArray = np.max(np.abs(actual[indexes] - expected), axis=0)
    return {
        "common_max_abs_error_v": float(errors[0]),
        "output_max_abs_error_v": float(errors[1]),
        "compared_points": len(indexes),
        "native_points": len(times),
        "comparison_rtol": 1e-4,
        "comparison_atol_v": 1e-9,
        "export_grid_s": 2e-6,
        "max_internal_step_s": 200e-9,
    }


def _sweep(model: BiasModel) -> list[dict[str, object]]:
    # These are sampled assumptions, not component tolerances or confidence bounds.
    rows: list[dict[str, object]] = []
    for contact in (10e3, 50e3, 1e6, 10e6):
        for cable in (100e-12, 1e-9, 10e-9):
            for gbw in (50e3, 100e3, 200e3):
                for gain in (1e4, 1e5, 1e6):
                    varied = replace(
                        model,
                        contacts_ohm=(contact,) * 8,
                        lead_c_f=cable,
                        input_c_f=cable,
                        gbw_hz=gbw,
                        open_loop_gain=gain,
                    )
                    poles = closed_poles(varied)
                    rows.append(
                        {
                            "contact_each_ohm": contact,
                            "lead_and_input_each_c_f": cable,
                            "assumed_gbw_hz": gbw,
                            "assumed_open_loop_gain": gain,
                            "rightmost_pole_real_per_s": float(np.max(poles.real)),
                        }
                    )
    return rows


def _dynamics_artifacts(root: Path, model: BiasModel, required: bool) -> dict[str, object]:
    root.mkdir()
    return {
        f"extra_pole_{pole:g}hz": _case_artifacts(
            root / f"extra_pole_{pole:g}hz", replace(model, extra_pole_hz=pole), required
        )
        for pole in (100.0, 1000.0, 100000.0)
    }


def _execution_identity(required: bool) -> dict[str, object]:
    root = Path(__file__).resolve().parents[1]
    native: str | None = None
    if required:
        executable = shutil.which("ngspice")
        if executable is None:
            raise RuntimeError("ngspice is absent")
        native = subprocess.run(
            [executable, "--version"], capture_output=True, text=True, timeout=5, check=True
        ).stdout.strip()
    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "ngspice": native,
        "model_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "uv_lock_sha256": hashlib.sha256((root / "uv.lock").read_bytes()).hexdigest(),
    }


def run_bias_study(
    out: str | Path, *, require_ngspice: bool = False, run_id: str | None = None
) -> Path:
    """Claim a unique directory and publish its manifest last; no mutable current alias.

    A caller verifies exit status and uses only the returned path/run ID. Failed
    attempts retain partial evidence but cannot publish a completion manifest.
    """
    identity = uuid4().hex if run_id is None else run_id
    if re.fullmatch(r"[0-9a-f]{32}", identity) is None:
        raise ValueError("run ID must contain 32 lowercase hexadecimal characters")
    if not isinstance(require_ngspice, bool):
        raise ValueError("require_ngspice must be boolean")
    model = load_bias_model()
    source_path = Path(__file__).resolve().parents[1] / "docs/references/ti/bias/source_record.json"
    source_bytes = source_path.read_bytes()
    execution = _execution_identity(require_ngspice)
    root = Path(out) / identity
    root.parent.mkdir(parents=True, exist_ok=True)
    root.mkdir()  # exclusive claim: never reuse or overwrite another generation
    summary: dict[str, object] = {
        "schema_version": 1,
        "study": "rev_a_bounded_linear_bias",
        "run_id": identity,
        "native_status": "executed_and_compared" if require_ngspice else "not_requested",
        "source_record_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "execution": execution,
        "baseline_sha256": model.baseline_sha256,
        "cases": {
            name: _case_artifacts(root / name, case, require_ngspice)
            for name, case in scenarios(model).items()
        },
        "sensitivity_samples": _sweep(model),
        "amplifier_dynamics_cases": _dynamics_artifacts(root / "dynamics", model, require_ngspice),
        "hardware_validated": False,
        "body_connection_permitted": False,
        "limitations": [
            "Unmeasured electrical dummy loads; not calibrated MCScap/scalp parameters.",
            "Assumed one/two-pole amplifier families and ideal PGA buffers, not a silicon model.",
            "For added-pole cases gbw_hz is the dominant gain product, not total unity-gain bandwidth.",
            "Linear steps are not power-up, slew/current limits or saturation recovery.",
            "Sampled assumptions do not establish global stability or physical safety.",
            "No TINA attachment was imported or executed; published topology was reconstructed.",
        ],
    }
    (root / "source_record.json").write_bytes(source_bytes)
    _write_json(root / "study.json", summary)
    manifest = {
        "schema_version": 1,
        "run_id": identity,
        "files": {
            p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*")
            if p.is_file()
        },
    }
    staged = root / ".manifest.tmp"
    _write_json(staged, manifest)
    staged.replace(root / "manifest.json")
    return root


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("reports/rev_a_bias"))
    parser.add_argument("--require-ngspice", action="store_true")
    parser.add_argument("--run-id")
    args = parser.parse_args(argv)
    try:
        root = run_bias_study(args.out, require_ngspice=args.require_ngspice, run_id=args.run_id)
    except (ValueError, RuntimeError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"run_id": root.name, "report": str(root / "study.json")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
