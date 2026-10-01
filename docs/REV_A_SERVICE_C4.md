# C4: routed AFE service feed and sense access

C4 adds AFE **J3 / J_SERVICE**, matching auxiliary **J104**. It does not enable
firmware, release either assembly, or qualify a power-loss protection system.
Base: merged PR75 `10676fd14ffdeffe86f338342c9346c28f7cb1c8`.
Read `checkpoints/20261001_service_c4.json` for the source-bound geometry and
`hardware/rev_a/service_c4.json` for the finite cable target.

## Circuit and cable

Both boards use `B6B-XH-A(LF)(SN)`; the cable target uses two `XHP-6` housings,
ten `SXH-001T-P0.6` contacts and five AWG24 conductors. Wire insulation OD must
be 0.9–1.9 mm. Target length between housing wire faces is 150 +/-5 mm, a new
planning choice, not a purchased assembly. The exact wire grade, crimp tooling,
strip/crimp dimensions, pull acceptance and qualified solder process remain
open. JST's cited drawings provide the connector dimensions, not those final
assembly approvals. Pin numbers are cavity identities viewed per the drawing,
not inferred from wire color, ribbon numbering, or an opposing end's photograph.

| AFE J3 | Auxiliary J104 | Function |
|---|---|---|
| 1 | 1 | Target ground return |
| 2 | 2 | AFE DVDD feed OUT to auxiliary buffer B supplies |
| 3 | 3 | Separately carried AFE DVDD sense |
| 4 | 4 | AVDD sense, downstream of R11 |
| 5 | 5 | Second target ground return |
| 6 | 6 | NC pad; both cable cavities empty, no terminal/conductor |

The feed and sense join on the AFE rail, **not at the auxiliary connector**.
Pin2 must not be connected to another regulator, VIN5 or MCU3V3. Pins2/3 are
separate copper itineraries ending at C33.1's DVDD node; pin4 ends at C31.1 on
AVDD. This is rail supervision, not a Kelvin measurement at the ADC die. The
controller still runs from its own regulator. Existing J1/J2 pin assignments,
including CLKSEL and NC pins, remain unchanged. The C3 manifest's former
"AFE access absent" assumption is replaced by "separate inspected harness;
no hot mating" in both contract and finite validator. The auxiliary's actual
48-instance/212-terminal circuit is unchanged.

Before eventual powered use, inspect the DETACHED cable for exact1:1 continuity,
isolation between all conductors, empty cavity6 and retention. Then check the
unpowered assembled circuit: returns1/5 and DVDD2/3 intentionally become common
on the AFE, so an assembled-only continuity test cannot detect every cable
swap/short. Avoid simultaneously connected sources. All power must be removed
before mating/unmating; no hot-plug or single-fault sequencing guarantee follows
from using a shrouded connector. Friction retention needs separate external
cable restraint and physical validation; no pull-force claim is made.

## Native placement and copper

J3 pin1 is at **(75,15) mm,180 degrees**, giving pins1–6 from x75 to62.5 at y15.
The selected pinned KiCad footprint is
`Connector_JST:JST_XH_B6B-XH-A_1x06_P2.50mm_Vertical`. Six0.95mm drills and its
pad geometry are checked independently. JST's reference mounting pattern is
0.9 +0.1/-0 mm with non-accumulating pitch tolerance; a nominal library hole is
not a guaranteed finished plated hole. Vendor DFM and assembly sign-off remain
required. Do not turn the header into six mounting screws or enlarge its holes
without coordinated review.

| Path | Front copper width | Authored centreline sum |
|---|---:|---:|
| J3.2 → C33.1, DVDD feed | 0.40 mm | 8.642 mm |
| J3.3 → C33.1, separate DVDD sense | 0.20 mm | 9.678 mm |
| J3.4 → C31.1, AVDD sense | 0.20 mm | 19.927 mm |

All11 new segments are on F.Cu; no new via or signal on In1. All **68 original
footprint forms and704 original track/via forms remain byte-identical**, as do
all other old non-zone root forms. Fresh native ground fill changes only the
zone form. Final AFE count:69footprints,251pads,593segments,122vias. The actual
native netlist has70parts/262terminals including the off-board controller.
The old input, AVDD1/VCAP and digital-output routing is not regenerated.
The feed width is a geometry decision, not a measured drop/current guarantee;
additional auxiliary loading, regulator headroom and fault trajectories remain
part of the existing C3/whole-system requirements.

## Carrier support and mating space

Two backing blocks are added to the existing carrier: XY[59,11.5]–[61,18] and
[76.5,11.5]–[78.5,18] mm, rising from z=-7.01 to the nominal PCB underside
z=-1.6. They brace the connector region without new PCB mounting holes.
Conservative bounding-box clearance to all back-layer pads/tracks/vias is
0.65mm. This surface screen deliberately does not imply no inner copper below
these regions, nor a guaranteed tolerance/load/bending limit. Solder tails and
fillets must not protrude into the support material.

A conservative18.5x8x12mm body/mate allocation at[59.5,11,0] clears the existing
frame and both seated IDC cartridges for vertical lifts0,5,20mm. A separate
solder-tail volume and a northward cable exit volume also clear the nominal
model. The tests reject receiver intrusion and require actual solid backing
at two witness locations. These are finite rigid geometry checks, not arbitrary
tilt, hand-access, flex, force, strain-relief or printed-fit validation. The
existing cartridge/bridge geometry is unchanged; only the base gains supports
and the reference component allocation gains J3. A physical unpowered fit and
qualified independent cable restraint are still required before use.

## Recovery and verification scope

The interrupted turn's main-source capture survived on GitHub, but its local
uncommitted implementation did not survive into the recovery runtime. The
recorded authoring operations, coordinates and route definitions were recovered
from its tool transcript and applied to the verified unchanged PR75 source.
New deterministic J3 item UUIDs and new recovery commits are used; no claim is
made that the vanished uncommitted PCB bytes or its local ancestry were restored.
The prior screenshots are not substituted for current native checks.

Current recovery first observed three missing-service failures on the unchanged
board, committed as`efc4e0e`; the support witness then failed on the old carrier
before support geometry was added. Fresh native service refill/DRC is0/0/0.
Three pad-escape cuts must disconnect their specific J3 pin while retaining
schematic parity and only the expected adjacent dangling-track diagnostic.
Reversal/subdivision controls remain connected. The cable-record controls reject
feed/sense swaps, a populated NC cavity, local auxiliary joining and weakened
power/approval restrictions. These are source/native fault checks, not physical
experiments or a guarantee that every wiring fault is detected automatically.

The former fault-copy implementation assumed the zone was the final board
object; placing J3 after it made a zone-removal mutation also delete J3. The
recovered canonical source keeps its zone last. No DRC severity, exclusion or
clearance was relaxed. All full final-head test/review outcomes must be read
from the live PR, not inferred from inherited progress messages or these
prepublication focused checks. Source-bound snapshot inventory includes the new
service plan, test and consumed footprint. Whole-board carrier binding remains
strict and names this reviewed geometry; it is not a metadata-normalizing mask.

## Remaining work and limits

Next source slice: **guarded C2 firmware SESSION/ARM/READY/ARMED integration**,
then auxiliary placement/routing. Retain the parked-low/control/clock/VCAP/reset
order and invalidate a whole capture on detected faults. This PR does not
change or enable firmware, implement analog input isolation, qualify supervisor
SENSE injection or close floating/intermediate-supply/leakage/rapid-fault limits.
Keep#45/#48, capacitor/stackup/E1/fixture and physical carrier-fit requirements
open. Added AFE header allowance$0.50 raises that planning subtotal to$94.84;
it does not price the auxiliary, service cable, crimp tools or holder manufacture,
and does not establish compliance with the$100 objective.

**No purchasing, fabrication, powered connection or person/animal connection
is authorized.**

Primary source checked during recovery2026-10-01, including drawings/table page
images: JST XH official catalog, pp2–5:
https://www.jst-mfg.com/product/pdf/eng/eXH.pdf . Its dimension/process notes remain
conditions to confirm, not acceptance of generic "JST-compatible" parts.
