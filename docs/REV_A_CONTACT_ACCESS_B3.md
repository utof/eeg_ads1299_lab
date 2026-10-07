# B3: supported sense tails, not clips under the cable

**Access-method decision and nominal geometry study; no build or power release.**
Baseline: main `8c08e012e58b9bde7ca2b0f3df9c0126d10b0c00`, tree
`7e7322374c84b58704f0d30388f458e165bfea2a` (PR92). Reuse B1/B2 and the current
K2 holder. Neither PCB, component, firmware nor approval gate changes here.

## Decision and reason

For the first separately approved commissioning setup, prefer **five separately
identified, insulated sense pairs**, attached by a reviewed fine-wire solder
process to C6 and C30-C33 and strain-relieved independently of their joints.
The instrument connects at supported outboard terminations, not by hanging
clips from capacitors. No new test PCB, permanent test header, global footprint
change or universal pogo fixture is justified by this inspection.

A straight top-down probe cannot reach every B2 landmark with K2 fully assembled:
C30 is below the J1 ribbon envelope; C33 is below its raised guide bridge. C6,
C31 and C32 have open vertical approaches ABOVE the component allocation, but
that does not make their occupied component pads convenient clip terminals.
Removing a keyed guide, lifting a live ribbon or substituting a remote sense
voltage would evade the problem rather than solve it.

**This selects an attachment method, not an already qualified fixture.** Actual
wire insulation, assembly/rework method, joints, restraints and instrument loading
must be accepted before use. If attachment cannot be made without damaging a
capacitor/pad or obstructing the mechanism, keep HOLD and make one targeted
access change; do not repeatedly rework the capacitor or waive the observation.
Murata identifies mechanical and thermal stress as causes of MLCC cracking [1].

## Five pairs; no common ground clip

Each row gets its own negative sense conductor, even though the four rail returns
and C6 return belong to the same schematic GND. Do not combine these conductors
outside the board or connect them to an unreviewed instrument common. They are
sense leads, never power feeds, discharge leads or substitute cable returns.
B2's instrument earth/USB/common-mode/loading review still applies to BOTH wires.

| B2 observation | Positive / negative terminals | Native pad centres, mm | Outboard relief bank |
|---|---|---|---|
| O5, VCAP1 | C6.1 / C6.2 | (52.20,49.38) / (52.20,55.62) | South, beyond y=74 |
| O2, incoming AFE rail | C30.1 / C30.2 | (63.35,29.50) / (65.25,29.50) | North, before y=4 |
| O3a, AVDD | C31.1 / C31.2 | (51.05,20.00) / (52.95,20.00) | North |
| O3b, separate AVDD1 landmark | C32.1 / C32.2 | (43.35,23.20) / (45.25,23.20) | North |
| O4, local DVDD | C33.1 / C33.2 | (74.05,23.00) / (75.95,23.00) | North |

Pad centres identify nets, NOT solder/probe placement targets. On C6 the footprint
is rotated 270 degrees; positive pad 1 is toward smaller Y. Retain capacitor
polarity and original component-to-board joints. Choose an exposed outer joint
under magnification after seeing the actual placement and solder fillet; do not
solder to the component's moulded/ceramic body or scrape mask to create a test pad.
Neither J3/J104 pin 6 nor a connector under its mate becomes a spare test point.

The 0805 copper extends 1.45 mm from each component origin along its long axis.
The proposed maximum 2.10 mm body occupies 1.05 mm per side when centred: only
0.40 mm nominal toe projection remains. Body offset, fillet and mask can consume
it. This calculation explains the fine-wire choice; it is NOT guaranteed exposed
metal or a new assembly placement tolerance. The existing cap disposition remains
in force; the proposed capacitors have not been substituted in active CAD.

## Mechanical arrangement to accept on the actual assembly

Use flexible insulated fine wire, provisionally a 0.10-0.15 mm conductor with
insulated OD no greater than 0.30 mm per wire. These are planning envelope limits,
not an approved wire identity, insulation rating or guaranteed solder-joint size.
Keep bare ends confined to their inspected joints; no exposed loops or terminals
near adjacent copper. Do not stretch wire taut to make it fit.

One small **nonconductive clamp/support bank north of K2**, and one south of it,
carry the fine-wire transitions and instrument cable weight. Secure both banks
and K2 to the same stable bench support. The banks are fixture items, not new
holes in either PCB. Give each pair identification and independent retention;
insulate unused outboard ends. Grip insulation, never crush bare conductors.
Do not use conductive carbon-filled print material or adhesive on a capacitor
as a substitute for a reviewed restraint. No specific clamp has been fabricated.

Between a joint and its first relief, use a small slack bend and support the wire
so handling the instrument cable cannot pull on the pad. Near-joint insulation,
slack and support placement need magnified inspection; their sub-4-mm geometry is
not validated by the envelope model. Do not let the wire rest on the ribbon or
bridge. Install the sense harness while de-energized, discharged and accessible;
then complete the normal K2 bridge/cartridge assembly without trapping it.

Route the lightweight insulated pairs in the **z=5.5 mm nominal layer**, above
the existing z=0..4 mm component allocation and below the lowest z=7 mm cable
saddle. The study reserves a 1.0 mm-diameter corridor per pair, including assumed
bundle width and movement. This leaves 1.0 mm nominal vertical separation to each
of those two allocations. Neither is a tested tolerance, force or movement bound.
The final supported wires must stay inside the allocated corridors, with actual
assembly tolerance checked; loose wires sagging onto components are not accepted.

C30 exits west below the ribbon before turning north at x=54.5 mm. C33 travels
north of the guide crossbar, under it during the initial exit, then west at
y=21 mm and north at x=57 mm, outside the J3 body allocation. C31/C32 use the open
north approach. C6 exits south at x=54.5 mm. Exact nominal polylines are in
`studies/b3_access_envelope.scad`; intersecting pair corridors indicate routing
space, not permission to join conductors. Arrange insulated crossings and local
slack without exceeding the envelope. The existing keys, bridges, clips, C4
backing and full socket seating remain unchanged and required.

## What the native geometry check actually establishes

The small SCAD file imports the CURRENT `carrier_k2.scad`; it is a read-only
inspection overlay, not another holder design and not a printable assembly.
A 0.5 mm-diameter vertical approach from z=4.1..30 mm was checked at two outer
contact candidates per capacitor. Against the assembled K2/header/socket/ribbon/
service envelopes, native OpenSCAD 2021.01 intersections were:

| Case | Added intersection volume, mm3 | Interpretation |
|---|---:|---|
| C6 / C31 / C32 vertical approaches | 0 (within numerical roundoff) | Clear above the allocation only; no proof of exposed joint or real probe fit |
| C30 vertical approaches | 1.7952 | Blocked; cable/guide volume cannot be ignored |
| C33 vertical approaches | 0.9840 | Blocked by the guide |
| Proposed pair corridors, z=5.5 mm | 0 (within numerical roundoff) | Nominal aerial routing has no K2 obstacle intersection |
| Same corridors raised to z=8.0 mm | 7.2344 | Deliberately bad placement detected; height is not arbitrary |

The disjoint 1 mm3 witness is subtracted from each mesh volume, allowing an empty
intersection to be exported normally. These are seven authoring cases, not new
project tests, an exhaustive clearance proof or physical experiments. Component
joints, actual wire/support compliance, full insertion/removal motion, tolerances,
probe loading and electrical performance are NOT modelled. Never present the
whole assembly view as a detailed populated PCB or print its reference envelopes.

Example inspection command from repository root:

```sh
openscad --hardwarnings --export-format asciistl -D 'mode="blocked_routes"' \
  -o /tmp/b3-corridor-witness.stl docs/studies/b3_access_envelope.scad
```

The result is an inspection mesh with a witness, not a manufacturing part. Modes
`vertical_c30`, `vertical_c33`, `blocked_raised` and `view` show the rejected
approaches and the proposed routing. Reconcile with changed source, never reroute
the PCB or overwrite K2 to preserve these historical numbers.

## Acceptance and next real engineering step

Before a sense harness is used, record the selected wire, accepted attachment
process, joint photographs, pad/polarity identity, insulation, strain relief and
complete supported cable route in B2's EXISTING run card. Inspect before and
after restraint/cable handling using an approved force/inspection method. Do not
run a generic ohmmeter test across assembled IC rails. Rework-induced damage can
be hidden; process and inspection acceptance cannot be replaced by continuity.

Keep the two leads close where practical and record lengths and the actual
instrument connection. Added wire is not electrically invisible: input current,
leakage, resistance, capacitance and loop response can affect readings [2]. No
bandwidth, fast-spike coverage or accuracy is assigned to this unbuilt harness.
B2's simultaneous observations and uncertainty-adjusted R/V checks remain required;
extra leads do not prove them. The rail contacts remain capacitor landmarks, not
new all-chip-terminal measurements. Do not use this harness for signal injection.

**Stop expanding the paper probe plan after this decision.** Carry the fixture
and instrument acceptances forward to before-power review, and next address the
existing before-fabrication layout/return-path items for a limited internal-test
pilot. Use the recorded pending regions and distinguish a needed source repair
from a condition that can be characterized later; do not waive #45/#48 or enlarge
reference-check allowances. Prices stay deferred, Moscow is the planning region,
and Q1 remains the sole unsent quote snapshot.

[1] Murata, ceramic-capacitor FAQ on mechanical/thermal cracking, accessed
2026-10-08: https://www.murata.com/en-global/support/faqs/capacitor/ceramiccapacitor/mnt/0007

[2] Tektronix, ABCs of Probes (B2's existing reference); attachment/loading is
part of the measurement, not just a convenience:
https://www.tek.com/en/documents/whitepaper/abcs-probes-primer

No physical construction, mating, energization, purchasing, fabrication,
external-input acquisition or person/animal connection is authorized here.
