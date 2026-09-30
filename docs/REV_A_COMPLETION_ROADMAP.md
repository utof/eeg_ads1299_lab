# Finish the person-disconnected Rev A prototype design

**Current checkpoint: selected stackup design target and E1 bench requirements.**
The completed AVDD1/output/CH1N repairs and grouped residual-coupling assessment
remain intact. JLCPCB JLC04161H-7628 is the selected design target; job-specific
layer/material/tolerance confirmation is still required. E1 now gives numeric
low-impedance dummy-source and interference targets, not measured performance
or an approval to operate. High-impedance stress is separate, not silently
qualified. Next source work is capacitor lifecycle/effective-C closure while
factory/fixture confirmation stays open. No indefinite nine-reroute queue.

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
| Input-path geometry/coupling | 1 combined decision after confirmations; physical work separate | Main paths and CH1N repaired; nine residual locations remain one six-pair item | Use E1 and confirmed geometry for one combined rework or separate pilot-risk decision |
| Stackup and input-test envelope | 0 for target definition; 1–2 plus vendor/fixture evidence to close | Named JLC04161H-7628 target and numeric E1 requirements selected | Obtain job-specific tolerances/material confirmation; demonstrate fixture/measurement floor; not a released stack |
| Components, mechanics and assembly | 2–3 | Primary part evidence, logical harness and selected lands exist | Next: #48 capacitor lifecycle/effective-C against E1; then #45 mounting/mates/assembly |
| Real power/console fault readiness | 1–3 plus physical checks | Firmware/console contracts exist; actual rail-loss behavior unqualified | Resolve exact interface and powered-off paths; define dummy-bench checks |
| Release package and delivered budget | 1–2 after blockers close | Not ready for fabrication or purchase | Independent release review, coherent outputs and delivered quote |
| Person-disconnected bench verification | 2–4 guided turns plus bench work | Physical prototype validation not started | Unpowered inspection, then staged dummy-source tests after prerequisites |

**Next: #48 capacitor lifecycle/effective-C, with supplier/fixture confirmation
kept on #45.** Read `REV_A_STACKUP_BENCH_REQUIREMENTS.md`: selected outer gaps
0.2104mm/core1.065mm are nominal public table values, not manufactured tolerance
bounds. Prepared factory questions were not sent. Public copper/Dk differences,
material availability and per-layer bounds require a dated drawing before
release. Do not encode unconfirmed dimensions as a fabricated fact.

E1 core is resistive1-10kohm per leg with measured fixture matching, 1-40Hz,
250SPS/gain24, <=0.50uVrms total noise and<=0.50uVpeak coherent aggregate with
explicit allocations/uncertainty. E1 is a chosen dummy-bench design requirement,
not a scalp/electrode specification, physical result or enabled firmware mode.
100k andstrong source-imbalance cases remain reported stress, not E1qualified.
The fixture and0.03uVpeak/0.05uVrms uncertainty floors are still to be established;
missing equipment orfloor-limited results cannot become passes. No instrument
purchase orcost is established by the $100 extra-parts objective.

The group in `REV_A_UPSTREAM_COUPLING_DISPOSITION.md` stays OPEN for the confirmed
construction andseparate pilot-risk review. The new six-case native sensitivity
repeat/723-point KCL consistency check is not actual E1performance orPCB
capacitance extraction. Do not claim an actual coupling bound from the simple
crossing areas or the deliberately analysis-only gap/Dk intervals. The4.5mm DNP
branch imbalance and earlier supply/output tradeoffs remain explicit. Make one
combined rework orreviewed pilot-risk decision when its inputs exist; meanwhile
advance the remaining finite component/mechanical/interface tasks.

A pilot design may be reviewed for manufacture before a physical board exists;
validated performance requires the later measurements. Do not create a circular
requirement to measure the first board before it can be made, or silently turn
the planned experiment into fabrication permission. All current gates remain
false; body use stays a separate, unestimated revision.

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
repairs are merged. Do not recreate them. Historical detailed
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
`REV_A_STACKUP_BENCH_REQUIREMENTS.md`, `REV_A_UPSTREAM_COUPLING_DISPOSITION.md`,
`REV_A_CH1N_CORRIDOR_REPAIR.md`,
`REV_A_INPUT_LAYOUT_REVIEW.md`,
`REV_A_DIGITAL_OUTPUT_REPAIR.md`,
`REV_A_AVDD1_REPAIR.md`, `REV_A_SCHEMATIC.md`, `REV_A_BENCH_HARNESS.md`,
`REV_A_FOOTPRINT_REVIEW.md`, `REV_A_TANTALUM_LANDS.md`,
`REV_A_CAPACITOR_EVIDENCE.md`, `REV_A_BULK_CAPACITOR_ASSESSMENT.md`,
`REV_A_SUPPLY_TIMING.md`, and open #45/#48. All purchasing, release,
physical-validation and body-use flags stay false.
