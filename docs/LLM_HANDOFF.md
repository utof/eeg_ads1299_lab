# Continue from L4: implement five accessible SPI series positions; no trace-surgery fallback

**Read `REPOSITORY_PUBLICATION.md` before GitHub publication or recovery.**
Read root `AGENTS.md`, `DEVELOPMENT.md` and `REV_A_BENCH_FIRST.md`. Start with
live main, open AND recently merged PRs and original review threads. Missing
chat replies have followed successful merges. Do not recreate their work.
Source publication, Codex review, CI and merge are different operations.

## Current source and next practical task

B2 merged in PR92 at `8c08e012e58b9bde7ca2b0f3df9c0126d10b0c00`, tree
`7e7322374c84b58704f0d30388f458e165bfea2a`. B1/PR91 and Q1/PR89 are already
merged, as are capacitor/S1-S4/P3/R1/C1-C4/F1/K2 decisions. PR90 is a closed
competing RFQ; never revive `quote_draft/`. B3 merged in PR93 at
`2a5d0e60cc823ffdfbea5d0c45164b6b648deb6c`, tree
`ed83eefb7d2286214d3a38dbea98a1c703491892`. L1 merged in PR94 at
`9af4a71c1f2895d4c9e8517ffae3f2cb58f26bd5`, tree
`42c3e2a08a2bf50ece59038a1ce997ec7cd02c26`. L2 merged in PR95 at
`ea853b338ebe6b79f01d283244eec77faebc64f4`, tree
`df5b2668f8aca78754d71c1207e97634317ae0c0`. L3 merged in PR96 at
`cc89a5b9cbdcdbd975109f75dd4a9d0587286384`, tree
`a211a23296f9981429dd162cf1501dfe1c7b5968`. Check live PR/main status for L4.

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

**L1 return-edge triage:** read `REV_A_PILOT_RETURN_DISPOSITION_L1.md` and
`studies/l1_return_triage.json`. The 20 historical envelope records are not
20 present defects: 19 are active in the planar check, two duplicate one
RAILS_OK location, and the old y=35 TARGET_VIN5 outline disappeared after R1.
The native count remains 18 affected tracks. Active residuals lie at other-net
via-clearance edges, not own-net exclusions; nominal penetration is 0.5 to
6.1901 um, NOT a fabrication tolerance, loop length or noise bound. Keep the
pending fixture and all guards unchanged. No mandatory reroute is established
solely to erase this counter, and no blanket extra ground-via rule is justified:
all 118 non-ground auxiliary vias join F/In2 about the same domain's In1 plane.
This retains copper for design/DFM continuation, NOT manufacture or electrical
acceptance. Real antipad/terminal/channel and stackup decisions are not waived.

**L2 complete-channel protocol/timing review:** read `REV_A_SPI_CHANNEL_L2.md`.
Keep the existing 1 MHz, MSB-first mode1 and command delays. The actual pinned
Arduino3.3.12 path programs mode1 and clocks eight-bit hardware transfers; it
is not ESP-IDF's per-device input-delay/dummy-cycle driver. The ADC launches
DOUT following rising SCLK; the logical MCU receive edge is falling, not the
C++ return event. Do not add dummy clocks, switch modes or slow SPI merely
because there is a cable. All hardware and actual firmware gates stay unchanged.

L2 maps four complete signal paths and separates setup, hold, command guards
and whole-frame timing. The conditional 11+17+11=39 ns subtotal uses the TXU
5 pF propagation test, NOT S2's assumed100pF or the actual cable. The ideal
500-39=461ns remainder is NOT qualified margin. Actual load/interconnect/MCU
aperture and monotonic receiver edges remain required; no numeric resistor is
selected and no termination waiver follows. Pulldowns are not source damping.
The source guard3us versus4*666ns gives336ns before uncertainty/skew, not a
measured receiver-local pass. 120clock-us per nominal4ms excludes software gaps;
status/DRDY checks are not a CRC or complete physical-edge guarantee.

**L3 decision:** read `REV_A_ANALOG_PILOT_L3.md`. Retain the six upstream
net-pair geometries for a proposed INTERNAL-TEST-ONLY first pilot rather than
reroute them now. All nine current locations were rechecked. This closes the
choice of pilot proposal, not manufacturing approval or external performance.
The release decision must explicitly accept the restricted purpose and the
possibility of another PCB revision before E1; no order or gate is authorized.
The existing 0x65/MUX101 internal test bypasses normal external selection; the
0x61/MUX001 alternative is internal short, NOT an external acquisition mode.
B1 remains required, BIAS/lead-off/SRB remain off. Mux switches do not isolate
pins from electrical damage or eliminate supply/package/parasitic coupling.
E1's external-source, noise, coherent-error and uncertainty limits stay intact.
Never claim that internal-test success qualifies the external R/C/channel path.

**L4 provision decision:** read `REV_A_SPI_PROVISION_L4.md`. Choose five
accessible series-component positions in the next custom-board revision, not
cut-and-flywire rework: AUX R117/U102.13 SCLK, R118/U102.12 MOSI,
R119/U102.11 CS, R120/U102.5 MCU-side MISO, and AFE R24/U1.43 DOUT.
These are proposed unused references, NOT implemented footprints or selected
nonzero resistor values. Four launches go into the nominal F.Fab body box
before their first via. R114 is a shunt pulldown and must stay receiver-side of
R120; replacing it with a small resistor would load MISO toward ground.
Prefer accessible existing-family 0603 lands with short driver-side routing;
final placement/parts/process still need native and physical-access review.
No parallel bypass: absent component means open, unlike a fitted 0-ohm link.
Zero ohms may represent an unpowered continuity baseline, never automatic
first-power/damping approval. No chip lifting, hidden cuts or aerial logic wires.

**Next source task:** implement these five series positions coherently across
schematics/BOM/PCB/contracts/fixtures, with failing split-net/path checks first,
native parity/refill/cut-track checks and independent review. Preserve unaffected
copper and all reference/domain/bypass guards; scope any necessary local change
explicitly. Do not write another generic rework/timing plan in place of this edit.
The three MCU-driven segments remain separate, not fixed by parts after U102;
no resistor at AUX J102 is automatically source termination at the DevKit.
DRDY/other control-channel requirements are not waived or silently added to the
five-site scope. Q1 is historical: record later accepted deltas without changing
its frozen input hashes. L1-L3/B1-B3, price searches and RFQ are not repeat tasks.

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
