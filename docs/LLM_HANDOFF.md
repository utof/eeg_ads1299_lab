# Continue from the published P3 branch and its review correction

**P3 is published in PR81**, branch `review/p3-reference-performance`, at
`9d22a6c21eee1bd8983ba61fb4c459870182e734`, tree
`751d8c8f1058f6d5663e215ce908e34bb5e6f46a`. The earlier local d78 candidate has
that identical tree; do not repeat its publication or reconstruct its copper.
Read live main/open PRs before acting: at this correction's start, main remained
P2 `70e8d41bd60d597ecc284859d7e1f71370dcd190`, and PR81 was not merged.

The published head's Quality, Schematic and Firmware workflows passed. Codex
review4174991282 requested clock shortening/separation;4174991286 identified the
stale handoff. A later review summary is not a substitute for resolving these
actual findings. This checkout contains **R1 local review corrections** on
`fix/p3-clock-review`, based on exact published9d22. Until live GitHub confirms a
new head, these corrections are not claimed published, reviewed or merged.
Their source/tests/history must be delivered together, not reduced to a screenshot.

Read root `AGENTS.md`, `DEVELOPMENT.md`, `HARDWARE_BASELINE_REV_A.md`, then
**REV_A_P3_CLOCK_REVIEW.md** and `checkpoints/20261004_p3_clock_review.json`.
Record exact current SHA/tree and dirty state. Preserve unrelated edits. Never
use the parking-grid importer or old authoring scripts to regenerate either board.

## Current routing and bounded next task

Native auxiliary project: `hardware/rev_a/auxiliary/auxiliary.kicad_pro` and its
PCB beside it. R1 changes ONLY MCU_SCLK copper and the resulting ground fill:
71.875101mm planar clock length instead of85.491637mm,4vias instead of5, minimum
same-layer clock/MISO trace-edge gap0.638848mm instead of0.230172mm. The new board
has52footprints/216pads/643segments/157vias. All831 other copper/footprint forms
are byte-identical to publishedP3, including every P2 footprint/bypass form.
Main AFE, schematic/BOM/profile, F1 firmware, C4 service cable, carrier, native
rules, dependency selections and approval gates are unchanged.

These are geometric improvements, not impedance/EMC/noise/timing certification.
The route is not fully direct, still has parallel spans and transitions, and
excludes off-board wire/package/via vertical length from its planar metric.
Do not infer that1MHz repetition determines the edge rate. No arbitrary series
termination or length-matching meanders are selected. The independent reviewer
must review the corrected copper and full-channel limitations.

**Next: publish this corrected descendant into PR81 and obtain exact-head CI and
renewed review.** Do not count the old9d22 green workflows as new-head checks or
merge while the two original findings lack a disposition. Once accepted, review
actual AFE_DVDD feed/return voltage drop with bounded current/copper/contact data,
and the remaining signal/return assumptions. Do not redo P1/P2, J3 or F1.

## Reference proof and its limits

F.Cu/In2.Cu signal routes refer to separate HOST_GND/TARGET_GND regions on In1;
no back-layer signal routing was introduced. The original15P2bypass routes and
full0.20mm reference corridors stay enforced. New global routes use a continuous
central0.10mm geometric strip with same-net through-contact silhouette+0.35mm
exclusions, plus a full-width spatial pending-envelope guard. Neither is an
EM solver or permission for arbitrary unreferenced copper.

`tests/fixtures/auxiliary_p3_pending_edges.json` retains the original20outlines
for18affected segment records, still PENDING_ELECTRICAL_REVIEW_NOT_A_RELEASE.
No new/grown/relocated region is allowed by R1. An initial new clock via enlarged
a STOP_N gap; the actual checker caught it and the new via was moved. Never
widen this fixture just to pass a reroute. Own-via/PTH clearance holes and actual
layer thickness still require return-path review, beyond the tiny residual sum.

The reference fast path remains unchanged: only an EMPTY exact grouped native
difference skips individual work; every nonempty group uses original per-track
checks. The measured2.29x probe improvement is historical P3 evidence, not a
whole-suite or CI runtime promise. Aggregate CAD budget450s and all per-command
limits, required tests and71%branch floor stay unchanged. Record current counts
from exact-head JUnit, not from old chat summaries or this document.

## AFE, service and mechanical state

Main AFE PCB: `hardware/rev_a/layout/rev_a.kicad_pcb`, SHA256
`60097ff4acf8408d5a172930de74bcd36aa50a379dd30a831e4bc64d3841c8a6`.
Its three-sheet project is under `hardware/rev_a/kicad/`. Counts remain
69footprints/251pads/593segments/122vias. Prior AVDD1/output/CH1N and header repairs
are retained with their documented longer-path and performance tradeoffs.

C4 AFE J3 matches auxiliary J104: pins1/5return,2actualDVDDfeedOUT,
3separateDVDDsense,4AVDDsense afterR11,6NC/no contact. Feed and sense meet at the
AFE local rail, not at the auxiliary; neither is Kelvin sense at the ADC die.
No external regulator drives pin2. J1.19 remains CLKSEL; J2NC staysNC.
`service_c4.json` selects twoXHP-6/tenSXH-001T-P0.6 contacts and fiveAWG24 wires,
150+/-5mm between wire faces, insulationOD0.9–1.9mm. Wire/crimp/process and actual
cable assembly are not qualified. Test detached1:1continuity/no shorts BEFORE
assembled checks: intentional rail/return joins can conceal wiring errors.
No hot mating. Source holes are not guaranteed finished holes.

The K2/C4 carrier includes local J3 underside backing without PCB mounting holes.
Cartridges/bridges, body/mate and cable envelopes are finite rigid checks only.
Fit, printer/material tolerances, shims, forces, retention and restraint require
unpowered validation. Auxiliary mounting/cable areas from P1 are preserved;
H4 is intentionally offset, not part of a rectangular hole pattern. No assembly
has been physically qualified. The auxiliary four-sheet circuit has48electrical
instances/212terminals/43BOMrows; four additional PCB mounting footprints.

## Firmware and electrical restrictions

F1 implements SESSION/ARM/READY/ARMED and terminal fault cleanup in the actual
sketch. BOARD_PROFILE_REVIEWED remainsfalse. Parkseven outputs low, obtain stable
READY/freshARM, then start the uninterrupted clock/VCAP/reset sequence. VCAP/clock
qualification cannot precede the controls which start that clock. Faults invalidate
the whole session; restored rails do not rearm. Polling cannot preempt blocked
platform I/O or recall emitted bytes. Host-side recording invalidation and actual
latched hardware feedback remain separate validation requirements.

C1's Adafruit5335/ISO7721DR console has separate HOST/TARGET supplies/returns;
INTERFACE aliases identify the target side only. Off-supply outputs are not
assumed high impedance. Both DevKitUSB connections stay excluded with accessories
attached; permanent-tail service requires removal before bare-board programming.
No fanout/auxiliary board has been built or powered.

The seven42.2k pulls are a conditional C3 migration, not a nominal-resistor proof:
high-state load97.2uA and disabled-low0.576V against0.600V leave only24mV under
stated assumptions. Intermediate-rail IOZ/leakage remains unspecified. Monitor
SENSE injection, initial latchQ, ground/feed breaks, analog-source exposure and
AVDD/DVDD asymmetry remain open. TPS3703's30us delay requires5%overdrive; the
4.47925V conservative test point is already belowE1minimum. No guaranteed
pre-E1/any-ramp shutdown is established. RAILS_OK is not an E1 performance pass.

## Retained prerequisites and reproducibility

E1 remains limited calibrated1–10kohm dummy input,1–40Hz,250SPS/gain24, not
scalp/body qualification. JLC04161H-7628 is a target, not confirmed factory
construction. The six-pair input/supply coupling item,#48capacitor lifecycle/
effective-C/assembly and#45vendor/fixture/mechanical evidence stay open. Fifteen
auxiliary bypasses are separate from33AFEcapacitors. The94.84USD AFE allowance
does not price auxiliary/cables/carrier/tools/delivery or establish100USDcompliance.
No unsolicited supplier message or purchasing/fabrication/powered/body permission.

Use locked uv and the shared `python -m tools.check` entry point. `--schematic`
requires native KiCad9.0.2 and pinned libraries; `--native` requires OpenSCAD2021.01,
ngspice, Node and compiler; `--firmware` uses the pinned Arduino target toolchain.
Missing tools are failures, not passes. Keep full logs under ignored reports;
keep small source evidence/needed reference inputs in Git. R1 includes native
original-route/reversal/subdivision controls, P3terminalcuts and source-snapshot
fault checks. These are not physical experiments or exhaustive fault coverage.

Report TLDR and category/remaining-turns/status/next-step roadmap. Distinguish
local/published/merged, old/new execution, full-native/target/software and physical
results. Preserve source history without squashing or reinterpreting old hashes.
Read live branch state before restoring anything from a previous chat archive.
