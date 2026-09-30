# Finish the person-disconnected Rev A prototype design

**Current checkpoint: K1 header selection is migrated; coded harness/carrier
geometry is defined but not physically qualified.** Both board headers are
HTSW-110-07-T-D; exact selective-solder process and hole/fit DFM stay open.
The IDSD cable configuration is an external design target, not a keyed or
approved standalone cable. Next is dimensioned carrier/cartridge CAD including
actual socket capture, engagement and strain relief, not another header search.

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
| Mechanics, connectors and assembly | 1–2 plus process/fit evidence | HTSW source migration and differently coded IDSD-cartridge concept complete; no carrier qualified | Next: dimensioned carrier/socket capture, raised receiver and strain relief; then actual interface review |
| Real power/console fault readiness | 1–3 plus physical checks | Firmware/console contracts exist; actual rail-loss behavior unqualified | Exact interface and powered-off paths; staged dummy-bench checks |
| Release package and delivered budget | 1–2 after blockers close | Not fabrication/purchase-ready | Independent release review, consistent outputs and delivered quote |
| Person-disconnected bench verification | 2–4 guided turns plus bench work | Physical prototype validation not started | Unpowered inspection, then staged dummy-source tests after prerequisites |

**Next: dimensioned keyed carrier/cartridge CAD.** Use `REV_A_CONNECTOR_K1.md`
and its source-bound record, including the raised receiver projection at C33,
0.0508mm lower zero-gap insertion margin, complete twenty-position pin map and
independent carrier/cable support. The exact 2D pose screen is not a completed
three-dimensional interlock or material/tolerance/force validation. Do not add
arbitrary PCB holes or repeat the completed BOM/schematic/PCB field migration.

K1 selects selective lead-free through-hole attachment after SMT; assembler
acceptance of the job-specific profile and unchanged1.00mm hole DFM remain pending.
All cable terminations, guide integrity, wrong/tilted approach and strain-relief
checks must precede a later allowed powered test. The bare cable remains unkeyed.
The planning subtotal is$94.34, not a delivered total; the historical$3 harness
reserve is unvalidated for the selected cable/carrier. Obtain a full quote
rather than silently claiming the$100 target is met.

Capacitor#48 remains open for exact lifecycle/approval/biased-C andassembly data.
The E1 low-impedance dummy targets and named unconfirmed JLC04161H-7628 stack
are unchanged. The residual six-pair coupling group remains open for confirmed
construction and separate combined-repair/pilot-risk review. Advance finite
mechanical/interface tasks while factory/fixture evidence is pending; never
invent confirmations or require measurements from a board before it exists.
Body use is a separate later revision, not unlocked by source or geometry tests.

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
