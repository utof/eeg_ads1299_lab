"""Rev A passive input study, composed from the public hardware and analog APIs.

Run: uv run --locked python -m lab.rev_a --require-ngspice
No silicon, distributed cable, BIAS-loop, fault protection or human-use model.
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
from collections.abc import Generator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import asdict, dataclass, fields, replace
from itertools import product
from pathlib import Path
from types import MappingProxyType
from typing import Literal
from uuid import uuid4

import numpy as np

from hardware.rev_a import load_documents, validate

from .analog import Drive, InputNetwork, export_spice, run_ngspice, transfer
from .data_types import FloatArray
from .validation import boolean, integer, number, read_object, text

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
    run_id: str
    baseline: RevABaseline
    cases: Mapping[str, CaseResult]
    corners: Mapping[str, Sequence[CaseResult]]
    leakage_bound_a: float
    spice_evidence: AnalyticOnly | NativeCompared
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        _validate_run_id(self.run_id)
        if not isinstance(self.baseline, RevABaseline):
            raise TypeError("study baseline must be a RevABaseline")
        if not isinstance(self.spice_evidence, (AnalyticOnly, NativeCompared)):
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
            "run_id": self.run_id,
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
        for rp, rn, cd in product((1 - rt, 1 + rt), (1 - rt, 1 + rt), (1 - ct, 1 + ct))
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


def _calculate_study(
    out: Path, baseline: RevABaseline, require_ngspice: bool, leakage_bound_a: float, run_id: str
) -> StudyReport:
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
        run_id=run_id,
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
    _write_json(out / "study.json", report.to_dict())
    return report


def _validate_run_id(run_id: str) -> None:
    if not isinstance(run_id, str) or re.fullmatch(r"[0-9a-f]{32}", run_id) is None:
        raise ValueError("run identity must be 32 lowercase hexadecimal characters")


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def _write_json(path: Path, value: object) -> None:
    path.write_text(_json_bytes(value).decode("utf-8"), encoding="utf-8")


def _plain_bytes(path: Path) -> bytes:
    if path.is_symlink():
        raise ValueError(f"symlink is not a study artifact: {path.name}")
    return path.read_bytes()


def _object_bytes(value: bytes, label: str) -> dict[str, object]:
    decoded: object = json.loads(value)
    return read_object(decoded, label)


def _exact_keys(value: Mapping[str, object], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise ValueError(f"{label}: unexpected schema or inventory")


def _hex_digest(value: object) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError("expected a SHA-256 digest")
    return value


@contextmanager
def _single_writer(out: Path, run_id: str) -> Generator[None, None, None]:
    out.mkdir(parents=True, exist_ok=True)
    lock = out / ".writer.lock"
    try:
        handle = lock.open("x", encoding="utf-8")
    except FileExistsError as exc:
        raise RuntimeError(
            "another writer or a stale writer lock exists; do not break it blindly"
        ) from exc
    try:
        with handle:
            handle.write(run_id + "\n")
        yield
    finally:
        lock.unlink()


def _run_parent(out: Path, name: str) -> Path:
    parent = out / name
    if parent.is_symlink():
        raise ValueError(f"symlink is not a run directory: {name}")
    parent.mkdir(exist_ok=True)
    return parent


def _expected_files(required: bool) -> set[str]:
    expected = {"study.json"}
    for scenario in _SCENARIOS:
        expected.add(f"{scenario}/response.csv")
        for drive in _DRIVES:
            expected.add(f"{scenario}/{drive}/network.cir")
            if required:
                expected.update(f"{scenario}/{drive}/{name}" for name in ("ac.txt", "ngspice.log"))
    return expected


def _artifact_bytes(root: Path, required: bool) -> dict[str, bytes]:
    if root.is_symlink() or root.parent.is_symlink():
        raise ValueError("symlink is not a run directory")
    contents: dict[str, bytes] = {}
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError("symlink is not a study artifact")
        if path.is_file() and path != root / "manifest.json":
            contents[path.relative_to(root).as_posix()] = path.read_bytes()
    if set(contents) != _expected_files(required):
        raise ValueError("study artifact inventory does not match requested outcome")
    return contents


def _source_identity() -> dict[str, object]:
    root = Path(__file__).resolve().parents[1]
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return {"commit": None, "worktree_dirty": None}
    return {"commit": commit, "worktree_dirty": bool(dirty)}


def _tool_versions(required: bool) -> dict[str, object]:
    native: str | None = None
    if required:
        executable = shutil.which("ngspice")
        if executable is None:
            raise RuntimeError("ngspice disappeared before publication")
        result = subprocess.run(
            [executable, "--version"], capture_output=True, text=True, timeout=5, check=True
        )
        native = result.stdout.strip()
    return {"python": platform.python_version(), "numpy": np.__version__, "ngspice": native}


def _manifest(report: StudyReport, root: Path, required: bool) -> dict[str, object]:
    return {
        "schema_version": 1,
        "study": "rev_a_passive_input",
        "run_id": report.run_id,
        "request": {"require_ngspice": required, "leakage_bound_a": report.leakage_bound_a},
        "baseline_sha256": report.baseline.documents_sha256,
        "source": _source_identity(),
        "tools": _tool_versions(required),
        "outcome": report.ngspice_status,
        "files": {name: _digest(data) for name, data in _artifact_bytes(root, required).items()},
    }


def study(
    out: str | Path,
    *,
    require_ngspice: bool = False,
    leakage_bound_a: float = 1e-9,
    run_id: str | None = None,
) -> StudyReport:
    """Publish a new generation, preserving previous successes as historical data.

    Rejected requests do not touch the output. Failed accepted attempts retain
    their private partial directory. Only a complete generation advances current.
    Readers must supply the expected run identity; current alone is not freshness.
    """
    identity = uuid4().hex if run_id is None else run_id
    _validate_run_id(identity)
    _finite_nonnegative(leakage_bound_a, "leakage bound")
    if not isinstance(require_ngspice, bool):
        raise ValueError("require_ngspice must be a boolean")
    baseline = load_baseline()
    out = Path(out)
    with _single_writer(out, identity):
        runs = _run_parent(out, "runs")
        pending = _run_parent(out, ".pending") / identity
        final = runs / identity
        if final.exists() or final.is_symlink() or pending.exists() or pending.is_symlink():
            raise ValueError("run identity already exists and cannot be reused")
        pending.mkdir()
        report = _calculate_study(pending, baseline, require_ngspice, leakage_bound_a, identity)
        manifest = _manifest(report, pending, require_ngspice)
        _write_json(pending / "manifest.json", manifest)
        pending.rename(final)
        pointer = {
            "schema_version": 1,
            "run_id": identity,
            "manifest_sha256": _digest(_plain_bytes(final / "manifest.json")),
        }
        staged_pointer = out / f".{identity}.current.tmp"
        _write_json(staged_pointer, pointer)
        staged_pointer.replace(out / "current.json")
    return report


def _decode_baseline(value: object) -> RevABaseline:
    fields_ = read_object(value, "baseline")
    return RevABaseline(
        profile_id=text(fields_, "profile_id"),
        documents_sha256=_hex_digest(fields_.get("documents_sha256")),
        resistor_mpn=text(fields_, "resistor_mpn"),
        capacitor_mpn=text(fields_, "capacitor_mpn"),
        series_resistance_ohm=number(fields_, "series_resistance_ohm"),
        differential_capacitance_f=number(fields_, "differential_capacitance_f"),
        resistor_tolerance=number(fields_, "resistor_tolerance"),
        capacitor_tolerance=number(fields_, "capacitor_tolerance"),
    )


def _decode_case(value: object) -> CaseResult:
    item = read_object(value, "case")
    parameters = read_object(item.get("parameters"), "network")
    _exact_keys(parameters, {field.name for field in fields(InputNetwork)}, "network")
    return CaseResult(
        parameters=InputNetwork(**{name: number(parameters, name) for name in parameters}),
        differential_gain_10hz=number(item, "differential_gain_10hz"),
        common_to_differential_50hz=number(item, "common_to_differential_50hz"),
        common_to_differential_60hz=number(item, "common_to_differential_60hz"),
        leakage_dc_bound_v=number(item, "leakage_dc_bound_v"),
    )


def _decode_corners(value: object) -> dict[str, tuple[CaseResult, ...]]:
    corners = read_object(value, "corners")
    result: dict[str, tuple[CaseResult, ...]] = {}
    for name, entries in corners.items():
        if not isinstance(entries, list):
            raise ValueError("corner results must be a list")
        values: list[object] = entries
        result[name] = tuple(_decode_case(entry) for entry in values)
    return result


def _decode_report(data: bytes, required: bool) -> StudyReport:
    raw = _object_bytes(data, "study report")
    cases = read_object(raw.get("cases"), "cases")
    errors = read_object(raw.get("ngspice_max_abs_error"), "native comparisons")
    limitations = raw.get("limitations")
    if not isinstance(limitations, list):
        raise ValueError("limitations must be a list of strings")
    values: list[object] = limitations
    if not all(isinstance(item, str) for item in values):
        raise ValueError("limitations must be a list of strings")
    strings = tuple(item for item in values if isinstance(item, str))
    for name in ("clamps_fitted", "hardware_validated", "body_connection_permitted"):
        if raw.get(name) is not False:
            raise ValueError("simulation cannot grant hardware or body approval")
    report = StudyReport(
        run_id=text(raw, "run_id"),
        baseline=_decode_baseline(raw.get("baseline")),
        cases={name: _decode_case(value) for name, value in cases.items()},
        corners=_decode_corners(raw.get("corners")),
        leakage_bound_a=number(raw, "leakage_bound_a"),
        spice_evidence=NativeCompared({key: number(errors, key) for key in errors})
        if required
        else AnalyticOnly(),
        limitations=strings,
    )
    if report.to_dict() != raw:
        raise ValueError("study report schema or derived values are inconsistent")
    return report


def _validate_metadata(manifest: Mapping[str, object], required: bool) -> None:
    source = read_object(manifest.get("source"), "source")
    _exact_keys(source, {"commit", "worktree_dirty"}, "source")
    commit = source["commit"]
    if commit is not None and (
        not isinstance(commit, str)
        or re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", commit) is None
    ):
        raise ValueError("invalid source commit")
    dirty = source["worktree_dirty"]
    if dirty is not None and not isinstance(dirty, bool):
        raise ValueError("invalid source worktree state")
    tools = read_object(manifest.get("tools"), "tools")
    _exact_keys(tools, {"python", "numpy", "ngspice"}, "tools")
    text(tools, "python")
    text(tools, "numpy")
    if required:
        if not text(tools, "ngspice"):
            raise ValueError("native tool version is missing")
    elif tools["ngspice"] is not None:
        raise ValueError("analytic-only run cannot claim native tool execution")


def _validate_manifest(
    manifest: Mapping[str, object],
    run_id: str,
    required: bool,
    leakage: float,
    baseline_digest: str,
) -> None:
    _exact_keys(
        manifest,
        {
            "schema_version",
            "study",
            "run_id",
            "request",
            "baseline_sha256",
            "source",
            "tools",
            "outcome",
            "files",
        },
        "manifest",
    )
    if integer(manifest, "schema_version") != 1 or text(manifest, "study") != "rev_a_passive_input":
        raise ValueError("unsupported manifest schema")
    if text(manifest, "run_id") != run_id:
        raise ValueError("manifest run identity mismatch")
    request = read_object(manifest.get("request"), "request")
    _exact_keys(request, {"require_ngspice", "leakage_bound_a"}, "request")
    if (
        boolean(request, "require_ngspice") != required
        or number(request, "leakage_bound_a") != leakage
    ):
        raise ValueError("manifest request does not match expected parameters")
    if _hex_digest(manifest["baseline_sha256"]) != baseline_digest:
        raise ValueError("manifest baseline digest does not match expected baseline")
    expected_status = "executed_and_compared" if required else "not_requested"
    if text(manifest, "outcome") != expected_status:
        raise ValueError("manifest outcome does not match request")
    _validate_metadata(manifest, required)


def read_study(
    out: str | Path,
    *,
    expected_run_id: str,
    require_ngspice: bool = False,
    leakage_bound_a: float = 1e-9,
    baseline_sha256: str | None = None,
) -> StudyReport:
    """Verify current against a caller-known request, then reconstruct immutable values.

    Digests detect mismatched/edited files, not malicious replacement of both
    manifest and pointer. No power-loss durability or hostile-writer guarantee.
    """
    _validate_run_id(expected_run_id)
    _finite_nonnegative(leakage_bound_a, "leakage bound")
    if not isinstance(require_ngspice, bool):
        raise ValueError("require_ngspice must be a boolean")
    baseline_digest = (
        load_baseline().documents_sha256
        if baseline_sha256 is None
        else _hex_digest(baseline_sha256)
    )
    out = Path(out)
    pointer = _object_bytes(_plain_bytes(out / "current.json"), "current pointer")
    _exact_keys(pointer, {"schema_version", "run_id", "manifest_sha256"}, "pointer")
    if integer(pointer, "schema_version") != 1:
        raise ValueError("unsupported pointer schema")
    if text(pointer, "run_id") != expected_run_id:
        raise ValueError("current run identity does not match requested run identity")
    root = out / "runs" / expected_run_id
    if root.is_symlink() or root.parent.is_symlink():
        raise ValueError("symlink is not a run directory")
    raw_manifest = _plain_bytes(root / "manifest.json")
    if _digest(raw_manifest) != _hex_digest(pointer.get("manifest_sha256")):
        raise ValueError("manifest digest mismatch")
    manifest = _object_bytes(raw_manifest, "manifest")
    _validate_manifest(manifest, expected_run_id, require_ngspice, leakage_bound_a, baseline_digest)
    digests = read_object(manifest.get("files"), "file digests")
    contents = _artifact_bytes(root, require_ngspice)
    _exact_keys(digests, set(contents), "manifest files")
    for name, data in contents.items():
        if _digest(data) != _hex_digest(digests[name]):
            raise ValueError(f"artifact digest mismatch: {name}")
    report = _decode_report(contents["study.json"], require_ngspice)
    if (
        report.run_id != expected_run_id
        or report.baseline.documents_sha256 != baseline_digest
        or report.leakage_bound_a != leakage_bound_a
    ):
        raise ValueError("study report does not match manifest request")
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("reports/rev_a_input"))
    parser.add_argument("--require-ngspice", action="store_true")
    parser.add_argument("--leakage-bound-na", type=float, default=1.0)
    parser.add_argument(
        "--run-id", help="Caller-chosen 32-character lowercase hex identity; never reuse"
    )
    args = parser.parse_args(argv)
    identity = uuid4().hex if args.run_id is None else str(args.run_id)
    try:
        report = study(
            args.out,
            require_ngspice=args.require_ngspice,
            leakage_bound_a=float(args.leakage_bound_na) * 1e-9,
            run_id=identity,
        )
    except (ValueError, RuntimeError, OSError) as exc:
        print(f"ERROR (run_id={identity}): {exc}", file=sys.stderr)
        return 1
    summary = {
        "run_id": report.run_id,
        "report": str(Path(args.out) / "runs" / report.run_id / "study.json"),
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
