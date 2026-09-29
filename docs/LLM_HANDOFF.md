# Continue from this repository

**Current checkpoint: 29 September 2026.** No previous chat or attachment is
required to recover the published source. Read this file and root `AGENTS.md`
first. This is a replaceable current checkpoint, not an append-only chat log.
Use the live Git/PR state; an old success report does not validate a later head.

## Start a fresh session

1. Fetch the repository and read `git status --short`, `git rev-parse HEAD`, the
   current `main`, and open PRs. Do not overwrite someone else's uncommitted work.
   Read this checkpoint on the branch you actually intend to change.
2. PR #60 is merged as `a4ac32c53e7e06eb3272db270afb1f3ac11a8c20`.
   Start from current main and inspect open PRs before changing anything. The
   supply-review continuation is on `review/rev-a-power-return`; read its live
   PR/head until merged, then use main. Before any merge, inspect the current
   diff, review comments, conflicts and exact-head checks, including base drift.
3. Read `docs/DEVELOPMENT.md` for the pinned environment and `hardware/rev_a/`
   plus `docs/HARDWARE_BASELINE_REV_A.md` for circuit decisions. Choose the next
   bounded task below, not a recreation of already published work.
4. Record the source SHA/tree used for your own checks. If tools or source-write
   access fail, distinguish what is published, merely local, or not executed.
   Do not use a substitute branch and call it this candidate.

The bridge commit `0eb2a121e51de8c1f103af5a0c991e4d782a59fe` has the exact original
routed tree `0c6dd0675c977cbcef2ef043cb49e9081b8c9b8f`. Its first parent is real
GitHub main `d2ee2964c14ef558a919eab77eb5eb153c4fdbc0`; its second parent is
reconstructed local head `07edcacc4c22bfd2ae5aa053c658d6c480b75f5e`. All ten
original local commits, including failing tests, remain reachable. These are
not invented GitHub ancestors. The original source is also on
`archive/connected-routing-local-07edcacc`. See
`docs/checkpoints/20260929_source_recovery.json` for identities and evidence.

## What exists now

The four-channel ADS1299-4 / off-board ESP32-S3 Rev A has a **fully connected
PCB draft**, not an approved manufacturing design. The canonical editable board
is `hardware/rev_a/layout/rev_a.kicad_pcb`; the three-sheet schematic, project
settings and local libraries are in `hardware/rev_a/kicad/`. Never regenerate
this board with the parking-grid importer. Existing tests intentionally also
exercise an unrouted import; those artifacts are not the authored PCB.

`docs/REV_A_ROUTING_COMPLETION.md` describes the completed 35 connections on
25 nets and inherited KiCad 9.0.2 refill/DRC result (0 parity, 0 other findings,
0 unconnected). The recovered board has 579 segments, 126 vias, 68 footprints,
245 pads and one filled In1 ground region. These historical counts describe
07edcacc, not a permanent numeric constraint on future reviewed layout work.
The recovery turn changed no copper, schematic, BOM, firmware or model.

**New execution:** recovery Actions run `36579755641` imported hash-checked
original Git objects and then separately checked out the candidate from GitHub,
verifying its full 280-file source tree, ten commits and board digest. This proves
source recovery, not electrical correctness. Consult PR #60's live final-head
Quality, Schematic and S3 results for new normal CI; a workflow file, queued job,
or this checkpoint is not a test pass. Full logs are CI artifacts with finite
retention. Keep small durable summaries and source identities in Git; reproduce
expired transient outputs from the committed source rather than requiring an
old chat ZIP. Never use a green run from an earlier head to approve a later one.

## Reproduce and inspect

```sh
uv sync --locked --all-extras
uv run --locked python -m tools.check
uv run --locked python -m tools.check --native --schematic
uv run --locked python -m tools.check --firmware
```

Install the declared native tools first. The ordinary environment is locked by
`uv.lock`; native KiCad 9.0.2 engine/libraries are pinned in
`.github/workflows/schematic.yml`, and Arduino setup is specified by
`firmware/toolchain.json` and `.github/workflows/firmware.yml`. The Actions jobs
are executable fresh-runner setup, not proof that tools exist in a new agent's
sandbox. Missing tools/network/cache must be reported, not skipped into success.
No installed tool/cache/compiled binary or font attachment is required from chat.

For a directly openable review copy with the correct same-basename project and
schematic, copy the existing source rather than invoking the importer:

```sh
set -eu
review_dir=$(mktemp -d "${TMPDIR:-/tmp}/eeg-review.XXXXXX")
cp -a hardware/rev_a/kicad/. "$review_dir/"
cp hardware/rev_a/layout/rev_a.kicad_pcb "$review_dir/rev_a.kicad_pcb"
printf 'Open %s/rev_a.kicad_pro\n' "$review_dir"
```

This is a disposable copy. Deliberately transfer any reviewed edits back to the
canonical tracked paths, inspect the diff and rerun the gates. Do not mistake
changes in the copy for committed source. The native tests already assemble
independent copies, refill zones and check actual routing/parity.

## Current review and next bounded task: AVDD1 local bypass rework

The first supply/bypass geometry review is in `REV_A_POWER_RETURN_REVIEW.md`,
with explicit paths/UUIDs in `checkpoints/20260929_power_return_geometry.json`.
It inspected the actual a4ac32c board recovered solely from GitHub, cross-checked
705 track/via forms and 245 pad positions, and independently refilled/checked a
copy with KiCad 9.0.2 (run36586282560:0/0/0,exit0). No copper was changed.
These are source/native-CAD results, not hardware measurements or whole-board
independent electrical approval.

**Do the AVDD1 cluster rework next**, not another source-recovery or general
warning-only pass. U1.54 reaches designated C16 through 11.936 mm of explicit
trace centreline and two vias; its C27 path is11.036 mm. The C16/U1.53 GND-plane
entries are9.325 mm apart. AVDD56 joins the positive trunk before those local
bypasses; C14 is also accessible through a shorter6.486 mm/two-via shared path.
These lengths exclude via barrels/pad spreading; plane-entry separation is not
return-current path length or loop inductance. No universal length/noise limit
was established. The finding is the departure from preferred direct local
bypass-before-plane topology, not an absent capacitor or a measured noise failure.

Review C16/C27 placement jointly with VCAP3 C9/C24 and neighboring C14 so that
54-to-bypass-to53 is compact before joining shared copper. Preserve front-side
assembly assumptions, ground-plane continuity, values/MPNs and other sensitive
paths. Do not split GND, add ferrites, move components under U1, or silently
transfer the detour to VCAP3. Establish the focused failing geometry/topology
regression before the repair; rerun native fill/parity/DRC and fault tests.
Keep any geometric target distinct from a manufacturer noise guarantee.

After that, review digital layer transitions/reference copper, then input P/N
paths split into connector-to-R and R-to-ADC sections. Record calculations,
source measurements and hypotheses separately. Do not infer good return
impedance from one GND region or failed analog performance from length mismatch
alone. No new generic simulator or approval registry is required.

Use `REV_A_COMPLETION_ROADMAP.md` for the current status/remaining-turn ranges.
Every completion report now starts with TLDR plus a category/estimated-turns/
done/next-slice table, followed by the useful evidence and specific next task.

Keep **#45 and #48 open**: actual console/interface powered-off behavior,
component lifecycle/effective capacitance and assembly lands, stackup, mounting,
connector mates/clearance and the delivered budget remain unresolved. Read
`REV_A_BENCH_HARNESS.md`, `REV_A_CAPACITOR_EVIDENCE.md`,
`REV_A_BULK_CAPACITOR_ASSESSMENT.md`, `REV_A_TANTALUM_LANDS.md` and
`REV_A_COMPLETION_ROADMAP.md` for those specific decisions. Older placement and
roadmap paragraphs are dated history, not instructions to undo completed copper.
Issue #45's older 76502e7/ded7be9 digital-only candidate is not this source;
do not infer its U1.51 ground-return adjustment belongs to 07edcacc.

## Finish each subsequent session without a private handoff dependency

Publish the scoped source/tests and required small reference inputs to a named
branch/PR before claiming delivery. Read back the remote head. Update this file
with what changed, the next bounded task, live PR/issue pointers and explicit
blockers. Record executed checks with their actual tested SHA, outcome, command
and evidence location; mark inherited results and unexecuted checks. Review and
merge with a merge commit only when the required checks/reviews are satisfied.
Unfinished work stays discoverable in a clearly identified open PR, not only in
`/mnt/data`, a conversation attachment, or an expiring Actions artifact. A blocked
write is a publication blocker, not permission to claim the repository is current.

## User and scope constraints

The user is an electronics beginner who prefers test-first, small meaningful
slices, functional calculations and understandable explanations. Additional
spending target is $100, not a verified delivered quote. Owned parts include
an unspecified ESP32, Arduino Uno and MCScap electrodes; selected ADS/S3 parts
are not proof of purchase. Exact MCU/board revision, electrode suffix and lead
properties still need physical confirmation. See `docs/references/mcscap/`;
do not turn family bounds into measurements of the user's electrodes or scalp.

Preserve all false hardware/purchase/release/body-use gates. BIAS, lead-off and
external acquisition are not enabled by completing routing. Models are bounded
hypotheses; target compilation is not physical verification. No fabrication,
purchasing, powered connection or body use is authorized by this checkpoint.
Historical handoff detail remains in Git, for example
`git show 07edcacc:docs/LLM_HANDOFF.md`; model and firmware scope lives in the
specific documents rather than duplicated, stale instructions here.
