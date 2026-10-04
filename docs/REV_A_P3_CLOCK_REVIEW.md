# R1: P3 clock-route and repository-handoff review correction

Base: published PR81 head `9d22a6c21eee1bd8983ba61fb4c459870182e734`, tree
`751d8c8f1058f6d5663e215ce908e34bb5e6f46a`. This is the actual GitHub source,
not the earlier local-only d78 commit. Read live PR81 before assuming a merge.
Review4174991282 requests a shorter clock route separated from MISO;
review4174991286 requests an accurate published-source handoff.

## Scoped copper change

Only MCU_SCLK tracks/vias are replaced. The existing 52 footprints and every
other net's copper are unchanged: 831 non-clock copper/footprint forms retain
exact bytes. The main AFE PCB, J3, auxiliary schematic/BOM, C4 cable, F1 firmware,
K2 carrier, clearances, reference-checker exclusions and release gates are not
changed. Fresh fills update the two original In1 ground regions without changing
their settings. There are no added components, termination resistors or meanders.

| Read-only native geometry | Reviewed P3 | R1 candidate |
|---|---:|---:|
| All MCU_SCLK planar trace length | 85.491637 mm | 71.875101 mm |
| Clock through-vias | 5 | 4 |
| Minimum same-layer clock/MISO trace-edge distance | 0.230172 mm | 0.638848 mm |
| Complete board segments / vias | 647 / 158 | 643 / 157 |

The clock is about15.93% shorter. The unnecessary far-right/bottom detour is
removed; all clock endpoints remain J102.18 and U102.2. The replacement has
17 segments and4 standard0.60/0.30mm vias, all0.20mm tracks on F.Cu/In2.Cu.
The old clock contained21 segments and5vias. The measurement includes all clock
trace centerlines and thus cannot conceal extra branches by measuring only a
shortest path. It excludes vertical via length, pad/package paths, the other
board and cables. Clearance uses native SEG-to-SEG distance less half of each
trace width, across every same-layer clock/MISO pair, including nonparallel
ones. It does not calculate via/pad coupling or trace impedance.

This is a conservative, bounded repair around the frozen neighboring copper,
not a claim of the mathematically shortest route. It still changes layers and
contains parallel portions. The75mm/4via/0.60mm targets are explicit regression
constraints for this repair, NOT manufacturer signal-integrity limits. Actual
edge rate, full-channel loading, layer construction, return transitions and
ringing remain open. A generic source resistor has not been invented to dispose
of those unknowns. The independent reviewer must assess this concrete revision
before the original concern is marked resolved remotely.

## Ground reference is retained, not waived

The first disposable candidate passed ordinary DRC but a newly positioned via
introduced additional reference-edge area under STOP_N. The existing P3 checker
correctly rejected it. Moving only that new clock via to(74.10,49.90)mm removed
the added gap; no pending polygon, numeric tolerance or same-net-contact exclusion
was enlarged. A second trial was still0.0096mm short of the newly selected MISO
gap target; the final via position satisfies it without relaxing that target.

A fresh native refill/DRC of the final candidate gives0parity/0other/0unconnected.
The existing P3 global reference test and all15P2 bypass checks pass. Original
full-width pending regions remain electrically unapproved. Own-contact clearance
holes, finite plane thickness and real return currents are not qualified by these
geometric tests. The untouched supply/sense, MOSI, MISO, CLKSEL and UART routes
retain their earlier review limitations.

## Independent regression controls

Test-only commit `33a070a` observed three native failures on the unchanged
published PCB:85.49mm exceeds75mm,5vias exceeds4, and0.230172mm is below0.60mm.
The checks then pass on the new copper. The before-review fixture preserves the
26 original clock forms and an aggregate digest of all831 unchanged forms.
A native original-route restoration remains DRC0/0/0 but fails all three geometry
targets. This distinguishes a connected circuit from this requested routing
improvement. Native reversal and exact subdivision of the new route preserve
both metrics and DRC0/0/0. All39 original terminal-cut tests remain active.

Two process-double cases also exposed omission of the new test/fixture from the
shared verification source snapshot; they are now included. The initial attempt
to select those two cases collected no tests and is NOT red-test evidence; the
subsequent explicit parametrized cases both failed before the snapshot correction.
No separate verifier framework or dependency is introduced. Source snapshots,
geometry tests and process doubles are not physical experiments.

## Publication and continuity

P3's eight source states were published through the GitHub object API, with each
intermediate tree verified. Commit metadata changed during that earlier transport;
the published9d22 tree equals the local d78 tree. This correction is a normal
local descendant of the exact published9d22 commit, whose eight remote commit
objects were independently reconstructed and verified against their Git IDs.
This is not a new branch of invented ancestry or a second reconstruction of the
P3 board. GitHub-write availability and final reviewed/published head must be
reported honestly; the local bundle alone does not update PR81.

The handoff now distinguishes the published P3 base from these new review fixes.
It no longer directs an agent to republish the already published P3 state, nor
claims85connections remain. Original published-head CI passed, but that does not
count as CI or review of this correction. Read the exact corrected-head results.

## Next bounded step

Publish the corrected source to PR81, run exact-head CI and request renewed review
of these two findings. Do not merge merely because the old head was green.
After those findings are accepted, review the AFE_DVDD feed/return voltage-drop
budget and the remaining full-channel edge/return assumptions. No routing
rebuild is required. Existing#45/#48 stackup, capacitor, mechanical, fixture,
source startup and delivered-budget conditions remain open. No purchasing,
fabrication, powered-connection or body-use permission changes.
