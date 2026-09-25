"""One-pole BIAS output rail/slew hypotheses, NOT ADS1299 overload specifications.

All node voltages are deviations from the midpoint. No supply startup, current
limiting, PGA clipping, input protection or human-use validation is represented.
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
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Literal
from uuid import uuid4

import numpy as np
import scipy
from scipy.integrate import solve_ivp

from .analog import run_ngspice_transient
from .data_types import FloatArray
from .rev_a_bias import BiasModel, bias_network_lines, load_bias_model, scenarios, state_matrices

_Mode = Literal["free", "lower", "upper"]
_EventName = Literal["lower", "upper", "release"]


def _finite(value: float) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)


@dataclass(frozen=True, slots=True)
class OutputLimits:
    """Assumed output deviations; default +/-2 V is NOT the BIAS input range.

    Default slew is the datasheet typical 0.07 V/us, not a guaranteed limit.
    This is an output-state projection hypothesis, not measured chip recovery.
    """

    lower_v: float = -2.0
    upper_v: float = 2.0
    slew_v_per_s: float = 70_000.0

    def __post_init__(self) -> None:
        if not all(_finite(v) for v in (self.lower_v, self.upper_v, self.slew_v_per_s)):
            raise ValueError("output limits must be finite real numbers")
        if not self.lower_v < 0 < self.upper_v or self.slew_v_per_s <= 0:
            raise ValueError("rails must contain zero and slew must be positive")
        # Absolute Radau state tolerance is 1e-10 V. Nanovolt-scale saturation
        # is outside this bounded experiment, not a supported device hypothesis.
        if min(-self.lower_v, self.upper_v) < 1e-6:
            raise ValueError("rails must be at least 1 uV from zero for this numerical model")


_DEFAULT_LIMITS = OutputLimits()


@dataclass(frozen=True, slots=True)
class InterferencePulse:
    """A known electrical dummy current: finite linear edges, no person involved."""

    amplitude_a: float = 5e-6
    on_s: float = 0.001
    off_s: float = 0.006
    rise_s: float = 1e-6

    def __post_init__(self) -> None:
        if not all(_finite(v) for v in (self.amplitude_a, self.on_s, self.off_s, self.rise_s)):
            raise ValueError("pulse values must be finite real numbers")
        if self.on_s < 0 or self.rise_s <= 0 or self.on_s + self.rise_s >= self.off_s:
            raise ValueError("pulse requires nonnegative onset and separated positive edges")

    def current(self, times: FloatArray) -> FloatArray:
        return np.asarray(
            np.interp(
                times,
                [self.on_s, self.on_s + self.rise_s, self.off_s, self.off_s + self.rise_s],
                [0, self.amplitude_a, self.amplitude_a, 0],
            ),
            dtype=np.float64,
        )


@dataclass(frozen=True, slots=True)
class OverloadTrace:
    time_s: FloatArray
    state_v: FloatArray
    limits: OutputLimits
    rail_events: tuple[tuple[float, _EventName], ...]

    def __post_init__(self) -> None:
        times = np.array(self.time_s, dtype=np.float64, copy=True)
        states = np.array(self.state_v, dtype=np.float64, copy=True)
        _validate_times(times)
        if states.shape != (len(times), 12) or not np.all(np.isfinite(states)):
            raise ValueError("trace requires twelve finite circuit states per time")
        if np.any(states[:, 11] < self.limits.lower_v - 1e-8) or np.any(
            states[:, 11] > self.limits.upper_v + 1e-8
        ):
            raise ValueError("projected output exceeded its assumed rails")
        events = tuple((time, name) for time, name in self.rail_events)
        previous = 0.0
        for time, name in events:
            if (
                not _finite(time)
                or not previous <= time <= times[-1]
                or name not in ("lower", "upper", "release")
            ):
                raise ValueError("invalid or unordered rail event")
            previous = time
        times.flags.writeable = states.flags.writeable = False
        object.__setattr__(self, "time_s", times)
        object.__setattr__(self, "state_v", states)
        object.__setattr__(self, "rail_events", events)


def _validate_times(times: FloatArray) -> None:
    if times.ndim != 1 or times.size < 2 or not np.all(np.isfinite(times)):
        raise ValueError("time must be a finite one-dimensional array with at least two samples")
    if times[0] != 0 or np.any(np.diff(times) <= 0) or times[-1] > 1:
        raise ValueError("time must start at zero, increase strictly and end within one second")


@dataclass(frozen=True, slots=True)
class _Segment:
    start: float
    stop: float
    initial_a: float
    rate_a_per_s: float

    def current(self, time: float) -> float:
        return self.initial_a + self.rate_a_per_s * (time - self.start)


def _segments(pulse: InterferencePulse, stop: float) -> list[_Segment]:
    points = [
        0.0,
        pulse.on_s,
        pulse.on_s + pulse.rise_s,
        pulse.off_s,
        pulse.off_s + pulse.rise_s,
        stop,
    ]
    values = [0.0, 0.0, pulse.amplitude_a, pulse.amplitude_a, 0.0, 0.0]
    return [
        _Segment(a, b, va, (vb - va) / (b - a))
        for a, b, va, vb in zip(points[:-1], points[1:], values[:-1], values[1:], strict=True)
        if b > a
    ]


@dataclass(frozen=True, slots=True)
class _Dynamics:
    matrix: FloatArray
    drive: FloatArray
    segment: _Segment
    limits: OutputLimits
    mode: _Mode

    def raw_rate(self, time: float, state: FloatArray) -> float:
        derivative: FloatArray = self.matrix @ state + self.drive * self.segment.current(time)
        return float(derivative[11])

    def __call__(self, time: float, state: FloatArray) -> FloatArray:
        derivative = self.matrix @ state + self.drive * self.segment.current(time)
        raw = float(derivative[11])
        limited = (
            max(-self.limits.slew_v_per_s, min(raw, self.limits.slew_v_per_s))
            if self.mode == "free"
            else 0.0
        )
        # Cf stores vm-out. Change both derivatives by the same correction,
        # so projection does not inject fictitious charge into the feedback capacitor.
        derivative[10] = float(derivative[10]) + limited - raw
        derivative[11] = limited
        return np.asarray(derivative, dtype=np.float64)


@dataclass(frozen=True, slots=True)
class _Event:
    dynamics: _Dynamics
    name: _EventName
    direction: float
    terminal: bool = True

    def __call__(self, time: float, state: FloatArray) -> float:
        if self.name == "release":
            return self.dynamics.raw_rate(time, state)
        bound = (
            self.dynamics.limits.upper_v if self.name == "upper" else self.dynamics.limits.lower_v
        )
        return float(state[11]) - bound


def _mode(state: FloatArray, rate: float, limits: OutputLimits) -> _Mode:
    if state[11] >= limits.upper_v and rate > 0:
        return "upper"
    if state[11] <= limits.lower_v and rate < 0:
        return "lower"
    return "free"


def _integrate_segment(
    times: FloatArray,
    states: FloatArray,
    initial: FloatArray,
    dynamics: _Dynamics,
    max_step_s: float,
) -> tuple[FloatArray, list[tuple[float, _EventName]]]:
    time, stop = dynamics.segment.start, dynamics.segment.stop
    state = initial.copy()
    mode = _mode(state, dynamics.raw_rate(time, state), dynamics.limits)
    recorded: list[tuple[float, _EventName]] = []
    for _ in range(64):
        active = replace(dynamics, mode=mode)
        events = (
            [_Event(active, "upper", 1), _Event(active, "lower", -1)]
            if mode == "free"
            else [_Event(active, "release", -1 if mode == "upper" else 1)]
        )
        result = solve_ivp(
            active,
            (time, stop),
            state,
            method="Radau",
            rtol=1e-8,
            atol=1e-10,
            max_step=max_step_s,
            events=events,
            dense_output=True,
        )
        if not result.success or result.sol is None:
            raise RuntimeError(f"overload integration failed: {result.message}")
        end = float(result.t[-1])
        _record_observations(times, states, time, end, result.sol)
        state = np.asarray(result.y[:, -1], dtype=np.float64)
        if result.status == 1:
            mode, name = _transition(mode, state, active.limits)
            recorded.append((end, name))
        if end == stop:
            return state, recorded
        if end <= time:
            raise RuntimeError("overload event integration made no time progress")
        time = end
    raise RuntimeError("overload integration exceeded the bounded event count")


def _record_observations(
    times: FloatArray,
    states: FloatArray,
    start: float,
    stop: float,
    solution: Callable[[FloatArray], FloatArray],
) -> None:
    """Sparse observation grids need not sample every integration segment."""
    selected = (times >= start) & (times <= stop)
    if np.any(selected):
        states[selected] = np.asarray(solution(times[selected]).T, dtype=np.float64)


def _transition(mode: _Mode, state: FloatArray, limits: OutputLimits) -> tuple[_Mode, _EventName]:
    if mode != "free":
        return "free", "release"
    bound: Literal["lower", "upper"] = "upper" if state[11] > 0 else "lower"
    target = limits.upper_v if bound == "upper" else limits.lower_v
    correction = target - float(state[11])
    state[10] = float(state[10]) + correction
    state[11] = target
    return bound, bound


def overload_response(
    time_s: FloatArray,
    model: BiasModel,
    pulse: InterferencePulse,
    limits: OutputLimits = _DEFAULT_LIMITS,
    *,
    max_step_s: float = 20e-6,
) -> OverloadTrace:
    """Hybrid Radau integration; hard-rail events retain all capacitor state.

    At a rail only outward motion is blocked. Release occurs when the circuit's
    requested output slope points inward. No hidden recovery delay is invented.
    """
    times = np.asarray(time_s, dtype=np.float64)
    _validate_times(times)
    if model.extra_pole_hz is not None:
        raise ValueError("only the one-pole amplifier has a defined projection hypothesis")
    if pulse.off_s + pulse.rise_s >= times[-1]:
        raise ValueError("time window must extend past the complete pulse")
    if not _finite(max_step_s) or max_step_s <= 0:
        raise ValueError("integration maximum step must be finite and positive")
    matrix, drive = state_matrices(model)
    state = np.zeros(12, dtype=np.float64)
    states = np.full((len(times), 12), np.nan, dtype=np.float64)
    recorded: list[tuple[float, _EventName]] = []
    for segment in _segments(pulse, float(times[-1])):
        dynamics = _Dynamics(matrix, drive, segment, limits, "free")
        state, events = _integrate_segment(times, states, state, dynamics, max_step_s)
        recorded.extend(events)
    return OverloadTrace(times, states, limits, tuple(recorded))


def export_overload_spice(
    path: str | Path,
    model: BiasModel,
    pulse: InterferencePulse,
    limits: OutputLimits = _DEFAULT_LIMITS,
    *,
    stop_s: float = 0.035,
    max_step_s: float = 100e-9,
) -> Path:
    """Independent behavioral-current integrator over the shared passive topology."""
    if model.extra_pole_hz is not None:
        raise ValueError("only the one-pole amplifier has a defined projection hypothesis")
    if not _finite(stop_s) or not pulse.off_s + pulse.rise_s < stop_s <= 1:
        raise ValueError("stop must follow the pulse and be at most one second")
    if not _finite(max_step_s) or max_step_s <= 0:
        raise ValueError("maximum timestep must be finite and positive")
    pwl = " ".join(
        f"{t:.15g} {i:.15g}"
        for t, i in zip(
            [
                0,
                pulse.on_s,
                pulse.on_s + pulse.rise_s,
                pulse.off_s,
                pulse.off_s + pulse.rise_s,
                stop_s,
            ],
            [0, 0, pulse.amplitude_a, pulse.amplitude_a, 0, 0],
            strict=True,
        )
    )
    omega = 2 * math.pi * model.gbw_hz / model.open_loop_gain
    lines = [
        "Assumed BIAS rail/slew projection -- electrical dummy model ONLY",
        "* Rails and projection topology are assumptions, not ADS1299 recovery specifications.",
        f"Iinterference 0 common PWL({pwl})",
        *bias_network_lines(model),
        f"Brate rate 0 V={{min(max(-{omega:.15g}*(v(state)+{model.open_loop_gain:.15g}*v(vm)),"
        f" -{limits.slew_v_per_s:.15g}),{limits.slew_v_per_s:.15g})}}",
        f"Bproject 0 state I={{(v(state)>={limits.upper_v:.15g} && v(rate)>0) || "
        f"(v(state)<={limits.lower_v:.15g} && v(rate)<0) ? 0 : v(rate)}}",
        "Cstate state 0 1 IC=0",
        "Eoutput out 0 state 0 1",
        ".save v(common) v(out) v(vm)",
        ".options reltol=1e-9 vntol=1e-10 abstol=1e-14 method=gear",
        ".control",
        "set wr_singlescale",
        "set wr_vecnames",
        "set numdgt=15",
        f"tran 1n {stop_s:.15g} 0 {max_step_s:.15g} uic",
        "let integration_start = time[0]",
        "let integration_stop = time[length(time)-1]",
        "print integration_start integration_stop > transient-window.txt",
        "let lin-tstart = 0",
        f"let lin-tstop = {stop_s:.15g}",
        "let lin-tstep = 2u",
        "linearize v(common) v(out) v(vm)",
        "wrdata transient.txt v(common) v(out) v(vm)",
        "quit",
        ".endc",
        ".end",
        "",
    ]
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines), encoding="utf-8")
    return target


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )


def _native_compare(
    netlist: Path, model: BiasModel, pulse: InterferencePulse, limits: OutputLimits
) -> dict[str, object]:
    times, actual = run_ngspice_transient(netlist, netlist.parent, columns=3, expected_stop_s=0.035)
    if times[0] != 0 or abs(float(times[-1]) - 0.035) > 1e-12:
        raise RuntimeError("overload transient does not cover the requested time window")
    grid = np.linspace(0, 0.035, 17501)
    if times.shape != grid.shape or not np.allclose(times, grid, rtol=0, atol=1e-12):
        raise RuntimeError("Invalid native overload observation grid: expected 2 us samples")
    expected = overload_response(times, model, pulse, limits).state_v[:, [1, 11, 10]]
    # Switching introduces finite-step boundary error: 100 uV is the declared
    # large-pulse numerical comparison tolerance, not a hardware accuracy claim.
    atol = 1e-9 if abs(pulse.amplitude_a) <= 1e-9 else 1e-4
    if not np.allclose(actual, expected, rtol=2e-4, atol=atol):
        raise RuntimeError(
            f"ngspice and hybrid ODE overload traces disagree: {netlist.parent.parent.name}"
        )
    if np.min(actual[:, 1]) < limits.lower_v - 1e-4 or np.max(actual[:, 1]) > limits.upper_v + 1e-4:
        raise RuntimeError("native output exceeds the declared numerical rail tolerance")
    return {
        "points_compared": len(times),
        "rtol": 2e-4,
        "atol_v": atol,
        "max_abs_error_common_output_summing_v": np.max(np.abs(actual - expected), axis=0).tolist(),
    }


def _case(
    root: Path, model: BiasModel, pulse: InterferencePulse, limits: OutputLimits, required: bool
) -> dict[str, object]:
    root.mkdir()
    times = np.linspace(0, 0.035, 3501)
    result = overload_response(times, model, pulse, limits)
    np.savetxt(
        root / "response.csv",
        np.column_stack((times, result.state_v)),
        delimiter=",",
        header="time_s,lead,common,i0,i1,i2,i3,i4,i5,i6,i7,summing,output",
        comments="",
    )
    netlist = export_overload_spice(root / "native" / "network.cir", model, pulse, limits)
    return {
        "model": asdict(model),
        "pulse": asdict(pulse),
        "limits": asdict(limits),
        "rail_events_s": result.rail_events,
        "final_common_output_v": result.state_v[-1, [1, 11]].tolist(),
        "native_comparison": _native_compare(netlist, model, pulse, limits) if required else None,
    }


def _execution_metadata(required: bool) -> dict[str, object]:
    root = Path(__file__).resolve().parents[1]
    native = None
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
        "uv_lock_sha256": hashlib.sha256((root / "uv.lock").read_bytes()).hexdigest(),
        "model_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "linear_model_source_sha256": hashlib.sha256(
            Path(__file__).with_name("rev_a_bias.py").read_bytes()
        ).hexdigest(),
    }


def run_overload_study(
    out: str | Path, *, require_ngspice: bool = False, run_id: str | None = None
) -> Path:
    """Retain unique generation artifacts; a manifest exists only after all work succeeds."""
    identity = uuid4().hex if run_id is None else run_id
    if re.fullmatch(r"[0-9a-f]{32}", identity) is None or not isinstance(require_ngspice, bool):
        raise ValueError("a 32-hex run ID and boolean native request are required")
    model = load_bias_model()
    source = Path(__file__).resolve().parents[1] / "docs/references/ti/bias/overload_sources.json"
    source_bytes = source.read_bytes()
    root = Path(out) / identity
    root.parent.mkdir(parents=True, exist_ok=True)
    root.mkdir()
    pulse, limits = InterferencePulse(), OutputLimits()
    configurations = {
        "small_signal": (model, replace(pulse, amplitude_a=1e-9), limits),
        "positive_overload": (model, pulse, limits),
        "negative_overload": (model, replace(pulse, amplitude_a=-5e-6), limits),
        "slow_slew_hypothesis": (model, pulse, replace(limits, slew_v_per_s=100.0)),
        **{
            name: (case, pulse, limits)
            for name, case in scenarios(model).items()
            if name in ("asymmetric", "open_input", "open_bias")
        },
    }
    cases = {
        name: _case(root / name, case, stimulus, bounds, require_ngspice)
        for name, (case, stimulus, bounds) in configurations.items()
    }
    (root / "source_record.json").write_bytes(source_bytes)
    _write_json(
        root / "study.json",
        {
            "schema_version": 1,
            "study": "assumed_one_pole_bias_output_projection",
            "run_id": identity,
            "native_status": "executed_and_compared" if require_ngspice else "not_requested",
            "execution": _execution_metadata(require_ngspice),
            "baseline_sha256": model.baseline_sha256,
            "cases": cases,
            "hardware_validated": False,
            "body_connection_permitted": False,
            "limitations": [
                "Unmeasured output rail/projection topology and dummy loads.",
                "Typical slew is not guaranteed; 100 V/s is a deliberately slow hypothesis.",
                "No input/PGA clipping, current limiting, supply startup or chip recovery validation.",
                "Finite window end values do not establish global recovery or stability.",
            ],
        },
    )
    files = {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in root.rglob("*")
        if p.is_file()
    }
    staged = root / ".manifest.tmp"
    _write_json(staged, {"schema_version": 1, "run_id": identity, "files": files})
    staged.replace(root / "manifest.json")
    return root


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("reports/rev_a_bias_overload"))
    parser.add_argument("--require-ngspice", action="store_true")
    parser.add_argument("--run-id")
    args = parser.parse_args(argv)
    try:
        root = run_overload_study(
            args.out, require_ngspice=args.require_ngspice, run_id=args.run_id
        )
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"run": str(root), "hardware_validated": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
