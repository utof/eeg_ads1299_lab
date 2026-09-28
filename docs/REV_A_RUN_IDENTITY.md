# Generation-bound Rev A evidence

Scope: issue #15 / PR #19. This changes publication and reading, not the passive
circuit, selected components, firmware, or hardware/body-use gates.

## What a successful command means

A run gets a unique, 32-character lowercase hexadecimal identity. `study()` returns
that identity in its immutable `StudyReport`. It never overwrites another run.

```text
reports/rev_a_input/
  current.json                 # last successfully published generation, NOT last attempt
  runs/<run-id>/
    manifest.json
    study.json
    <scenario>/response.csv
    <scenario>/<drive>/network.cir
    <scenario>/<drive>/ac.txt       # native runs only
    <scenario>/<drive>/ngspice.log  # native runs only
  .pending/<failed-run-id>/     # partial evidence; never interpreted as completed
```

The manifest records schema/study identity, requested leakage and native mode,
validated baseline digest, source commit/dirty status when available, Python/NumPy
and (when executed) ngspice versions, outcome, and SHA-256 for **every artifact**.
There are ten hashed files in an analytic run and twenty-two in a native run.
`manifest.json` itself is bound by its SHA-256 in `current.json`.

A private run directory is completed first, then renamed into `runs/`; only then
is a staged `current.json` atomically replaced. A failed final pointer replacement
can leave an unreferenced completed directory, but cannot advertise it as current.
The supported writer does not modify published generations. This is logical
immutability, not filesystem permissions or protection from external editing.

## Request identity is mandatory when reading

**Do not interpret `current.json` alone as proof that the command just requested
succeeded.** It deliberately retains the last successful generation on failure.
Automated callers choose an identity *before* the request, check the command's
exit status, and verify that same identity and parameter set:

```bash
export RUN_ID="$(uv run --locked python -c 'import uuid; print(uuid.uuid4().hex)')"
uv run --locked python -m lab.rev_a --out reports/rev_a_input \
  --run-id "$RUN_ID" --require-ngspice --leakage-bound-na 1
uv run --locked python - <<'PY'
import os
from lab.rev_a import read_study
report = read_study(
    "reports/rev_a_input", expected_run_id=os.environ["RUN_ID"],
    require_ngspice=True, leakage_bound_a=1e-9,
)
print(report.run_id, report.ngspice_status)
PY
```

For manual use, omit `--run-id` and use the ID printed by the successful command.
Never reuse an identity, including one left in `.pending/` after failure.

The reader checks the pointer, manifest schema, exact requested mode/leakage,
baseline digest, exact artifact inventory and file digests. It parses the same
report bytes that were hashed and reconstructs validated immutable domain values;
derived status, metrics, corner structure and false safety flags must agree.
Symlink artifacts/run directories and unlisted files are rejected. By default the
expected baseline is the current validated hardware contract; a caller examining
a known older contract can explicitly supply its `baseline_sha256`.
The reader verifies the **current** generation, not arbitrary historical folders.

## Failure and concurrency semantics

Malformed numbers, unknown options, missing option values and `--help` are rejected
by argument parsing without interpreting or deleting an output path. Rejected
numeric/identity/baseline requests also preserve history. A previously successful
ID still identifies historical success; it cannot satisfy a different expected ID.

Accepted attempts acquire `.writer.lock` by exclusive creation. A second writer is
rejected rather than sharing files or waiting. The lock is removed on normal
success or handled failure. A process kill can leave it behind: confirm that no
writer is active and inspect/preserve partial evidence before manually removing a
stale lock. There is no automatic lock breaking, multi-host coordination, or crash
recovery service. Different output roots remain independent.

Partial write, calculation or rename failures retain their files for diagnosis.
Old flat `study.json` outputs are neither deleted nor accepted as current; they
remain legacy, unverified-by-this-reader artifacts. Consumers must migrate paths
from `<out>/study.json` to the path printed by the command or use `read_study`.

## Evidence and limits

The test-first CI source `c4eaf9e7b83f752758bb3d06aa42b548c036bfb4` failed the new
CLI generation assertion with the existing 248 tests plus five subtests passing:
[run 36163330566](https://github.com/utof/eeg_ads1299_lab/actions/runs/36163330566).
The expanded suite covers rejected CLI, successful/failed reruns, actual
interleaved writer exclusion, duplicate/partial IDs, write and both rename
failures, stale pointers, artifact edits, symlinks, schema corruption, rehashed
inconsistent report values, and generated rerun sequences. Consult PR #19's
exact final head checks for the completed implementation, not the test-only run.

Atomic pointer replacement is not an fsync/power-loss durability guarantee, a
transaction with arbitrary external readers, or resistance to malicious writers.
A party able to replace files, manifest and pointer together can recompute hashes;
this is **integrity checking, not authenticity or proof of simulator execution**.
Source `worktree_dirty=true` means the commit alone does not describe all local
source edits; absent Git metadata remains explicitly unknown. A valid generation
still only represents the stated illustrative circuit and requested comparisons.
It never proves physical hardware, electrode calibration, protection, or safety.
