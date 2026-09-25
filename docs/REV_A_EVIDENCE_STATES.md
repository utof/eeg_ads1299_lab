# Rev A completion evidence: structural guarantees and their boundary

Tracking: issue #12 and PR #13. This is a small change to the existing `lab.rev_a` result boundary, not a domain framework or a new simulation engine.

## The problem

A frozen dataclass did not freeze its nested dictionaries and lists. The previous `StudyReport` also accepted `ngspice_status`, comparison errors, and three safety flags independently. A caller could construct a report labelled `executed_and_compared` with no comparison evidence, mutate a returned case collection, or supply `body_connection_permitted=True` through an untyped runtime boundary. Static typing rejected some such calls, but the constructors did not.

The existing study runner already rejected numerical disagreement and invalid leakage inputs and removed old completion markers. Those orchestration protections were useful; they did not establish the stronger completed-value invariant.

## What is now represented by construction

`AnalyticOnly` and `NativeCompared` are separate immutable outcomes. The public status is derived from the outcome; it is not an independently writable field. `NativeCompared` requires exactly the six expected scenario/drive keys and finite nonnegative error values and defensively snapshots its mapping.

A `StudyReport` requires all three scenarios and eight distinct corner networks per scenario. Case metrics and the report's leakage bound reject negative or nonfinite values. Case mappings and nested corner sequences are defensively copied into read-only mappings and tuples. Changing a caller's original dictionary or list cannot change the report afterward.

The ideal-source pole is derived from the selected baseline rather than stored independently. The simulation's `clamps_fitted`, `hardware_validated`, and `body_connection_permitted` properties remain false and are not constructor parameters. A passive simulation has no authority to grant these approvals.

The existing read properties and JSON field names are preserved. Code serializing the complete report should use `report.to_dict()` rather than `dataclasses.asdict(report)`: the explicit serializer produces a detached JSON-compatible snapshot of the read-only collections. JSON output contains the familiar `ngspice_status` and `ngspice_max_abs_error`; it does not expose a second competing `spice_evidence` field.

## What this does not prove

A structurally valid summary is not cryptographic proof that ngspice ran. Unit tests can intentionally construct artificial complete comparison fixtures; those are not recorded native executions. The actual study runner still owns the real simulator invocation and complex-transfer `allclose` comparison. Its native integration tests remain necessary.

Neither Python types nor frozen values can prevent all disk errors, external file edits, process termination, reflection, or concurrent writers. The current output-directory contract still requires separate directories for concurrent runs. Final `study.json` publication uses the existing staged replacement, but the CSVs, netlists and logs are not an atomic multi-file transaction or content-authenticated generation. Argument parsing also precedes study execution; this change does not claim a complete lifecycle guarantee for arbitrary malformed CLI syntax.

These are deliberately narrow structural guarantees within the supported API, not a proof that every possible scientific result is true or that every invalid state in the whole repository is impossible. Hardware JSON, selected components, firmware, historical results and all original safety gates are unchanged.

## Executed before/after evidence, 2026-09-24

The final test-only source `b199ae8bff8e47bd52b619de3fb99cad8413ef25` reached pytest after passing formatting, lint, strict typing, complexity, architecture and static hardware checks. [Run 36051729526](https://github.com/utof/eeg_ads1299_lab/actions/runs/36051729526) reproduced **14 intended runtime failures**, with **223 tests and 5 subtests passing**. The already-existing failed-rerun behavior passed its control. Earlier authoring runs stopped at lint/type checks and are not counted as behavioral failure evidence.

Corrected source `9f0e2749985cf9142127364cd9daaa59493e3d28` passed all three normal PR jobs in [run 36052353540](https://github.com/utof/eeg_ads1299_lab/actions/runs/36052353540): Python 3.11 quality, Python 3.13 quality, and Native integration.

| Check | Observed result |
|---|---|
| Software tests | 248 passed; 5 subtests passed |
| Native/integration tests | 4 passed |
| Strict Pyrefly, including warnings | 0 diagnostics |
| Ruff / complexipy / Tach / static hardware contract | Pass; no function above complexity 15 |
| Actual branch coverage | 354/470 = 75.32%; unchanged floor 71% |
| Rev A comparisons | All six executed with ngspice 42 |
| Maximum absolute complex-transfer difference | 2.4425019869840343e-15 V/V |
| Ideal-source pole | 3393.0615079498434 Hz; unchanged |
| Localhost replay | 2,248 accepted packets; two intentional omissions detected |
| Tracked source after checks | Unchanged |

[The native artifact](https://github.com/utof/eeg_ads1299_lab/actions/runs/36052353540/artifacts/10830394575) retains 54 files. This evidence belongs to the exact source/run above; later documentation-only heads have separate workflow results.

New tests include explicit constructor/mutation regressions, completeness and finite-value checks, detached serialization, and **Hypothesis-generated sequences of successful and failed reruns**. Hypothesis was already installed. No new dependency, DDD library, state-machine framework or mutation-testing dependency was introduced.
