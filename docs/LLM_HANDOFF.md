# Continue from this repository

**Current checkpoint: mechanical envelope M1 and connector process constraint.**
No previous chat or ZIP is required. Read root `AGENTS.md`, this file and live
Git/PR state before changing source. A missing chat report is not evidence that
work was lost.

## Start from the actual published source

Fetch main and open PRs; record actual SHA/tree and `git status --short`.
Preserve other people's uncommitted work. PR #69 is merged as
`8c3440ed6714bfebaac74768a0d371401a22e89e`, tree
`81acc1aa34c29faa7a0305d2247826909a6c2f13`. The mechanical continuation is on
`review/mechanical-envelope`: inspect its live head/checks/review until merged, then
use current main. Recheck head/base, actual diff, conflicts, reviews and
exact-head CI before a merge. Never count queued, inherited or superseded
runs as a pass for a later head.

Canonical authored PCB: `hardware/rev_a/layout/rev_a.kicad_pcb`. Project,
three schematic sheets and local libraries: `hardware/rev_a/kicad/`.
Never regenerate the authored board with the parking-grid importer; its
intentionally unrouted test output is not this board. Read `DEVELOPMENT.md`
and `HARDWARE_BASELINE_REV_A.md` before source changes.

## Current result and next bounded task

Read **`REV_A_MECHANICAL_ENVELOPE.md`** and its
`checkpoints/20260930_mechanical_envelope.json` first. M1 selects a hole-free
external nonconductive edge-carrier concept, independently supported MCU and
strain relief. Current outline is78x58mm, not the78.05x58.05 stroked graphic box.
Four1.5x6mm surface contact allocations and8x28mm header mating allocations
were screened against native outside copper/courtyard bounding boxes. No carrier,
physical force/material/insulation or actual plug fit has been validated; buried
copper remains, so these are not drilling sites. Candidate bulk1.35mm height
fits below existing C6's3.10mm reference maximum, without qualifying a BOM swap.

**Concrete process blocker:** Samtec's TSW catalog says PBT, not lead-free
solderable, lead wave only; the combined family spec's SMT reflow table is not
exact through-hole TSW approval. Exclude the current headers from the assumed
SMT reflow stage and HOLD their later attachment process pending written exact
process confirmation or a separately reviewed high-temperature alternative.
Do not assume lead-free hand soldering or silently substitute HTSW. Both J1/J2
are unkeyed same-form headers carrying incompatible functions; final keying must
prevent reverse/offset/wrong-header mating, not merely label it.

**Next bounded source task:** resolve one connector/process and polarized-mate
route (evaluate high-temperature counterpart, actual mating/strain-relief
assembly, full pin/land/process compatibility). Only then make any synchronized
BOM/schematic/PCB-field/test change and finalize the carrier drawing. M1 is a
measured planning envelope, not a CAD carrier or fabrication release. Preserve
the existing copper and pin map; no arbitrary mounting holes or nine-reroute loop.
Current oriented header locations are now corrected in the harness prose; its
actual electrical mapping remains unchanged. Supplier responses, final fixture
material/tolerances and insertion-force checks are not invented or claimed done.


The board remains SHA256
`5da65b4307f0336883da9aeae48711b28c1944ec587f5d3174f12db4e9921875`:
582 segments,122 vias,68 footprints,245 pads. These are dated identity facts,
not permanent constraints on later reviewed repairs. This continuation changes
only documentation/evidence, not CAD, BOM, production code/model, dependencies,
rules or approval flags.

Read **`REV_A_CAPACITOR_E1_DECISION.md`** and
`checkpoints/20260930_capacitor_e1.json`. The review maps33 fitted capacitors
to their actual networks. Four old bulk instances have discontinued cores;
22 old1-uF/100-nF instances have planned-stop cores; five C0G instances have
in-production cores. Historical source snapshots remain unchanged. Core status
is not exact-orderable stock or a last-buy guarantee.

New qualification identities: **GRM188R61C105KA12D**,1uF/X5R/16V/0603, and
**GRM188R72A104KA35D**,100nF/X7R/100V/0603. The previously identified bulk-L
**GRM21BR61C106KE15L** remains the10-uF target. These are a shortlist, not
substituted BOM parts. The D suffixes come from dated manufacturer-authored
references, not guessing. Manufacturer coreB versus the100-nF retailer NRND
warning remains unresolved. Current approval/assembly data and guaranteed
biased-C minima are not obtained; all three minimum fields remain null.
The1-uF target reduces25V to16V and needs internal VCAP pin-specific review,
not simply an external5-V rail comparison.

The local regulator input/output pairs are2uF nominal each. Output effective
network0.47–200uF/ESR<=0.1ohm is NOT a criterion for every cap. VREF's10-uF
minimum and VCAP's specified100uF/1uF/1uF+0.1uF/1uF connections are separate.
T491 ESR2.2/0.7ohm belongs to reference/VCAP1, not the LDO output. Total nominal
VIN/AVDD/DVDD is12.1/26.2/14.1uF; do not count all four bulk parts onAVDD.
Typical plots and initial-tolerance arithmetic do not qualify real minima,
startup, noise, aging or assembly.

The initial mechanical envelope has now been reviewed separately in M1.
Keep #48's exact lifecycle/approval/biased-C/impedance requests and #45's factory,
connector process and actual fixture questions open. No supplier request or
purchase has been made. Do not rediscover the same capacitor shortlist or treat
M1's centred-body margins as solder/placement/process qualification.

After applicable evidence or an explicitly reviewed limited pilot-part risk
disposition exists, use ONE synchronized BOM/schematic/PCB-field/test migration.
Trace all26 affected instances; internal VCAP roles may differ from rail roles.
Do not change only BOM strings, transfer D to the bulk-L target, rewrite old
snapshot tests or quietly mark missing minima qualified. A first board cannot
supply premanufacture measurements; pilot release review and later physical
validation are distinct. Neither is authorized by this checkpoint. #48 stays
OPEN rather than being closed by a new shortlist.

## Preserve E1, previous repairs and their limits

`REV_A_STACKUP_BENCH_REQUIREMENTS.md` selects JLCPCB JLC04161H-7628 as the
DESIGN TARGET, not a confirmed fabrication stack:1.6mm,1oz outer/0.5oz inner,
nominal0.2104mm outer gaps/core1.065mm, F/In1GND/routedIn2/B. NP-155F is a
material target, not confirmed availability. Public35/40.64um copper and
4.6/4.43coreDk discrepancies, per-layer tolerances and via DFM remain open.
Prepared factory questions were not sent. Overall +/-10% thickness is not a
per-gap bound; proposed analysis intervals are not supplier worst-case limits.

E1 is a limited calibrated dummy-source design target, NOT measured electrodes
or scalp qualification:1–10kohm per leg,0.1%matching; fixture<=100pF/leg,
<=1pF mismatch to be measured. Existing250SPS/gain24,1–40Hz;10uV–10mVpeakAC,
<=50mVDC differential and<=60mVtotal; instantaneousCM2.40–2.60V andAVDD4.75–5.25V
including ripple. Noise<=0.50uVrms; coherent aggregate<=0.50uVpeak, with the
published class allocations and uncertainty. ClassU95<=0.03uVpeak andnoiseU95
<=0.05uVrms are not demonstrated fixture capabilities.100k/asymmetric cases
are reported stress outsideE1; never relabel failed core cases as stress.
Use actual sample rate and the explicit alias-sensitive spots. No inverse
filtering/notching or assumed phase cancellation may turn a failure into a pass.
No external dummy acquisition, BIAS, lead-off or SRB mode was enabled.

The nine residual upstream B/In2 locations remain one OPEN six-pair coupling
item for confirmed construction and separate combined-repair/pilot-risk review.
The prior hypothetical mutual-C example is not extracted PCB capacitance or
actual E1 loading. Do not start another unlimited simulator or nine automatic
reroutes. The AVDD1, MISO/DRDY and CH1N repairs are already merged. Keep longer
VCAP3/C24 and AVDD56/C14 paths,44.132mm DRDY and33.884mm CH1N, actual edges,
barrels/cables and the4.5mm DNP-branch imbalance explicit. Existing targeted
native geometry guards remain active. Read the detailed repair reports rather
than rerunning authoring helpers over current source.

The original reconstructed07edcacc history remains reachable. The separate
chat-local1689234 and issue45's76502e7 variants are different unmerged sources;
do not overlay them onto current main.

## Reproduce and verify

```sh
uv sync --locked --all-extras
uv run --locked --all-extras python -m tools.check
uv run --locked --all-extras python -m tools.check --native --schematic
uv run --locked --all-extras python -m tools.check --firmware
```

Install declared native tools first. `uv.lock` is authoritative; KiCad9.0.2
engine/libraries are pinned in `.github/workflows/schematic.yml`. Arduino setup
is in `firmware/toolchain.json` and its workflow. Executable CI setup is not
proof of tools in a sandbox. Missing tools/network/cache are blockers, not
skipped passes. Avoid concurrent environment resync. Native CAD, host helpers,
actual target compilation and physical tests are different scopes.

Source capture36732187218 restored exact905347 from GitHub. The local baseline
ordinary gate passed1091tests+14subtests and86.06%branches with71%floor unchanged;
it did not run local native CAD or S3 compilation. Read the capacitor PR's live
final-head results and review. The executable accounting/corrupt-data controls
are analysis checks, not new project tests. Transient artifacts may expire;
the dated facts, candidate identities and reproduction code are committed.

A disposable native inspection copy, never importer regeneration:

```sh
set -eu
review_dir=$(mktemp -d "${TMPDIR:-/tmp}/eeg-review.XXXXXX")
cp -a hardware/rev_a/kicad/. "$review_dir/"
cp hardware/rev_a/layout/rev_a.kicad_pcb "$review_dir/rev_a.kicad_pcb"
printf 'Open %s/rev_a.kicad_pro\n' "$review_dir"
```

Transfer reviewed edits back to canonical tracked paths deliberately; changes
in a disposable copy are not committed source.

## Finish each slice and respect scope

Publish source/tests/necessary small inputs to a named PR, read back the head,
update this checkpoint and `REV_A_COMPLETION_ROADMAP.md`, and record commands,
actual source SHA and outcomes. Distinguish local/hosted, new/inherited and
published/unpublished work. Required review/checks precede merge; preserve
history with a merge commit. Keep WIP in an open PR, not solely a sandbox/chat.
Report TLDR, then category/remaining-turns/status/next-slice table, useful
verification and the specific next bounded step. Test-count growth is not
engineering progress; an analysis probe is not another project test.

The user is an electronics beginner who prefers explained, test-first bounded
slices. The extra-parts target is$100, not a delivered or instrumentation quote.
Owned unspecified ESP32/Arduino/electrodes do not establish ADS/S3 purchase,
board revision, electrode suffix or measured lead properties. Keep #45/#48 open
for remaining supplier/stackup, component, mechanical/mating/assembly, actual
console/rail-loss and delivered-budget decisions. The logical pin map exists;
the remaining interface work is actual wiring/operating behavior, not another
pin list. All purchasing, fabrication, powered-connection and body-use gates
remain unchanged/false. Body use is a separate later revision and review.
