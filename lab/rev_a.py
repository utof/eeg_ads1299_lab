"""Rev A passive input study, composed from the public hardware and analog APIs.

Run: uv run --locked python -m lab.rev_a --require-ngspice
No silicon, distributed cable, BIAS-loop, fault protection or human-use model.
"""

import argparse
import hashlib
import json
import math
import sys
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, replace
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from types import MappingProxyType
from typing import Literal

import numpy as np

from hardware.rev_a import load_documents, validate

from .analog import Drive, InputNetwork, export_spice, run_ngspice, transfer
from .data_types import FloatArray

_SCENARIOS = frozenset(("ideal_source_limit", "balanced", "impedance_mismatch"))
_DRIVES: tuple[Drive, ...] = ("differential", "common")
_COMPARISONS = frozenset(f"{name}/{drive}" for name in _SCENARIOS for drive in _DRIVES)


def _finite_nonnegative(value: float, name: str) -> None:
    if isinstance(value, bool) or not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be finite and nonnegative")


@dataclass(frozen=True)
class RevABaseline:
    profile_id: str
    documents_sha256: str
    resistor_mpn: str
    capacitor_mpn: str
    series_resistance_ohm: float
    differential_capacitance_f: float
    resistor_tolerance: float
    capacitor_tolerance: float

    def __post_init__(self) -> None:
        for value in (self.series_resistance_ohm, self.differential_capacitance_f):
            if not math.isfinite(value) or value <= 0:
                raise ValueError(
                    "Rev A baseline resistance/capacitance must be finite and positive"
                )
        for value in (self.resistor_tolerance, self.capacitor_tolerance):
            if not math.isfinite(value) or not 0 <= value < 1:
                raise ValueError("Rev A baseline tolerance must be finite and in [0, 1)")


@dataclass(frozen=True, slots=True)
class CaseResult:
    parameters: InputNetwork
    differential_gain_10hz: float
    common_to_differential_50hz: float
    common_to_differential_60hz: float
    leakage_dc_bound_v: float

    def __post_init__(self) -> None:
        if not isinstance(self.parameters, InputNetwork):
            raise TypeError("case parameters must be an InputNetwork")
        for value in (
            self.differential_gain_10hz,
            self.common_to_differential_50hz,
            self.common_to_differential_60hz,
            self.leakage_dc_bound_v,
        ):
            _finite_nonnegative(value, "case metric")


@dataclass(frozen=True, slots=True)
class AnalyticOnly:
    """No native evidence exists; there is no success flag to toggle."""


@dataclass(frozen=True, slots=True)
class NativeCompared:
    """Complete comparison summary, produced after the numerical checks.

    This enforces structure, not cryptographic proof that a simulator ran.
    The study runner owns execution and the real allclose comparison.
    """

    errors: Mapping[str, float]

    def __post_init__(self) -> None:
        errors = dict(self.errors)
        if set(errors) != _COMPARISONS:
            raise ValueError("native evidence requires exactly all six scenario/drive comparisons")
        for value in errors.values():
            _finite_nonnegative(value, "comparison error")
        object.__setattr__(self, "errors", MappingProxyType(errors))


def _snapshot_corners(
    corners: Mapping[str, Sequence[CaseResult]],
) -> Mapping[str, tuple[CaseResult, ...]]:
    snapshot = {name: tuple(values) for name, values in corners.items()}
    if set(snapshot) != _SCENARIOS:
        raise ValueError("corner results require exactly the three study scenarios")
    for values in snapshot.values():
        if len(values) != 8 or any(not isinstance(value, CaseResult) for value in values):
            raise ValueError("each scenario requires eight CaseResult corners")
        if len({value.parameters for value in values}) != 8:
            raise ValueError("each scenario requires eight distinct corner networks")
    return MappingProxyType(snapshot)


@dataclass(frozen=True, slots=True)
class StudyReport:
    baseline: RevABaseline
    cases: Mapping[str, CaseResult]
    corners: Mapping[str, Sequence[CaseResult]]
    leakage_bound_a: float
    spice_evidence: AnalyticOnly | NativeCompared
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.baseline, RevABaseline):
            raise TypeError("study baseline must be a RevABaseline")
        if type(self.spice_evidence) not in (AnalyticOnly, NativeCompared):
            raise TypeError("study evidence must be AnalyticOnly or NativeCompared")
        _finite_nonnegative(self.leakage_bound_a, "leakage bound")
        cases = dict(self.cases)
        if set(cases) != _SCENARIOS:
            raise ValueError("case results require exactly the three study scenarios")
        if any(not isinstance(value, CaseResult) for value in cases.values()):
            raise TypeError("study scenarios must contain CaseResult values")
        object.__setattr__(self, "cases", MappingProxyType(cases))
        object.__setattr__(self, "corners", _snapshot_corners(self.corners))
        object.__setattr__(self, "limitations", tuple(self.limitations))

    @property
    def ideal_source_pole_hz(self) -> float:
        b = self.baseline
        return 1 / (2 * math.pi * 2 * b.series_resistance_ohm * b.differential_capacitance_f)

    @property
    def ngspice_status(self) -> Literal["not_requested", "executed_and_compared"]:
        if isinstance(self.spice_evidence, NativeCompared):
            return "executed_and_compared"
        return "not_requested"

    @property
    def ngspice_max_abs_error(self) -> Mapping[str, float]:
        if isinstance(self.spice_evidence, NativeCompared):
            return self.spice_evidence.errors
        return MappingProxyType({})

    @property
    def clamps_fitted(self) -> Literal[False]:
        return False

    @property
    def hardware_validated(self) -> Literal[False]:
        return False

    @property
    def body_connection_permitted(self) -> Literal[False]:
        return False

    def to_dict(self) -> dict[str, object]:
        """Produce a detached JSON-compatible view, preserving the report schema."""
        return {
            "baseline": asdict(self.baseline),
            "cases": {name: asdict(value) for name, value in self.cases.items()},
            "corners": {
                name: [asdict(value) for value in values] for name, values in self.corners.items()
            },
            "ideal_source_pole_hz": self.ideal_source_pole_hz,
            "leakage_bound_a": self.leakage_bound_a,
            "ngspice_status": self.ngspice_status,
            "ngspice_max_abs_error": dict(self.ngspice_max_abs_error),
            "limitations": list(self.limitations),
            "clamps_fitted": self.clamps_fitted,
            "hardware_validated": self.hardware_validated,
            "body_connection_permitted": self.body_connection_permitted,
        }


def load_baseline() -> RevABaseline:
    """Reject contract drift before deriving parameters from selected parts."""
    profile, bom, sources = load_documents()
    errors = validate(profile, bom, sources)
    if errors:
        raise ValueError("Rev A baseline rejected: " + "; ".join(errors))
    parts = {part["id"]: part for part in bom["line_items"]}
    network = profile["input_network"]
    snapshot = json.dumps([profile, bom, sources], sort_keys=True, allow_nan=False).encode("utf-8")
    try:
        return RevABaseline(
            profile_id=profile["profile_id"],
            documents_sha256=hashlib.sha256(snapshot).hexdigest(),
            resistor_mpn=parts["input_r"]["mpn"],
            capacitor_mpn=parts["input_c"]["mpn"],
            series_resistance_ohm=network["series_resistance_each_ohm"],
            differential_capacitance_f=network["differential_capacitance_f"],
            resistor_tolerance=parts["input_r"]["spec"]["tolerance_fraction"],
            capacitor_tolerance=parts["input_c"]["spec"]["tolerance_fraction"],
        )
    except KeyError as exc:
        raise ValueError(f"Rev A baseline is missing a required component field: {exc}") from exc


def _models(baseline: RevABaseline) -> dict[str, InputNetwork]:
    # Source RC and 1 GOhm loading are study assumptions, not ADS silicon claims.
    balanced = InputNetwork(
        r_series_p=baseline.series_resistance_ohm,
        r_series_n=baseline.series_resistance_ohm,
        c_differential=baseline.differential_capacitance_f,
        r_electrode_p=10000.0,
        r_electrode_n=10000.0,
        c_electrode_p=100e-9,
        c_electrode_n=100e-9,
        r_input_p=1e9,
        r_input_n=1e9,
        c_common_p=100e-12,
        c_common_n=100e-12,
    )
    return {
        "ideal_source_limit": replace(
            balanced,
            r_electrode_p=1e-3,
            r_electrode_n=1e-3,
            c_electrode_p=0.0,
            c_electrode_n=0.0,
            r_input_p=1e12,
            r_input_n=1e12,
            c_common_p=0.0,
            c_common_n=0.0,
        ),
        "balanced": balanced,
        "impedance_mismatch": replace(
            balanced, r_electrode_p=5000.0, r_electrode_n=50000.0, c_common_n=200e-12
        ),
    }


def _case_result(model: InputNetwork, leakage_a: float) -> CaseResult:
    frequencies: FloatArray = np.array([10.0, 50.0, 60.0])
    differential = transfer(frequencies, model, "differential")
    common = transfer(frequencies, model, "common")
    rp, rn = model.r_series_p + model.r_electrode_p, model.r_series_n + model.r_electrode_n
    # At DC, capacitors are open. Independent +/-I injections can have opposite
    # signs, so the worst differential offset is I * (Rth_p + Rth_n).
    dc_bound = leakage_a * (1 / (1 / rp + 1 / model.r_input_p) + 1 / (1 / rn + 1 / model.r_input_n))
    return CaseResult(
        parameters=model,
        differential_gain_10hz=float(abs(differential[0])),
        common_to_differential_50hz=float(abs(common[1])),
        common_to_differential_60hz=float(abs(common[2])),
        leakage_dc_bound_v=dc_bound,
    )


def _corners(model: InputNetwork, baseline: RevABaseline) -> list[InputNetwork]:
    rt, ct = baseline.resistor_tolerance, baseline.capacitor_tolerance
    return [
        replace(
            model,
            r_series_p=model.r_series_p * rp,
            r_series_n=model.r_series_n * rn,
            c_differential=model.c_differential * cd,
        )
        for rp, rn, cd in product((1 - rt, 1 + rt), (1 - rt, 1 + ct))
    ]


def _write_response(out: Path, model: InputNetwork) -> None:
    frequencies: FloatArray = np.geomspace(0.1, 100000.0, 241)
    differential = transfer(frequencies, model, "differential")
    common = transfer(frequencies, model, "common")
    out.mkdir(parents=True, exist_ok=True)
    np.savetxt(
        out / "response.csv",
        np.column_stack(
            (frequencies, differential.real, differential.imag, common.real, common.imag)
        ),
        delimiter=",",
        header="frequency_hz,differential_real,differential_imag,common_real,common_imag",
        comments="",
    )


def _spice_case(out: Path, model: InputNetwork, drive: Drive, required: bool) -> float | None:
    netlist = export_spice(out / "network.cir", model, drive)
    # Even an analytic-only rerun must not retain a previous simulator pass.
    (out / "ac.txt").unlink(missing_ok=True)
    (out / "ngspice.log").unlink(missing_ok=True)
    if not required:
        return None
    frequencies, actual = run_ngspice(netlist, out)
    expected = transfer(frequencies, model, drive)
    if not np.allclose(actual, expected, rtol=1e-5, atol=1e-8):
        raise RuntimeError(f"Rev A ngspice and nodal solver disagree: {out.name}")
    return float(np.max(np.abs(actual - expected)))


def study(
    out: str | Path, *, require_ngspice: bool = False, leakage_bound_a: float = 1e-9
) -> StudyReport:
    """Write deterministic cases and corners; publish success only at completion.

    A report is the completion marker. Intermediate CSV/netlists are not evidence
    of a successful run. Different concurrent runs require different directories.
    """
    out = Path(out)
    report_path = out / "study.json"
    report_path.unlink(missing_ok=True)
    _finite_nonnegative(leakage_bound_a, "leakage bound")
    baseline = load_baseline()
    models = _models(baseline)
    cases = {name: _case_result(model, leakage_bound_a) for name, model in models.items()}
    corners = {
        name: [_case_result(corner, leakage_bound_a) for corner in _corners(model, baseline)]
        for name, model in models.items()
    }
    comparisons: dict[str, float] = {}
    for name, model in models.items():
        _write_response(out / name, model)
        for drive in _DRIVES:
            error = _spice_case(out / name / drive, model, drive, require_ngspice)
            if error is not None:
                comparisons[f"{name}/{drive}"] = error
    report = StudyReport(
        baseline=baseline,
        cases=cases,
        corners=corners,
        leakage_bound_a=leakage_bound_a,
        spice_evidence=NativeCompared(comparisons) if require_ngspice else AnalyticOnly(),
        limitations=(
            "Passive small-signal input network only; no ADS1299 silicon or digital decimation model.",
            "Source RC and input resistance are illustrative assumptions, not electrode/ADS measurements.",
            "Shunt capacitance is at ADC input nodes; no distributed cable or cable-coupling model.",
            "Ideal-source limit uses 1 milliohm sources and 1 teraohm loads, not exact zero/infinity.",
            "Eight deterministic BOM tolerance corners are not a proof of global response extrema.",
            "Leakage is a hypothetical DC sensitivity bound; clamps remain DNP, not qualified devices.",
            "No BIAS-loop, power-integrity, fault-current, ESD, layout or human-use safety validation.",
            "Document digest is SHA-256 of sorted-key JSON [profile, BOM, sources], not raw file bytes.",
        ),
    )
    with TemporaryDirectory(prefix=".study-", dir=out) as directory:
        staged = Path(directory) / "study.json"
        staged.write_text(
            json.dumps(report.to_dict(), indent=2, allow_nan=False) + "\n", encoding="utf-8"
        )
        staged.replace(report_path)
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("reports/rev_a_input"))
    parser.add_argument("--require-ngspice", action="store_true")
    parser.add_argument("--leakage-bound-na", type=float, default=1.0)
    args = parser.parse_args(argv)
    try:
        report = study(
            args.out,
            require_ngspice=args.require_ngspice,
            leakage_bound_a=float(args.leakage_bound_na) * 1e-9,
        )
    except (ValueError, RuntimeError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    summary = {
        "report": str(Path(args.out) / "study.json"),
        "ideal_source_pole_hz": report.ideal_source_pole_hz,
        "ngspice_status": report.ngspice_status,
        "ngspice_max_abs_error": dict(report.ngspice_max_abs_error),
        "case_metrics": {
            name: {
                "differential_gain_10hz": case.differential_gain_10hz,
                "common_to_differential_50hz": case.common_to_differential_50hz,
                "common_to_differential_60hz": case.common_to_differential_60hz,
                "leakage_dc_bound_v": case.leakage_dc_bound_v,
            }
            for name, case in report.cases.items()
        },
    }
    print(json.dumps(summary, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
