# Ground plane and supply routing — unfinished bench PCB

This continuation recovers the reference/VCAP draft and adds actual ground and
supply copper. The interrupted turn's later 35-airwire board was not available;
only its description and native-tool receipt survived. This candidate was rebuilt
from the preserved reference/VCAP board, not presented as that missing file.
No schematic, BOM, firmware, component/footprint geometry, model, dependency or
hardware/purchasing/body-use approval changes here.

## Actual copper and its limits

The editable source remains `hardware/rev_a/layout/rev_a.kicad_pcb`. The existing
68 footprints, 245 pads, positions, values, MPNs, eight DNP choices, schematic
paths and all previous 140 tracks/36 vias are preserved. This slice adds 159
track segments, 67 through vias and one natively filled ground zone: totals are
299 segments, 103 vias and one zone. The provisional 78 x 58 mm outline and four
enabled copper layers are unchanged; fabrication materials, layer thicknesses,
impedance targets, mounting and enclosure decisions are NOT finalized.

The GND region is on In1.Cu, inset 0.5 mm from the outline. Its requested copper
clearance is 0.25 mm; thermal gap/bridge width are both 0.3 mm. KiCad's actual
9.0.2 zone filler generates one connected copper region, including its clearance
holes. All 74 ground pads have native connectivity, through existing returns or
new local front-copper spokes and 0.6/0.3 mm through vias. All tracks on In1 are
on GND. One connected region does not establish low impedance, a measured return
current distribution, noise performance, or adequate manufacturing tolerances.

The positive supply networks are also connected:

- VIN_5V_AFE: J1 supply contact to the regulator's IN/EN and input capacitor bank,
  and the upstream side of the unchanged 10-ohm analog feed resistor R11.
- AVDD: R11's downstream side to the analog supply/AVDD1 bypass groups, the
  required unused ADS1299-4 input pads and optional-clamp upper-rail pads.
- DVDD: regulator OUT to its local capacitors, digital bulk/bypass network and
  ADS supply pins. This daughterboard regulator still does not power the MCU.

R11 is not bridged, and the two rails retain separate net identities. Most rail
branches run on In2.Cu; the header-to-VIN trunk uses B.Cu, while local pad and
capacitor connections use F.Cu. New supply widths range from 0.2 mm at tight
pin escapes to 0.5 mm at the header trunk. These are draft choices, not a
qualified copper-temperature, voltage-drop or transient-impedance calculation.
The DNP clamps remain DNP even though their rail pads are routed.

All existing VREFP and VCAP1–4 positive-side front-layer connections are untouched.
This does NOT imply every new supply bypass is via-free: AVDD1's escape uses a
via to avoid crossing VCAP3. Its complete loop length/return geometry remains
part of independent electrical layout review. Connecting the net is not enough
to settle the high-frequency decoupling quality.

## Independent native evidence, including adverse cases

Native DRC distinguishes three arrays throughout this work:

| Candidate | Schematic parity findings | Other DRC findings | Unconnected items |
|---|---:|---:|---:|
| Preserved reference/VCAP source | 0 | 0 | 134 |
| Rebuilt ground plane | 0 | 0 | 82 |
| Rebuilt ground plus three supplies | 0 | 0 | 35 |

Every canonical run still returns exit 5: digital, connector and BIAS connections
are unfinished. There are no DRC exclusions or loosened clearance rules. Initial
routing attempts produced real crossings, adjacent-pad clearances and via
conflicts; copper was moved instead of relaxing those rules. None of the counts
is a fabrication acceptance waiver.

Five initial tests failed on the preserved board before copper was added: no
filled plane and airwires on GND, VIN, AVDD and DVDD. The new checks use KiCad's
connectivity engine rather than an authoring-script list of expected routes.
The existing eight cut-capacitor-return tests still isolate their negative
terminals even with a plane present. Five cut-sensitive-positive-route tests and
the prior input-route fault remain active.

Three new rail-cut tests remove exposed supply copper and require an airwire
on that rail while schematic parity stays correct. The initial DVDD fault cut
a short track fully covered by its pad, so it correctly did NOT disconnect; that
ineffective fault was replaced with the adjacent exposed segment, not used as
false evidence of detection. All three effective cuts are rejected.

Plane faults remove the entire zone or clip its source outline while leaving
the old full-board fill cached. An additional control removes the cached fill
while keeping a valid outline. The former cases must expose ground airwires;
the latter must recover actual connected copper by a fresh native refill.
An observed pre-fix failure showed why the old DRC-only helper was insufficient.

## Refill is part of validation, not a decorative preview

KiCad distinguishes a zone outline from physical filled copper and requires
refill after edits. The existing board-test helper now runs the actual pinned
native filler before DRC on every copied board containing a zone. It checks the
native version, retains a subprocess log and records zone net, layer and region
count. Fault boards are refilled independently, never using the canonical result.
Unchanged canonical results are reused per test module to avoid repeating the
same fill for every pad/net assertion; these are not claimed as extra unique
native experiments.

The helper uses the system Python belonging to the installed KiCad package.
`KICAD_PYTHON` can explicitly select that interpreter for a recovered local
installation; the default is `/usr/bin/python3`. Missing bindings, wrong native
version, timeout or failed fill are failures, not skips. This is a small test
adapter, not a new project dependency, CAD framework or verification runner.
`tools.check --schematic` remains the entry point. The power test joins the
before/after source snapshot (48 inputs); a changed-test fault was observed
failing before that dependency was added.

The native binding was recovered from the existing pinned Debian KiCad package
using disposable PR #59, closed without merging. Its tool receipt establishes
availability only. This design's actual refill, DRC and fault results establish
its separate local execution evidence. Native libraries/caches are not included
in the design delivery.

## What remains

Finish the 35 digital, connector and BIAS connections, review planes and return
paths under those new routes, finalize component/lifecycle and interface/power-loss
choices, then complete the full layout and manufacturing review. The previously
documented bulk-capacitor qualification target has not silently replaced the old
BOM. No physical voltage, current, noise, temperature or powered-off behavior is
measured by these native CAD checks. Do not fabricate or connect a person from
this incomplete draft. All existing approval gates remain false.

Primary tool basis: KiCad 9 PCB Editor documentation, Working with zones and DRC:
https://docs.kicad.org/9.0/en/pcbnew/pcbnew.html
