# Continue from this repository

**Current checkpoint: input geometry/coupling review after merged PR #64.**
No previous chat or attachment is needed. Read this file and root `AGENTS.md`
first; use live Git/PR state, not a historical success or a missing chat reply.

## Start a fresh session

Fetch current main and open PRs; inspect `git status --short`, `git rev-parse
HEAD` and `git rev-parse HEAD^{tree}` before changing anything. Preserve other
people's uncommitted work. PR #64 is merged as
`5197c5b9478391e305c5d41f6c992bbdcd6bfd56` (tree
`eecf9efb62f13d2cbda4d3815bed3de05a231fb6`). The input review is on
`review/input-layout-coupling`: read its live head/checks/review while unmerged;
after merge use current main. Do not reroute MISO/DRDY again merely because the
previous chat did not display its completion report. Before any merge recheck
head/base, actual diff, conflicts, review findings and exact-head CI.

Read `DEVELOPMENT.md`, `HARDWARE_BASELINE_REV_A.md` and the applicable detailed
review before changes. Canonical board: `hardware/rev_a/layout/rev_a.kicad_pcb`.
Project, three schematic sheets and local libraries: `hardware/rev_a/kicad/`.
Never regenerate the authored board with the parking-grid importer. Its
intentionally unrouted test output is not the completed layout.

## What is published and what remains a hypothesis

The reviewed board has 584 segments, 122 vias, 68 footprints and 245 pads, with
one native filled In1 GND region. Its source SHA256 is
`232b7c68a63ae13aebcf71f8c0b1f210421c30452a1afc7b7c86dc1c118b23a3`.
These are a dated source identity, not permanent constraints on reviewed repairs.
The input review changes no copper, schematic, BOM, firmware or model.

PR #62 repaired AVDD1 and fixed three native guard traversal defects before
acceptance. Read `REV_A_AVDD1_REPAIR.md`; longer VCAP3/C24 and designated
AVDD56/C14 paths still need whole-board supply/noise consideration. PR #64
moved MISO/DRDY long spans onto F over In1 with bounded local In2 escapes.
Its final reviewed e0184fb8 head has the same tree as merge5197; all five hosted
jobs passed and Codex reported no major issues after the arc-guard and stale
roadmap findings were corrected. See PR64 and `REV_A_DIGITAL_OUTPUT_REPAIR.md`.
DRDY grows to44.132mm authored sum; 0.30mm parallel front edge spacing,
stackup/edge/cable/barrel effects remain unqualified. Source/AI review and DRC
are not professional or physical electrical qualification.

## Current result and next bounded task

Read `REV_A_INPUT_LAYOUT_REVIEW.md` and
`checkpoints/20260930_input_geometry.json`. Eight main R-to-C-to-ADC paths
are already F-only and have only0.435mm magnitude P/N centreline difference.
The B-layer filtered-input copper is instead a branch to each DNP diode pad3;
its P/N branch sums differ by4.5mm. DNP parts are not fitted, but their copper
is still connected. Do not turn either length difference into a capacitance,
CMRR, noise, safety or matching guarantee.

The input B/In2 screen has13 unique net-pair crossing locations (22 raw pairs,
with overlapping AVDD items deduplicated). Three are **CH1N_DUMMY crossing the
IN2P/IN3P/IN4P DNP branches** with no GND layer between. In1 is above both
layers, even where its fill projects onto each crossing. Four other upstream
input overlaps and six supply overlaps are retained, not waived.

**After the input-review PR checks/review/merge, rework the CH1N_DUMMY corridor
first to remove those three cross-channel overlaps.** Prefer a suitable F
corridor over In1; preserve front R/C/U1 itineraries, pad/net/population
inventory, all AVDD1/VCAP and output-repair copper, ground continuity and rules.
First observe a focused geometry-policy failure; then implement and test the
repair with actual refilled DRC/parity and connected-but-wrong-layer/benign
controls. If F placement causes worse neighboring geometry, reconsider rather
than chase a count. Do not add matching meanders, delete DNP branches or adopt
a new protection/filter circuit implicitly. Other upstream overlaps, branch
asymmetry and actual parasitic/coupling effects remain explicit follow-through.

Four native illustrative passive runs demonstrate conditional conversion from
unequal capacitance-to-ground using existing `lab.analog`; they do NOT model
cross-channel mutual capacitance or assign capacitance to board lengths. The
detailed review contains the exact assumptions, equation, native grid and
reproduction snippet. No new production model/dependency or measured electrode,
PCB or silicon parameter was introduced.

Fresh GitHub source capture36696579521 and baseline ordinary+schematic checks
used clean5197:1091ordinary+14subtests,145KiCad and22console cases;86.06%branches,
unchanged71%floor. The22 console cases are a subset of the existing98native
suite; that command did not run all98native or the S3 target. Geometry checks
covered706track/via items,245pad positions,eight main itineraries and13 unique
crossings. Analysis runs are not added project tests. Read the live input-review
PR's final-head verification separately; inherited passes do not validate a
newer head. Main has a fully connected draft, not fabrication approval.

## Reproduce and inspect

```sh
uv sync --locked --all-extras
uv run --locked --all-extras python -m tools.check
uv run --locked --all-extras python -m tools.check --native --schematic
uv run --locked --all-extras python -m tools.check --firmware
```

Install required native tools first. The lockfile is authoritative; native
KiCad9.0.2 engine/libraries are pinned in `.github/workflows/schematic.yml`;
Arduino setup is in `firmware/toolchain.json` and the Firmware workflow. Jobs
are executable fresh-runner setup, not proof a sandbox already has tools.
Missing tools/network/cache are blockers, never skipped into success. Avoid
concurrent uv sync/hook resync against a running environment. Expired artifacts
should be reproducible from source; a chat cache/font/binary is not a dependency.

Use a disposable project copy, not the importer:

```sh
set -eu
review_dir=$(mktemp -d "${TMPDIR:-/tmp}/eeg-review.XXXXXX")
cp -a hardware/rev_a/kicad/. "$review_dir/"
cp hardware/rev_a/layout/rev_a.kicad_pcb "$review_dir/rev_a.kicad_pcb"
printf 'Open %s/rev_a.kicad_pro\n' "$review_dir"
```

Transfer reviewed edits back to canonical tracked paths deliberately. Changes
in a temporary copy are not committed source. Review/test each actual head.

## Finish without private handoff dependencies

Publish source/tests/necessary small reference inputs to a named PR, read back
its head, update this checkpoint and `REV_A_COMPLETION_ROADMAP.md`, and record
commands/outcomes with their actual tested SHA. Distinguish new/inherited,
local/hosted, published/unpublished and unexecuted work. Merge only after actual
review and required checks, preserving history with a merge commit. Keep WIP
in a discoverable PR, not solely `/mnt/data`, chat or expiring CI artifacts.
Each report starts with TLDR then category/estimated-remaining-turns/status/
next-slice table. Do not mistake test-count growth for engineering progress.

The original reconstructed local07edcacc history remains reachable through
bridge0eb2a121 and archive/connected-routing-local-07edcacc; it was not earlier
GitHub publication. The chat-local1689234 variant and issue45's76502e7 variant
are different unmerged sources, not patches to apply over current main.

## Unresolved decisions and user constraints

Keep #45/#48 OPEN. Read the completion roadmap and the bench-harness, capacitor
evidence/bulk assessment, tantalum-land and power documents for the actual
remaining stackup, mounting/mating/assembly, capacitor lifecycle/effective-C,
console/interface rail-loss behavior and delivered-budget decisions. Do not
recreate the already-published logical AFE/DevKit pin map or silently approve a
live adapter. Models are bounded hypotheses; target compilation is not a bench
test. Body use is a separate later revision.

The user is an electronics beginner; favor explained, test-first bounded slices.
Additional spending target is $100, not a delivered quote. Owned unspecified
ESP32, Arduino Uno and MCScap electrodes do not establish purchase/revision of
the selected ADS/S3. Exact electrode suffix/lead properties and board revision
need physical confirmation; family bounds are not user's measurements.
Preserve all false hardware/purchase/release/body-use gates. BIAS, lead-off and
external acquisition are not enabled by routing. No purchasing, fabrication,
powered connection or body-use authorization is granted by this checkpoint.
