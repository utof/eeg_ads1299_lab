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
   Start from current main and inspect open PRs before changing anything.
   PR #61 is merged as
   `1e86c049c46b52b3f1889f6bef7941763f965f79`. The AVDD1 repair is **PR #62**,
   branch `fix/rev-a-avdd1-local-bypass-retry`; read its live head/checks/review
   until merged, then use main. Before any merge, inspect the current
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

## AVDD1 review continuation

Use live PR #62 (`fix/rev-a-avdd1-local-bypass-retry`) until merged, then main.
This is the board with SHA256
`611218bae6559fb2488309fc80eee20ce2d6b5855977d52d600f947099179b43`.
The chat-only `1689234` / `e73e26bc...` candidate is different and is not this
PR's ancestor. Do not overwrite this source with that archive or reuse its test
counts as current evidence. The current source was fetched in a separate
GitHub checkout; no chat attachment is needed to continue it.

Codex's actual review `4137830251` found that the pre-plane guard stopped at the
first capacitor. The continuation reproduced two DRC-clean inter-capacitor
faults before fixing per-capacitor traversal; 15 focused native cases then
passed, including three benign split/reversal controls. Copper stayed unchanged.
Read `REV_A_AVDD1_REPAIR.md` and its continuation checkpoint. Check the live
final-head CI and renewed Codex result before merge; older green runs do not
cover the correction. After this review is closed, do digital reference/return
transitions, not another bypass rewrite or source-recovery pass. Keep the
longer VCAP3/AVDD56 paths explicit in broader electrical review.

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

## Current repair and next bounded task: digital return paths

PR #62 contains the actual AVDD1 local bypass repair. Read
`REV_A_AVDD1_REPAIR.md` and `checkpoints/20260929_avdd1_repair.json`.
Source before repair is1e86c049; first published repair/test head isa19bfc45.
Use the live PR head and final CI/review, not a historical pass for an earlier
head. Publication run36622822760 verified a separate fresh GitHub checkout.
The failed preceding turn left reusable tool artifacts but only an incomplete
source transfer; this turn did not claim to recover its unverified repair.

Five existing front-side caps C16/C27/C9/C24/C14 moved. U1.54 and U1.53 now
reach the local AVDD1 caps on front copper before joining shared supply/ground.
Repaired board digest is611218bae6559fb2488309fc80eee20ce2d6b5855977d52d600f947099179b43;
counts are581segments/121vias/68footprints/245pads, not permanent future limits.
Native field/relative-pad comparison preserves all values/MPNs/footprints/DNP,
and the other63footprint positions. No signal tracks were added to In1.

**Do not report that every path improved.** C24's VCAP3 path is now6.016mm,
and U1.56's designated C14 path is6.713mm, with a nearer shared C15 alternative
of3.663mm. These are explicit trace-centre itineraries, not measured impedance.
The broader supply/noise review is not closed by the local repair. The original
PR61 review remains a dated pre-repair record, not an instruction to undo it.

Tests first exposed four missing local AVDD1 paths, then two early-plane-join
loopholes. Eleven added native cases include DRC-clean fault boards: a general
connected supply cannot substitute for a bounded local bypass. Native via
identification uses KiCad item type, not isinstance on its connectivity proxies.
The test's whole-item metric is not a shortest conductive distance, and its
cap-contact boundary is not an exhaustive arbitrary-geometry proof. Review
future long/overlapping boundary tracks explicitly; do not inflate the claim.

**Next after live PR review/CI: digital reference and layer-transition review**
on the current authored board. Inventory active digital signal vias/layers,
identify reference copper and local GND bottlenecks, then record concrete
findings against manufacturer guidance and the proposed (still unqualified)
stackup. Fix a detectable defect test-first; do not impose blanket stitching
rules or invent a qualified stackup. Input P/N geometry/coupling follows, split
into connector-to-resistor and resistor-to-ADC sections. Retain the capacitor
tradeoffs in the eventual whole-board electrical review. No generic simulator,
approval-registry framework, arbitrary meanders or split ground plane is needed.

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

The follow-up pad-contact probe also reproduced two missed mid-bank entries
when the C16 pad bridges separated track ends. The pad-contact red/fix history
is retained in `f805fe04` / `86b45e6d`; 19 focused native cases passed after
traversing intermediate bank pad contacts. Read the current exact PR head's
full CI/review results, not the preceding 15-case checkpoint. No copper changed
in either review correction. Keep the current PR authoritative over local168.

The renewed Codex review also found a side-branch-to-via gap at the target
track (`4138094514`). Test-first `80810770` / fix `e14d52e3` distinguish such
pre-capacitor spurs from legitimate post-bank feeds. The complete focused set
is now 23 native cases, superseding earlier 15/19-case checkpoints. Finish the
live final-head CI/review before merge; then proceed to digital returns, not
another recreation of the AVDD1 layout. See the review document for remaining
conservative contact/whole-item geometry limits and physical tradeoffs.

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
