# L1: pilot return-path triage, not a copper-release certificate

2026-10-08. Inspected main `2a5d0e60cc823ffdfbea5d0c45164b6b648deb6c`,
tree `ed83eefb7d2286214d3a38dbea98a1c703491892` after B3/PR93.

**Decision: do not schedule 18 reroutes or blanket ground-via additions merely
to remove the pending-edge counter.** The recorded residuals are small edge
overlaps beside *other-net* via clearances, not 18 cuts through the checked
central return strip. Retain this copper for design/DFM continuation. This is
NOT acceptance for fabrication, an electrical waiver, or proof that the full
return paths are satisfactory. The existing pending fixture, native guards,
all false qualification fields and #45/#48 remain unchanged.

The practical result is a located inventory and finite disposition below:
stop treating the original count as an unexplained collection of PCB defects,
but do not treat its small total area as a noise or manufacturing guarantee.
No PCB, component, firmware, production code, test or threshold changes here.

## 1. What the 18 records actually mean on the current board

The original `auxiliary_p3_pending_edges.json` contains **20 allowed polygon
records for 18 source segments**. It is a historical spatial envelope, not a
list of 20 necessarily present defects. Comparing it with the current board and
the clean PR93 native reference output gives:

| Quantity | Current observation |
|---|---:|
| Affected segment records in native output | 18 |
| Original envelope records still uncovered in the planar check | 19 of 20 |
| Distinct remaining nominal XY polygons after removing one duplicate | 18 |
| Native sum over affected segments | 0.0022149715565 mm2 |
| Union of active original outlines, without the shared duplicate | approximately 0.00214156 mm2 |
| Maximum nominal inward penetration from a trace edge | 6.1901 um |

One TARGET_VIN5 outline near `(68.8,35.0)` mm is now covered: R1 removed the
old MCU_SCLK via at `(69.35,35.0)` mm. The second outline on that same long supply
segment remains near y=36, so the *segment count* stayed 18. Two RAILS_OK segments
also report the very same outline near `(52.4,46.65)` mm; summing their areas
counts it twice. These are bookkeeping distinctions, not new copper changes.
Keep the entire original allowed envelope byte-identical; no benefit is claimed
from deleting historical allowance data or changing its pending status.

All 19 active records are beside a **different non-ground net's 0.60 mm via**.
They are not explained away by the checker's own-net contact exclusions. Fifteen
have 0.5 um nominal trace-edge penetration. Four have larger penetrations:

| Victim net / source track prefix | Nearby via net / centre, mm | Nominal penetration |
|---|---|---:|
| ARM_REQ / cd6846f4 | SESSION / (61.50,61.00) | 6.1901 um |
| MCU_CS / 85cf5ec6 | MCU_DRDY / (56.65,34.15) | 5.4697 um |
| TARGET_VIN5 / 90ba6800 | BUS_OE / (71.20,29.30) | 4.2102 um |
| CLR_N / 515aa3a3 | BUS_OE / (72.40,59.45) | 2.3219 um |

The complete 20-row locator, exact track/via UUIDs and input hashes are in
[studies/l1_return_triage.json](studies/l1_return_triage.json). Depth is measured
normal to the source segment from its full-width edge to the recorded outline's
furthest inward vertex. It is NOT clearance between signal copper, ground-return
length, fabricated tolerance, capacitance or interference amplitude. The source
has 0.25 mm zone clearance around these foreign vias; the trace and via need not
short merely because their projections overlap a clearance opening on In1.

**No cosmetic sub-micrometre reroute.** Removing these numerical-scale overlaps
alone would neither establish registration tolerance nor resolve the much larger
intentional antipads. A useful future reroute must improve a specified channel/
return arrangement with meaningful geometry and preserve all bypass, isolation,
mounting and original-copper constraints. Do not add meanders to make a counter
zero. Conversely, these shapes are real outputs of the native geometry check:
do not relabel them harmless numerical noise or suppress them.

## 2. Actual transitions: one reference conductor, not two planes to stitch

Source endpoint inspection finds **118 non-ground vias**, each joining F.Cu and
In2.Cu traces. This includes supply vias, not just logic. The other 39 vias are
ground connections with front traces. All vias physically span F-to-B; unused
barrel sections remain. There are 385 front and 258 In2 track segments and no
back-layer auxiliary tracks. In1 holds the two separate HOST/TARGET references;
In2 is routed copper, not another reference plane.

F and In2 approach opposite faces of the **same domain's In1 conductor**. That
is not automatically a handoff between two disconnected reference planes [1].
A generic extra ground via has no second ground plane to join in this design.
Do not add 118 stitching vias or bridge HOST/TARGET. This does not make existing
transitions ideal: local antipads, through-hole landing groups, trace-to-plane
spacing, package returns and cables still shape real current paths [1,2].
The 56 auxiliary plated-through pads are separate terminal structures, not part
of that via count. Native central-spine coverage excludes same-net through
contacts expanded by 0.35 mm; it cannot certify the current detour around those
excluded holes, even though the 15 local bypass guards remain stronger.

The AFE's earlier concrete repairs are already present: MISO/DRDY have no B-layer
tracks, and CH1N's selected detour remains on F/In2. Do not repeat their old
publication/repair instructions. The remaining analog upstream B/In2 coupling
is still one six-net-pair item, not nine independent repairs; its current owner
is `REV_A_UPSTREAM_COUPLING_DISPOSITION.md` plus the E1 requirements.

## 3. Finite pilot disposition: what is retained, what still blocks what

| Item | Decision now | Dependent stage / remaining evidence |
|---|---|---|
| Located nominal auxiliary edge residuals | No mandatory reroute established by these shapes alone; retain and keep guarded | Manufacturing/layout acceptance still requires actual stack/process and an explicit scoped pilot decision; not a general full-width approval |
| F/In2 same-reference transitions | No blanket stitching or plane split | Review actual antipad/terminal geometry as part of each used channel; do not infer impedance from the central-spine check |
| Repaired MCU_SCLK and AFE outputs | Preserve the completed repairs | Full clock/data path setup/hold, ringing and receiver loading remain separate; 1 MHz is a clock rate, not an edge-rate specification |
| Long CLKSEL, arm and supervisory nets | Length alone does not justify detours or matching | Startup/fault transitions still have fast edges; infrequent switching does not exempt logic thresholds, false-edge or rail-fault behavior |
| Supply feeds and sense/return paths | Reuse S1-S4 and B2, no new calculator | Actual rail/current/ground/ramp evidence before the approved powered stage; no steady voltage-loss result certifies HF return impedance |
| Six AFE upstream coupling pairs and P/N imbalance | Keep as one explicit unresolved electrical item, not automatic reroutes | Before fabrication: obtain applicable stack information and decide coordinated rework versus a deliberately limited internal-test pilot. E1 external-source acceptance remains separate and unproved |
| Capacitor migration, lands and stack construction | Preserve active-versus-proposed distinction in Q1 | Applicable manufacturer/assembler evidence or explicit bounded disposition before coordinated active-source change and populated fabrication; #45/#48 stay open |

An internal-test capture does not qualify external-input noise, channel order,
CMRR, E1 coupling or body use. Its input mux also does not remove power, ground,
package or digital-bus interactions. Later characterization can be scheduled
later; the *decision to accept a limited pilot experiment* cannot be silently
assumed later after fabricating. Nothing in this table moves an existing gate.

## 4. Next bounded engineering task

**Check one complete SPI read channel at the existing 1 MHz setting.** Trace
clock launch through the selected buffer and interconnect to the ADC, and data
return through its buffer to the actual MCU sample event. Reconcile source code
with applicable setup/hold and propagation-delay conditions; distinguish minimum
from typical/maximum and retain cable/loading/edge uncertainty. Include the
actual waveform measurement needed where a paper bound is missing. This is a
specific logic-function decision needed even for the internal-test pilot, not a
new general circuit model, price search or another probe plan.

Do not choose a generic termination resistance or reroute solely from geometric
length. A timing pass would not itself dispose ringing, maximum ratings or
manufacturing requirements. B1-B3's existing run card and contact method remain
the place for real equipment/attachment approval; no new measurement framework.

## 5. Evidence and reproducibility boundaries

Read-only source inspection parsed all 643 auxiliary segments, 157 vias and
216 pads. Its 39 per-net layer-length/via totals match the saved native report.
The separately exported PR93 refilled board has the same sorted track/via/pad
fields as current source. SHA256s of both boards, the pending envelope, old-clock
fixture and checker are in the locator; all Q1 input/schedule hashes stay intact.

The existing native report came from PR93's exact head `9f78bf7d85`, workflow
37700373324, artifact11517449242 (ZIP SHA256
`c438dbaecfe3a5e102e12d16444018c5dec0ce19005a7399d4e6baaf9169bfad`).
This inspection does NOT claim a new local native refill or electrical test.
Integer shoelace areas, direction-reversal depth checks and full planar polygon
subtraction locate the residuals. Shapely2.1.2 was an existing authoring tool,
not a project dependency or replacement gate. Native integer clipping and this
planar cross-check differ by at most about1.04e-8 mm2 per reported segment;
the native values remain authoritative. No project threshold was adjusted.
The planar union figure uses the active recorded outlines, not a fresh EM model.

Initial authoring hypotheses (all residuals beside own-net vias; all 20 old
outlines still present) were rejected by the source audit. No source was changed
to make those hypotheses true. No new project tests are warranted merely to
freeze this prose. Current-head CI/review must be read on this PR; prior PR93
results do not establish a new-head pass. Local locked setup failed dependency
DNS and the installed uv differs from the required version; no local full gate,
hooks, KiCad, target build or physical measurement is claimed by this note.

[1] TI SLLA284G, p16 Figure4-13, single versus multiple reference-plane changes;
page image inspected 2026-10-08: https://www.ti.com/lit/pdf/slla284

[2] TI SCAA082A, p16 Figure15, local via-clearance slots and routing direction;
page image inspected 2026-10-08: https://www.ti.com/lit/an/scaa082a/scaa082a.pdf

[3] TI ADS1299 SBAS499C, p72, layout/return and separation guidance; page image
inspected 2026-10-08: https://www.ti.com/lit/ds/symlink/ads1299.pdf

Moscow/no deep price research direction retained. No vendor contacted. No
purchase, fabrication, physical fixture construction/mating, power, external-input
acquisition or person/animal connection is authorized by this design triage.
