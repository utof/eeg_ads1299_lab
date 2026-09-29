# Continue from this repository

**Current checkpoint: digital return review after merged PR #62.** No previous chat or attachment is
required to recover the published source. Read this file and root `AGENTS.md`
first. This is a replaceable current checkpoint, not an append-only chat log.
Use the live Git/PR state; an old success report does not validate a later head.

## Start a fresh session

1. Fetch the repository and read `git status --short`, `git rev-parse HEAD`, the
   current `main`, and open PRs. Do not overwrite someone else's uncommitted work.
   Read this checkpoint on the branch you actually intend to change.
2. PR #62 is merged as `5ece3051f685c9fc70dee804d83061d5e59b2f48`.
   The current digital geometry review is on `review/digital-return-paths`.
   Read its live PR/head/checks until merged; afterwards use current main.
   Do not substitute the competing chat-local1689234 variant. Before merging,
   inspect the live diff, review comments, conflicts, exact-head CI and base drift.
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
Board SHA256 is611218bae6559fb2488309fc80eee20ce2d6b5855977d52d600f947099179b43.
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

The merged AVDD1 candidate has581segments,121vias,68footprints,245pads and
one filled In1 GND region. These are the reviewed board's counts, not permanent
constraints on later repairs. `REV_A_ROUTING_COMPLETION.md` is the dated original
07edcacc routing milestone; `REV_A_AVDD1_REPAIR.md` records the subsequent repair.

A fresh digital-review source checkout is recorded in Actions run36631345873.
It fetched exact main5ece3051, not the competing local archive. The clean baseline
full local gate passed1091ordinary+14subtests,98native and135KiCad cases; the new
review record binds geometry to its unchanged board digest. For the later
review/documentation head, inspect that PR's actual final checks/review. Keep
small durable summaries and necessary source in Git; transient CI artifacts may
expire. A workflow file, queued job or old success is not a pass for a new head.

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

## Current digital review and next bounded task

Read `REV_A_DIGITAL_RETURN_REVIEW.md` and
`checkpoints/20260930_digital_return_geometry.json`. The review used actual
merged5ece3051, not the old chat ZIP. The authored PCB was not changed.
Nine inter-board digital nets have134segments/15vias. MISO has32.565mm and
DRDY15.675mm on B.Cu; their back-layer spans cross six routed In2 traces in
projection, with no reference plane between those layers. F/In2 transitions
instead straddle the same In1 ground conductor. Source declares no dielectric
stackup, so1.6mm general thickness is not impedance/return qualification.

**Next: a focused MISO/DRDY output-corridor reroute.** Compare placing their
long spans on F.Cu over In1, with only necessary short escapes. Preserve the
AVDD1 repair, input/BIAS routes, values/MPNs, ground continuity and existing
rules. Inspect the merged MISO/DRDY antipad pair and actual reference at the
new escapes. Do not blindly add a GND via at every signal via or introduce an
extra/split plane. The six crossings are not shorts or a measured noise failure;
this is a layout improvement decision under explicit unmeasured assumptions.

Write a failing scoped route/reference regression for the chosen repair before
changing copper; challenge it with disconnected and connected-but-wrong-layer
copies while preserving benign routing edits. Refill and run full native parity/
DRC, compare exact source, then obtain actual review and final-head CI. A new
geometric contract is not a manufacturer noise limit. If front routing causes
worse nearby coupling/returns, document and reconsider rather than chase a count.

The digital screen identified three local merged fill openings, but no new
board-spanning split. It does not prove optimal return impedance. Remaining
SCLK/CS and CLK/START local groups remain review items. Input P/N geometry/
coupling follows the output repair, split connector-to-R and R-to-ADC. No new
generic simulator or approval registry is needed. Full stackup, cable, receiver
loading and edge-rate evidence still belong to release/physical review.

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
