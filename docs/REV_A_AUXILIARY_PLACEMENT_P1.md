# P1 auxiliary PCB: authored placement, not a routed board

Base main `bc761c69558bbcf87a4c357c778828cc4da4928f`, tree
`0c4da842a103d0708cfbcc889696bf98373ef5e8` (F1, merged PR77).
Open `hardware/rev_a/auxiliary/auxiliary.kicad_pro` and its adjacent
`auxiliary.kicad_pcb` with KiCad9.0.2. The board is now authored source: do not
regenerate it from an importer or a historical authoring helper.

**P1 places all48 electrical instances and four mechanical mounting holes. It
contains no tracks, vias or filled copper planes.** Native parity is zero and
no other DRC finding remains, but **157 connections are unfinished; exit5 is
required, not a clean routing pass**. Physical layout/return-path qualification,
release and purchasing remain prohibited. Current board/land identities and
measurements are in `checkpoints/20261002_auxiliary_placement_p1.json`.

## The placement decision

The nominal outline is90x75mm, with1.6mm nominal thickness. All electrical parts
are front-side. The48 electrical footprints retain all212 schematic terminals;
four board-only NPTH pads bring the total to52footprints/216pads. The existing
four-sheet auxiliary circuit and43-row electrical BOM are unchanged. The main
AFE board, J3, carrier, firmware, hardware profile and dependencies are unchanged.
The only C3 manifest prose correction acknowledges the already-merged F1
handshake while retaining the absence of automatic analog-source isolation.

The functional flow is deliberate rather than a compact parking grid:

| Region | Placement purpose |
|---|---|
| Left-side HOST island | J103 computer-module tails, U101 host-side bypass and one side of the isolator |
| North TARGET edge | J101 AFE wire landings, with accessible individual solder joints |
| Middle upper TARGET | U102-U104: AFE pins face north, MCU pins face south; each supply gets its own adjacent bypass |
| Middle lower TARGET | U105-U108 monitors, local sense pulls and supply bypasses, away from the fastest top-edge bus region |
| Southwest TARGET | J104 separate DVDD feed/sense and AVDD-sense connection, with a reserved mating area |
| South TARGET edge | U109-U111 arming logic and J102 controller wire landings |
| East TARGET edge | J105 regulated5V power and J106 remote STOP contact tails |

This keeps long external wire access away from local supply-pin escape areas.
It does not establish actual cable inductance, crimp/solder process, conductor
bend radius, field coupling or operator tool access. Wire landings are not a
new connector purchase or interchangeable pin-header mapping.

## Four layers and a barrier on every copper layer

**Select four layers for the auxiliary routing target:** front signals, inner
separate-domain ground regions, inner separate-domain power regions, and slower
back-side control routes. TI's ISO7721 low-EMI guidance calls for at least four
layers in that order and no planes/traces/pads/vias beneath the barrier [1]. An
initial two-layer authoring draft failed the new layer-policy check and was
changed before this source milestone. Choosing four layers is not a measurement
of EMI, an approved factory stackup or a claim of controlled impedance.

The all-layer no-copper corridor is **x20.5..23.5mm, across the whole y0..75mm
board height**. U101's body spans it; no copper object may do so. It explicitly
forbids pads, vias, tracks and copper pours on F.Cu, In1.Cu, In2.Cu and B.Cu.
The current minimum HOST/TARGET pad-bounding-box gap is3.0mm, independently
measured from the native board, not inferred from the rule text alone.

A separate native rule requires3.0mm between HOST-net copper and other assigned
nets even away from that strip. Actual copper-fault tests demonstrate both this
rule and the inner/outer-layer keepout. Unconnected copper and mechanical items
still need review during routing. **3.0mm is this low-voltage prototype's chosen
geometric separation, not a certified creepage/clearance, mains, medical or
whole-system isolation rating.** The two circuits must not be joined through
mounting hardware, external cable shields or the bench equipment either.

No inner plane exists yet. The displayed dielectric entries and1.6mm nominal
thickness are planning defaults, not a vendor-confirmed construction. Do not
silently reuse the AFE's earlier named stackup as an auxiliary supplier approval.
Actual copper weights, dielectric gaps/material, finished dimensions, isolation
surface contamination and process tolerances remain part of release review.

## Local bypass and sense placement

All15 selected100nF capacitors remain unchanged. Each supply-pad centre is within
2.5mm of its associated IC supply-pad centre; the largest measured distance is
2.1875mm. Both supply pins of each TXU and both domains of the isolator have
separate local capacitors. The four sense pulldowns stay within3.0mm of their
respective monitor sense pin. Each expected pair and rail is checked, rather
than accepting whichever nearby capacitor happens to exist.

These are **placement budgets**, not short-loop inductance measurements. Routing
must give each capacitor an appropriate local return and avoid shared long
supply/return stubs. The package-specific PW pin locations are preserved; TI's
illustrated DTR example is guidance, not a reason to substitute its footprint
or pin numbers [2]. Follow the supervisor's short sense/supply and digital/analog
separation guidance when routing [3]. The C3 leakage margins and conditional
fault timing are not closed by moving these parts close together.

## Selected land, explicitly scoped clearance

Native U111 uses the previously selected0.5mm-pitch footprint, with0.35mm-wide
pads and0.15mm gap. An explicit **U111-pad-to-U111-pad minimum of0.15mm** permits
that unchanged selected land. Other default copper clearances remain0.20mm;
HOST/TARGET has its separate3.0mm requirement. This is a new narrowly scoped
auxiliary rule, not a global clearance reduction, ignored DRC finding, changed
footprint or relaxation of the main AFE rules. Native mutation of the U111 pad
gap below0.15mm produces the expected actual DRC failure.

The exact rule parse is guarded against broadening its footprint scope or
lowering either minimum. The primitive selected land must still be accepted by
the PCB/assembly process; a software clearance pass does not establish yield,
mask registration, solderability or the supplier's production limits.

## Mounting and cable access

Four **2.7mm nominal NPTH clearance holes for an M2.5-style support** sit at
(5,5),(85,5),(5,70),(85,70)mm. They are mechanical-only, excluded from the
schematic, electrical BOM and placement output. No fastener or spacer is
selected or purchased. Each has a6x6mm reserved mounting allocation checked
against native copper-pad boxes; the minimum allocation-to-pad gap is1.0mm.
Use independently supported, nonconductive fixture elements until a mechanical
assembly is reviewed. Hole diameter alone does not qualify a screw-head, washer,
post, force, board deflection or a conductive base crossing both domains.

Declared XY working allocations (mm) are:

| Interface | xmin,ymin,xmax,ymax |
|---|---|
| J101 AFE tails | 26,0,78.5,12 |
| J102 MCU tails | 26,61.5,83,75 |
| J103 HOST tails | 0,29,14.5,35 |
| J104 XH rail service | 27,50,45.5,58 |

Other component courtyards do not enter them. These rectangles reserve design
space but are not exact maximum mate, tool, strain-relief or cable envelopes.
The MCU/module are independently supported outside this board; no daughterboard
or enclosure is implicitly suspended from the wire joints. J104's five-wire1:1
service cable and all C4 disconnected-continuity rules remain unchanged.

Reference labels are on Fab for the placement inspection view; large functional
warnings are on silkscreen. Final assembly artwork, circuit labels, cable
restraint and mounting drawings remain unfinished. No ready-to-print carrier
or assembled enclosure is delivered by P1.

## Checks and reproducibility

Run the existing locked entry point from the repository root:

```sh
uv sync --locked --all-extras
uv run --locked --all-extras python -m tools.check
uv run --locked --all-extras python -m tools.check --schematic
```

Use the declared KiCad9.0.2 engine and libraries. Native tests operate on copies,
not the authored PCB. The new native selection compares every transformed pad
with its selected library land, all contact nets, board outline/layers, domain
membership, barrier policy,15bypass pairs, mounting allocations, mating areas,
buffer orientation and the separate feed/sense nets. Native parity independently
compares the actual board and four-sheet schematic. A benign placement move must
still pass; corruption controls must fail the relevant geometric or native rule.

The focused file has16cases: one ordinary presence/state check and15native CAD
cases. It includes real outer- and inner-layer barrier violations, an off-strip
HOST/TARGET spacing fault and an underspaced U111 pad pair. Missing-board,
source-snapshot/policy and four-layer requirements were observed failing before
their implementations; original test commits are retained. These are not
physical experiments, an exhaustive collision/fault search or proof of a routed
return path. Count these cases inside their actual full-suite selection, not
again as additional independent tests.

The source receipt now includes this PCB, exact custom-rule file, mounting land
and both new test sources. Old ERC diagnostic suppression checks, all circuit
contracts and existing AFE routing guards remain active. The corrected F1 prose
is not an electrical graph change. Final whole-gate and review evidence must be
read against the current PR head, never inferred from baseline results.

Authoring found overlapping placements and the stock fine-pitch gap before
correction; no exclusions were added to conceal them. Native SaveBoard/export
may expand a project file or create a user-local PRL. The original strict project
configuration was restored; exports and mutation tests must use independent
copies so those tool-generated settings cannot silently modify the source.
The authoring helper is evidence, not a new dependency or instruction to overwrite
this board later. Runtime caches and font files are not part of the source.

## Next slice and limits

**Route auxiliary ground references and the local bypass loops first**, then
power and signals, while keeping the full four-layer barrier and actual domain
supply provenance intact. Do not short J104 feed/sense at this board or connect
HOST_GND to TARGET_GND. Preserve placement budgets; revise a location explicitly
if an honest routing/return-path review shows a problem. Then require fresh
native fill/DRC, signal/return inspection and updated mechanical access evidence.
No AFE-board or firmware reconstruction is part of that slice.

All#45/#48 physical limits, capacitor evidence, fast/partial-rail uncertainty,
analog-source exposure, K2/C4 fit, factory construction and measurement needs
remain open. F1 already implements the guarded software but cannot qualify
physical shutdown timing or retract transmitted bytes. P1 has157airwires and
no auxiliary routability/manufacturing claim. Four-layer fabrication, assembly,
mounting parts and complete cables are unquoted; the$94.84 AFE planning subtotal
does not establish the user's$100 additional-parts target. All purchasing,
fabrication, powered-connection and body-use flags remain false.

## Primary layout references inspected 2026-10-02

[1] TI ISO772x SLLSEP3G, printedpp31-32, layout figure inspected:
https://www.ti.com/lit/ds/symlink/iso7721.pdf
[2] TI TXU0304 SCES935A, printedpp25-26, example figure inspected:
https://www.ti.com/lit/ds/symlink/txu0304.pdf
[3] TI TPS3703 SBVS249B, printedp27, layout figure inspected:
https://www.ti.com/lit/ds/symlink/tps3703.pdf
[4] KiCad9 custom-rule condition and clearance precedence documentation:
https://docs.kicad.org/9.0/en/pcbnew/pcbnew.html
Manufacturer examples are component guidance, not approval of this board.
