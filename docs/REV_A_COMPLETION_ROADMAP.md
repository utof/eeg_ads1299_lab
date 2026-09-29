# Finish the person-disconnected Rev A prototype design

**Current checkpoint: 29 September 2026, AVDD1 copper repair in PR #62.** This is the
completion plan for the four-channel ADS1299-4 + off-board S3 bench prototype,
not permission for physical use. PR #60 published the exact connected board
and repository-first handoff. PR #62 repairs that local AVDD1 bypass topology; check its live head/review/CI
status before using main. Other electrical reviews remain open.

## Glanceable roadmap

Estimates below are **remaining substantial chat turns**, not elapsed time,
commit counts, guarantees or a safety score. A turn can combine related work;
new findings can add work. Manufacturing/shipping and physical measurements are
not completed by chat and are excluded from a design-turn countdown. Do not sum
overlapping categories into a promised completion date. Refresh this table after
each bounded deliverable; show it in completion reports after a short TLDR.

| Category | Estimated remaining turns | Done / current status | Next slice or blocker |
|---|---:|---|---|
| Source, core software/firmware and checks | 0 for current baseline; maintain | Published on main; pinned CI and target build; fresh agents can start from repo | Keep source, review and actual test heads aligned |
| PCB connectivity draft | 0 for initial routing | Fully connected; fresh native DRC/parity0/0/0; no manufacturing approval | Preserve completed copper except reviewed electrical repairs |
| Supply/bypass review and repair | 0–1 follow-through | AVDD1 repaired in PR #62; inter-capacitor, pad-contact and side-branch guard findings reproduced and corrected; not noise-qualified | Finish renewed exact-head CI/review; retain VCAP3/AVDD56 tradeoffs in broader review |
| Digital-return and input-path review | 2–3 | Neither review is closed | Digital reference/layer transitions, then input P/N geometry and coupling |
| Components, stackup, mechanics and assembly | 2–4 | Primary part evidence, logical harness and selected lands exist; decisions still open | #48 capacitor lifecycle/effective-C; #45 stackup, mounting, mates and process |
| Real power/console fault readiness | 1–3 plus required physical checks | Firmware/console contracts exist; actual rail-loss behavior unqualified | Resolve exact interface and powered-off paths; state dummy-bench checks |
| Release package and delivered budget | 1–2 after blockers close | Not ready for fabrication or purchase | Independent release review, coherent outputs and delivered quote |
| Person-disconnected bench verification | 2–4 guided turns plus actual bench work | Physical prototype validation not started | Unpowered inspection, then staged dummy-source tests after prerequisites |

**Next: digital layer-transition and return-path review** after PR #62 checks
and review are resolved. Read `REV_A_AVDD1_REPAIR.md` for the actual repair,
its connected-but-indirect fault controls, and the longer C24/C14 path tradeoffs.
No BOM, schematic, firmware, model, dependency or approval changes. These are
native CAD and source-geometry results, not noise qualification. Body-connected
work remains a separate,
unestimated later revision, not the last checkbox in this bench-board table.

## Three different finish lines

**Design-support simulation complete** means the final selected circuit has its
relevant passive-input and supply cases run under a stated design envelope;
assumptions, failures and deferred questions are explicit. It does not require a
transistor-level ADS1299 model or claiming unknown electrode/board parameters are
measured. Existing BIAS studies remain bounded hypotheses. Because Rev A firmware
keeps external acquisition/BIAS and body use disabled, further physiological and
full BIAS realism is not a prerequisite for every bench-board layout operation.
The optional TPS7A20 reference-engine discrepancy must be resolved or explicitly
bounded/deferred with its design consequence; it must not silently become an
unlimited simulator-development project on the PCB critical path.

**Ready-to-fabricate bench design** means an editable native schematic and routed
PCB, final outline/stackup and mating choices, source-consistent BOM, checked
polarity/placement, clean ERC and complete DRC including schematic parity, and a
reviewed Gerber/drill/assembly/placement package. It also includes an exact
board-qualified wiring worksheet, separate programming/acquisition power plans,
a no-person bring-up procedure and a delivered quote. Exported files or an empty
parity array alone do not meet this definition.

**Working hardware validated** additionally needs physical assembly, inspection
and person-disconnected measurements. Firmware compilation or a model cannot
supply missing oscilloscope, noise, power-loss or real-interface evidence.
Body-connected operation remains a different, later revision and safety review;
it is not unlocked by a fixed number of chat turns or by finishing this PCB.

## What is already implemented

Selected passive-input, bounded BIAS/overload and supply studies, the guarded
S3 target, three-sheet native schematic, all-pad/BOM/cache and footprint checks,
physical header/UART worksheet, T491 land choice, PCB placement and initial
routing are implemented. Their assumptions and historical results remain in the
specific documents; do not recreate them to fill a new session.

Design-support model closeout can overlap component and interface decisions.
The optional TPS7A20 reference-engine discrepancy still needs a finite disposition,
not an unlimited simulator project. The supplied parts are selections, not proof
of purchase. Current physical data and a delivered quote remain necessary.

Older estimates for parking-grid placement/routing describe earlier stages and
are retained in Git history. They are superseded by the current table rather
than silently decremented. An actual design flaw should lead to a focused repair,
not an indefinite chain of warnings; the present next repair is explicitly named.

## Scope discipline for the next continuations

Every slice should advance a concrete exit condition in the table or fix a reproducible
fault blocking it. Do not add general frameworks, repeat completed model setup,
turn every uncertainty into a new permanent approval registry, or use test-count
growth as the measure of progress. Prefer evidence at the relevant boundary:
source facts for component identity, native CAD for connectivity, routed-board
DRC for geometry, and physical measurements for real power/noise behavior.

The existing `REV_A_BENCH_HARNESS.md` already answers logical GPIO to physical
DevKit/AFE pad mapping. The new work is completing the actual cable/interface,
placement orientation and operating procedure, not writing the same pin list
again. Both boards use J1, so retain AFE/DEVKIT prefixes. UART pins17/18 are
separate application routing, not electrical isolation. No simultaneous normal
DevKit USB/header supply inputs or unknown live adapter is authorized.

## Changes over the recent three-day work window

Read exact commit/CI records for execution identity; the following groups changes
rather than counting small commits or disposable workbenches as deliverables.

- 25 September: source-traceable BIAS, extra-pole and overload hypotheses; independent
  AC/transient checks; simulator-output identity/completion protections; guarded
  S3 target build and bounded power-model investigation. Physical realism remains limited.
- 26 September: corrected power-up low-state/CLKSEL contract and actual-sketch
  tests; full three-sheet schematic; all-pad graph, BOM export and local-symbol
  agreement checks; physical header/UART route worksheet and executable integration.
- 27 September into 28 September Berlin time: installed footprint geometry checks;
  direct capacitor lifecycle/typical data and candidate/orderable evidence; inverse
  source-voltage and explicit timing studies; project-local T491 nominal reflow
  lands, resolved binary-fixture publication, and the native PCB import.

The recent binary transfer/recovery iterations were delivery friction, not new
electrical design progress. The completed fixture and merged #57 remove that
specific loop. Manufacturer land choices and typical-data caveats remain visible;
the uploaded research is not a substitute for the verified current repository.

Reference entry points: `HARDWARE_BASELINE_REV_A.md`, `LLM_HANDOFF.md`,
`REV_A_POWER_RETURN_REVIEW.md`, `REV_A_PCB_IMPORT.md`, `REV_A_SCHEMATIC.md`, `REV_A_BENCH_HARNESS.md`,
`REV_A_FOOTPRINT_REVIEW.md`, `REV_A_TANTALUM_LANDS.md`,
`REV_A_CAPACITOR_EVIDENCE.md`, `REV_A_BULK_CAPACITOR_ASSESSMENT.md`,
`REV_A_SUPPLY_TIMING.md`, and open issues #45 and #48. All current purchasing,
release, physical-validation and body-use flags remain false.
