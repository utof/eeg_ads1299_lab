# CH1N source-corridor repair

## Scope and identity

This continues the input review in PR #65, from main
`779b8efaa0c5e1b84cdbee49a07b053e3debe7b7`, tree
`0a2e5eabd627dbabd26706e046540f44ab9852f6`. It edits the authored PCB, never the
parking-grid importer. The repair branch is `fix/ch1n-corridor`; inspect its
live PR/head/checks/review until merged, then use current main.

The board SHA256 changes from
`232b7c68a63ae13aebcf71f8c0b1f210421c30452a1afc7b7c86dc1c118b23a3` to
`5da65b4307f0336883da9aeae48711b28c1944ec587f5d3174f12db4e9921875`.
`checkpoints/20260930_ch1n_corridor.json` records exact removed/added forms,
itineraries, preservation checks, and remaining crossing locations. This is
geometric design evidence, not extracted capacitance or physical qualification.

## The actual change

CH1N_DUMMY still connects J2.2 to R2.1. Its middle corridor moves out of the
DNP-branch region to x=34.9 mm on In2. The entry is front copper to a via at
(31, 30.75); the inner path runs above the input bank, down its right side,
then back to the existing via at (31.7, 43). The original final front connection
to R2 and that second via remain byte-identical. No footprint moves.

This removes all four previously identified CH1N B/In2 projected overlaps:
IN2P, IN3P and IN4P branches to DNP diode pads, plus CH3N_DUMMY. The native
full-width screen finds no overlap between this net's In2 traces and any
foreign back-layer track or pad. The eight main R/C/U1 itineraries and every
DNP branch remain unchanged. DNP devices are still unpopulated; no protection
or filter redesign is implied.

The complete input crossing inventory drops from 13 to 9 unique net-pair
locations (22 to 18 raw segment pairs). The remaining three CH2N/input overlaps
and six AVDD/input overlaps are the same previously recorded locations, not
new crossings or automatically accepted coupling performance. See the JSON.

## Why this is not an all-front route

Existing front routing obstructs a compact all-front connection. A disposable
0.025-mm grid trial found a roughly 47.8-mm front route around the header; that
trial is not a proof of the globally shortest possible layout. Another tested
32.4-mm F/In2 candidate threaded front copper between other channels' resistor
pads. The selected route avoids that new front-layer adjacency, at the cost of
about 1.5 mm more trace than that candidate. No unrelated copper was pushed.

| CH1N authored trace sum | Before, mm | After, mm |
|---|---:|---:|
| F.Cu | 10.882 | 15.296 |
| In2.Cu | 12.597 | 18.588 |
| B.Cu | 0 | 0 |
| Total | 23.479 | 33.884 |
| Through vias | 2 | 2 |

**The route is longer by 10.406 mm.** It is not a timing, noise or length-matching
improvement claim. The In2 span is a deliberate corridor, not described as a
short local escape. In1 ground faces both F and In2; at the crossing-free new
In2 corridor there is no foreign B track immediately underneath. Where it
projects across other channels' front fanout, In1 is physically between them.
This removes the specific overlap arrangement without claiming zero fringing,
parallel-route coupling, package/cable effects or a qualified stackup.

The two vias are physical F-B through vias connecting F/In2 traces. Unused barrel
parts are not extracted. No blind vias, plane split, blanket stitching, matching
meanders, component/value changes or new layer assignment are introduced. The
In1 filled ground remains one region, but that alone is not proof of a good
return path. Dielectric spacing, actual source spectrum and physical performance
remain unresolved. Do not map these lengths to picofarads or measured CMRR.

## Preservation and native checks

Exactly nine old segments and one old via are removed; seven segments and one
via are added. All 68 footprint forms and 696 retained track/via forms remain
byte-identical, including the last two CH1N front segments and resistor-side
via. The other non-zone board forms and zone source settings are unchanged;
only the native-filled polygon changes. There are now 582 segments, 122 vias,
68 footprints and 245 pads. New tracks are 0.20 mm; the new via is 0.60/0.30 mm.
No signal tracks were added on In1. No schematic, BOM, firmware, model, dependency,
clearance, severity, exclusion or approval gate changes.

Raw source and native item coordinates/nets/layers/straight-segment lengths were
cross-checked for all 704 track/via items. The old and new main-input itinerary
items are byte-identical. A separate determinant centreline screen re-enumerated
the nine remaining crossing locations. These checks complement, not replace,
native refill, parity and DRC. They are analysis checks, not extra project tests.

## Test-first policy and fault controls

Test-only `3f75b5e2b33b04b239be6c7c549bac32e0d6f59d` preserves one intended native
failure on the unchanged board: the new CH1N policy sees four foreign back-layer
partners and 0.012736 mm2 of uncovered trace projection, while ordinary native
DRC still reports 0 parity / 0 other / 0 unconnected. The two existing CH1N
connectivity/cut cases selected alongside it pass. This is one new failing
case, not three failures.

The new guard lives in the already-snapshotted `tests/test_pcb_placement.py`.
It allows only F/In2 routing, at most two vias, no positive-area In2/foreign-B
copper overlap, and full-width projection onto the fresh single In1 filled
region. Native integer polygon Booleans include full trace shapes, not just
centreline samples or arc endpoints. The tiny residual-area limit is the
existing output screen's 0.00001 mm2 geometric tolerance, not a noise limit.

Only CH1N's own through-pad and via clearance shapes are exempted from the
reference mask: the actual zone clearance of 0.25 mm plus 25 um approximation
margin, with native shape error 5 um. Those physical openings still exist. No
foreign hole or added reference window is waived. Ground copper outside the
filled zone is not added to this mask, so the screen can conservatively reject
geometry needing explicit review. It does not evaluate every parasitic field.

The first proposed corridor passed DRC and removed the overlaps but failed the
reference guard at a neighboring via-clearance edge. Moving its inner vertical
run outward corrected the copper, without relaxing the mask or tolerance.
The selected route then passed the complete new focused set:

- One canonical CH1N policy case.
- Three harmful, still-connected native copies: restore the original crossing
  route; move the new inner corridor to B; add a small In1 pour window beneath
  the inner corridor. Each freshly refills and passes ordinary DRC, but fails
  the intended policy.
- Three accepted controls: reverse endpoints, subdivide a trace, and put the
  same small pour window away from CH1N. The last is benign only for this scoped
  guard, not a blanket approval of arbitrary plane edits elsewhere.

These are **seven added native cases**, not an exhaustive mutation score or
physical experiments. The focused nine-case run also includes the two existing
CH1N cases; do not add it again to the complete suite. The all-net cut test now
cuts the new exposed CH1N trunk rather than an obsolete UUID; its native
connectivity expectation is unchanged.

## Execution, review and next task

Fresh source-capture run 36701686057 checked out exact main779b8efa from GitHub.
The clean baseline ordinary+schematic gate passed with 1,091 ordinary tests,
14 subtests, 145 native KiCad cases and the 22 console subset; branch coverage
86.06%, existing 71% floor unchanged. That baseline command did not request all
98 native/integration cases or an S3 target build. Read the repair PR's live
final-head results and independent review for subsequent acceptance; neither
this document nor a queued workflow is a pass.

Reproduction uses the existing locked commands:

```sh
uv sync --locked --all-extras
uv run --locked --all-extras python -m pytest -q tests/test_pcb_placement.py -k ch1n
uv run --locked --all-extras python -m tools.check --native --schematic
```

The engineering basis remains the source-bound PR65 input review. TI SCAA082A,
sections 1.4, 1.6 and 2.2/2.5, provides general coupling/reference/slot guidance:
https://www.ti.com/lit/an/scaa082a/scaa082a.pdf . Relevant page images were
inspected. It addresses high-speed layout and is not a quantitative low-frequency
EEG crosstalk criterion or manufacturer millimetre limit for this input. KiCad9
native shape/refill/DRC is used for geometry and connectivity, not field extraction.

**Next: dispose of the remaining nine upstream input/supply overlaps together**,
choosing one bounded combined repair or an explicit stackup/bench-test disposition
rather than endless single-crossing iterations. The routes involved are CH3P,
CH3N and CH4N against CH2N/AVDD; no filtered-INn branch remains among these nine.
Then advance the finite stackup/component/mechanical/interface decisions in
#45/#48. The 4.5-mm DNP-branch imbalance and other source/cable/parasite assumptions
remain separate characterization issues. No purchasing, fabrication, powered
connection or body-use authorization is granted.
