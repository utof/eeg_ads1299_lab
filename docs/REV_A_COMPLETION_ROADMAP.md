# Finish the person-disconnected Rev A prototype design

**Current checkpoint: scoped CH1N corridor repair after merged PR #65.**
The MISO/DRDY repair is already merged. The current `fix/ch1n-corridor` PR removes
four CH1N unshielded projected overlaps without moving footprints or other nets,
but lengthens that source route. Read its live review/check/merge status. Main
R/C/U1 paths and DNP branches remain intact; no measured noise or fabrication
approval is implied. Nine other upstream input/supply locations remain for one
bounded combined disposition, not nine automatically required chat turns.

## Glanceable roadmap

Estimates are **remaining substantial chat turns**, not elapsed time, commit
counts, guarantees or a safety score. Related tasks overlap; new findings can
add work. Manufacturing/shipping and physical measurement time are excluded.
Do not sum overlapping categories into a promised completion date. Refresh
this table after each meaningful slice and show it after the report's TLDR.

| Category | Estimated remaining turns | Done / current status | Next slice or blocker |
|---|---:|---|---|
| Source, core software/firmware and checks | 0 for baseline; maintain | Published source, pinned checks and target build; repo-only continuation | Keep source, review and actual test heads aligned |
| PCB connectivity draft | 0 for initial routing | Fully connected; native parity/DRC clean; not fabrication approval | Preserve completed copper except reviewed repairs |
| Supply/bypass review and repair | 0 for scoped AVDD1 repair | Reviewed and merged in PR #62 | Retain VCAP3/AVDD56 tradeoffs in whole-board review |
| Digital-return review and output repair | 0 for scoped output repair | PR #64 merged; no MISO/DRDY B tracks; native controls and review completed | Retain longer DRDY, spacing, stackup/edge/cable limits |
| Input-path geometry/coupling | 1–2 for residual disposition; current PR acceptance first | Main paths reviewed; CH1N repair implemented with native controls; four overlaps removed, nine remain | Address remaining upstream/supply locations together; decide combined repair or explicit stackup/bench disposition |
| Components, stackup, mechanics and assembly | 2–4 | Primary part evidence, logical harness and selected lands exist; decisions open | #48 capacitor lifecycle/effective-C; #45 stackup, mounting, mates and process |
| Real power/console fault readiness | 1–3 plus physical checks | Firmware/console contracts exist; actual rail-loss behavior unqualified | Resolve exact interface and powered-off paths; define dummy-bench checks |
| Release package and delivered budget | 1–2 after blockers close | Not ready for fabrication or purchase | Independent release review, coherent outputs and delivered quote |
| Person-disconnected bench verification | 2–4 guided turns plus bench work | Physical prototype validation not started | Unpowered inspection, then staged dummy-source tests after prerequisites |

**Next after CH1N repair acceptance: one combined disposition for the remaining
nine upstream input/supply overlap locations.** Read `REV_A_CH1N_CORRIDOR_REPAIR.md`
and its JSON: three CH2N/input and six AVDD/input positions remain; no filtered
INn DNP branch remains in that list. A crossing is not a measured failure. Choose
a bounded combined repair or an explicit stackup/bench-test disposition, retaining
the cost/geometry tradeoffs rather than iterating indefinitely. Then proceed to
finite stackup/component/interface/mechanical decisions. The 4.5-mm DNP branch
imbalance and real parasitics remain characterization items, not instructions
to add arbitrary meanders. Body use is a separate, unestimated revision.

## Three different finish lines

**Design-support simulation complete** means the selected circuit's relevant
passive-input and supply cases run under a stated design envelope, with unknowns,
failures and deferrals explicit. It does not require transistor-level ADS1299
modeling or pretending illustrative electrode/PCB parameters were measured.
Existing BIAS studies remain bounded hypotheses. Rev A keeps external
acquisition/BIAS and body use disabled; physiological realism is not a
prerequisite for every dummy-bench layout operation. The optional TPS7A20
reference-engine discrepancy needs a finite disposition or bounded deferral
with design consequence, not unlimited simulator work on the PCB critical path.

**Ready-to-fabricate bench design** requires native schematic and routed PCB,
final outline/stackup and mating choices, consistent BOM, reviewed polarity/
placement, clean ERC and complete DRC/parity, plus a reviewed Gerber/drill/
assembly/placement package. It also requires a board-qualified wiring worksheet,
separate programming/acquisition power plans, no-person bring-up procedure and
a delivered quote. Exported files or an empty parity array alone are insufficient.

**Working hardware validated** additionally needs physical assembly, inspection
and person-disconnected measurements. Firmware compilation or simulations cannot
supply missing scope, noise, rail-loss or interface evidence. Body connection
is a later revision and safety review, not unlocked by a fixed number of turns.

## Scope discipline

Each slice must advance a concrete exit condition or repair a reproducible
problem. Prefer source facts for identity, native CAD for connectivity/geometry,
and physical measurements for real power/noise behavior. No general workflow,
model or approval registry should be added merely to restate an uncertainty.
Do not use test-count growth as engineering progress.

Passive-input, bounded BIAS/overload and supply studies, guarded S3 firmware,
three-sheet schematic, all-pad/BOM/cache and footprint checks, header/UART
worksheet, T491 land choice, initial placement/routing and the AVDD1/output/CH1N scoped routing
repairs are implemented (inspect the current repair PR status). Do not recreate them. Historical detailed
results remain in Git and their specific documents. Tool/source-transfer
iterations were delivery friction, not additional electrical design milestones.

`REV_A_BENCH_HARNESS.md` already maps GPIO to physical DevKit/AFE pads. The
remaining work is the actual cable/interface, orientation and operating
procedure, not another pin list. Both boards use J1: preserve AFE/DEVKIT
prefixes. UART17/18 are application routing, not isolation. Simultaneous normal
DevKit USB/header supply inputs or an unknown live adapter are not authorized.
Parts are selections, not proof of purchase. Actual owned revision/lead data and
a delivered quote remain necessary; the user's additional-spending target is
$100, not an established cost.

Reference entry points: `HARDWARE_BASELINE_REV_A.md`, `LLM_HANDOFF.md`,
`REV_A_CH1N_CORRIDOR_REPAIR.md`, `REV_A_INPUT_LAYOUT_REVIEW.md`,
`REV_A_DIGITAL_OUTPUT_REPAIR.md`,
`REV_A_AVDD1_REPAIR.md`, `REV_A_SCHEMATIC.md`, `REV_A_BENCH_HARNESS.md`,
`REV_A_FOOTPRINT_REVIEW.md`, `REV_A_TANTALUM_LANDS.md`,
`REV_A_CAPACITOR_EVIDENCE.md`, `REV_A_BULK_CAPACITOR_ASSESSMENT.md`,
`REV_A_SUPPLY_TIMING.md`, and open #45/#48. All purchasing, release,
physical-validation and body-use flags stay false.
