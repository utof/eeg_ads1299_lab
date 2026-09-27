"""Bounded shared-source analog-feed hypothesis, not a regulator or hardware approval."""

import argparse
import hashlib
import json
import math
import sys
from dataclasses import asdict, dataclass, fields, replace
from itertools import pairwise
from pathlib import Path
from uuid import uuid4

import numpy as np

from hardware.rev_a import load_documents, validate

from .analog import run_ngspice_transient
from .data_types import FloatArray
from .validation import stored_array

_EDGE = 1e-9
_COMPARISON_V = 1e-4


@dataclass(frozen=True, slots=True)
class SupplyTiming:
    """Explicit ideal-edge experiment schedule, never a device startup requirement.

    Defaults preserve the historical 1/8/12/20 ms fixture and its 4..20 ms
    observation interval. Observation does not change source/load waveforms.
    """

    source_on_s: float = 0.001
    burst_on_s: float = 0.008
    burst_off_s: float = 0.012
    stop_s: float = 0.02
    observation_s: tuple[float, float] = (0.004, 0.02)

    def __post_init__(self) -> None:
        events = (self.source_on_s, self.burst_on_s, self.burst_off_s, self.stop_s)
        for value in events:
            _finite_time(value)
        for start, stop in pairwise(events):
            # The actual native source uses a 1 ns edge. It must be representable
            # and finish before the next phase, not silently overlap or vanish.
            if not start < start + _EDGE < stop:
                raise ValueError("timing phases must be ordered and longer than the native edge")
        if not isinstance(self.observation_s, tuple) or len(self.observation_s) != 2:
            raise ValueError("observation_s must be a pair of times")
        for value in self.observation_s:
            _finite_time(value)
        begin, end = self.observation_s
        if not self.source_on_s < begin < end <= self.stop_s:
            raise ValueError("observation must start after source-on and end within the study")


def _finite_time(value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("timing must contain finite nonnegative real numbers")
    if not math.isfinite(value) or value < 0:
        raise ValueError("timing must contain finite nonnegative real numbers")


_DEFAULT_TIMING = SupplyTiming()


@dataclass(frozen=True, slots=True)
class SupplyCase:
    """Conductance loads and effective capacitance are assumptions, not measurements.

    MCU conductance is on the shared bus, upstream of the analog feed. burst_g_s
    is ADDED to idle_g_s; it is not the total conductance during a burst.
    """

    source_v: float = 4.95
    feed_r_ohm: float = 10.0
    shared_r_ohm: float = 0.1
    capacitance_f: float = 10e-6
    analog_g_s: float = 0.002
    idle_g_s: float = 0.02
    burst_g_s: float = 0.08

    def __post_init__(self) -> None:
        for field in fields(self):
            value: object = getattr(self, field.name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
            ):
                raise ValueError(f"{field.name} must be a finite real number")
            positive = field.name in ("source_v", "feed_r_ohm", "capacitance_f")
            if value < 0 or (positive and value == 0):
                raise ValueError(f"invalid physical parameter: {field.name}")


def steady_state(case: SupplyCase, *, burst: bool = False) -> tuple[float, float]:
    """Return AVDD equilibrium (V) and loaded time constant (s), via Thevenin.

    Looking upstream from the feed: Vth=Vs/(1+Rs*Gm), Rth=Rs/(1+Rs*Gm).
    The analog conductance loads that source and also shortens its RC time constant.
    """
    if not isinstance(burst, bool):
        raise ValueError("burst must be boolean")
    mcu_g = case.idle_g_s + (case.burst_g_s if burst else 0.0)
    divider = 1 + case.shared_r_ohm * mcu_g
    resistance = case.feed_r_ohm + case.shared_r_ohm / divider
    loading = 1 + case.analog_g_s * resistance
    voltage = (case.source_v / divider) / loading
    tau = (resistance / loading) * case.capacitance_f
    if not math.isfinite(voltage) or voltage <= 0 or not math.isfinite(tau) or tau <= 0:
        raise ValueError("parameter combination exceeds the finite numerical domain")
    return voltage, tau


def rail_response(
    case: SupplyCase, times_s: FloatArray, *, timing: SupplyTiming = _DEFAULT_TIMING
) -> FloatArray:
    """Exact ideal-edge response for the explicit schedule on an increasing grid.

    The capacitor starts uncharged. Event states do not depend on query spacing
    or on the observation interval; the defaults preserve the historical trace.
    """
    times = stored_array(times_s, np.float64, 1, "times_s")
    if times.size == 0 or times[0] < 0 or times[-1] > timing.stop_s or np.any(np.diff(times) <= 0):
        raise ValueError("times_s must increase within the requested study window")
    idle, tau_idle = steady_state(case)
    burst, tau_burst = steady_state(case, burst=True)
    volts = np.zeros_like(times)
    initial = 0.0
    for start, stop, final, tau in (
        (timing.source_on_s, timing.burst_on_s, idle, tau_idle),
        (timing.burst_on_s, timing.burst_off_s, burst, tau_burst),
        (timing.burst_off_s, timing.stop_s, idle, tau_idle),
    ):
        selected = (times >= start) & (times <= stop)
        volts[selected] = initial + (final - initial) * -np.expm1(-(times[selected] - start) / tau)
        initial += (final - initial) * -math.expm1(-(stop - start) / tau)
    return volts


def supply_netlist(case: SupplyCase, *, timing: SupplyTiming = _DEFAULT_TIMING) -> str:
    """Two-node circuit, independent of the reduced analytical equation.

    One-nanosecond edges make native breakpoints explicit. The analytical step
    is ideal; the fixed five-case comparison allows 100uV, not exact equivalence.
    A zero-ohm shared source is represented by a zero-volt source, not a tiny R.
    """
    steady_state(case)
    steady_state(case, burst=True)
    shared = (
        "Vshared source bus 0"
        if case.shared_r_ohm == 0
        else f"Rshared source bus {case.shared_r_ohm:.17g}"
    )
    return f"""Assumed shared-source analog feed -- NOT a hardware validation
Vsource source 0 PWL(0 0 {timing.source_on_s:.17g} 0 {timing.source_on_s + _EDGE:.17g} {case.source_v:.17g} {timing.stop_s:.17g} {case.source_v:.17g})
{shared}
Rfeed bus avdd {case.feed_r_ohm:.17g}
Vburst control 0 PWL(0 0 {timing.burst_on_s:.17g} 0 {timing.burst_on_s + _EDGE:.17g} 1 {timing.burst_off_s:.17g} 1 {timing.burst_off_s + _EDGE:.17g} 0 {timing.stop_s:.17g} 0)
Bmcu bus 0 I={{v(bus)*({case.idle_g_s:.17g}+{case.burst_g_s:.17g}*v(control))}}
Banalog avdd 0 I={{v(avdd)*{case.analog_g_s:.17g}}}
Cbulk avdd 0 {case.capacitance_f:.17g}
.options reltol=1e-8 abstol=1e-12 vntol=1e-10
.control
set wr_singlescale
set wr_vecnames
set numdgt=15
tran 1u {timing.stop_s:.17g} 0 1u
let integration_start = time[0]
let integration_stop = time[length(time)-1]
print integration_start integration_stop > transient-window.txt
wrdata transient.txt v(avdd)
quit
.endc
.end
"""


def _window_extrema(case: SupplyCase, timing: SupplyTiming) -> tuple[float, float]:
    # Each first-order phase is monotonic. Only events INSIDE the requested
    # observation interval constrain it; earlier charging history still matters.
    begin, end = timing.observation_s
    times = np.array(
        sorted(
            {begin, end} | {t for t in (timing.burst_on_s, timing.burst_off_s) if begin < t < end}
        )
    )
    volts = rail_response(case, times, timing=timing)
    return float(np.min(volts)), float(np.max(volts))


def source_voltage_window(
    case: SupplyCase, limits_v: tuple[float, float], *, timing: SupplyTiming = _DEFAULT_TIMING
) -> tuple[float, float]:
    """Source interval meeting rail limits throughout the requested observation window.

    Return (required source minimum, allowed source maximum). Lower > upper
    means EMPTY, not a reversed feasible interval. The case's source_v is ignored:
    this linear conductance/ideal-C hypothesis is solved at unit source voltage.
    This is neither a supply recommendation nor a capacitor/boot qualification.
    """
    if not isinstance(limits_v, tuple) or len(limits_v) != 2:
        raise ValueError("limits_v must be a pair of positive ordered rail limits")
    for value in limits_v:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("rail limits must be finite real numbers")
        if not math.isfinite(value) or value <= 0:
            raise ValueError("rail limits must be positive finite numbers")
    if limits_v[0] > limits_v[1]:
        raise ValueError("rail limits must be ordered")
    low_factor, high_factor = _window_extrema(replace(case, source_v=1.0), timing)
    if low_factor <= 0:
        raise ValueError("unit rail response exceeds the finite numerical domain")
    lower, upper = limits_v[0] / low_factor, limits_v[1] / high_factor
    if not math.isfinite(lower) or not math.isfinite(upper):
        raise ValueError("source interval exceeds the finite numerical domain")
    return lower, upper


def _model_metrics(
    case: SupplyCase,
    limits_v: tuple[float, float],
    timing: SupplyTiming,
    source_range_v: tuple[float, float],
) -> dict[str, object]:
    low, high = _window_extrema(case, timing)
    source_low, source_high = source_voltage_window(case, limits_v, timing=timing)
    idle_v, idle_tau = steady_state(case)
    burst_v, burst_tau = steady_state(case, burst=True)
    return {
        "idle_equilibrium_v": idle_v,
        "burst_equilibrium_v": burst_v,
        "idle_time_constant_s": idle_tau,
        "burst_time_constant_s": burst_tau,
        "model_window_min_v": low,
        "model_window_max_v": high,
        "model_lower_margin_v": low - limits_v[0],
        "model_source_window_v": [source_low, source_high],
        "model_source_window_feasible": source_low <= source_high,
        "model_source_range_covered": source_low <= source_range_v[0]
        and source_high >= source_range_v[1],
        "model_margin_ok": limits_v[0] <= low and high <= limits_v[1],
    }


def _check_observation_window(times: FloatArray, timing: SupplyTiming) -> None:
    if times[0] > 1e-8 or not math.isclose(
        float(times[-1]), timing.stop_s, rel_tol=0, abs_tol=1e-12
    ):
        raise RuntimeError("incomplete observed supply window")
    for start, stop in (
        (timing.source_on_s, timing.burst_on_s),
        (timing.burst_on_s, timing.burst_off_s),
        (timing.burst_off_s, timing.stop_s),
    ):
        if np.count_nonzero((times > start) & (times < stop)) < 2:
            raise RuntimeError("insufficient supply observations in a requested phase")


def _run_case(
    root: Path,
    case: SupplyCase,
    limits_v: tuple[float, float],
    timing: SupplyTiming,
    source_range_v: tuple[float, float],
) -> dict[str, object]:
    root.mkdir()
    netlist = root / "network.cir"
    netlist.write_text(supply_netlist(case, timing=timing), encoding="utf-8")
    result: dict[str, object] = {
        "name": root.name,
        "parameters": asdict(case),
        **_model_metrics(case, limits_v, timing, source_range_v),
        "native_execution_complete": False,
        "native_comparison_passed": False,
        "outcome": "rejected",
        "error": None,
    }
    try:
        times, volts = run_ngspice_transient(
            netlist,
            root,
            columns=1,
            expected_stop_s=timing.stop_s,
            expected_vectors=("v(avdd)",),
        )
        _check_observation_window(times, timing)
        result["native_execution_complete"] = True
        expected = rail_response(case, times, timing=timing)
        error = float(np.max(np.abs(volts[:, 0] - expected)))
        passed = error <= _COMPARISON_V
        np.savetxt(
            root / "comparison.csv",
            np.column_stack((times, expected, volts[:, 0])),
            delimiter=",",
            header="time_s,analytical_avdd_v,ngspice_avdd_v",
            comments="",
        )
        result.update(
            {
                "rows": len(times),
                "last_time_s": float(times[-1]),
                "max_abs_error_v": error,
                "native_comparison_passed": passed,
                "outcome": "comparison_passed" if passed else "comparison_mismatch",
                "error": None
                if passed
                else "native trajectory differs from the analytical hypothesis",
            }
        )
    except (RuntimeError, ValueError) as exc:
        result["error"] = str(exc)
    return result


def run_supply_study(out: Path, *, timing: SupplyTiming = _DEFAULT_TIMING) -> Path:
    """Keep every fixed-case result before rejecting incomplete or mismatched native runs.

    A model rail-margin breach does NOT mean execution or comparison failed.
    Each invocation owns a unique directory; no old success is relabeled as new.
    """
    profile, bom, sources = load_documents()
    errors = validate(profile, bom, sources)
    if errors:
        raise ValueError("invalid hardware contract: " + "; ".join(errors))
    power = profile["power"]
    case = SupplyCase(
        source_v=power["external_source_nominal_v"]
        * (1 - power["external_source_tolerance_fraction"]),
        feed_r_ohm=power["analog_feed_resistance_ohm"],
        analog_g_s=power["analog_branch_design_current_budget_a"]
        / power["external_source_nominal_v"],
    )
    limits_v = (power["avdd_operating_min_v"], power["avdd_operating_max_v"])
    source_range_v = (
        case.source_v,
        power["external_source_nominal_v"] * (1 + power["external_source_tolerance_fraction"]),
    )
    cases = (
        ("stiff_source", replace(case, shared_r_ohm=0.0)),
        ("shared_0p1_ohm", case),
        ("shared_0p5_ohm", replace(case, shared_r_ohm=0.5)),
        ("shared_1_ohm", replace(case, shared_r_ohm=1.0)),
        ("bulk_100uf", replace(case, shared_r_ohm=1.0, capacitance_f=100e-6)),
    )
    root = out / uuid4().hex
    root.mkdir(parents=True)
    snapshot = json.dumps([profile, bom, sources], sort_keys=True, allow_nan=False).encode("utf-8")
    (root / "baseline.json").write_bytes(snapshot)
    results = [
        _run_case(root / name, value, limits_v, timing, source_range_v) for name, value in cases
    ]
    passed = all(result["native_comparison_passed"] is True for result in results)
    repository = Path(__file__).resolve().parents[1]
    report = {
        "schema_version": 1,
        "run_id": root.name,
        "purpose": "bounded_shared_source_analog_feed_hypothesis",
        "cases": results,
        "baseline_sha256": hashlib.sha256(snapshot).hexdigest(),
        "source_sha256": {
            name: hashlib.sha256((repository / name).read_bytes()).hexdigest()
            for name in ("lab/rev_a_supply.py", "lab/analog/_spice.py", "uv.lock")
        },
        "native_comparison_passed": passed,
        "comparison_tolerance_v": _COMPARISON_V,
        "native_edge_duration_s": _EDGE,
        "margin_window_s": list(timing.observation_s),
        "timing": asdict(timing),
        "configured_source_range_v": list(source_range_v),
        "operating_limits_v": list(limits_v),
        "hardware_validated": False,
        "body_connection_permitted": False,
        "limitations": [
            "Shared resistance, effective capacitance and MCU conductance are unmeasured assumptions.",
            "Analog load is a conductance calibrated to the current budget at nominal source voltage.",
            "Capacitors are ideal; no regulator, PSRR, ESR, ESL, radio trace or complete board is modeled.",
            "Timing and observation window are explicit hypotheses, not a device startup specification.",
            "100uV compares sampled native finite-edge traces to ideal steps, not physical accuracy.",
            "A comparison pass can expose a model margin breach; neither validates hardware.",
        ],
    }
    (root / "study.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    files = {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
    }
    (root / "manifest.json").write_text(
        json.dumps({"run_id": root.name, "files": files}, indent=2) + "\n"
    )
    if not passed:
        raise RuntimeError(f"Supply execution/comparison failed; evidence retained at {root}")
    return root


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("reports/rev_a_supply"))
    parser.add_argument("--source-on-ms", type=float, default=1.0)
    parser.add_argument("--burst-on-ms", type=float, default=8.0)
    parser.add_argument("--burst-off-ms", type=float, default=12.0)
    parser.add_argument("--stop-ms", type=float, default=20.0)
    parser.add_argument(
        "--observe-ms", type=float, nargs=2, default=[4.0, 20.0], metavar=("BEGIN", "END")
    )
    args = parser.parse_args()
    source_on_ms: float = args.source_on_ms
    burst_on_ms: float = args.burst_on_ms
    burst_off_ms: float = args.burst_off_ms
    stop_ms: float = args.stop_ms
    observe_ms: list[float] = args.observe_ms
    try:
        timing = SupplyTiming(
            source_on_s=source_on_ms / 1000,
            burst_on_s=burst_on_ms / 1000,
            burst_off_s=burst_off_ms / 1000,
            stop_s=stop_ms / 1000,
            observation_s=(observe_ms[0] / 1000, observe_ms[1] / 1000),
        )
        root = run_supply_study(args.out, timing=timing)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {"study": str(root), "native_comparison_passed": True, "hardware_validated": False}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
