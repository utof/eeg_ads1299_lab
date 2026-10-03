# P3 auxiliary routing: connected draft, not a manufacturing release

P3 continues the authored P2 board, not an importer output. The local base is
`4731c4193b2006b72861c6d1acae90f3584678f8`, the already-reviewed parent included
in live main `70e8d41bd60d597ecc284859d7e1f71370dcd190`; both have tree
`6c81cadb2e9b0afcd92d560245e2cb621ce7619b`. No different main tree was assumed.
Read live main/open PRs before continuing. At authoring, P3 is local on
`feat/auxiliary-routing-p3`; publication and independent exact-head review must
be established separately, not inferred from this file or a successful local test.

## What changed

All **85 remaining connections across 39 nets** now have native copper paths:
global HOST/MCU/AFE supplies, VIN5 feed, UART, nine directional bus lanes on both
sides, sense, supervisor, arm, ready and stop wiring. Native KiCad 9.0.2 fresh
refill/DRC reports **0 parity / 0 other findings / 0 unconnected, exit 0**. This
is the first completely connected auxiliary draft, not powered verification.

All **52 P2 footprint forms, 62 prior track forms and 39 prior via forms remain
byte-identical**, as do both ground-zone definitions after removing only filled
polygon cache forms. The original AFE board, C4 service cable plan, F1 firmware,
K2 mechanics, BOM, schematic, project rules and dependencies are unchanged.
The committed preservation fixture records original P2 UUIDs/raw-form hashes,
not hashes generated from the new routing. Native fills are refreshed on copies.

New copper: **585 segments and 119 through vias**. Final auxiliary totals:
**647 segments, 158 vias, 52 footprints and 216 pads**. Signal routing uses front
and In2 only; In1 remains the two separate ground references, and no signal is
routed on the back. New vias retain 0.60/0.30 mm diameter/drill. Local escapes
and ordinary signals are 0.20 mm; global supply branches use 0.30 mm and VIN5
uses 0.60 mm where the existing pin-field geometry allows, with explicit narrower
escapes. Widths alone do not qualify current, voltage drop, transient loading
or the final manufacturing process. No clearance or isolation rule was changed.

The all-layer HOST/TARGET barrier and independent 3 mm native separation remain.
Mounting and termination allowances, asymmetric H4 and separate AFE feed/sense
nets are preserved. Supply domains have not been joined. Reference labels remain
on fabrication layers; final assembly artwork is not complete.

## Routing and return-path review performed here

Front and In2 routing were selected to stay on opposite sides of the same In1
reference within each domain, rather than switching between two unrelated
planes. That avoids intentionally transferring the reference from ground to a
power plane. It does **not** establish impedance or a negligible return loop:
actual dielectric spacing is not confirmed, through-via stubs remain, and
antipad shape and nearby copper affect the fields. Henry Ott's original return-
path discussion distinguishes this same-plane case from changing to another
plane [1]; TI likewise emphasizes actual return paths rather than net labels [2].

The first connected attempt had small ground voids beneath several new routes.
New copper was locally rerouted away from those regions. Two signal vias near
through-hole returns also created isolated ground slivers; moving only those
new vias restored exactly **one filled region per domain**, without changing
zone/island policies. A new MCU supply escape crossed U111's VCC pad, providing
an unintended alternate path around the old C115 bypass branch. It was moved
around that pad. The original native bypass-cut checks still detect all fifteen
removed local paths; their expected missing connections were not waived.
Nineteen duplicate new trace forms and eight unnecessary new vias were removed.
Abandoned routes and failed DRC attempts are not counted as successful results.

The **existing P2 proof is unchanged in strength**: all fifteen local supply
paths remain short, with continuous 0.20 mm In1 reference corridors under their
actual segments and between the local ground vias. It still uses native filled
polygon subtraction, not endpoint chords. The historical restriction that every
board trace belong to the partial P2-only net list is retired: ground-specific
width/via/access checks remain, while P3 adds its own global-route proof. Cut and
bend mutation selectors now identify the intended original bypass, not whichever
new short escape happens to share the pad coordinate.

For global routing a supplemental **continuous central 0.10 mm reference-spine
screen** follows every actual segment. Same-net through-contact copper silhouettes
expanded by 0.35 mm are explicitly excluded: these contacts necessarily cut the
ground, with the existing 0.25 mm clearance and minimum-width fill shaping. This
bounded geometric screen is **not full trace-width coverage or a field-solver
result**, and is not substituted for the stronger P2 bypass checks.

The proof also reports the entire trace-width projection, without deleting its
findings: **18 edge slivers remain**, totaling approximately **0.0022884 mm²**
(maximum single residual about **0.0006758 mm²**) outside the declared own-contact
exclusions. Their UUIDs/net/layer/areas are in the checkpoint. They are near hole
clearances rather than breaks across the checked central spine; a source-CAD
measurement at these scales is not a fabricated tolerance guarantee. Independent
layout review must dispose of these and the layer-transition/edge-rate tradeoffs
before any pilot release. P3 does not claim completely uninterrupted full-width
reference, measured EMC/noise, or actual isolation qualification.

The per-net copper-length table is an **inventory sum**, including branches;
it is not path delay or extracted parasitics. MCU_SCLK and MCU_CLKSEL carry
roughly 85.5 and 89.0 mm of authored copper respectively; the console TX route
is also relatively long. These and the supply/sense corridors are explicit
review targets, not evidence that a convenient routing pattern is electrically
optimal. Further shortening must preserve the checked P2 local copper and the
mounting/cable allocations. No automatic length matching or arbitrary meanders
are proposed as a substitute for that review.

## Reproduce and falsify

Use the pinned environment and real native tools:

```sh
uv sync --locked --all-extras
uv run --locked --all-extras python -m tools.check --schematic
```

The new completion test first failed on the original 85-airwire board in
`9d0ac97`, before any route was added. P3 additionally removes real terminal
escapes on **each of the 39 completed nets**, freshly refills each copy and
requires the corresponding native disconnection with schematic parity retained.
Only expected dangling trace/via diagnostics are allowed on those damaged copies.
One cut per net is not an exhaustive mutation or physical fault score.

A real ground-only void beneath the routed AFE_SCLK segment leaves native
connectivity and ordinary DRC clean, but fails the new reference-spine proof.
The same-size void away from routing passes; reversing/subdividing the signal
also passes. Existing P2 ground/bypass cuts, reference voids, P1 isolation and
mount/access checks remain active. Source preservation and all new test inputs
are included in the shared verification entry point; there is no second project
orchestrator or required authoring helper. The 450-second CAD-batch limit and
individual native timeouts remain unchanged.

Final local/hosted outcomes must be tied to the actual finished head. A source
archive, an inherited CI pass, or this document is not a new hosted run/review.
No native command in this slice is a physical electrical experiment. No new
Arduino build or full native-integration result is implied by targeted PCB checks.

## Next bounded task

**Independent review of the fully connected auxiliary layout**, emphasizing
return/antipad geometry, long clock/control routes, supply necks/drop, sense
coupling, layer construction, mounting/termination access and the C1/C2 disabled
state limits. Resolve a concrete finding with a scoped, failure-first correction;
do not regenerate either board or repeat F1/J3. Complete source publication and
exact-head CI/review before calling the P3 candidate delivered on main.

The 42.2 kΩ pull budget, rail-detector delay/overdrive, broken feedback, actual
leakage and analog-source behavior remain conditional. Supplier stackup, #48
capacitor evidence, fixture/measurement floor, actual cable/crimp/material and
whole delivered budget remain open. No fabrication, purchasing, powered setup
or body use is approved. No component or budget allowance changed here.

[1] Henry Ott, *PCB Stack-Up, Part 6: Return Path Discontinuities*, original
engineering note, checked 2026-10-03:
https://hott.shielddigitaldesign.com/techtips/pcb-stack-up-6.html
[2] Texas Instruments Precision Labs, *PCB trace as a wave guide*, checked
2026-10-03: https://www.ti.com/video/6307562268112
