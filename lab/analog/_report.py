"""Reproducible educational circuit reports; no hardware approval is implied."""

import json
import shutil
from dataclasses import asdict, replace
from pathlib import Path
from typing import NotRequired, TypedDict

import numpy as np

from ._model import Drive, InputNetwork
from ._solver import transfer
from ._spice import export_spice, run_ngspice


class CircuitReport(TypedDict):
    model: str
    parameters: dict[str, float]
    differential_gain_10hz: float
    balanced_cm_leakage_50hz: float
    mismatch_cm_leakage_50hz: float
    mismatch_differential_uV_for_100mV_common: float
    monte_carlo_trials: int
    tolerance_gain_10hz_minmax: list[float]
    ngspice: dict[str, str]
    safety_validation: bool
    ngspice_comparisons: NotRequired[dict[str, float]]


def circuit_report(out: str | Path, seed: int = 42, require_ngspice: bool = False) -> CircuitReport:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    report_path = out / "circuit_report.json"
    report_path.unlink(missing_ok=True)
    if require_ngspice and not shutil.which("ngspice"):
        raise RuntimeError(
            "Native SPICE validation required but ngspice unavailable; no SPICE pass claimed."
        )
    f = np.geomspace(0.1, 100_000, 241)
    balanced = InputNetwork()
    mismatch = replace(balanced, r_electrode_n=50_000)
    hd = transfer(f, balanced)
    hc = transfer(f, mismatch, "common")
    rows = np.column_stack([f, np.abs(hd), np.abs(hc)])
    np.savetxt(
        out / "circuit_response.csv",
        rows,
        delimiter=",",
        header="frequency_hz,differential_gain,common_to_differential_gain",
        comments="",
    )
    rng = np.random.default_rng(seed)
    trial = []
    for _ in range(200):
        # Independent uniform tolerances; this is an assumption, not measured yield.
        d: dict[str, float] = asdict(balanced)
        for k in d:
            tolerance = 0.01 if k.startswith("r_") else 0.05
            d[k] *= rng.uniform(1 - tolerance, 1 + tolerance)
        n = InputNetwork(**d)
        trial.append([abs(transfer([10], n)[0]), abs(transfer([50], n, "common")[0])])
    np.savetxt(
        out / "tolerance_trials.csv",
        trial,
        delimiter=",",
        header="gain_10hz,common_to_diff_50hz",
        comments="",
    )
    mismatch_gain = float(abs(transfer([50], mismatch, "common")[0]))
    report: CircuitReport = {
        "model": "independent linear nodal solve; passive network only",
        "parameters": asdict(balanced),
        "differential_gain_10hz": float(abs(transfer([10], balanced)[0])),
        "balanced_cm_leakage_50hz": float(abs(transfer([50], balanced, "common")[0])),
        "mismatch_cm_leakage_50hz": float(abs(transfer([50], mismatch, "common")[0])),
        "mismatch_differential_uV_for_100mV_common": mismatch_gain * 100_000,
        "monte_carlo_trials": len(trial),
        "tolerance_gain_10hz_minmax": [
            float(np.min(np.array(trial)[:, 0])),
            float(np.max(np.array(trial)[:, 0])),
        ],
        "ngspice": {"status": "not_run", "reason": "ngspice not installed"},
        "safety_validation": False,
    }
    cases: list[tuple[str, InputNetwork, Drive]] = [
        ("balanced", balanced, "differential"),
        ("mismatch", mismatch, "common"),
    ]
    for name, n, drive in cases:
        net = export_spice(out / f"{name}.cir", n, drive)
        if shutil.which("ngspice"):
            sf, sh = run_ngspice(net, out / f"ngspice_{name}")
            expected = transfer(sf, n, drive)
            error = float(np.max(np.abs(sh - expected)))
            if not np.allclose(sh, expected, atol=1e-8, rtol=1e-4):
                raise AssertionError(f"ngspice/nodal disagreement in {name}: {error}")
            report.setdefault("ngspice_comparisons", {})[name] = error
            report["ngspice"] = {"status": "executed_and_compared"}
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
