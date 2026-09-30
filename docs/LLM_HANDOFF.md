# Continue from this repository

**Current checkpoint: CH1N corridor repair after merged input review PR #65.**
No previous chat or attachment is needed. Read this file and root `AGENTS.md`
first; use live Git/PR state, not a historical success or a missing chat reply.

## Start a fresh session

Fetch current main and open PRs; inspect `git status --short`, `git rev-parse
HEAD` and `git rev-parse HEAD^{tree}` before changing anything. Preserve other
people's uncommitted work. PR #65 is merged as
`779b8efaa0c5e1b84cdbee49a07b053e3debe7b7` (tree
`0a2e5eabd627dbabd26706e046540f44ab9852f6`). The current repair is on
`fix/ch1n-corridor`: read its live PR/head/checks/review while unmerged; after
merge use current main. Do not repeat the already-merged AVDD1 or MISO/DRDY
repairs. Before any merge recheck head/base, actual diff, conflicts, review
findings and exact-head CI.

Read `DEVELOPMENT.md`, `HARDWARE_BASELINE_REV_A.md` and the applicable detailed
review before changes. Canonical board: `hardware/rev_a/layout/rev_a.kicad_pcb`.
Project, three schematic sheets and local libraries: `hardware/rev_a/kicad/`.
Never regenerate the authored board with the parking-grid importer. Its
intentionally unrouted test output is not the completed layout.

## What is published and what remains a hypothesis

The CH1N repair board has 582 segments, 122 vias, 68 footprints and 245 pads,
with one native filled In1 GND region. Its source SHA256 is
`5da65b4307f0336883da9aeae48711b28c1944ec587f5d3174f12db4e9921875`.
These are a dated source identity, not permanent constraints on reviewed repairs.
Only CH1N corridor copper and filled ground change; all footprints and other
nets' copper remain intact. No schematic, BOM, firmware or model changes.

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

Read `REV_A_CH1N_CORRIDOR_REPAIR.md` and its source-bound JSON for the current
repair. Read `REV_A_INPUT_LAYOUT_REVIEW.md` for the unchanged main-path and DNP
branch distinction, conditional sensitivity assumptions and earlier geometry.

CH1N's four B/In2 overlaps (filtered IN2P/IN3P/IN4P DNP branches and CH3N_DUMMY)
are removed. Its In2 corridor now stays right of foreign back copper, with
front entry and original front termination at R2. No footprint moves or DNP
branch removals. All eight main R/C/U1 itineraries remain byte-identical. An
all-front trial would take a substantial header detour; another short candidate
threaded front copper between other channels' resistor pads. The selected
corridor avoids both choices but grows CH1N from 23.479 to 33.884 mm. It still
has two through vias; 18.588 mm is on In2 and is NOT a short local escape. This
is a geometric repair, not length matching or measured-noise improvement.

Test-first3f75b5e recorded the old policy failure with native DRC0/0/0. The new
native full-width guard rejects foreign B overlap, wrong layer and reference
windows; it accepts endpoint reversal, subdivision and an off-route window for
this net. There are seven new cases; the nine-case focused run includes two
existing CH1N cases. Own contact holes are explicitly exempted, not physically
removed. Read final repair-PR execution and independent review before accepting
this source. Baseline main779b8efa ordinary+schematic passed1,091ordinary plus
14subtests,145KiCad and22console subset; that is not the later final-head run.
Fresh GitHub source capture36701686057 identifies that exact baseline.

**After repair review/checks/merge, address the remaining nine upstream
input/supply overlap locations together.** They involve CH3P/CH3N/CH4N against
CH2N/AVDD; the three filtered/unfiltered DNP-branch crossings are gone, and the
residual list is unchanged from the prior review except removal of four CH1N
locations. Choose one bounded combined repair or explicit stackup/bench-test
disposition, then advance finite component/stackup/mechanical/interface choices.
Do not run an unlimited sequence of single-crossing reviews or assume a crossing
is a measured noise failure. Preserve main analog fanout, DNP pads and prior
AVDD1/output repairs. No matching meanders or circuit redesign is implied.

The unchanged main P/N path differences (0.435 mm) and DNP branch differences
(4.5 mm) are not capacitance/noise guarantees. The earlier four native passive
sensitivity cases model illustrative capacitances to ground, NOT cross-channel
mutual coupling or actual board/electrode/silicon parameters. Keep all such
assumptions explicit. Native geometry controls are not physical experiments.

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
