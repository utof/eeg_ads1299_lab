# Continue PR98: reference repair applied; reconcile dependent studies and K2

Read root `AGENTS.md`, `REPOSITORY_PUBLICATION.md`, `DEVELOPMENT.md` and
`REV_A_BENCH_FIRST.md`. Check live main, PR98 and original review threads.
**Do not apply the archived candidate again. It is already active source.**

Use the [hosted capability preflight](REPOSITORY_PUBLICATION.md#hosted-capability-preflight)
before proposing downloads or local setup. Missing local Git/gh/KiCad/pcbnew/DNS
is not a global blocker. Connected source-only publication and separate read-only
hosted native execution work. An explicit denial must not be retried or bypassed;
the historical runtime-packaging denial does not describe these accepted routes.

## Current engineering state

Main was checked at `c2f93ee30eb47f80a7702603f20ed22e6cce86af` (PR97).
Continue draft PR98, `work/l5-spi-series`, from its live head. This slice published
preflight commit `220e926395e0afbc5e150818e37278706b239b44`, then actual repair
`3519b21e335584244771c73c5c87b70d66037a7e`, tree
`9475d027c1a0ba1c3cf9c35c2da9e0a1be07888c`. Later documentation commits must not
be mistaken for a new hardware revision or a separate native execution.

The five DNP/NOT_SELECTED SPI positions were applied at27c6525d, native net-order
and two unused-via defects corrected atf5338e69, and fresh ground fill saved at
3f98404f. Native XML/CSV fixtures are genuine exports, not hand-edited graphs.
Those operations and all later test repairs remain in ancestry. Historical exact
receipts are `checkpoints/20261010_l5_applied_native.json` and
`checkpoints/20261010_l5_full_native.json`; do not rewrite them as current passes.

## C104/P3 repair now applied, not another proposal

Native triage on e10d0f60 located a 0.1470094296705 mm2 C104 return-reference gap
beside R118's driver via and 0.002076282133 mm2 of new full-width reference loss
at AFE_MISO track c4455c3b beside R118's downstream via. A first candidate violated
the unchanged 0.20 mm clearance rule and was rejected before publication.

The accepted repair moves exactly THREE new SPI vias and their SIX attached
track endpoints. The SCLK driver via moves from(38.75,23.05) to(38.9,23.15),
MOSI driver from(38.1,23.7) to(38.075,23.025), and MOSI downstream from(38.6,19.25)
to(38.45,19.25), in mm. No footprint, net code/name, layer, width, drill or zone
outline/settings change. Only the actual native TARGET_GND filled_polygon cache
is transplanted after refill. All other authored geometry and the AFE stay intact.

The explicit L5 preservation map remains23 before/41 after. Only the NINE after
hashes of those exact geometry forms change. The original before map and P2/clock
snapshots remain unchanged; unrelated and partially applied changes still fail.

Reverse/split controls now target live AFE_SCLK trace58e213eb instead of removed
36f3b6dd. The reference-void control derives its location from that live trace's
midpoint; its remote control remains in HOST_GND. The actual reference checker,
frozen pending-edge outlines, corridor widths, antipad exclusions, clock limits
and fault acceptance criteria are unchanged. Neither a broad exemption nor a
lowered threshold is part of this repair.

## Exact evidence and its boundary

See `checkpoints/20261011_l5_reference_repair.json` for all source blobs, SHA256s,
commands, movements and failed/passing run identities. Read-only run38092481309,
job114331583320 used pinned KiCad9.0.2 and uv0.12.18 with the unchanged lock. It
checked e10d0f60 plus the independently reconstructed three-file tree
`21d4c3247c7b873aa9bc799fd4d861836cdf5125`:

* 113 actual native cases passed, zero failures/errors/skips, JUnit238.409s.
  The selection contains49 auxiliary-routing,42 auxiliary-ground,15 SPI fault,
  6 clock and1 reference-performance cases. It includes all39 legacy terminal
  cuts, all15 SPI cuts/shorts, the repaired C104/P3 checks, equivalent-copper and
  reference-void controls. These are not API doubles or collection-only results.
* 11 ordinary source-preservation cases passed. The canonical auxiliary board
  had0 schematic mismatches,0 other DRC findings and0 unfinished connections.
* Artifact11684458355 SHA256
  feaa687dfb218495181db08bcc48635c8c1e80f3efbe41d56e6997842f82b5dc was downloaded;
  ZIP/CRC, JUnits, three source-file Git/SHA256 hashes and both independent trees
  were verified. Actual native fill was compared with independent coordinate
  edits: no other source byte differed. The three files were applied on220e9263
  to retain the preflight docs, producing published tree9475d027.

This is a FOCUSED selection, NOT the complete project gate or complete native
selection. Do not borrow it as a pass for another source revision. The full
ordinary gate has known S2/S3/S4 failures; a full native selection after3519 is
being inspected separately. Read its actual results before extending any claim.
The older3f984 full-selection timeout and its ten markers are historical failures,
not evidence that the repaired C104/P3 controls still fail. Do not repeat that fix.

Local checks used installed pytest, not a successfully synchronized local locked
environment. Full native execution occurred on GitHub. Source publishers had
write permission only for verified source data; no project/artifact code executed
there. The read-only native job authored only disposable copies. Product workflows,
selected dependencies, firmware, Q1 and release flags were unchanged.

## Agent instructions are now guarded at every entrypoint

AGENTS.md, README.md, DEVELOPMENT.md and this handoff all link near the beginning
to the hosted capability preflight. The existing three-case entrypoint test now
also requires that specific link in each opening. It failed before the docs and
passes afterward; this tests discoverability, not all future assistant behavior.
Do not tell the user that local setup is required without actual relevant
connected/hosted failure under current schemas. Use the working scoped publication
and native job examples in REPOSITORY_PUBLICATION; do not blindly rerun fixed jobs.

## Next bounded engineering task

Reconcile S2/S3/S4 with the applied five-site topology. Start with the14 exact
historical failures in20261010_l5_applied_native.json and current exact-head CI.
Source bindings name pre-L5 BOM/contracts; S2 also assumes unsplit driver nets.
**Do not simply refresh hashes.** Account for open DNP positions versus expressly
conditional fitted current paths, preserving historical evidence and every
unknown/qualification-false result. No numerical resistor is selected by this work.

K2's strict AFE whole-board binding/access review remains. R24 is at(57.0,29.4);
old placements, board outline and mating interfaces are retained, but nominal
clearance is not populated solder/tool-access evidence. Review K2/B3 and existing
native mechanical checks before changing its binding. Do not loosen it.

Complete ordinary/native/firmware gates and independent exact-head review remain
required before merge. Keep the450s complete native budget and71% branch floor.
A previous complete selection exceeded450s: remove genuinely redundant work only
with equivalent results if it still does, never extend time or omit cases to pass.
Inspect original reviews and subsequent comments; a diagnostic or documentation
review is not complete engineering acceptance. PR98 remains draft and unmerged.

## Retained engineering and physical boundaries

All five series positions remain DNP/NOT_SELECTED: absent parts are OPEN, not
zero ohms. R114 remains42.2k on the receiver side; logical MOD1.GPIO13 stays
with J1.5 downstream of R24. Original driver-length figures predate this small
via adjustment; current source geometry, not those historical figures, must be
used for any later timing/access assessment. No termination performance or
physical rework access is established. No cut/flying-wire fallback is approved.

Retain L1-L4/B1-B3, all15 bypass corridors,39 earlier terminal cuts, domain/mounting
and pending-reference guards. MISO/MISO_DRV share original whole-channel budgets.
The proposed pilot remains INTERNAL-TEST-ONLY with six upstream analog pairs;
E1 acceptance and possible further revision cost remain separate. Internal mux
modes are not an isolation barrier; MCU launches/other controls remain separate.

B1 uses J2, not J1; B2's run card and B3 insulation/restraint/earth/uncertainty
requirements remain. Keep R -> fresh F1 arm -> wake/clock ->150ms -> VCAP1>1.1V ->
reset, not a raised-VCAP1 requirement while parked in PWDN. BOARD_PROFILE_REVIEWED
staysfalse; both DevKit USB ports stay excluded. Retain HOST/TARGET isolation,
complete-run fault invalidation and analog fault limits. STOP is not a disconnect.
No assembly, measurement instrument or human/animal connection is qualified.

Moscow remains a planning assumption; Q1 is the sole frozen unsent packet. No
prices/outreach, purchasing, fabrication, physical work/rework/mating, powering,
external-input acquisition or person/animal use is authorized.
