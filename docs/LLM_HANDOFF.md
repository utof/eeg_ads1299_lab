# Continue from this repository

**Current checkpoint: selected stackup design target and numerical E1 bench envelope.**
No prior chat/ZIP is needed. Read root `AGENTS.md`, this checkpoint and live Git/PR
state before choosing the next bounded task. A missing chat reply is not proof
that source work was lost.

## Start here

Fetch main/open PRs; record actual SHA/tree and `git status --short`. Preserve
other people's uncommitted work. PR #67 is merged as
`8403c4eefc6fd6f1303a75510755f16f983e71c4`, tree
`4f5bebbc578c15f63c3463f2b3cef0bd28fbdfa9`. The requirements continuation is on
`docs/stackup-bench-envelope`: inspect its live PR head/checks/review until
merged, then use current main. Recheck head/base, diff, conflicts, reviews and
actual exact-head CI before merging. Do not repeat the completed AVDD1,
MISO/DRDY or CH1N copper repairs. A queued check or an old result is not a pass.

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

Read **`REV_A_STACKUP_BENCH_REQUIREMENTS.md`** and
`checkpoints/20260930_stackup_bench_envelope.json` before further requirements or
coupling decisions. They select **JLCPCB JLC04161H-7628** as the design target:
1.6mm, 1oz outer/0.5oz inner, nominal pressed outer gaps0.2104mm/core1.065mm;
retain F / In1 GND / In2 routed / B. Nan Ya NP-155F is the material target from
the vendor calculator guide, not a confirmed order/lot. Public 35um/40.64um
outer-copper and4.6/4.43 core-Dk differences are explicitly recorded.
**Factory drawing, material availability and per-layer tolerances remain
unconfirmed.** Overall +/-10% board thickness is NOT a per-gap guarantee. A
prepared vendor request is in the document; it was not sent. Do not write this
unconfirmed target into fabrication outputs or call it released. Proposed
0.17-0.25mm/Dk4.0-4.8 sensitivity intervals are not vendor bounds.

**E1 is a new limited dummy-bench design target, not the user's measured
electrodes or a general EEG qualification.** Core source1-10kohm per leg,
0.1%P/N matching; fixture<=100pF/leg and<=1pF mismatch, to be measured. Actual
AFE load remains unchanged/unknown beyond datasheet characteristics. Core
1-40Hz,250SPS,gain24;10uV-10mVpeakAC with<=50mVDC differential offset and
<=60mVtotal; instantaneousCM2.40-2.60V;AVDD4.75-5.25V including ripple.
Total noise<=0.50uVrms; coherent aggregate<=0.50uVpeak at each victim/frequency.
Input-channel total allocation0.20uVpeak for up tothree10mVpeak aggressors;
AVDD1mVpeak, common10mVpeak anddigitalactivity each allocate0.10uVpeak.
Use uncertainty-inclusive bounds with no cancellation; coherent class U95
<=0.03uVpeak andnoiseU95<=0.05uVrms. No inverse-filter correction of noise/error;
10Hz-normalized transfer-shape check is separate. See the document for the
exact matrix, sampling/PSD andalias-sensitive spot tests: fMOD=fCLK/2=1.024MHz,
4096*actual sample rate, not an assumed zero at a nominal sinc notch.
100k/100k and1k/100k are separately reported stress cases outside E1. Do not
relabel an E1failure as stress. None of the fixture/source/instrument floor,
real spectra, power-up orphysical performance has been validated.

The nine residual upstream B/In2 locations remain ONE OPEN six-pair coupling
item. E1 provides numbers for the next pilot-risk/rework decision, not acceptance
of the existing copper. The restricted mutual-C example was repeated at1k/10k/
100k, with six unique native cases/seven executions and a separate723-point
four-node KCL check. It does not extract capacitance, include actual silicon/
aliases/PSRR, or guarantee E1. Updated reproduction blocks and results are in
the requirements document/JSON. Analysis cases are not added project tests.

**Next independently actionable source slice: #48 capacitor lifecycle and
effective-capacitance closure.** Resolve the actual shortlisted values/MPNs,
voltage/temperature derating and assembly constraints against this fixed E1
scope. Do not restart an unlimited simulation or nine independent reroutes.
In parallel, #45 needs the named factory drawing and a separately reviewed,
calibrated dummy fixture/measurement-chain plan. Continue finite component,
mechanical andinterface work while awaiting those facts; never mark missing
supplier values confirmed. Once confirmed geometry and fixture feasibility are
known, choose a combined upstream reroute or a separate bounded pilot-risk
review. No pilot fabrication orpoweredtest authorization is granted here.

Local source capture36720518554 checked exactmain8403 andits tree/board. The
baseline ordinary gate passed1091tests+14subtests and86.06%branches; it did NOT
run localnative/KiCad/S3. Read the requirements PR's actual final-head checks
for newer evidence. Tools/caches and earlier passes are not proof of execution.

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
Read this requirements PR's actual final-head checks/review, not just an older
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
