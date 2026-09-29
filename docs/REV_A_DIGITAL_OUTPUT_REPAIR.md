# MISO/DRDY output corridor repair

## Scope and identity

This repairs the exact authored PCB reviewed in PR #63, main
`f834221a092f78dee4191305a3c3a8a03def0283`, not the parking-grid importer.
See `checkpoints/20260930_digital_output_repair.json` for source identities,
coordinates, native item UUIDs, lengths and scoped reference-policy results.
The board SHA256 after this repair is
`232b7c68a63ae13aebcf71f8c0b1f210421c30452a1afc7b7c86dc1c118b23a3`.
The live repair branch is `fix/digital-output-corridor`; inspect its PR/checks
until merged, then continue from main. This document does not anticipate a
successful final-head CI or review that has not yet happened.

## Actual copper change

Both long output spans move from B.Cu to F.Cu. Short In2.Cu escapes remain
beside U1; F and In2 face the same continuous In1 ground conductor. The long
F routes are therefore separated from routed In2 copper by ground, unlike the
six unshielded B/In2 projected crossings recorded in the preceding review.
There is no B.Cu track on either output after this repair. This does not imply
zero coupling, controlled impedance, optimal return paths or measured timing.

An all-front path was blocked by existing front fanout, including CLKSEL.
Rather than move unrelated signals, each output uses two through vias and a
bounded local In2 escape. These are physical F-B vias connecting F/In2 tracks;
the unused barrel portion is not modelled. The original MISO source via stays
byte-identical. The former shared MISO/DRDY source clearance opening is gone:
a freshly refilled and unfractured native plane reports four distinct openings
for the four output vias, not one merged pair. This is a local fill observation,
not a guarantee of return impedance. Other SCLK/CS and CLK/START groups remain
unchanged review items. No ground split or blanket stitching rule was added.

| Output | Before F / In2 / B, mm | After F / In2 / B, mm | Vias before / after |
|---|---|---|---|
| MISO | 5.180 / 0 / 32.565 | 28.474 / 7.268 / 0 | 1 / 2 |
| DRDY | 20.824 / 0 / 15.675 | 36.257 / 7.875 / 0 | 2 / 2 |

These sums include every authored segment on the net, including any prior
branch/overlap; they are not shortest conductive itineraries and exclude barrel
and pad spreading. Total DRDY trace grows from36.499 to44.132mm; do not call
that a length/timing improvement. MISO changes37.745 to35.742mm. The two long
parallel front runs have0.45mm centre separation (0.30mm copper-edge gap) where
they run together. Neither that gap nor the longer DRDY path is a qualified
crosstalk or delay specification; edge rates, loads, harness and dielectric
stackup still need release/bench review. The change removes the specific
unshielded layer arrangement without claiming that every metric improves.

All68 footprint forms and all245 pad positions remain unchanged. Exactly20 old
output segments and two old output vias are removed;23 segments and three vias
are added. All680 retained track/via forms and every other non-zone board form
remain byte-identical. Totals are584segments/122vias. The sole GND zone source
settings are unchanged; only native filled copper is updated. No signal tracks
were added to In1. Tracks remain0.15mm, new vias0.60/0.30mm. No schematic, BOM,
firmware, model, dependency, clearance/severity/exclusion or approval change.

## Test-first boundary and controls

`c33d578` preserves two actual native failures on the original board: MISO and
DRDY violate the new local layer policy while canonical DRC remains0/0/0.
The native guard is in the already-snapshotted `tests/test_pcb_placement.py`.
It requires F-only long spans, at most two output vias, at most10mm of In2 in
the ADC-side rectangle, and a single filled In1 GND region. Those bounds are
local design decisions, not manufacturer frequency/noise limits. The
rectangle test uses endpoints only for straight In2 tracks; non-straight In2
tracks are now explicitly unsupported and rejected, not silently bounded by
their endpoints.

It also subtracts the actual native filled ground polygon from each output's
**full trace-width projection**, using integer polygon Booleans, not sparse
centreline probes. Only that output's own through-pad/via clearance shapes are
exempt. Their margin is the actual zone-local0.25mm plus25um for polygon
approximation (native shape error5um); it is not a general reference-gap
allowance. Other-net voids and added plane windows are not exempted. GND pads
and tracks outside filled copper are not added to the reference mask, so the
check can conservatively reject copper that needs explicit review.

The initial nine new native cases passed after repair: two canonical guards, two connected
wrong-layer copies, one connected reference-window copy, and four benign
reversal/subdivision copies. Each modified board is independently refilled
and DRC checked. The wrong-layer copies move each short escape to B without
breaking connectivity. A small pour-only keepout beneath both long front runs
leaves one connected ground region and normal DRC0/0/0, yet both full-width
reference checks fail. Benign edits preserve acceptance. Existing MISO/DRDY
cut-track probes now target the new exposed trunks; the test expectation is
unchanged. The initial nine cases are part of the full native suite, not added to
its total again. No exhaustive mutation score or physical experiment is claimed.

Development found and corrected native clearance collisions, an initially
wrong assumption about zone clearance, and a mutation-probe bug: native vector
getters must be copied before reversing track endpoints. Actual clearance was
read, not relaxed; test expectations were not weakened to accept zero-length
or colliding tracks. Intermediate failed/time-limited runs are not passes.

## Independent review correction: curved-escape loophole

Codex finding4139341193 on8bde876 identified that endpoints do not bound a
curved In2 track. Test-only21f97c9 reproduced the actual native failure: a DRDY
arc bows to y=36.8mm while both endpoints remain at y=36.4mm, inside the local
rectangle. The whole In2 route is8.292mm, ordinary DRC is0/0/0, full-width
reference is intact, and the old guard incorrectly accepts it.

Fix1c208f6 makes `inner_tracks_straight` an explicit gate field. Non-straight
In2 geometry is rejected until separately designed/reviewed support exists;
this is not a claim to test an arc's complete centreline bounds. Both canonical
outputs and the new native arc regression then passed. The final addition is
ten native cases total (initial nine plus this arc), not ten more after nine.
The copper is unchanged by this review fix. No length/clearance/error margin
was enlarged to pass the arc.

## Verification and next task

Fresh KiCad9.0.2 refill/DRC on the candidate has0parity/0other/0unconnected and
exit0. The complete baseline gate passed on exactf834221a. The initial focused
nine-case result and three-case review retest are separate from final-head
verification: read the
live PR's final local/hosted reports and independent review before merge.
One local8bde876 combined gate reached the existing300s native-suite timeout;
it is retained as a failed run, not a pass. Its hosted five-job gate completed
successfully, but that earlier head does not validate the later review fix.
No project process timeout or engineering threshold was relaxed.
A clean source identity, green software tests and native DRC are not professional
or physical electrical qualification. Normal final gates include the existing
AVDD1/VCAP, all-net cut and schematic-parity controls; do not substitute only the
new output tests for them.

After this scoped repair is reviewed/merged, perform the input P/N geometry and
coupling review, separately connector-to-resistor and resistor-to-ADC. Preserve
the AVDD1 repair and its documented neighboring-path tradeoffs. Keep#45/#48 open:
stackup/mechanical/assembly, capacitor lifecycle/effective-C, real console/rail-loss
behaviour and delivered budget remain unresolved. No purchase, fabrication,
powered connection or body use is authorized.

The engineering basis remains `REV_A_DIGITAL_RETURN_REVIEW.md` and its primary
TI sources. This repair adds native geometric evidence, not new vendor claims.
