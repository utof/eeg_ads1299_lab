# P3 reference-check runtime: bounded exact-batch fast path

Base: `0719ba7e19eb4654aa4e43a862a8ffae0b32be9d`, tree
`cf437800d3915657fd86e500ebca64f5cada67e0`. This source preserves the complete
P3 connected copper and the pending-edge regression fix. It is **local and
unpublished** until a remote branch is read back; do not infer CI or review.
No PCB, circuit, BOM, firmware, carrier, dependency, electrical acceptance rule,
per-command timeout or shared 450-second CAD allowance changes.

## Why this optimization, not another timeout increase

The previous shared gate timed out at 450 seconds; its separately allowed
284-case diagnostic run took 505.58 seconds. Those results remain historical
fail/pass records, not rewritten. A fresh ordinary baseline in this session
passed 1232 tests plus 14 subtests. The unchanged 0719 CAD baseline then passed
284 cases in 364.18 seconds in a separate worktree. **The old timeout was not
reproduced in this environment.** A few brief focused probes overlapped that
baseline; it is a context measurement, not a controlled whole-suite benchmark.

Native profiling identified the P3 probe's repeated polygon subtractions: 1200
projections of 600 signal segments repeatedly processed the full ground-plane
polygon. The target reference has 8805 points, including fractured hole paths.
The profiled native subtract calls consumed about 1.18 seconds of a 1.43-second
probe. Other CAD checks and fresh native refill/DRC account for much of the full
suite; optimizing this kernel is not a promise of a proportionate suite speedup.

## What changed, and why the geometric acceptance is preserved

Group the **same exact full-width and 0.10 mm spine rectangles** by electrical
net. All rectangles retain the original integer-coordinate construction and
orientation. Subtract the same net-specific contact exclusions and the same
fresh reference-plane polygon from that group, using the pinned KiCad engine.
If and only if the result has **zero polygon outlines**, every rectangle in the
group is covered. Such a group needs no repeated per-segment subtraction.

Every nonempty group takes the original path: check each spine, calculate each
full-width gap, and reject growth outside the original pending envelopes on the
same net/layer. The per-segment 1e-6 mm2 numerical criterion is unchanged. There
is **no group area tolerance, contour simplification, tile clipping, sparse
point sampling, enlarged exclusion or reuse across board mutations**. Grouping
never crosses nets or the HOST/TARGET reference boundary. Layer/width/via checks
and the complete route inventory still execute even for an empty group.

This is the set relation: if `(union of query rectangles) - permitted copper`
is empty, the difference for each rectangle is empty. Nonempty results are NOT
assumed bad or good in aggregate; they fall back to the previous individual
checks. Because native polygon semantics matter, a regression explicitly checks
nested/duplicated full-width and spine outlines around a small central void;
that void must not disappear by an even-odd overlap cancellation.

The geometry kernel remains `uncovered()`, operating on the whole native ground
reference. The new audit independently reruns it for all 1200 projections and
requires the exact same 18-record gap inventory. This is a differential check
against the preserved kernel, not an independent electromagnetic model. Existing
pending gaps remain electrically unapproved and their file/hash are unchanged.

## Observed failure-first and equivalence evidence

Test commit `80c112a` observed two failures on the old probe: excessive repeated
native polygon work, and a changed new audit file missing from the schematic
input snapshot. The implementation commit `0fe282f` addresses both. The snapshot
contains 92 entries rather than 91 solely because that new source file is now
included. The whole 43-case focused audit/gate selection passed afterward.

The deterministic work assertion counts vertices passed as right-hand operands
to actual native subtraction calls (including batch preparation). Original:
10,618,414; optimized: 3,280,208, a 69.1% reduction for the canonical board. It is
a work proxy, not a CPU instruction count or runtime guarantee. The assertion
requires no more than half the naive repeated reference work, avoiding a flaky
wall-clock test. No native check result is cached across processes.

A separate preserved-old-script/new-script comparison used the SAME freshly
refilled board copy for each pair. Five fresh processes per version, alternating
order, gave median 1.4502 seconds before and 0.6345 seconds after (about 2.29x).
All ten JSON results matched. Eight further native board variants matched both
acceptance and failure class: reverse, split, remote-void, reference-void,
edge-growth, edge-remote, reverse-residual and split-residual. Each of those
variants was freshly refilled and had DRC parity/other/unconnected = 0/0/0; the
intended reference void and edge growth still failed their reference checks.

During authoring, passing a borrowed outline from a temporary SWIG parent caused
a native crash; retaining the rectangle while copying its outline fixed object
lifetime. A helper-name collision was also corrected before the implementation
commit. Those attempts are retained as failures, not reported as passing tests.
A scratch contour-unfracturing experiment changed geometric differences slightly
and was rejected; it is not part of the committed solution.

## Reproduce and next step

```sh
uv sync --locked --all-extras
uv run --locked --all-extras python -m pytest tests/test_reference_performance.py tests/test_schematic_gate.py
uv run --locked --all-extras python -m tools.check --schematic
```

The source checkpoint stores paired timings and counts; final shared-gate
outcomes must be read from their actual tested head, not inferred from these
focused results or the historical diagnostic run. The new native audit is
included alongside ALL 284 inherited CAD cases, not in place of any of them.
No full native integration, S3 build, hosted CI, independent reviewer or physical
experiment follows from this local runtime work.

Next is normal authorized publication of the full retained history, exact-head
hosted checks and a separate electrical/layout review. Automated publication
workflows were previously blocked and were not retried or bypassed in this
slice. Do not rebuild P3 copper. Keep its 18 pending edge records, long supply/
clock/control paths, sense coupling, stackup, #45/#48, complete delivered budget
and all fabrication/purchasing/powered-connection/body-use restrictions open.

Native polygon API reference (cross-checked with the installed 9.0.2 binding):
https://docs.kicad.org/doxygen/classSHAPE__POLY__SET.html
