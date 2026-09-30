# Continue from this repository

**Current checkpoint: combined upstream-coupling disposition after merged PR #66.**
No prior chat/ZIP is needed. Read root `AGENTS.md`, this checkpoint and live Git/PR
state before choosing the next bounded task. A missing chat reply is not proof
that source work was lost.

## Start here

Fetch main/open PRs; record actual SHA/tree and `git status --short`. Preserve
other people's uncommitted work. CH1N PR #66 is merged as
`b88d3746f5f2c72dd60ffbb201213ac9010b19a4`, tree
`54d8bb7df44d437626100ffa6da06fd65116c6a3`. The combined assessment is on
`review/upstream-coupling-disposition`: use its live PR head until merged, then
current main. Recheck head/base, diff, conflicts, reviews and actual exact-head
CI before merge. Do not repeat the completed AVDD1, MISO/DRDY or CH1N repair.

Canonical authored board: `hardware/rev_a/layout/rev_a.kicad_pcb`. Project,
three schematic sheets and local libraries: `hardware/rev_a/kicad/`. Never
regenerate this board with the parking-grid importer; its deliberately unrouted
test output is not the authored layout. Read `DEVELOPMENT.md` and
`HARDWARE_BASELINE_REV_A.md` before source changes.

## State and next bounded task

Board SHA256 remains
`5da65b4307f0336883da9aeae48711b28c1944ec587f5d3174f12db4e9921875`:
582 segments,122 vias,68 footprints,245 pads. These are dated identity facts,
not permanent constraints on reviewed repairs. This assessment changes no copper,
BOM, schematic, firmware, model, dependency, rule or approval gate.

**Next: choose/document a vendor four-layer stackup and the bounded
person-disconnected input/coupling test envelope.** Read
`REV_A_UPSTREAM_COUPLING_DISPOSITION.md` and its source-bound JSON first. The
nine residual upstream B/In2 locations form six electrical pairs: CH3P/CH3N/
CH4N against CH2N/AVDD. They are ONE item held for the stackup/budget decision,
not nine queued reroutes, not waived and not a measured noise failure.

The immediate deliverable is an exact vendor stackup/revision with layer
spacing/copper/material tolerances, plus explicit supported source/load range,
aggressor node spectra, intended band/rate/gain, allocated coherent-error and
broadband-noise budgets and a feasible measurement floor. Unset values are
blockers, not permission to adopt illustrative 5k/50k/1pF/10pF numbers as
requirements. Compare candidate stackups against the existing F/GND/In2/B
copper; changing a layer name does not add shielding. Do not silently redesign
the circuit, split ground, add ferrites or disable tests.

Once these inputs exist, choose one combined upstream repair or document
bounded experimental risk for separate pilot-release review. A simple B-to-F
swap at unchanged XY was tested on a disposable copy and gives30 native DRC
entries (including shorts); it is not a repair. This does NOT prove a carefully
redesigned combined route impossible or inferior. Avoid large speculative
detours solely to improve a crossing count. Keep #45 OPEN pending disposition.

Seven native illustrative mutual-capacitance runs and an independent equation
quantify sensitivity to assumptions; they do not extract PCB capacitance or
model silicon, supply PSRR, magnetic/cable coupling, digital filtering or
aliasing. The exact reproducible example includes native-result checks and
three controls; an incorrect-output software double is rejected. These are
analysis runs, not added project tests or physical evidence.

Pilot fabrication and physical validation are separate finish lines: a first
PCB cannot be measured before it exists. Before pilot fabrication, require
defined design inputs and separate risk/release review. Before performance
validation, require calibrated person-disconnected measurements with the
chosen budget and startup/interface prerequisites. No approval is granted by
this distinction; do not turn the future test plan into claimed current sensing.

## Preserve previous work and its limits

PR #62 fixed AVDD1 and three guard traversal gaps. Keep the longer VCAP3/C24
and AVDD56/C14 routes visible in whole-board review. PR #64 repaired MISO/DRDY
long spans and the arc-screen bug; DRDY remains44.132mm authored total and
parallel spacing/real edges/cables remain unqualified. PR #66 removed all four
CH1N unshielded overlaps but lengthened that route to33.884mm with18.588mm
on In2; it is not front-only. Existing targeted native guards remain active.

The eight required R/C/U1 input paths remain front-only; their0.435mm P/N
centreline differences and the4.5mm DNP-branch difference are NOT electrical
balance/noise guarantees. The earlier ground-C sensitivity example is different
from the new upstream mutual-injection example. Do not treat an unpopulated
diode footprint as absent copper or qualified protection.

Read the detailed AVDD1, digital-output, input-layout and CH1N review documents
for exact source-bound geometry. Temporary investigation helpers/outputs are
not alternative source or instructions to overwrite later edits. Original
reconstructed07edcacc history remains reachable; the separate chat-local1689234
and issue45's76502e7 variants must not be overlaid onto current main.

## Reproduce and inspect

```sh
uv sync --locked --all-extras
uv run --locked --all-extras python -m tools.check
uv run --locked --all-extras python -m tools.check --native --schematic
uv run --locked --all-extras python -m tools.check --firmware
```

Install the required native tools first. `uv.lock` is authoritative; KiCad9.0.2
engine/libraries are pinned in `.github/workflows/schematic.yml`. Arduino setup
is in `firmware/toolchain.json` and its workflow. Executable fresh-runner setup
does not mean the next sandbox has those tools. Missing tools/network/cache
must fail, not be skipped into a pass. Avoid concurrent environment resync.
Read this assessment PR's actual final-head checks/review, not just an older
pass. Baseline, analysis, final-head and post-merge execution are distinct.

For a disposable native project copy, never an importer regeneration:

```sh
set -eu
review_dir=$(mktemp -d "${TMPDIR:-/tmp}/eeg-review.XXXXXX")
cp -a hardware/rev_a/kicad/. "$review_dir/"
cp hardware/rev_a/layout/rev_a.kicad_pcb "$review_dir/rev_a.kicad_pcb"
printf 'Open %s/rev_a.kicad_pro\n' "$review_dir"
```

Deliberately transfer reviewed edits back to canonical tracked paths; temporary
copy edits are not committed source. Retain small durable evidence in Git;
expired CI logs can be regenerated, not demanded from an old chat.

## Finish each slice

Publish source/tests/necessary small inputs to a named PR; read back its head,
update this checkpoint and `REV_A_COMPLETION_ROADMAP.md`, and record commands,
actual source SHA and outcome. Distinguish local/hosted, new/inherited and
published/unpublished work. Required checks/review precede merge; preserve
history with a merge commit. Keep WIP discoverable in a PR, not solely a sandbox
or attachment. Report TLDR, then category/remaining-turns/status/next-slice table,
then useful evidence and the specific next task. Test-count growth is not design
progress; analysis checks are not project tests.

## User constraints and unresolved release work

The user is an electronics beginner preferring explained, test-first bounded
slices. Additional spending target is$100, not a delivered quote. Unspecified
owned ESP32/Arduino/electrodes do not confirm selected ADS/S3 purchase or actual
electrode suffix/lead properties. Family bounds are not user measurements.
Keep #45/#48 open: final stackup, capacitor lifecycle/effective-C, mounting,
connector mates/assembly, actual console/rail-loss behavior and delivered budget
still need resolution. Do not recreate the already-published logical pin map;
the remaining interface question concerns actual wiring and operating behavior.

All hardware/purchase/release/body-use flags remain false. BIAS, lead-off and
external acquisition are not enabled by routing. No person/animal connection,
purchasing, fabrication or powered connection is authorized by this checkpoint.
Body use remains a separate later revision and review.
