# Continue from B3: supported sense access, no more generic probe planning

**Read `REPOSITORY_PUBLICATION.md` before GitHub publication or recovery.**
Read root `AGENTS.md`, `DEVELOPMENT.md` and `REV_A_BENCH_FIRST.md`. Start with
live main, open AND recently merged PRs and original review threads. Missing
chat replies have followed successful merges. Do not recreate their work.
Source publication, Codex review, CI and merge are different operations.

## Current source and next practical task

B2 merged in PR92 at `8c08e012e58b9bde7ca2b0f3df9c0126d10b0c00`, tree
`7e7322374c84b58704f0d30388f458e165bfea2a`. B1/PR91 and Q1/PR89 are already
merged, as are capacitor/S1-S4/P3/R1/C1-C4/F1/K2 decisions. PR90 is a closed
competing RFQ; never revive `quote_draft/`. Inspect live status for B3's merge.

Read **`REV_A_CONTACT_ACCESS_B3.md`** and its small read-only
`studies/b3_access_envelope.scad`. The existing K2 ribbon blocks a straight
approach to C30; its guide blocks C33. Prefer five separately identified,
insulated fine-wire sense pairs on C6/C30-C33 with independently supported
outboard relief, rather than clips under the cable. No board/header/holder
redesign or general pogo fixture is justified by the nominal clearance study.
The SCAD imports current K2 and models routing SPACE, not actual wire joints,
clamps, populated PCB bodies, qualified probe hardware or printable parts.

Native OpenSCAD intersections detect both blocked approaches and a deliberately
raised bad corridor. The proposed z=5.5 mm aerial corridors avoid the retained
K2 envelopes; they do NOT qualify the local solder exits, installed insulation,
sag/strain, tolerances, removal motion or measurement response. A 4 mm component
allocation and bare pad dimensions are not real exposed-metal/clearance evidence.
Actual wire/attachment process, joint inspection and restraints remain before-use
requirements. Separate negative sense conductors must not become an external
common ground bus, power return or unreviewed instrument-earth connection.

**Next independent build step:** review the existing before-fabrication layout/
return-path items for the limited internal-test pilot. Start with the recorded
18 pending auxiliary reference records/20 outlines and source-defined return
transitions. Identify specific source repairs versus explicit limited-pilot
engineering dispositions versus later measurements. Do not enlarge reference
allowances, add arbitrary meanders or declare whole-channel performance from
DRC0. Record exact remaining external evidence where it is necessary; do not
repeat a broad supply, capacitor, RFQ or probe-family search to avoid it.

B1-B3 now define the intended startup fixture, observations and contact approach.
Do not add another generic measurement plan. Actual implementation/commissioning
must use B2's EXISTING run card: selected instruments, accepted sense-lead process,
connection/earth sketch, coverage, uncertainty, numeric ramp/current/thermal and
shutdown/discharge limits. No approved settings or measurements exist yet.

## Standing user direction

Delivery planning is **Moscow, Russia**; no postcode, supplier, delivery feasibility
or outreach permission is inferred. Avoid detailed price/stock research. Keep
Q1 at `REV_A_PILOT_QUOTE_PACKET.md` and `quote/` as the sole frozen unsent snapshot;
its 18 source and two schedule hashes remain unchanged. Active versus proposed
MPNs are intentionally different at 26 AFE ceramic sites, not applied substitutions.
No contact/order/production is implicit in "next". The historical USD94.84 is not
a delivered kit price or proof of the USD100 objective.

Use clearly labelled reversible assumptions to advance independent work. Plan
around an off-the-shelf regulated 5 V bench source with output enable/current
limiting, not a raw battery or custom charger. Available 1 A capacity is neither
measured consumption nor an initial current-limit setting. Do not block unrelated
build decisions on the missing instrument model or invent evidence to fill it.
Each slice closes a decision, repairs a demonstrated defect or prepares a specific
physical check. No new code framework or broad refactor without an actual need.

## Preserved engineering boundaries and authoritative detail

AFE authored PCB: `hardware/rev_a/layout/rev_a.kicad_pcb`, SHA256
`60097ff4acf8408d5a172930de74bcd36aa50a379dd30a831e4bc64d3841c8a6`.
Auxiliary: `hardware/rev_a/auxiliary/auxiliary.kicad_pro` and adjacent PCB.
Never run the parking-grid importer or old authoring helpers over either board.
Keep the 15 bypass corridors, 39 terminal-cut tests, domain/mounting guards and
18 pending reference records/20 outlines. The central 0.10 mm reference strip
and own-contact exclusions are not full-width ground, impedance or SI proof.

Read `REV_A_PILOT_CAPACITOR_DISPOSITION.md` and `REV_A_100NF_REUSE_DECISION.md`:
proposed 15 x 1 uF, four x 10 uF and seven AFE 100 nF replacements remain
unapplied; 15 auxiliary 100 nF and C0G/T491 remain selected. Internal VCAP3 is
boosted; typical curves, nominal values and body envelopes are not guaranteed
joint-corner capacitance, transient or mounted-height limits. Coordinated accepted
BOM/CAD/contracts/fixtures changes follow the applicable process/electrical
responses or explicit limited-pilot disposition, not isolated MPN edits.
AFE's named stack target is not factory approval or an approved auxiliary stack.

B1: J2-only keyed cable; contacts 1-8/10 common, BIAS9 and NC11-20 individually
isolated. Preserve pre-join identity because commoning hides permutations. J1 is
forbidden; reversed mis-mating can short its 5 V feed. Physical retention and
detached-passive test conditions remain unqualified; no generic assembled-IC
ohmmeter acceptance. C4: pins1/5 return,2 AFE DVDD OUT,3 separate DVDD sense,
4 AVDD sense after R11,6 empty. Feed/sense join only on AFE. No hot mating.

B2: capacitor contacts are landmarks, not all-chip-terminal voltage proof. Preserve
R -> fresh F1 arm -> wake/clock ->150 ms -> VCAP1 >1.1 V at V -> reset. Do not
demand raised VCAP1 with PWDN parked before R. BOARD_PROFILE_REVIEWED stays false;
the distributed onboard-UART stopped build is not the hypothetical reviewed
C1-header acquisition. Neither acknowledgment automatically measures voltage.
Both DevKit USB ports remain excluded with accessories; HOST/TARGET must not
be bridged by supply links, instruments, chargers or shields. STOP/polling is
not a power disconnect or guarantee against fast faults. Digital buffering does
not protect analog electrode inputs. Preserve complete-run fault invalidation.

S3's 21 physical input terms remain unknown; S4's conditional regulator/current
information is not an assembled-source qualification. Keep source/current/peak,
leakage, sense injection, partial-rail and ground-break conditions open for their
actual dependent stage. No powered protocol, external acquisition or person/
animal use is released. Keep #45/#48 and manufacturing/fixture requirements open.

## Verification and completion reporting

Use locked uv and the single `tools.check` gate, with unchanged 450 s CAD budget
and 71% branch floor. Retain installation/tool errors; do not use an unlocked
substitute as a pass. B3's seven native envelope cases are authoring diagnostics,
not additions to the project test totals or physical experiments. Inspect actual
exact-head CI and independent review before merge; read back main/tree afterward.

Report TLDR and category/remaining-turns/status/next-step roadmap. Distinguish
nominal source geometry, physical workmanship, instrument qualification and
release. Purchasing, fabrication, building/mating fixtures, powering, external
inputs and body connection are not authorized by a documentation/source merge.
