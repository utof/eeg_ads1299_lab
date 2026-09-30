# K2: dimensioned captive-cartridge and removable carrier CAD

**State: executable fit prototype, NOT a released fixture or proven interlock.**
Base `dbc99981a592904428f2432094dc62c4a13dcc55`; PCB SHA256
`dfe893f958128ba28eb69188cf6debbbc9fcafa0ef5dd67bd58627d4b8a26842`.
No PCB, pin mapping, BOM, firmware, electrical model or approval flag changed.
K1's HTSW migration is already complete. Historical M1/K1 records stay unchanged.

## What now exists

Open `hardware/rev_a/mechanical/view_k2.scad` in **OpenSCAD 2021.01**. Select
`assembly` or `exploded` for inspection; select individual parts for mesh export.
`carrier_k2.scad` is the editable solid-model library, with no external libraries
or font dependency. This is actual constructive-solid geometry, not a picture
standing in for CAD. Its millimeter dimensions are below and in the source.
The green board and dark connector blocks in the assembly are simplified
reference envelopes, not supplier STEP models or a populated-board rendering.

The package comprises a base, two removable coded guide bridges, two captive
cartridge bodies, two covers, four edge retainers and two separate cable bars.
Corresponding part names are `carrier`, `bridge_J1`, `bridge_J2`,
`cartridge_J1`, `cartridge_J2`, `cap`, `edge_clip`, and `strain_bar`.
The same cap/bar is reused; right-side edge clips mirror the left part in the
assembly. `assembly` is NOT one printable part and includes reference hardware.
Fasteners, rivets, shims, compliant liners, controller support and terminated
cable ends are not invented purchased/qualified components of this CAD.

## Three 3D constraints corrected

**A closed guide wall obstructs the cable.** The actual IDSD drawing shows a
side-exiting ribbon, not a cable that emerges vertically through the lid [1,2].
K2 opens the -X receiver wall over the middle 25.6 mm, retaining corner-return
tabs and the +X coded rib. The cartridge has a corresponding side window.
The previously checked closed rectangular K1 cross-section must NOT be used as
proof of this slotted 3D guide. K2 has its own native collision tests.

**An integral raised bridge obstructs board installation.** A disposable first
solid model had 517.18 mm3 of overlap with the board/component allocation at
an intermediate vertical installation pose. The guides are now separately
removable, mounted to the base's outboard rails AFTER the PCB is seated and its
edge retainers installed. Left/right bridge fastener pitches are 36/30 mm to
avoid a two-fastener bridge interchange. No mounting hole is added to the PCB.
This is a modeled assembly sequence, not demonstrated physical handling.

**Local cable clearance did not guarantee assembly clearance.** The combined
frame/retainer test exposed J2 ribbon collisions with the earlier tall outboard
rail and clips: 214.57 mm3 seated and 20.81 mm3 after 2-mm withdrawal. The rails
now end at z=4 and clips at z=5.5, below the ribbon. Only the bridge mounting
pedestals remain raised to z=9.5, beyond the ribbon's y extent. Eight complete-
support probes (both ports, four heights) pass after this source repair. The
previous isolated receiver/saddle tests could not detect this interference.

## Dimensions and datums

PCB top is z=0; XY is the existing KiCad coordinate system. The 78 x 58 mm board
occupies x=10..88, y=10..68. J1/J2 pin-grid centers are (81.27,38.43) and
(16.27,43.43). All receiver/cartridge coordinates below are relative to those
centers; the socket datum is its mating face. Pin1/orientation is NOT inferred
from a mirrored mating-face view or wire color.

| Feature | K2 model dimension / condition |
|---|---|
| Base | x=-6..96, y=4..74, z=-10..-7: 102 x 70 x 3 mm |
| Base mounting | Four 3.2-mm holes, (0,7), (0,71), (92,7), (92,71); fixture only |
| Outboard rails | x=2..9.5 and 88.5..96; y=20..64; rail top z=4; separate bridge pedestals reach z=9.5 |
| PCB underside | Nominal z=-1.6; 5.4-mm nominal space to base; actual thickness/shims unresolved |
| PCB support strips | M1 regions x=10..11.5,y=32..38 and48..54; x=86.5..88,y=27..33 and43..49 |
| Top retainer contacts | 0.8 x 6 mm, inside those strips; clips end at z=5.5; nominal 0.10-mm top gap, not a prescribed clamp force |
| Bridge mounting | J1 x=91.5,y=23.43/53.43; J2 x=6.5,y=25.43/61.43; 2.8-mm clearance holes |
| Rail pilots | 2.0 mm; exact fastener/thread/material process UNQUALIFIED |
| Guide ring | 10.4 x 31 mm outside, 8.4 x 29 mm bore, z=9.5..14.5 |
| Cable opening | -X side, y=-12.8..12.8; full guide height; end tabs retained |
| Entrance bevel | 0.2-mm nominal bore bevel; key rib remains a positive stop |
| Coded rib | x=3.4..4.2, y=code +/-1; code J1=+7, J2=-7 mm |
| Cartridge guide section | 8.0 x 28.6 mm; groove x=3.2..4.0,y=code +/-1.2 |
| Socket pocket | 5.5 x 27.4 mm; full aperture through the top before lid fitting |
| Mating opening | 5.5 x 25.8 mm; end retaining ledges only, z=-0.6..0 relative to socket face |
| Guide body / ears | Body up to z=12.8; 12-mm-wide fastening ears z=12.8..14.3 |
| Cover / axial stop | Cover z=14.3..15.8; two internal end bosses stop at z=9.70 |
| Cover attachment | Four 1.5-mm holes at x=+/-4.8,y=+/-11; mechanically upset nonconductive rivet concept, NOT a qualified rivet/process |
| Cable saddle | Center x=-16 from each port, 8 x 32 mm; floor z=8.5; bar underside z=10.7 |
| Cable bar fastening | Two 2.2-mm holes at y=+/-14.8; liners/shims and accepted pull load still required |
| Working space | 21 mm above PCB plus 10 mm axial removal allocation; supersedes K1's 17/8-mm planning values |

The bridges' lowest cable-support floor is z=7.0 and receiver bottom z=9.5;
neither rests on C33. The collision screen uses a conservative z=0..4 component
allocation outside K1's cartridge columns and M1's four contact strips. The
original reference C33 maximum body is 1.35 mm, not a new substitution approval.
This is not a detailed solder/placement/cable-volume model of every component.

## Socket capture and full seating

Use the K1 selected IDSD cable, not the old SSW board-tail socket. Drawing AE
bounds give 26.77..27.28 mm length and 9.14..9.52 mm body height; 5.08-mm width
is REF, not a manufacturer maximum [1]. **Measured width <=5.30 mm is a K2
inspection requirement**, not a published guarantee. Reject/resize the pocket
through review if the real part does not satisfy this envelope. Do not machine
or press the connector body into a too-small pocket.

The lower ledges sit under only the socket ENDS, outside the male header's
25.527-mm maximum drawn length. They do not cover any of the 20 contacts and
put no plate between the two mating faces. Model tests preserve zero-added-gap
seating with up to 0.56 mm of shell overtravel relative to a seated socket.
The nearest enlarged ear remains nominally 0.28 mm above the guide at that
extreme. Manufacturing, print error, flash, creep and pin sway are NOT included.
K1's 0.0508-mm lower insertion arithmetic margin is still small and unqualified;
it was not enlarged by this CAD. The <=9.0-mm pin-top allocation must be checked
on the actual assembly, not inferred from a REF body height.

The cover and end ledges mechanically capture the socket. For the intended
non-swappable assembly, the four nonconductive rivets must be permanently upset
and require destructive replacement for disassembly. Adhesive alone or a loose
removable sleeve is not accepted. Rivet selection, setting force, material and
retention load remain OPEN; a CAD hole is not a validated rivet. The one-sided
cable window rejects the modeled opposite cable exit, but **does not prove the
factory wire-to-contact mapping**. Before permanently closing a cartridge,
verify all 20 contact/conductor identities, pin1 orientation and port label by
unpowered continuity. Incorrect factory or cartridge assembly is not magically
corrected by the external key. Do not omit contacts to create a polarizing key.

## Cable travel, retention and assembly sequence

The model reserves a 25.4-mm-wide, 1.6-mm-high cable envelope at z=6.2..7.8
relative to the socket face, encompassing the drawing's height variation with
an explicitly chosen allowance. It is not a maximum cable specification. The
cartridge window spans z=6.1..10.1. A nominal-only first model clipped the larger
envelope; the window and saddle/bar heights were corrected in the solids.

The separate saddle connects to the carrier, not the socket. **Remove/release
the bar before withdrawing the cartridge.** A rigid lifted-ribbon control
collides with a still-installed bar; no flexible-cable simulation or unspecified
service loop is being credited as a pass. Fit liner and shim thickness to the
actual cable with controlled compression, then validate pull/retention forces;
no compression limit or bend radius is inferred from this rectangle. The real
first bend, 101.6-mm cable routing to the independently supported controller,
free-end termination, capacitance/imbalance and strain-relief loads remain open.
The controller is deliberately not stacked on the AFE or hung from its pins.

Assembly/inspection order (all unpowered, no person attached):

1. With bridges and top retainers removed, locate the PCB on the four edge
   supports. Adjust the actual thickness/datum and capture it without bending;
   the nominal model's 0.10-mm retainer gap is not a production clamp setting.
2. Fit both retainers on each side, then the correctly indexed bridge to each
   rail with BOTH fasteners. Confirm component and PCB clearance. A missing or
   loose bridge fastener, damaged key or bare socket bypasses the intended system.
3. Assemble/continuity-check and permanently capture the correctly oriented
   socket. Seat it axially without using the cover to force a resistant plug.
   Verify full socket seating and contact engagement, then fit the independent
   cable bar with its reviewed liner/shims. Insulate all unused free conductors.
4. For disconnection, release cable restraint before axial withdrawal. For PCB
   removal, remove guide bridges before the retainers and PCB. No hot plugging.

These are prototype design requirements, not permission to begin fabrication,
assembly or powered operation under the still-false project gates.

## Native checks and their limits

`tests/test_carrier_cad.py` renders actual CGAL solids through OpenSCAD. STL
vertices must be finite, triangles nondegenerate by edge identity, and each
undirected edge used twice. Signed-tetrahedron volume measures actual Boolean
intersections, not a copied expected rectangle calculation. A disjoint 1-mm3
witness makes a legitimately empty intersection exportable; exporter failure,
warning, missing file or timeout is never interpreted as empty space.

Tests cover both correct seated ports; wrong port/reversal/quarter-turn/pitch
shifts/missing groove; sixteen first-contact tilt probes on J1 (+/-5,+/-15 degrees
about either horizontal axis, correct and wrong cartridges); cable travel with
released clamp, including both ports against the complete frame and edge retainers; socket retention and exit direction; board installation; and
closed part meshes. A removed rib makes the wrong-port control pass, so the
key's presence matters to the actual solid test. The closed-wall cable control
collides. These are **sampled rigid-solid checks, not a continuous collision-free
trajectory, arbitrary-angle proof, force simulation or physical qualification**.
In particular, combined-axis tilt, deformed/undersized plastic, partially
assembled guides, incomplete rivets, bare plugs and intentional forcing remain
outside the claimed result. Small correctly aligned insertion and full seating
must ultimately be checked on real unpowered parts.

The board relationship is explicitly hash-bound to the reviewed unchanged PCB.
Changing that board requires mechanical re-review, not silently keeping the
old carrier assessment. A 1-um skin is excluded ONLY at the intended bottom
support contact in the obstacle probe to avoid zero-volume STL faces. This is
not a manufacturing clearance allowance or removal of an unrelated obstacle.

First tests observed missing CAD, followed by real cable-envelope and board-
installation collisions in earlier solid iterations. The renderer preflight
also failed before OpenSCAD was added as a required native tool. Final gates
must be read at their actual commit; intermediate failures are not passes.
No electrical model, tolerance threshold or existing hardware gate was relaxed.

## Reproduce

Ubuntu 24.04's pinned native package is `openscad=2021.01-6build4` [3]. No new
Python dependency or separate verification orchestrator is introduced. The
ordinary gate remains renderer-free; `tools.check --native` now requires it,
and pytest temporary geometry/logs are retained below the selected native output.

```sh
uv sync --locked --all-extras
uv run --locked python -m tools.check
uv run --locked python -m tools.check --native
# Focused real CAD execution (fails if the renderer is missing):
uv run --locked python -m pytest tests/test_carrier_cad.py -q
# Export a single unapproved fit-prototype part, not the reference assembly:
mkdir -p reports/k2
openscad --hardwarnings --export-format asciistl -D 'part="cartridge_J1"' \
  -o reports/k2/cartridge_J1.stl hardware/rev_a/mechanical/view_k2.scad
```

No local native KiCad refill or S3 build follows merely from these OpenSCAD
renders. Use the normal exact-head hosted CAD/firmware gates for that evidence.
No changes to electrical source are required to inspect this prototype.

## Remaining decisions and next bounded task

This closes the **initial dimensioned CAD deliverable**, not mechanical release.
Actual connector-width/cable/board measurements, print/machining/material/rivet/
fastener processes, capture strength, insertion/withdrawal forces, tilt/deflection,
controller mounting and cable-end routing need independent fit/process review
and unpowered validation before acceptance. Do not demand a tested first board
before allowing a separate pilot-risk review; neither pilot manufacture nor
body use is approved here. No order or supplier contact occurred.

The next independently actionable source slice is the **actual controller-side
termination and powered-off console/interface plan**: one exact connection
architecture and its back-power/startup restrictions, using the existing
logical pin map and K1 cable free ends. Keep the specific K2 physical fit list,
#48 capacitor evidence and #45 factory/fixture/coupling conditions open rather
than treating another green check as release. No new PCB mounting holes or
repeat HTSW migration.

## Primary references

[1] Samtec IDSX assembly drawing AE, sheet1, read as drawing including cable exit:
https://suddendocs.samtec.com/prints/idsx-xx-x-xx.xx-xxx-xxx-mkt.pdf
[2] Samtec IDSD catalog, F-226, section diagram and insertion range:
https://suddendocs.samtec.com/catalog_english/idsd.pdf
[3] Ubuntu 24.04 OpenSCAD package (2021.01-6build4):
https://packages.ubuntu.com/noble/openscad
[4] OpenSCAD documentation / official CLI implementation:
https://openscad.org/documentation.html

Dimensions not explicitly attributed to a manufacturer are K2 design choices,
not approvals, published part tolerances, a material certificate or test results.
