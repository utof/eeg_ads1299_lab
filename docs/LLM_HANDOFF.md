# Continue PR98: hardware APPLIED; fix remaining native reference and study blockers

Read root `AGENTS.md`, `REPOSITORY_PUBLICATION.md`, `DEVELOPMENT.md` and
`REV_A_BENCH_FIRST.md`. Check live main, PR98 and original review threads.
**Do not apply the archived candidate again. It is already active source.**

## Actual source state

Main remains `c2f93ee30eb47f80a7702603f20ed22e6cce86af` (PR97). Continue draft
PR98, `work/l5-spi-series`. Source application `27c6525d3ef1721b7c48f7db52c69896b8759d3a`
actually installed the eleven preserved PCB/schematic/BOM/contract/test files on
`08a8ddd0`, retaining all later population/preservation/selector/fault-test repairs.
Its tree is `f8a8c4a5064ae60a86a73fbd13767b0cfbb03364`.

Real native findings were corrected at `f5338e69edfd0e7614adcb2be36253597ee05b5f`,
tree `bd59a0cb3027eea46d88ea4fe464380416d423fd`. Five top-level driver-net declarations
now precede their footprints: KiCad had loaded the original driver pads as no-net
when the declarations appeared later. Numeric net codes, pad fields and planar
routing were retained. Exactly two unused single-layer auxiliary via stubs were
removed, UUIDs `71d75102-d62b-56fa-836c-16e727e27d6b` and
`c6fdfa53-7da1-5491-8519-b5f54483d35b`. Their exact hashes extend only the explicit
L5 preservation mapping to **23 before / 41 after**. Original P2/clock snapshots
remain unchanged; no blanket exception was added.

The actual native XML/CSV exports are now fixtures, with exact inventory increases
for one AFE resistor and four auxiliary resistors. The pin-move and nonpolar-swap
loops remain intact (15576 move cases, 55 accepted nonpolar swaps). One formatter
change preserved its full Python AST. No circuit was changed merely to satisfy a
snapshot, and no XML was hand-edited.

`3f98404f2755331359f2aa95354a0a3ea934ae92`, tree
`79ac4f265df0cc4521fb162c34ae41c0401c2990`, saves only the fresh native TARGET_GND
filled_polygon. Its outline/settings and every other auxiliary source byte are
unchanged. The other seven zone forms, including AFE's ground fill, already match
the new native output exactly. Do not call these caches unverified/stale anymore.
No global KiCad reserialization or new geometry was substituted for authored PCB.

## Verification: bind every claim to its actual source

The durable receipt is `checkpoints/20261010_l5_applied_native.json`.

* Before correction, read-only KiCad9.0.2 run38074668398 on27c6525d reported AFE
  1 parity/2 other DRC and AUX 4 parity/18 other DRC findings. Both had zero
  unfinished connections. Fifteen fault cases stopped at canonical setup; no
  mutation ran. All seven schematic sheets already had zero ERC findings.
* After correction, run38075526473/job114281578606 checked exactf5338e69/treebd59a0c.
  Both freshly refilled boards have zero parity, other DRC and unfinished items;
  seven schematic sheets have zero ERC. **All15 native fault cases passed**:
  ten pad-side cuts and five copper bridges, zero errors/skips,32.755s. Artifact
  11678039527 SHA256 d725b438a10282962f9804b564083a73ef6db06bd9b0bcafba1b6029a1daa454
  was ZIP/CRC/internal-hash/JUnit checked. These are executed KiCad cases, not
  API doubles. Each fault still requires its exact pad/track UUID and net witness.
* The FULL ordinary Python3.11 gate atf5338e69 FAILED: fourteen failures are in
  current-return S2, supply-acceptance S3 and steady-source S4. Source bindings
  still name the pre-L5 BOM/contract; S2 also assumes unsplit driver nets. The
  1404 JUnit cases include subtests; do not turn that into an ordinary-pass count.
  Format/lint/types/complexity/architecture/baseline passed. Artifact11677939676
  and its digest/JUnit were independently checked; failed case names are in the
  receipt. All five original missing-position requirements now pass.
* Local installed-pytest338 focused cases passed on the exact14-file correction
  tree. This is not a local locked/full gate. Local uv/dependency/network issues
  remain, but do not imply loss of GitHub writes or hosted KiCad.

The complete schematic selection on saved-fill3f98404f did NOT finish inside the
unchanged450s budget. Run38076033192/job114283053171 ended with ten visible failure
markers and no final JUnit; do not invent complete totals or call it a pass.
Artifact11679241216, SHA256
b4f99687b26f58f972c7f700d1fafa32add266aeb020a233b014e7ec29e2de0c,
was ZIP/CRC/source-identity checked. Exact retained failures and log hashes are in
`checkpoints/20261010_l5_full_native.json`. The canonical C104 bypass probe reports
`C104 return local reference gap`. P3 reports unreviewed full-width reference
growth at trackc4455c3b-ea0d-5d22-8a62-23973dd1e173. Reverse/split mutation controls
still seek removed trace36f3b6dd-9d7a-54fe-9c03-f7ebe5f77ae8 and fail before mutation.
These are additional native source/review blockers, not contradicted by clean DRC
or the separate15-case SPI pass. No manufacturing, populated-access, timing/noise
or physical-safety pass follows.

## Working publication and native tools: no manual setup handoff

The documented PR81 SOURCE-ONLY publisher pattern worked. Run38074447882 checked
existing patch/manifest/file hashes and historical candidate tree, applied exactly
11 files on08a8, published a temporary branch and independently cloned it. The
complete tree was also independently reconstructed through GitHub object actions.
The PR ref then advanced with a non-force expected-head update. Run38075413943
published the predetermined14-file native correction and genuine export fixtures,
requiring the independently computed whole tree. These are not recovery archives
masquerading as active source.

Native authoring used a SEPARATE contents:read job, pinned KiCad9.0.2/locked uv,
exact source checkout and persist-credentials:false. It ran existing native
helpers/tests and retained outputs without changing source. Source publishers do
not execute project or artifact code with write privileges; artifact XML/PCB is
data. Product .github, firmware, dependencies, frozen Q1 and release flags remain
unchanged. Workbench workflows are outside the PR engineering tree.

The saved-fill push succeeded; its optional bundle export then failed because a
raw unreferenced commit is not a bundle ref. Publication was independently verified
by reading the remote commit/tree and reproducing that exact commit object locally;
all authored bytes and its one-file tree matched. Do not rerun its completed push.
A future bundle export should first create a local named ref, not use a raw SHA.
Read REPOSITORY_PUBLICATION for exact workbench paths and records. The earlier
blocked RUNTIME-PACKAGING operation remains distinct and must not be retried.
Do not ask the user to install Git/KiCad merely because this terminal lacks them.

## Next bounded task: C104/reference triage, then dependent source consistency

First examine the canonical C104 ground-return corridor and the P3 reference-growth
finding under fresh native fill. Determine the actual clearance/route and split-net
exclusion cause; fix the source or justify a narrowly reviewed representation
correction, never erase the finding by widening pending outlines or lowering limits.
Repair the two obsolete reverse/split mutation targets using real surviving copper
while retaining the independent equivalent-copper and reference-void checks. The
450s complete-selection overrun also remains a failure: improve redundant work
only with equivalent results, not extra time or omitted cases.

Then reconcile S2/S3/S4 with the APPLIED five-site topology. Read the14 exact failures
and the original study assumptions first. **Do not blindly refresh hashes** or
pretend unpopulated series positions are fitted links: account for driver/downstream
paths and conditional fit assumptions, preserve historical evidence, and retain
all unknown/qualification-false behavior. No numerical resistance is selected.

K2's whole-board hash/access review remains pending. R24 is at(57.0,29.4) with the
existing0603 land family; previous footprint positions, board outline and mating
interfaces remain. Its courtyard is inside the old blanket component allocation,
but this is only nominal source inspection, not populated solder/tool access.
Review K2/B3 and existing native mechanical checks before changing the strict
binding. Do not loosen it or invent physical workmanship evidence.

Read all original candidate review findings plus the newer stale-handoff finding
4238731205. The DNP/preservation/native fault work now has real applied evidence,
but acceptance requires exact applied-head complete checks and independent review.
The current documentation correction addresses the stale 'unapplied' claim; never
borrow a previous source review or a workbench diagnostic as a complete gate pass.
PR98 remains draft and must not merge while full gates or review blockers remain.

## Preserved engineering boundaries

Five positions R117-R120/R24 remain DNP/NOT_SELECTED; absent parts are OPEN, not
zero ohms. R114 stays the42.2k receiver-side shunt; logical MOD1.GPIO13 remains
with J1.5 downstream. No existing footprint moved. Driver legs of about5.3-10.9mm
and two vias remain an access-versus-source-distance tradeoff, not qualified
termination. No copper cut/flying-wire fallback or fitted resistance is approved.
MISO/MISO_DRV share original whole-channel budgets; no per-segment allowance reset.

Retain L1-L4/B1-B3, all15 bypass corridors,39 earlier terminal cuts, domain/mounting
and pending return records,450s CAD budget,71% floor, selected profile and firmware.
The pilot proposal stays INTERNAL-TEST-ONLY with six upstream analog pairs retained;
E1 external-input acceptance and possible revision cost remain separate.
B1 uses J2, not J1. B2's existing run card and B3 insulation/restraint/earth/uncertainty
conditions remain. BOARD_PROFILE_REVIEWED staysfalse; both DevKit USB ports remain
excluded. Preserve HOST/TARGET isolation and complete-run fault invalidation.
STOP is not a power disconnect. No assembly or instrument qualification is implied.

Moscow is a planning assumption. Q1 remains the sole frozen unsent packet. No
price/outreach campaign, purchasing, fabrication, physical work/rework/mating,
powering, external acquisition or person/animal connection is authorized.
