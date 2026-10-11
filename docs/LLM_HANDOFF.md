# Continue PR98: S1-S4 reconciled; K2 and independent acceptance remain

Read root `AGENTS.md`, `REPOSITORY_PUBLICATION.md`, `DEVELOPMENT.md` and
`REV_A_BENCH_FIRST.md`. Read live main/PR98 heads and the original review threads.
**The five SPI sites and reference repair are already applied. Never reapply the
archived candidate or recreate completed geometry and fault tests.**

Use the [hosted capability preflight](REPOSITORY_PUBLICATION.md#hosted-capability-preflight)
before suggesting local downloads/setup. Connected GitHub source publication and
separate read-only hosted KiCad/CI work. Missing local Git/gh/KiCad/pcbnew/DNS is
not a global blocker. Respect actual explicit denials; the old runtime-packaging
operation is separate and has not been retried or bypassed.

## Published engineering and provenance

Main was checked at `c2f93ee30eb47f80a7702603f20ed22e6cce86af`. Continue draft PR98,
`work/l5-spi-series`; nothing in this slice authorizes a merge or physical work.
The hardware is still the reference-repaired `3519b21e335584244771c73c5c87b70d66037a7e`
geometry. No PCB, schematic, active BOM/contract, firmware, dependency, product
workflow, Q1 or release flag changed during the supply reconciliation.

Six real commits were imported through `bcff4880d035aa0b91e17b51c9f43a5727b15aa8`,
tree `f15982a95988de6c4ef73861662fbcc6200e0361`. They descend from actual075ffd6c;
no synthetic materialization ancestry or recreated input-commit metadata was
published. The source-linked S2/S3 checkpoints must remain available in history:
S1 input6e4a207e/tree0c89cb59 and S2 input7bc15dcb/treeb0886ef1. Later formatting
and current-handoff commits are not new hardware revisions.

## S1: new native extraction, not a blind hash replacement

Read-only pinned KiCad9.0.2 run38112788509 first reproduced the old recorded-source
failure, then reran the unchanged native path algorithm against current source.
All selected17 paths, grouped resistance-square terms, via/PTH counts, numerical
assumptions and qualification=false were identical to the historical S1 record.
Only source commit/tree and the two PCB identities changed. All5 existing S1
checks passed afterward, including both deliberately altered-board rejections.
The record now binds to actual hardware3519b21e/tree9475d027. This is a native
SUPPLY-path preservation result, not unchanged SPI wiring or an impedance bound.
Historical S1 source remains in Git; earlier checkpoints were not overwritten.

## S2-S4: actual open positions versus conditional examples

All five R117-R120/R24 positions are OPEN_DNP / NOT_SELECTED; resistance is null
and acquisition_possible=false. S2 checks both frozen native XML graphs and all
five exact driver/downstream partitions before calculating. R114 remains on the
R120 receiver side and logical MOD1.GPIO13 stays downstream of R24 with J1.5.
No resistor value, including zero ohms, is selected by a calculation.

S2 reports zero IDEAL DC through each absent series component, explicitly not
zero leakage/displacement/protection/current elsewhere or an isolation barrier.
Actual total operating-current maximum stays null. Its prior quiet/acquisition
numbers are retained only as conditional receiver-voltage/completed-transition
examples AFTER separately reviewed population. Series loss, settling and real
receiver voltage are not inferred; the original seven-pull/count/KCL arithmetic
and all eight unknown bounds are unchanged.

S3 binds the reconciled S1/S2 inputs and explicitly reports OPEN_DNP and no
as-authored acquisition. All21 default voltage bounds remain null; the original
eight signed voltage-window recipes and physical_qualification=false remain.
New malformed-population/approval controls remain effective under optimized
Python as well. S4 binds the reconciled S2/S3 records and requires separate SPI
population review as well as the existing firmware and commissioning reviews.
Its vendor applicability conditions, numerical regulator example, unknown loads,
empty measurements and distributed firmware=false configuration are unchanged.

## Verification identities and limits

Read `checkpoints/20261011_l5_supply_reconciliation.json` for exact native capture,
source publication, formatter and final hosted gate identities/results. Local
installed-pytest authoring checks passed64 S2-S4 cases before final formatting;
this is not a local locked gate. The first published bcff4880 hosted gate stopped
at formatting of two executable Markdown blocks. Do not reuse that failed result
as a pass or recreate already-correct examples; formatting preserved their ASTs.
The only dependent S4 formatter adjustment is the corresponding S3 document hash.

The source-only publisher verifies immutable bytes, full tree and exact changed
paths, publishes a temporary non-main branch, and independently clones it. Native
execution is separate, contents:read and no persisted credentials. Workbench jobs
are outside this engineering tree. The real six-commit source bundle, all12 blobs
and independent tree composition were checked before the leased PR ref update.
The ordinary/native/firmware gates still use the one existing tools.check runner.

## Next bounded engineering task

Review K2's strict AFE whole-board binding and actual R24 placement/access before
changing its expected identity. Its current test still names the pre-L5 board.
R24 is at(57.0,29.4); the old component placements, outline, mating interfaces and
carrier SCAD are unchanged, but that alone is not populated solder/tool-access
proof. Use the existing carrier/service CAD and native OpenSCAD checks; retain
all wrong-port, tilted-insertion, cable, support and altered-board controls.
Do not blindly replace a hash or imply that an unspecified fitted part has a
qualified height or safe rework clearance. Separate nominal DNP/allocated-envelope
compatibility from actual fitting and workmanship acceptance.

Independent exact-source review remains required. The last requested Codex
review returned usage-limit exhaustion (comment6103095217); no review of the new
supply slice is claimed. Retain the original threads and findings; do not infer
approval from an older review, another account, a green subset or successful
source transport. Keep PR98 draft until complete gates and review are accepted.

## Retained boundaries

Keep the450s complete native CAD budget,71% branch floor, all39 prior terminal
cuts,15 SPI faults,15 bypass corridors and reference/domain/mounting requirements.
The C104/P3 repair and surviving reverse/split/reference-void targets already pass;
use the historical20261011 reference/native checkpoints instead of repeating it.
MISO and MISO_DRV retain the original combined whole-channel reference budgets.

L1-L4/B1-B3 and#45/#48 remain. The proposed first pilot is INTERNAL-TEST-ONLY with
six upstream analog pairs retained; E1 external-input acceptance and possible
additional PCB revision cost remain separate. Internal mux modes are not electrical
isolation. MCU launch stages and other controls remain a separate decision.
B1 uses J2; B2's run card and B3 contacts/insulation/restraint/earth/uncertainty checks
remain. Keep R -> fresh F1 arm -> wake/clock ->150ms -> VCAP1>1.1V -> reset, not
raised VCAP1 while parked in PWDN. BOARD_PROFILE_REVIEWED staysfalse; both DevKit
USB ports stay excluded. STOP is not a power disconnect.

Moscow remains a planning assumption and Q1 the sole frozen unsent packet. No
prices/outreach, purchases, fabrication, physical construction/rework/mating,
powering, external-input acquisition or person/animal connection is authorized.
