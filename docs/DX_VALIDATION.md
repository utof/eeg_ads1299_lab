# DX validation record — 2026-09-23

This is a dated software/native-integration result, not hardware approval. The original `VALIDATION.json`, `results/`, `docs/RESULTS.md`, and `requirements-tested.txt` are retained as historical evidence.

## Executed snapshot

Source commit: `3dff928aa3fe042ab626b2b24ba64cea7a01e399` on `dx/quality-foundation`.

Verified GitHub Actions run: [Quality #4 — run 35913793737](https://github.com/utof/eeg_ads1299_lab/actions/runs/35913793737), completed successfully on 2026-09-23.

All three jobs passed: `Python 3.11 quality`, `Python 3.13 quality`, and `Native integration`. Both Python jobs installed the project and development tools from `uv.lock` with `uv sync --locked --all-extras`. These were Linux runners; this record does not claim macOS or Windows CI coverage.

The native job used Python 3.13.15 and ngspice 42. Its logged shared gate results were:

| Check | Observed result |
|---|---|
| Ruff format | 55 files already formatted |
| Ruff lint | All checks passed |
| Pyrefly strict, minimum severity `warn` | 0 diagnostics |
| complexipy | No function with cognitive complexity greater than 15 |
| Tach | All modules validated |
| Static hardware baseline | PASS; explicitly not hardware or safety validation |
| Software tests | 140 passed, 3 deselected, 5 subtests passed |
| Native/integration test selection | 3 passed, 140 deselected |
| Measured branch coverage | 261 / 360 = 72.50%; configured floor 71.00% |
| Combined line/branch figure printed by coverage.py | 83.61%; not the branch-only ratio |

The two pytest selections cover 143 tests without counting the software tests again just because multiple CI jobs ran them. The 90% core branch-coverage target is future work, not an achieved result.

## Actual simulator and transport execution

The strict circuit command ran ngspice and reported `executed_and_compared` for the **existing educational passive network**, not the next Rev A-specific model. Maximum absolute complex-response differences against the independent nodal solve were:

- Balanced differential case: `4.502029904938123e-16`.
- Mismatched common-mode case: `1.6666753876341406e-15`.

Those are numerical agreement measurements for this linear model and solver pair. They are not measurements of a physical ADS1299, a BIAS-loop stability result, or a safety guarantee. The existing illustrative component values remain distinct from the selected Rev A component contract.

The longer real localhost UDP replay accepted **2,248 packets**, detected **2 deliberately omitted samples**, and found **one intact four-second spectral window**, with a 10-Hz synthetic peak in all four channels. The native tests also exercised the portable C++ transport helper and Node arithmetic checks. None is an ESP32 target firmware compilation.

The run uploaded JUnit XML, coverage, per-check logs, simulator netlists/output/logs, and loopback reports. In particular, the `native-integration` artifact is [artifact 10774490821](https://github.com/utof/eeg_ads1299_lab/actions/runs/35913793737/artifacts/10774490821). Artifact retention is 14 days, so rerun CI when fresh downloadable evidence is required; a retained Markdown summary is not a substitute for a new execution.

## Failure-first evidence and recovery limits

The interrupted source transfer was recovered by checking old/new content hashes before writing the recovered entries. The first independent recovery audit at source `b374c349b0145bac65ef3b7b53cdadad9fe72539` correctly failed: the missing `tools.check` implementation caused test collection, architecture, and type-check failures, and the unfinished utility scripts failed lint/type checks. See [recovery audit 35913194799](https://github.com/utof/eeg_ads1299_lab/actions/runs/35913194799).

The missing tools were completed, the existing runner tests passed, and a subsequent observed E402 failure was fixed by removing the loopback script's `sys.path` workaround and using the installed package imports. No checker was disabled to resolve those failures. This records observed red/green evidence; it does not prove the test-first chronology of every line originally recovered from the interrupted session.

## Scope and repeatability

Repeat the shared ordinary gate with `uv run --locked python -m tools.check`, and the required native integration with `uv run --locked python -m tools.check --native`. See [DEVELOPMENT.md](DEVELOPMENT.md) for setup and output locations. Later commits have their own CI runs; the numbers above identify the exact executed snapshot rather than asserting that an untested future tree is validated.

The selected hardware BOM/profile, firmware source and review gates are outside this DX change. No human connection is authorized. No physical hardware test, ESP32 target build, new Rev A network/BIAS/power simulation, KiCad ERC/DRC, or delivered purchasing quote is established by these checks. Required-status branch protection is a separate repository setting, not automatically enabled by adding a workflow.
