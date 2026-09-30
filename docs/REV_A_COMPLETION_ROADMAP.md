# Finish the person-disconnected Rev A prototype design

**Current checkpoint: mechanical planning envelope M1 reviewed.**
Selected a hole-free edge-carrier concept and quantified support/mating spaces,
without moving copper or adopting capacitor substitutes. The current TSW header
has a concrete solder-process restriction; an unkeyed plug is not a polarized
harness. Next is one coordinated connector/process/mate decision, then final
carrier details. M1 is not an approved fixture or manufacturing release.

## Glanceable roadmap

Estimates are **remaining substantial chat turns**, not elapsed time, commits,
guarantees or a safety score. Related tasks overlap and new findings can add
work. Manufacturing/shipping and physical measurements are excluded. Do not
sum the rows into a promised completion date. Refresh this table with each
meaningful slice and show it after the user-facing report's TLDR.

| Category | Estimated remaining turns | Done / current status | Next slice or blocker |
|---|---:|---|---|
| Source, core software/firmware and checks | 0 for baseline; maintain | Published source, pinned checks and target build; repo-only continuation | Keep source, review and actual test heads aligned |
| PCB connectivity and scoped repairs | 0 for completed routing | Fully connected; AVDD1, digital-output and CH1N repairs merged | Preserve copper except reviewed changes; physical performance not qualified |
| Residual input/supply coupling | 1 combined decision after confirmations | Nine locations remain one six-pair item | Confirmed construction plus E1 for combined rework or separate pilot-risk decision |
| Stackup and bench-input envelope | 0 for target definition; 1–2 plus external evidence to close | Named JLC04161H-7628 and numerical E1 selected | Factory drawing/tolerances/material and calibrated fixture/floor still unconfirmed |
| Capacitor decision/migration | 1 synchronized review after applicable evidence | Shortlist and33-instance node accounting complete; no BOM migration | #48 exact lifecycle/approval, biased-C/impedance and internal VCAP conditions or explicit limited pilot-risk disposition |
| Mechanics and assembly | 1–2 plus process/fixture evidence | M1 dimensions, candidate-height and contact/mating screens complete; carrier concept selected | NEXT: TSW process/high-temperature alternative and polarized actual mate; then carrier drawing/force/tolerance review |
| Real power/console fault readiness | 1–3 plus physical checks | Firmware/console contracts exist; actual rail-loss behavior unqualified | Exact interface and powered-off paths; staged dummy-bench checks |
| Release package and delivered budget | 1–2 after blockers close | Not fabrication/purchase-ready | Independent release review, consistent outputs and delivered quote |
| Person-disconnected bench verification | 2–4 guided turns plus bench work | Physical prototype validation not started | Unpowered inspection, then staged dummy-source tests after prerequisites |

**Next: connector/process and polarized-mate decision.** Read
`REV_A_MECHANICAL_ENVELOPE.md`: the existing TSW-110-07-T-D is not automatically
compatible with lead-free SMT reflow. Confirm an exact approved attachment
process or qualify a high-temperature counterpart before a synchronized BOM/
schematic/PCB-field/test change. Select an actual mate with strain relief and
reverse/offset/wrong-header prevention; the SSW example is a geometric PCB-tail
socket reference, not a released cable. M1's8x28mm allocations exclude cable,
finger/tool and adapter volumes. Its four1.5x6mm edge strips have surface copper
clearance, not permission to drill through buried copper. Material, retention,
board strain, finished dimensions and fit need the carrier drawing and checks.
Keep supplier and capacitor approval requests open rather than restating them
as completed. No procurement or fabrication permission changed.

`REV_A_CAPACITOR_E1_DECISION.md` records the three qualification targets:
GRM21BR61C106KE15L, GRM188R61C105KA12D and GRM188R72A104KA35D. Exact D/L identities
are documented; no full approval or production land/process guarantee follows.
Four legacy bulk instances have discontinued cores and22 small decouplers
planned-stop cores. C0G/T491 choices are retained, not newly lifecycle-certified.
The100-nF retailer NRND/coreB discrepancy is open. Typical plots do not provide
joint guaranteed minima; LDO, reference andVCAP requirements are different.
After applicable evidence or a separately reviewed limited pilot-part risk
exists, use one coordinated BOM/schematic/PCB-field/test update. Internal VCAP
roles may need a different decision from rail decouplers. No part was purchased
and no supplier request was sent in this source review.

## Preserve fixed targets and outstanding uncertainty

Read `REV_A_STACKUP_BENCH_REQUIREMENTS.md`: JLC04161H-7628 is a selected DESIGN
target, not a factory-confirmed build. Public nominal0.2104mm outer gaps and
1.065mm core are not tolerance bounds. Material availability, public copper/Dk
discrepancies and per-layer/process values need a dated drawing. Overall board
thickness tolerance is not a tolerance for each gap. Questions are prepared,
not sent or answered; no confirmed stack is encoded in manufacturing data.

E1 is a low-impedance calibrated dummy-source design requirement, not scalp
qualification or already measured performance:1–10kohm per leg, controlled
fixture matching,1–40Hz,250SPS/gain24,<=0.50uVrms noise and<=0.50uVpeak coherent
aggregate with explicit allocations/uncertainty. High-Z/asymmetric conditions
are separately reported stress. Actual fixture and0.03uVpeak/0.05uVrms uncertainty
floors remain unproven. Missing equipment or floor-limited data is inconclusive,
not a pass. The extra-parts objective of$100 is not an instrumentation budget
or delivered quote. No external acquisition mode was enabled.

The six-pair group in `REV_A_UPSTREAM_COUPLING_DISPOSITION.md` stays OPEN. Its
illustrative mutual-C example does not extract actual capacitance or prove E1.
The4.5mm DNP-branch imbalance and existing supply/output tradeoffs remain explicit.
Keep the capacitor/internal-pin evidence distinct from that upstream model.
Choose a combined routing change or separately reviewed pilot risk when the
relevant inputs exist; meanwhile advance finite mechanical/interface work.

A first pilot may be reviewed for manufacture before a physical board exists;
validated performance requires later measurements. Do not create a circular
requirement to measure an unbuilt board or quietly turn a planned experiment
into fabrication permission. Body use is a separate, unestimated revision.

## Three different finish lines

**Design-support simulation complete** means relevant selected-circuit cases
run under stated assumptions, with unknowns and failures explicit. It does
not require a transistor-level ADS1299 model or invented electrode/PCB values.
BIAS studies remain bounded hypotheses; external acquisition and body use stay
disabled. The optional TPS7A20 reference-engine discrepancy requires a finite
disposition or justified deferral, not unlimited simulator work on the PCB path.

**Ready-to-fabricate bench design** requires final native schematic/routing,
outline/stackup/mates, consistent qualified-or-explicit-pilot-risk BOM, reviewed
polarity/placement, clean complete ERC/DRC/parity, and a consistent Gerber/drill/
assembly/placement package. It needs a wiring worksheet, separate programming
and acquisition power arrangements, no-person bring-up procedure and delivered
quote. Exported files or an empty parity array are not sufficient.

**Working hardware validated** additionally requires actual assembly/inspection
and person-disconnected measurements. Firmware compilation and simulations do
not supply real rail-loss, noise, fixture or interface evidence. Body connection
requires its own later revision/review, not a fixed number of turns.

## Avoid repeated or unbounded work

The passive-input and bounded BIAS/supply studies, guarded S3 firmware,
three-sheet schematic, all-pad/BOM/cache and footprint checks, logical UART/
header worksheet, T491 land choice, routing and AVDD1/output/CH1N repairs are
already implemented. Do not recreate them. Historical detailed results remain
in Git and their specific reports. Temporary source-transfer/tool iterations
are delivery friction, not additional engineering milestones or dependencies.

`REV_A_BENCH_HARNESS.md` already maps GPIO to actual DevKit/AFE pads. Remaining
work is cable/interface/orientation and operating behavior, not another pin
list. Both boards use J1; keep AFE/DEVKIT prefixes. UART17/18 is routing, not
isolation. Simultaneous normal DevKit USB/header supply or an unknown live
adapter remains unauthorized. Selected parts are not proof of purchase;
actual owned board revision, lead information and delivered quote remain needed.

Reference entry points: `AGENTS.md`, `LLM_HANDOFF.md`,
`REV_A_MECHANICAL_ENVELOPE.md`, `REV_A_CAPACITOR_E1_DECISION.md`,
`REV_A_STACKUP_BENCH_REQUIREMENTS.md`,
`REV_A_UPSTREAM_COUPLING_DISPOSITION.md`, `REV_A_CH1N_CORRIDOR_REPAIR.md`,
`REV_A_INPUT_LAYOUT_REVIEW.md`, `REV_A_DIGITAL_OUTPUT_REPAIR.md`,
`REV_A_AVDD1_REPAIR.md`, `REV_A_SCHEMATIC.md`, `REV_A_BENCH_HARNESS.md`,
`REV_A_FOOTPRINT_REVIEW.md`, `REV_A_TANTALUM_LANDS.md`,
`REV_A_CAPACITOR_EVIDENCE.md`, `REV_A_BULK_CAPACITOR_ASSESSMENT.md`,
`REV_A_SUPPLY_TIMING.md`, and open #45/#48. All purchasing, release,
physical-validation, powered-connection and body-use gates remain unchanged.
