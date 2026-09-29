# Continue from this repository

**Current checkpoint: MISO/DRDY output repair after merged PR #63.** No previous chat or attachment is
required to recover the published source. Read this file and root `AGENTS.md`
first. This is a replaceable current checkpoint, not an append-only chat log.
Use the live Git/PR state; an old success report does not validate a later head.

## Start a fresh session

1. Fetch the repository and read `git status --short`, `git rev-parse HEAD`, the
   current `main`, and open PRs. Do not overwrite someone else's uncommitted work.
   Read this checkpoint on the branch you actually intend to change.
2. PR #63 is merged as `f834221a092f78dee4191305a3c3a8a03def0283`.
   The output repair is on `fix/digital-output-corridor`; inspect its live PR,
   exact-head checks and review until merged, then use current main. Do not
   substitute old chat-local variants. Before merging, inspect live head/base,
   diff, review comments, conflicts and exact-head CI, including base drift.
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

## Merged AVDD1 repair

PR #62's reviewed head330f34c7 and merge5ece3051 have the same tree81640a52.
Read `REV_A_AVDD1_REPAIR.md` and PR62 for its actual failure-first review history
and completed CI. Its three traversal defects were corrected, not waived.
Its historical board SHA256 was611218bae6559fb2488309fc80eee20ce2d6b5855977d52d600f947099179b43.
The separate chat-local1689234/e73e26bc variant was not merged or overlaid.
Keep longer VCAP3/C24 and designated AVDD56/C14 routes visible in whole-board
supply/noise review. Source review/native DRC did not measure that performance.

## What exists now

The four-channel ADS1299-4 / off-board ESP32-S3 Rev A has a **fully connected
PCB draft**, not an approved manufacturing design. The canonical editable board
is `hardware/rev_a/layout/rev_a.kicad_pcb`; the three-sheet schematic, project
settings and local libraries are in `hardware/rev_a/kicad/`. Never regenerate
this board with the parking-grid importer. Existing tests intentionally also
exercise an unrouted import; those artifacts are not the authored PCB.

The output-repair candidate has584segments,122vias,68footprints,245pads and
one native filled In1 region. Its board SHA256 is
232b7c68a63ae13aebcf71f8c0b1f210421c30452a1afc7b7c86dc1c118b23a3.
All footprints, other-net copper and the AVDD1/VCAP repair stay byte-identical.
`REV_A_ROUTING_COMPLETION.md`, `REV_A_AVDD1_REPAIR.md` and
`REV_A_DIGITAL_RETURN_REVIEW.md` describe earlier exact-source milestones;
the current delta is `REV_A_DIGITAL_OUTPUT_REPAIR.md`.

Source capture36641566165 fetched exactmainf834221a from GitHub. The full
baseline local gate passed1091ordinary+14subtests,98native and135KiCad cases.
Two failure-first native output cases precede the repair. Ten added native
cases exercise canonical geometry, connected wrong-layer/reference-window
faults, a curved-escape review regression and benign edits. Their focused result is not a final-head whole-suite
pass: read the live repair PR's actual final checks and review. Keep durable
summaries/source in Git; expired logs should be reproducible without a chat ZIP.

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

## Current output repair and next bounded task

Read `REV_A_DIGITAL_OUTPUT_REPAIR.md` and
`checkpoints/20260930_digital_output_repair.json`. Neither output has B.Cu
tracks now. Long spans run on F over In1; bounded In2 escapes beside U1 share
that same ground conductor. Four output-via fill openings are distinct after
native refill. Full-width projected-reference checks exempt only each output's
own through-contact voids, not unrelated plane gaps. The local10mm/rectangle
policy is not a manufacturer limit or a field solution. Codex4139341193 exposed
a curved-escape loophole; a DRC-clean native arc failed before the straight-In2
requirement fixed it. Curved In2 tracks are explicitly unsupported, not accepted
by testing only their endpoints.

The changed tradeoff is explicit: DRDY total authored segment sum grows36.499
to44.132mm; the parallel front runs have0.30mm copper-edge separation. No
measured coupling/noise/delay claim is made. Keep the existing AVDD1 neighboring
capacitor tradeoffs, SCLK/CS and CLK/START fill groups, final dielectric stackup,
edge rates, receiver and cable behavior in whole-board/release review.

**After the output-repair PR checks/review are resolved and merged, next is
input P/N geometry/coupling review.** Measure connector-to-R separately from
R-to-ADC, using actual pads/tracks/vias, layers, neighborhoods and reference
copper. Compare positive/negative paths without treating unequal lengths alone
as a failed analog specification. Bound parasitic/coupling hypotheses before
adding matching meanders; no generic simulator or approval registry is needed.
Do not reapply the earlier source-capture or copper authoring helpers over later
work. Continue from the actual live source, not historical board hashes.

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
