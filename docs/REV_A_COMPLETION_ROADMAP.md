# Finish the person-disconnected Rev A prototype design

**Current checkpoint: K2 initial dimensioned carrier/cartridge CAD.**
Editable solid models and native collision/mesh tests now exist. The base uses
no new PCB holes; raised bridges are removable for board installation, the
side-exiting cable has a window, and capture/cable-restraint parts are modeled.
This is an unapproved fit prototype, not a qualified interlock or finished
manufacturing process. Physical fit/force/continuity and material/fastener/
termination evidence remain open. K1 header migration is not repeated.

## Glanceable roadmap

Ranges are estimated remaining substantial chat turns, excluding supplier,
manufacturing, shipping and physical measurement time. Categories overlap;
these are neither promises nor a safety/readiness score.

| Category | Estimated remaining turns | Done / current status | Next slice or blocker |
|---|---:|---|---|
| Source continuity and core software | 0 for baseline; maintain | Published source, handoff and pinned checks | Keep actual source/review/test heads aligned |
| Initial routing and scoped repairs | 0 for completed scope | AVDD1, MISO/DRDY, CH1N and HTSW identity changes retained | Preserve physical-performance limitations |
| Residual input/supply coupling | 1 combined decision after confirmations | Nine locations remain one six-pair item | Confirmed stack/E1 evidence, then combined repair or separate pilot risk |
| Stackup and E1 definition | 0 for targets; 1–2 plus external evidence to close | Named construction and numerical targets | Factory drawing and calibrated fixture/uncertainty capability |
| Capacitor decision/migration | 1 coordinated review after evidence | Exact shortlist and33-node accounting, not substitutions | #48 lifecycle/assembly/biased-C/impedance evidence |
| Mechanical carrier and coded cartridges | 0 for initial CAD; 1–2 plus physical fit/process review | Executable K2 solids and scoped native collision tests | Actual dimensions, captive assembly, retention/tilt/force, controller support and cable route |
| Controller termination and power-off interface | 1–3 plus physical checks | Logical map exists; actual wiring/rail-loss behavior unqualified | **Next: one exact cable-end/console architecture and startup/back-power restrictions** |
| Fabrication outputs and delivered budget | 1–2 after blockers close | No release/purchase approval | Separate release review, consistent files and delivered quote |
| Person-disconnected bench validation | 2–4 guided turns plus bench work | Not started | Unpowered inspection, then staged dummy-source tests after prerequisites |

Read `REV_A_CARRIER_K2.md` before interpreting the CAD. K2 replaces the closed
K1 receiver rectangle with a slotted 3D guide and independently checks it;
do not recycle the912-pose K1 rectangle count as a K2 mechanical proof. The
modeled16 tilt cases are finite rigid probes, not continuous trajectory or
material tolerance qualification. Bridges must be removed for PCB installation;
release cable bars before withdrawal. Controller and free-end cable termination
remain independently supported/insulated requirements, not depicted hardware.

Next source work is the actual controller-side termination and powered-off
console/interface plan, using the existing pin map rather than making another
pin list. Carry concrete K2 fit/process questions on#45 while advancing this
finite task. The prior capacitor and stackup/E1 limitations remain unchanged.

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
