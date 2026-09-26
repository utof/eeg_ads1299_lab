"""Bounded shared-source analog-feed hypothesis, not a regulator or hardware approval."""

import argparse
import hashlib
import json
import math
import sys
from dataclasses import asdict, dataclass, fields, replace
from pathlib import Path
from uuid import uuid4

import numpy as np

from hardware.rev_a import load_documents, validate

from .analog import run_ngspice_transient
from .data_types import FloatArray
from .validation import stored_array

_START = 0.001
_BURST_ON = 0.008
_BURST_OFF = 0.012
_STOP = 0.02
_MARGIN_START = 0.004
_EDGE = 1e-9
_COMPARISON_V = 1e-4


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


def rail_response(case: SupplyCase, times_s: FloatArray) -> FloatArray:
    """Exact ideal-edge response on any increasing float64 query grid in [0,20ms].

    The capacitor starts uncharged; source turns on at 1ms, added load at 8ms,
    and load removal at 12ms. Event states do not depend on query spacing.
    """
    times = stored_array(times_s, np.float64, 1, "times_s")
    if times.size == 0 or times[0] < 0 or times[-1] > _STOP or np.any(np.diff(times) <= 0):
        raise ValueError("times_s must increase within the 0..20ms study window")
    idle, tau_idle = steady_state(case)
    burst, tau_burst = steady_state(case, burst=True)
    volts = np.zeros_like(times)
    initial = 0.0
    for start, stop, final, tau in (
        (_START, _BURST_ON, idle, tau_idle),
        (_BURST_ON, _BURST_OFF, burst, tau_burst),
        (_BURST_OFF, _STOP, idle, tau_idle),
    ):
        selected = (times >= start) & (times <= stop)
        volts[selected] = initial + (final - initial) * -np.expm1(-(times[selected] - start) / tau)
        initial += (final - initial) * -math.expm1(-(stop - start) / tau)
    return volts


def supply_netlist(case: SupplyCase) -> str:
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
Vsource source 0 PWL(0 0 {_START:.17g} 0 {_START + _EDGE:.17g} {case.source_v:.17g} {_STOP:.17g} {case.source_v:.17g})
{shared}
Rfeed bus avdd {case.feed_r_ohm:.17g}
Vburst control 0 PWL(0 0 {_BURST_ON:.17g} 0 {_BURST_ON + _EDGE:.17g} 1 {_BURST_OFF:.17g} 1 {_BURST_OFF + _EDGE:.17g} 0 {_STOP:.17g} 0)
Bmcu bus 0 I={{v(bus)*({case.idle_g_s:.17g}+{case.burst_g_s:.17g}*v(control))}}
Banalog avdd 0 I={{v(avdd)*{case.analog_g_s:.17g}}}
Cbulk avdd 0 {case.capacitance_f:.17g}
.options reltol=1e-8 abstol=1e-12 vntol=1e-10
.control
set wr_singlescale
set wr_vecnames
set numdgt=15
tran 1u {_STOP:.17g} 0 1u
let integration_start = time[0]
let integration_stop = time[length(time)-1]
print integration_start integration_stop > transient-window.txt
wrdata transient.txt v(avdd)
quit
.endc
.end
"""


def _model_metrics(case: SupplyCase, limits_v: tuple[float, float]) -> dict[str, object]:
    # Each first-order phase is monotonic; endpoints include every continuous-time
    # extremum within this SPECIFIED post-startup window. This excludes power-up.
    times = np.array([_MARGIN_START, _BURST_ON, _BURST_OFF, _STOP])
    volts = rail_response(case, times)
    low, high = float(np.min(volts)), float(np.max(volts))
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
        "model_margin_ok": limits_v[0] <= low and high <= limits_v[1],
    }


def _check_observation_window(times: FloatArray) -> None:
    if times[0] > 1e-8 or not math.isclose(float(times[-1]), _STOP, rel_tol=0, abs_tol=1e-12):
        raise RuntimeError("incomplete observed supply window")
    for start, stop in ((_START, _BURST_ON), (_BURST_ON, _BURST_OFF), (_BURST_OFF, _STOP)):
        if np.count_nonzero((times > start) & (times < stop)) < 2:
            raise RuntimeError("insufficient supply observations in a requested phase")


def _run_case(root: Path, case: SupplyCase, limits_v: tuple[float, float]) -> dict[str, object]:
    root.mkdir()
    netlist = root / "network.cir"
    netlist.write_text(supply_netlist(case), encoding="utf-8")
    result: dict[str, object] = {
        "name": root.name,
        "parameters": asdict(case),
        **_model_metrics(case, limits_v),
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
            expected_stop_s=_STOP,
            expected_vectors=("v(avdd)",),
        )
        _check_observation_window(times)
        result["native_execution_complete"] = True
        expected = rail_response(case, times)
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


def run_supply_study(out: Path) -> Path:
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
    results = [_run_case(root / name, value, limits_v) for name, value in cases]
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
        "margin_window_s": [_MARGIN_START, _STOP],
        "operating_limits_v": list(limits_v),
        "hardware_validated": False,
        "body_connection_permitted": False,
        "limitations": [
            "Shared resistance, effective capacitance and MCU conductance are unmeasured assumptions.",
            "Analog load is a conductance calibrated to the current budget at nominal source voltage.",
            "Capacitors are ideal; no regulator, PSRR, ESR, ESL, radio trace or complete board is modeled.",
            "The 4..20ms margin window excludes power-up; it is not a startup specification.",
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
    args = parser.parse_args()
    try:
        root = run_supply_study(args.out)
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
