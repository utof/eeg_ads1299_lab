# Retained native power evidence

`uv run --locked python -m tools.check --native` now runs the handwritten
switch compatibility pilot into its own `rev_a_power/<run-id>/` evidence folder.
The normal native artifact upload retains the six circuit netlists, fresh raw
integration endpoints, voltage tables, initialization bytes, simulator logs,
source record and digest manifest. No vendor library or network download is
needed by this gate.

The command invokes:

```bash
uv run --locked python -m lab.rev_a_power --require-complete-switches --out reports/check/rev_a_power
```

This mode fails when any requested switch execution is rejected or incomplete.
It first preserves the investigation, including failures, and then returns a
nonzero exit with the exact evidence-directory path. A completed investigation
manifest remains a record of the attempted probes, not a claim that all passed.
`pilot.json` exposes the derived `switch_execution_complete` boolean separately
from each endpoint's compatibility comparison.

A complete but incompatible inverse-switch result is legitimate diagnostic
evidence, not a failed execution. Therefore this gate requires all six
executions to complete, not all six hypotheses to agree. The existing native
tests independently require the usual and normalized endpoint cases to match
their unchanged divider tolerance. Physical regulator and body-use flags stay
false. Optional vendor startup/shutdown compatibility is not promoted by this
handwritten-fixture gate.

Ordinary `lab.rev_a_power` calls retain the previous behavior: exit zero means
an investigation was recorded, including rejected probes. The new requirement
is explicit in both CLI and Python API; the default is false. Its scope is the
six switch executions only, not success of optional vendor probes.

Six focused regressions failed before implementation: missing shared-gate
command, missing failure propagation, absent completion flag and unsupported
CLI option. Corrected tests cover complete/incomplete execution with/without
the requirement, retained negative evidence, and a deliberately wrong completed
endpoint that must remain distinguishable from missing simulation evidence.
Private library lifetime and publication are small local helpers, not a new
runner or evidence framework. No comparison threshold or CI coverage floor is
lowered.
