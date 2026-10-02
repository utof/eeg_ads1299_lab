# P2 auxiliary ground references and local bypass routing

Base is P1 main `3926fa02816b6812bcacd6113db180278186c258`, tree
`d3020772347f15b5c13db31703ba18d7e7a2e195`. This is a **partial-routing source
milestone**, not a completed PCB or manufacturing release. The checkpoint
`checkpoints/20261002_auxiliary_ground_p2.json` identifies the authored board,
measured native geometry, test-first revisions and remaining limitations.
The existing AFE/J3, auxiliary schematic/contract/BOM, F1 firmware, K2 carrier,
Python dependencies, selected component lands and approval gates are unchanged.

## Copper implemented

Two distinct ground reference zones occupy **In1.Cu**, one HOST_GND and one
TARGET_GND. Neither is joined across the existing full-height isolation corridor.
HOST bounds are x0.5–20.25mm; TARGET bounds x23.75–89.5mm; both use y0.5–74.5mm.
The nominal plane-edge gap is3.5mm. The independent existing3.0mm HOST/TARGET
clearance rule still applies to all copper, including the isolator pads which
set the smaller whole-board gap. This is not qualified creepage, working-voltage
insulation, medical/body suitability, measured EMI or a supplier-confirmed stack.

All **59 ground terminals** (3 HOST,56 TARGET) are connected in native DRC.
Of these,42 SMD terminals have short front-copper access to39 through vias;
17 through-hole ground terminals join their corresponding reference with
thermal relief. Each zone refills to exactly one connected region. This is
native topological continuity, not a resistance/inductance or thermal test.

Every one of the **15 existing100nF bypass capacitors** now has its own direct
F.Cu supply path to the assigned IC supply pad. These traces are1.75–2.1875mm
long and0.20mm wide. SMD ground-access paths are at most2.1875mm to a same-net
via. All new vias are0.60mm diameter/0.30mm drill; no via-in-pad was selected.
The In1 zone clearance is0.25mm with0.20mm minimum filled width. PTH thermal
settings are0.25mm gap/0.30mm spokes; their actual solder/process suitability
remains unqualified. The custom U111 pad-pair rule and every pre-existing
clearance/exclusion/severity setting are unchanged.

The board now contains **62 tracks,39 vias,two filled zones and five rule areas**
(the original isolation corridor plus four new mounting exclusions). All52
footprint forms remain byte-identical to P1, including the reviewed asymmetric
H4 position. No component, pad, drill, termination area or board outline moved.
Only the original title/draft-description forms change to identify P2; all
other old board forms, including the original barrier, remain byte-identical.

**157 to85 unconnected items**: 57 ground-network joins plus15 local bypass
joins are complete. The remaining global supply feeds, controls, UART/SPI and
sense paths are intentionally unfinished. Native9.0.2 reports0schematic parity,
0other findings and85unconnected, requiring exit5. That is NOT a clean completed
routing result. A capacitor-to-IC connection does not mean that the external
supply feed or a complete signal path has been routed.

## Reference paths, not just net labels

The independent native proof checks the actual F.Cu segment graph between each
capacitor and supply pin, accepting reversal/subdivision rather than one exact
segment text or UUID. Each SMD ground pad must have a <=2.5mm front-track path
to a same-net through via lying in the refilled reference. Native DRC separately
checks all actual pads, thermals and nets; geometry does not substitute for it.

A continuous **0.20mm-wide chosen reference corridor** must remain filled
under each local supply trace and between the corresponding capacitor/IC ground
vias. The check subtracts the actual native filled polygon from each corridor,
with <=1e-6mm² residual allowance for integer polygon arithmetic. It does not
sample a few points and assume the intervening copper exists. The corridors
are geometric design requirements, not an extracted return-current distribution,
loop-inductance limit or measured bypass performance. The longest direct
capacitor/IC ground-via separation is approximately11.57mm across a buffer;
that planar connection must not be described as a2mm complete electrical loop.

These are In1 references only. In2/B.Cu routing and any required additional return
vias/reference construction must be reviewed explicitly in the next slice.
No continuous B-side return plane is implied by selecting a four-layer board.
Keep future signal vias/plane cuts out of the guarded local reference corridors,
or make a separately reviewed, tested geometry adjustment rather than relaxing
the checks to accept an accidental cut.

## Mounting copper exclusion

The four existing6×6mm fastener allocations are now copper-excluded on **all
four layers**. Their coordinates follow each actual mounting pad, including
H4's reviewed offset. Tracks,vias and fills are prohibited; filled In1 copper
is independently checked not to enter them. The original hole and mounting
footprint remain unchanged.

KiCad treats the NPTH hole as a PAD object, so a blanket pad prohibition would
reject the hole itself (the first native trial did expose exactly those four
findings). These new areas therefore allow PAD/footprint objects; the existing
P1 independent all-electrical-pad versus mount-allocation check continues to
reject electrical pads in those regions. This is not an exception allowing a
new signal pad under a fastener. Material, screw/washer size, creepage around
mounts, dimensional tolerances, forces and actual fixtures still require review.

## Failure-first and negative controls

On unchanged P1, the new checks produced16 intended native failures: the ground
completion check and15 missing local supply paths. After routing, an actual
refilled copy with a small In1 void beneath C110's supply trace still had the
same85airwires, zero parity and zero other DRC findings. The original connectivity/
length check accepted it. A separate failing regression preceded the continuous
reference-corridor check, which now rejects that same copy. Moving the void
away from the local circuit remains accepted.

Each of15 separate capacitor-path cuts is refilled and rerun through DRC. Every
cut adds one native unconnected item, preserves schematic parity and triggers
the relevant local-path failure. Removing either complete plane disconnects the
appropriate ground network. Removing a return via, changing a reference layer
or removing a mounting exclusion fails its specific guard. Harmless trace
reversal/subdivision and the remote-void control remain accepted. These are
modified CAD copies, not physical experiments or an exhaustive mutation score.

A further same-net audit exposed a return via whose annulus was only0.114mm
from the neighboring R111 ground-pad bounding box. Native DRC did not treat
same-net proximity as an error. A failure-first check now requires at least
0.20mm annulus-to-SMD-bounding-box clearance. Moving that one shared U110 return
via from(58.65,57.4) to(58.65,57.2)mm and updating its two branch endpoints
corrected it without moving any component, changing via size or replacing old
rules. The final native proof passes this geometric allowance; it is not a
fabricator's solder-mask registration or assembly guarantee.

The two new probe/test files are bound into the existing tools.check source
receipt. Two software snapshot-change controls failed before registration and
now reject stale proof. There is no parallel validation orchestrator. Final
ordinary/native/KiCad/target counts belong to the actual PR head and retained
logs; focused selections are subsets, not extra passes to add to the totals.

## Continue and inspect

Open `hardware/rev_a/auxiliary/auxiliary.kicad_pro` in pinned KiCad9.0.2. Run the
existing `uv run --locked --all-extras python -m tools.check --schematic` after
installing its declared native engine/libraries. Always refill modified copies;
cached polygons or an old passing report must not certify new geometry. The
new tests are `tests/test_auxiliary_ground.py` plus the native-only probe text
in `tests/auxiliary_ground_probe.py`. Authoring scratch scripts are not project
dependencies and must not be replayed over subsequent copper edits.

**Next: route the remaining global power feeds and signals**, preserving C4's
separate feed/sense nets, HOST/TARGET barrier, fixed mounting/cable allocations
and these local reference connections. Refill and review actual return paths
when completed. Keep#45/#48, capacitor/stackup/fixture/console-fault and delivered
budget decisions explicit. There is no new supplier confirmation, physical
assembly, fabrication/purchasing/powered-connection or body-use authorization.

Primary guidance checked2October2026: TI ISO7721 SLLSEP3G pp31–32 and TXU0304
SCES935A pp25–26. Their local bypass/ground/reference guidance informs this
layout; it does not qualify the complete assembly or its effective capacitors.
The TXU layout example is the DTR package, not this board's selected PWR land;
only its general local bypass/reference guidance is used, not a pin-layout copy.
https://www.ti.com/lit/ds/symlink/iso7721.pdf
https://www.ti.com/lit/ds/symlink/txu0304.pdf
