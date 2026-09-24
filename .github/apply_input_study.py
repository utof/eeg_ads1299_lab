"""Reviewed feature edits; removed before formatting and the final source commit."""
from pathlib import Path


def edit(path: str, before: str, after: str) -> None:
    file = Path(path)
    source = file.read_text(encoding="utf-8")
    if source.count(before) != 1:
        raise RuntimeError(f"Expected one reviewed fragment in {path}: {before!r}")
    file.write_text(source.replace(before, after), encoding="utf-8")


Path("lab/rev_a.py").write_text(r'''"""Rev A passive input study, composed from the public hardware and analog APIs.

Run: uv run --locked python -m lab.rev_a --require-ngspice
No silicon, distributed cable, BIAS-loop, fault protection or human-use model.
"""

import argparse
import hashlib
import json
import math
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass, replace
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal

import numpy as np

from hardware.rev_a import load_documents, validate

from .analog import Drive, InputNetwork, export_spice, run_ngspice, transfer
from .data_types import FloatArray


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
                raise ValueError("Rev A baseline resistance/capacitance must be finite and positive")
        for value in (self.resistor_tolerance, self.capacitor_tolerance):
            if not math.isfinite(value) or not 0 <= value < 1:
                raise ValueError("Rev A baseline tolerance must be finite and in [0, 1)")


@dataclass(frozen=True)
class CaseResult:
    parameters: InputNetwork
    differential_gain_10hz: float
    common_to_differential_50hz: float
    common_to_differential_60hz: float
    leakage_dc_bound_v: float


@dataclass(frozen=True)
class StudyReport:
    baseline: RevABaseline
    cases: dict[str, CaseResult]
    corners: dict[str, list[CaseResult]]
    ideal_source_pole_hz: float
    leakage_bound_a: float
    ngspice_status: Literal["not_requested", "executed_and_compared"]
    ngspice_max_abs_error: dict[str, float]
    limitations: tuple[str, ...]
    clamps_fitted: Literal[False] = False
    hardware_validated: Literal[False] = False
    body_connection_permitted: Literal[False] = False


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
    dc_bound = leakage_a * (
        1 / (1 / rp + 1 / model.r_input_p) + 1 / (1 / rn + 1 / model.r_input_n)
    )
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
        np.column_stack((frequencies, differential.real, differential.imag, common.real, common.imag)),
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
    if isinstance(leakage_bound_a, bool) or not math.isfinite(leakage_bound_a) or leakage_bound_a < 0:
        raise ValueError("leakage bound must be finite and nonnegative")
    out = Path(out)
    report_path = out / "study.json"
    report_path.unlink(missing_ok=True)
    baseline = load_baseline()
    models = _models(baseline)
    cases = {name: _case_result(model, leakage_bound_a) for name, model in models.items()}
    corners = {
        name: [_case_result(corner, leakage_bound_a) for corner in _corners(model, baseline)]
        for name, model in models.items()
    }
    comparisons: dict[str, float] = {}
    drives: tuple[Drive, ...] = ("differential", "common")
    for name, model in models.items():
        _write_response(out / name, model)
        for drive in drives:
            error = _spice_case(out / name / drive, model, drive, require_ngspice)
            if error is not None:
                comparisons[f"{name}/{drive}"] = error
    report = StudyReport(
        baseline=baseline,
        cases=cases,
        corners=corners,
        ideal_source_pole_hz=1 / (
            2 * math.pi * 2 * baseline.series_resistance_ohm * baseline.differential_capacitance_f
        ),
        leakage_bound_a=leakage_bound_a,
        ngspice_status="executed_and_compared" if require_ngspice else "not_requested",
        ngspice_max_abs_error=comparisons,
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
        staged.write_text(json.dumps(asdict(report), indent=2, allow_nan=False) + "\n", encoding="utf-8")
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
            args.out, require_ngspice=args.require_ngspice, leakage_bound_a=args.leakage_bound_na * 1e-9
        )
    except (ValueError, RuntimeError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(asdict(report), indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''', encoding="utf-8")

edit("tach.toml", 'path = "tests"\ndepends_on = [', 'path = "tests"\ndepends_on = ["lab.rev_a", ')
with Path("tach.toml").open("a", encoding="utf-8") as stream:
    stream.write('''
[[modules]]
path = "lab.rev_a"
depends_on = ["hardware.rev_a", "lab.analog", "lab.data_types"]

[[interfaces]]
from = ["lab.rev_a"]
expose = ["RevABaseline", "CaseResult", "StudyReport", "load_baseline", "study", "main"]
''')
edit("tools/check.py", '    run_step(\n        "loopback",', '''    run_step(
        "rev-a-input",
        [sys.executable, "-m", "lab.rev_a", "--require-ngspice", "--out", str(out / "rev_a_input")],
        out,
    )
    run_step(
        "loopback",''')
edit("README.md", "## Contributing: uv and Conventional Commits\n", '''## Rev A input-network study

The selected Rev A input components now feed a reproducible passive-network study, rather than remaining isolated hardware JSON. Start with the numerical calculation; then run the independent simulator comparison when ngspice is installed:

```bash
uv run --locked python -m lab.rev_a --out reports/rev_a_input
uv run --locked python -m lab.rev_a --require-ngspice --out reports/rev_a_input_native
```

The study validates and loads the locked 4.99 kOhm / 4.7 nF component values and BOM tolerances, checks an ideal-source reference, compares balanced and mismatched source impedances, evaluates eight tolerance corners per case, and reports 50/60 Hz common-mode conversion plus hypothetical DC leakage sensitivity. The native command actually runs six ngspice comparisons. `uv run --locked python -m tools.check --native` includes this study and retains its evidence under `reports/check/rev_a_input/`.

All source/load/parasitic assumptions appear in the report. Clamps remain DNP. **This is not an ADS1299 silicon, distributed-cable, BIAS-loop, physical-hardware or human-use safety model.** Read the [Rev A study guide](docs/REV_A_INPUT_STUDY.md) before interpreting the numbers.

## Contributing: uv and Conventional Commits
''')
with Path("docs/LLM_HANDOFF.md").open("a", encoding="utf-8") as stream:
    stream.write('''
## Rev A passive input study (issue #10)

After the adversarial fixes in PR #9 were merged and main passed all three checks, the next addition was `lab.rev_a`, an explicit consumer of the public `hardware.rev_a` and `lab.analog` APIs. It does not change generic analog defaults, hardware JSON or firmware. Run it through uv and read `docs/REV_A_INPUT_STUDY.md`. The native quality gate includes its six real ngspice comparisons and keeps reports in the normal ignored evidence directory.

This closes the first executable selected-component/passive-input bridge, not the entire Rev A simulation plan. BIAS-loop stability, power/decoupling and input-fault analysis still need their own appropriate models; target-specific S3 compilation, schematic review and physical measurements are separate gates. Do not treat the illustrative ADC-node parasitics as a distributed cable model or the DC leakage sensitivity as qualified clamp protection.
''')
Path("docs/REV_A_INPUT_STUDY.md").write_text('''# Rev A passive input-network study

Tracking: issue #10. This is the first executable connection between the locked Rev A component contract and the existing analog simulator. It is intentionally one focused module, `lab.rev_a`, composing public APIs rather than adding board branches to the solver or a simulation framework.

## Run and inspect

Install/synchronize the uv environment described in the README, from the repository root:

```bash
uv sync --locked --all-extras
uv run --locked python -m lab.rev_a --out reports/rev_a_input
uv run --locked python -m lab.rev_a --require-ngspice --out reports/rev_a_input_native
uv run --locked python -m lab.rev_a --leakage-bound-na 2 --out reports/rev_a_input_2na
uv run --locked python -m tools.check --native
```

The first command sequence needs no simulator; the report explicitly says `not_requested`. `--require-ngspice` must execute and compare all six native cases or fail. The shared native gate also runs the study and retains its JSON, CSVs, netlists and simulator logs under `reports/check/rev_a_input/` for the normal CI artifact upload.

`study.json` is the completion marker. It records exact model parameters, canonical document digest, selected part numbers, nominal metrics, 24 tolerance-corner results (eight per scenario), simulator comparison errors, and limitations. Each scenario has a `response.csv` with frequency and real/imaginary differential/common transfer. Each drive has a self-contained `network.cir`; requested native runs also produce fresh `ac.txt` and `ngspice.log`.

A failed new attempt does not leave an earlier success report. An analytic-only rerun clears old simulator outputs for its cases. A completed JSON report is atomically replaced; intermediate CSV/netlists are not themselves proof of completion. Use separate directories for concurrent runs. Committed historical `results/` remain untouched.

## Selected facts versus assumptions

The public hardware validator must accept the unchanged profile, BOM and sources before any model is built. Series resistance **4,990 ohms per leg**, differential capacitance **4.7 nF**, resistor tolerance **1%**, capacitor tolerance **5%**, and the selected part numbers come from `hardware/rev_a/board_profile.json` and `bom.json`. The snapshot digest hashes sorted-key JSON `[profile, BOM, sources]`; it is not represented as a hash of raw file bytes. No fitted common-mode capacitor or clamp is added to the baseline.

The source/electrode impedances and input loading below are **illustrative numerical assumptions**, not measurements or qualified ADS1299 input specifications:

| Scenario | Source resistance P / N | Source parallel capacitance P / N | ADC-node shunt capacitance P / N | Input load per leg |
|---|---|---|---|---|
| Ideal-source limit | 1 mOhm / 1 mOhm | 0 / 0 | 0 / 0 | 1 TOhm |
| Balanced | 10 kOhm / 10 kOhm | 100 nF / 100 nF | 100 pF / 100 pF | 1 GOhm |
| Impedance mismatch | 5 kOhm / 50 kOhm | 100 nF / 100 nF | 100 pF / 200 pF | 1 GOhm |

The nonzero shunt values represent assumed **ADC input-node parasitics**, not fitted capacitors or a claim that all real cable capacitance is located there. Upstream lead capacitance, distributed cable behavior, shielding and capacitive mains coupling require a different explicit topology.

## Independent checks and interpretation

For ideal zero-impedance sources and infinite input loading, the differential network has

```text
H(f) = 1 / (1 + j*2*pi*f*(Rp + Rn)*Cd)
fc = 1 / (2*pi*(Rp + Rn)*Cd) = approximately 3393.06 Hz
```

That is an analytic reference, not a measured bandwidth or the ADS digital filter response. The near-ideal finite-resistance model is tested against the reference. A second independent half-circuit equation checks a finite, purely resistive balanced source/load case. Symmetric common-mode excitation should cancel at the differential output; mismatch converts part of it into differential voltage. The reported common-mode transfer is V/V: multiply by an assumed common-mode amplitude to obtain differential amplitude.

Each scenario evaluates every combination of Rp at +/-1%, Rn at +/-1%, and Cd at +/-5%. These **eight deterministic corners are not a statistical distribution or proof of global extrema**: nonmonotone metrics may have interior extrema. The report preserves each corner instead of labelling an unproved global worst case.

The optional leakage value is a **hypothetical independent DC current bound per input**, default 1 nA. With capacitors open at DC and independent opposite-sign currents, the differential bound is

```text
Ibound * (((RsourceP + RseriesP) || RinputP)
        + ((RsourceN + RseriesN) || RinputN))
```

The report uses amperes and volts internally; `--leakage-bound-na` takes nanoamperes. This sensitivity calculation does not fit or qualify BAV199 devices. Clamps stay DNP; there is no transient/ESD/fault-protection claim.

## What remains outside the model

There is no ADS1299 silicon/PGA loading model, digital decimation, BIAS-loop stability, power supply/decoupling, PCB extraction, ESD, fault-current, target-firmware build or physical measurement here. The model cannot authorize purchasing, board manufacture or body connection. All original hardware safety gates remain false.

The next modeling work should address BIAS-loop and power integrity with their own justified models, then reconcile results with a reviewed schematic. Do not expand this passive transfer solver with unrelated safety or firmware conditionals.
''', encoding="utf-8")
