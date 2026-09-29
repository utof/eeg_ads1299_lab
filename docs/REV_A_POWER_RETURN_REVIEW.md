# Rev A supply/bypass geometry review

**Dated review: 29 September 2026.** Source `a4ac32c53e7e06eb3272db270afb1f3ac11a8c20`,
tree `4147e35011321cfdd1fd4263ede3700f409107fc`. The authored board is
`hardware/rev_a/layout/rev_a.kicad_pcb`, SHA256
`71b066ed8c9842035553bbc125b5c428877d180b2b2ef66ba986a2032830899f`.
No copper, component, schematic, firmware, model, dependency or approval flag was
changed by this review. This is the first bounded supply-loop review, not closure
of the whole electrical review or a physical noise measurement.

## Disposition: rework AVDD1's local bypass cluster next

The earlier ground/power note already called out the AVDD1 escape for review.
The new contribution is the measured source geometry, exact component/track
identities, the shared-supply junction, and a specific next rework boundary.

**PR-AVDD1-01: revise the local U1.54/53 bypass arrangement before fabrication.**
U1.54 reaches its designated 1 uF capacitor C16 through an 11.936 mm explicit
trace-centreline itinerary, including two vias and 8.908 mm on In2. The 100 nF
C27 path is similarly indirect. The C16 negative terminal and U1.53 enter the
GND plane at vias 9.325 mm apart. A neighboring AVDD56 branch joins the positive
trunk before either designated bypass is reached. These observations differ
from TI's preferred local bypass-before-planes arrangement [1,2]. They justify
a focused layout revision, **not** a claim that a measured noise specification
has already failed or that 11.936 mm is a universal prohibited length.

There is also a shorter, shared path from U1.54 to C14: 6.486 mm with two vias.
Therefore this finding is **not** 'AVDD1 has no bypass capacitor'. All these
capacitors share the AVDD net. Their functional `ContractRef` names are useful
review labels, not electrical isolation or proof of which capacitor supplies
an instantaneous current pulse. C14 has not been reassigned to the C16 BOM role.

## Measured positive-side itineraries

All lengths below are calculated from the source, not measured on hardware.
Sum `hypot(dx, dy)` for the ordered track portions in the accompanying
[geometry record](checkpoints/20260929_power_return_geometry.json). A transition
uses an actual same-net via at the same coordinates. Via barrels, pad spreading
and overlap shortcuts, capacitor internals and ground-plane current distribution
are excluded. These are explicit itineraries, **not shortest electrical paths,
complete loop lengths, extracted inductances, or propagation-delay estimates**.

| U1 supply pad | Capacitor reached | F.Cu (mm) | In2.Cu (mm) | Trace sum (mm) | Positive-path vias |
|---|---|---:|---:|---:|---:|
| 19 AVDD | C11.1 / C_AVDD_19 | 2.182 | 0 | 2.182 | 0 |
| 21 AVDD | C12.1 / C_AVDD_21 | 1.963 | 0 | 1.963 | 0 |
| 22 AVDD | C12.1, shared alternative | 2.463 | 0 | 2.463 | 0 |
| 56 AVDD | C14.1 / C_AVDD_56 | 1.913 | 0 | 1.913 | 0 |
| 59 AVDD | C15.1 / C_AVDD_59 | 1.950 | 0 | 1.950 | 0 |
| **54 AVDD1** | **C16.1 / C_AVDD1_54** | **3.028** | **8.908** | **11.936** | **2** |
| 48 DVDD | C17.1 / C_DVDD_48 | 2.063 | 0 | 2.063 | 0 |
| 50 DVDD | C18.1 / C_DVDD_50 | 3.902 | 0 | 3.902 | 0 |
| 54 AVDD1 | C14.1, shared alternative | 2.653 | 3.833 | 6.486 | 2 |
| 54 AVDD1 | C27.1 / C_AVDD1_HF | 2.928 | 8.108 | 11.036 | 2 |

The pad22 row deliberately measures a path to the neighboring C12, not its
nominal C13/C_AVDD_22. C13 is present and connected. These comparisons are not a
complete nearest-capacitor search or a sign-off of the other supply groups.

### Reconstruct the AVDD1 path and junction

The ordered C16 path starts at U1.54 `(49.25, 31.3375)` on F.Cu, runs inward to
via `84baee1b-6160-5959-a408-2f6fed4d6025` at `(48.85, 33.1)`, then returns outward
on In2 through `(49.05, 32.9)` and `(49.05, 26.075)`. It reaches via
`2d0e6ef9-cf08-53ed-aa54-3fc96a2f5151` at `(50.85, 26.075)` and then C16.1
`(49.75, 26.075)` on F.Cu. Exact track UUIDs and all partial endpoints are in JSON.

At `(49.05, 30.15)` on In2, track
`00006ae0-24f8-54be-b149-f7ffe03f487b` branches to `(48.25, 30.15)`, via
`f482e4d0-28c4-5cd6-8333-353274a7e8d7`, C14.1 and U1.56. This is a real junction
on the interior of the long track, not an apparent crossing of different layers.
The C27 branch is farther along at `(49.05, 26.125)`. Thus this is shared copper
before the designated C16/C27 bypass bank, rather than a private local loop
followed by a connection to the common supply.

## Negative-side plane entries: do not confuse connectivity with the loop

| Intended pin pair and capacitor | Capacitor-to-GND-via spoke (mm) | U1-return-to-GND-via spoke (mm) | Distance between plane entries (mm) |
|---|---:|---:|---:|
| U1.54 / U1.53, C16 | 0.950 | 1.563 | **9.325** |
| U1.59 / U1.58, C15 | 0.650 | 1.582 | **5.289** |

For C16, the entries are `(49.75, 23.575)` and `(49.75, 32.9)`. For C15, they are
`(45.85, 27.875)` and `(47.5, 32.9)`. C15's U1.58 entry is shared with U1.57.
The record identifies both spokes and vias for each pair.

Entry separation is only a geometric descriptor. It is **not the return path
length or loop area**, and cannot be added to the positive length to obtain an
inductance. The filled In1 region carries current outside the explicit drawn
GND tracks. Consequently the explicit In1 trace from the VCAP3 ground vias toward
U1.53 is not proof that all charge-pump return current is forced through those
VCAP3 spokes. A short positive route on U1.59 is likewise not proof that its
complete loop is satisfactory. No ground-plane split is recommended.

## Why this is a cluster rework, not a straight-line shortcut

The existing F.Cu VCAP3 fanout from U1.55 to C9/C24 crosses the vicinity of the
apparent direct route from U1.54 toward C16. Moving or adding one straight track
without considering that fanout would introduce a crossing or merely move the
problem to another sensitive node. The next slice should review placement of
C16/C27 jointly with C9/C24 and C14, not silently move components under the ADC
body or to an unreviewed second assembly side.

Target a compact direct local 54-to-capacitor-to-53 connection before joining
shared supply/return copper, while preserving the solid GND plane and the
neighboring VCAP3, AVDD56 and AVDD59 functions. Keep existing capacitor values,
MPNs, population flags and voltage assumptions. This review does not select a
new capacitor, ferrite bead, stackup or assembly process.

**Repair acceptance:** preserve an observed failing regression for the agreed
local-bypass topology/geometry, with any dimensional bound explicitly justified
as a project layout target rather than a TI noise guarantee. Demonstrate the
reworked positive and negative routes with coordinates/UUIDs and comparison to
this record; verify neighboring VCAP3/rail returns, clearance, courtyards and
native parity after fresh fill. A targeted fault must still expose a broken
local path even when global AVDD/GND connectivity survives. Keep required native
routing faults and full exact-head gates. Do not add a generic field solver or
merely lower the reported length while leaving the same shared pre-bypass loop.

## What actually ran

A fresh GitHub checkout, not the previous chat ZIP, supplied source and native
geometry. Read-only capture run [36585335942][3] used KiCad 9.0.2 at source a4ac32c.
The 280-file original recovery is earlier history; this turn used the current
published checkout, not a reconstruction of it. Its artifact SHA256 was checked.

I separately read the original board's token-tree coordinates/net IDs/widths for
all **705 segment/via forms** and transformed all **245 pad positions** from their
footprint coordinates. Those values and UUIDs agree with the native extraction.
The selected route portions were checked for matching net/layer and actual vias;
the two return entries were checked against their GND spokes/vias. This second
calculation is not an independent professional electrical review.

Fresh native run [36586282560][4] then copied the exact same board, built
connectivity, refilled zones and ran KiCad's all-severity schematic-parity DRC:
**0 parity findings, 0 other findings, 0 unconnected items, exit 0**, with one
filled In1 GND region. I downloaded the artifact, checked its SHA256 and all
**14 payload hashes**, and read the actual JSON/log. The copied refill did not
change tracked source. The workflow commit is d42b783, but the explicitly checked
board source is a4ac32c; these identities must not be confused.

This is useful negative evidence: ordinary DRC still passes on the geometry
flagged for bypass rework. It does not refute the electrical-review finding.
No new full local locked gate ran because required packages were unavailable in
the offline cache. Consult this review PR's actual exact-head hosted results for
normal quality/native/target checks. There is no physical noise, capacitance,
power-loss or body-use validation, and no new model or copper repair in this slice.

## Primary basis and remaining scope

[1] TI **SBAS499C**, January 2017, retrieved 29 September 2026: pin table p6,
power guidance p70, layout pp72-73. Those relevant page images were inspected.
The pin table specifies the capacitor endpoint pairs 54/53 and 59/58 separately.
Its charge-pump description is inconsistent with the AVDD1 discussion on p70;
this review uses the explicit AVDD1 name/pins54/53 and does not relabel pin59
as AVDD1 or invent a new silicon model.

[2] TI engineer **Brian Pisani**, E2E answer to *ADS1299/98 does AVDD1/AVSS1 really
produce significant noise?*: recommends local bypass directly between AVDD1 and
AVSS1 before the planes/pours; notes the EVM is not necessarily optimal and that
a layout choice can be evaluated against actual satisfactory performance. This
is vendor engineering guidance, not a guaranteed mm limit or an assertion that
every differing layout fails. No corresponding Rev A physical performance
measurement exists to justify retaining this departure.

The next step is the bounded AVDD1 cluster rework above, then digital reference
transitions and input P/N parasitic review. Existing #45/#48 stay open. Final
stackup, mounting, assembly/lifecycle/effective-capacitance decisions, console
powered-off behavior and delivered quote are still separate requirements.
Publication and source review do not authorize fabrication, purchasing, powered
connection or body use. See the current [roadmap](REV_A_COMPLETION_ROADMAP.md).

[1]: https://www.ti.com/lit/ds/symlink/ads1299.pdf
[2]: https://e2e.ti.com/support/data-converters-group/data-converters/f/data-converters-forum/462184/ads1299-98-does-avdd1-avss1-really-produce-significant-noise
[3]: https://github.com/utof/eeg_ads1299_lab/actions/runs/36585335942
[4]: https://github.com/utof/eeg_ads1299_lab/actions/runs/36586282560

For exact reproducible capture/check instructions, read the two workflow files
at investigation commits `7a403e4aed241d1c399caeefd062cac0dea8486e` and
`d42b783baab48ca661297d364e79b6286a27a739` on branch
`investigate/layout-return-review-20260929`. They deliberately inspect the named
historical source and are not product dependencies or permission to overwrite
later changes. The source plus the committed route itineraries suffice to
recalculate the numbers; the expiring artifacts are not the only continuation
input. Source facts and measurements must be refreshed for any later repair.
