# Finish the person-disconnected Rev A prototype design

**Checkpoint: 2026-09-28, Europe/Berlin.** This is a bounded completion plan for
the existing four-channel ADS1299-4 + off-board ESP32-S3 bench prototype. It does
not redefine the long-standing hardware roadmap or grant physical approval.
The native schematic, harness and simulation infrastructure are already present;
they must not be reconstructed in each continuation.

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

## Present position in the original roadmap

1. Selected passive-input bridge: implemented with independent native comparisons.
2. BIAS and power studies: implemented at explicitly limited model scope. Supply
   timing, inverse source voltage and complete source-band checks now exist.
   Remaining work is applying a finite final envelope, not more generic timing APIs.
3. Schematic and S3: three native sheets, all-pad connectivity, BOM/cache checks,
   physical DevKit header map, guarded real target compilation and geometry checks
   are implemented. PR #57's T491 land-pattern/fixture blocker is merged. This
   continuation adds the first native, parity-checked PCB import; it is still a
   parking grid, NOT a layout. Final part/interface/process decisions remain.
4. Placement/routing, fabrication package, delivered quote and staged dummy-only
   bring-up: not complete. This is now the main work rather than another recovery loop.
5. Body-connected revision: outside this bench-prototype completion estimate.

## Remaining critical path and rough number of substantial continuations

A continuation means a coherent design deliverable with tests/review where
applicable, not a guaranteed duration or one test assertion. **Plan about 8–12
further substantial continuations to a reviewed fabrication candidate**, after
this PCB-import slice. This is an engineering planning estimate, not a promise.
New electrical defects, supplier/approval gaps or tool failures can add work;
shared decisions can combine slices. Do not count manufacturing lead time or
physical measurements as work a chat agent has already performed.

| Deliverable | Estimated slices | Concrete exit condition |
|---|---:|---|
| Close the finite component and operating-envelope choices | 2–3 | Resolve the discontinued/planned-stop ceramic roles, use exact orderable/assembly data, state acceptable source/load/timing margins, rerun relevant models; synchronize any approved BOM/CAD changes. No guaranteed capacitance is inferred from a typical plot. |
| Close bench interface and mechanical choices | 1–2 | Select actual connector/mates and console interface, address both powered-off signal directions, define startup dummy fixture and measurement access; choose outline, stackup and mounting/clearance rules. Unknown owned-board identity remains a physical prerequisite. |
| Native PCB placement and routing | 3–4 | Place by electrical function, preserve decoupling/returns and input symmetry, route all required nets with appropriate planes and rules; no airwires or unexplained electrical/geometry violations. |
| Independent release review, exports and wiring package | 2–3 | Full ERC/DRC/parity pass, resolve review findings, verify assembly orientations and exports against source, deliver BOM/PnP/drill/Gerber and exact bench wiring/bring-up instructions with current quote. |

The design-support simulation closeout is approximately **2–4 of those slices**,
not an additional block of unlimited work. It can overlap component/interface
choices and early placement. Layout may proceed as a draft while specific part
choices are open, but fabrication must not pass those unresolved decisions.
If review finds an actual power-interface or placement flaw, repair the design
rather than adding only another documentation warning.

## Scope discipline for the next continuations

Every slice should close one item in the table or fix a concrete reproducible
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
`REV_A_PCB_IMPORT.md`, `REV_A_SCHEMATIC.md`, `REV_A_BENCH_HARNESS.md`,
`REV_A_FOOTPRINT_REVIEW.md`, `REV_A_TANTALUM_LANDS.md`,
`REV_A_CAPACITOR_EVIDENCE.md`, `REV_A_BULK_CAPACITOR_ASSESSMENT.md`,
`REV_A_SUPPLY_TIMING.md`, and open issues #45 and #48. All current purchasing,
release, physical-validation and body-use flags remain false.
