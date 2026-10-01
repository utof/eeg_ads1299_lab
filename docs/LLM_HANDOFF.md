# Continue from this repository

**Current checkpoint: C2 pin-level bus-interlock architecture candidate.**
Start from live main/open PRs, AGENTS.md and DEVELOPMENT.md. Record exact source
SHA/tree and worktree state. C1 is merged at
`99bafcea6b3fa518e76704061daf722aae539360`, tree
`1448f9179fffaa43431053b4383ba9cc80fa98f2`; this continuation is on
`docs/bus-interlock-c2` until reviewed/merged. Use its live PR, then current main.
Preserve unrelated edits and merge history; do not repeat K1/K2/C1 because an
old chat reply is missing. No old ZIP or runtime capture is a source dependency.

Canonical PCB: `hardware/rev_a/layout/rev_a.kicad_pcb`; sheets/project:
`hardware/rev_a/kicad/`. Never regenerate the authored board with the importer.
PCB SHA256 `dfe893f958128ba28eb69188cf6debbbc9fcafa0ef5dd67bd58627d4b8a26842`
remains unchanged, with582segments/122vias/68footprints/245pads. C2 changes no
CAD, BOM/profile, firmware, production model, dependencies, rules or approval.

## Current result and next bounded task

Read **REV_A_BUS_INTERLOCK_C2.md** and
`checkpoints/20261001_bus_interlock_c2.json`. Three TXU0304PWR buffers cover
seven MCU-to-AFE and two AFE-to-MCU lanes; A supply is actual MCU3V3, B supply
actual AFE DVDD. Four TPS3703 monitors sense MCU3V3, DVDD, AVDD and VIN5, but
ALL monitor VDD pins use MCU3V3 with the local control logic. The two3.3V
variants are TPS3703A4330DSER; the two5V variants TPS3703A5500DSER. C2 is a
pin-level architecture target, **not an installed protection circuit**.

SN74LVC2G74DCUR plus two Schmitt SN74LVC1G97DBVR gates latch a fresh ARM edge;
any detected rail fault or SESSION low clears it. Good-rail recovery, SESSION
release and an ARM input held high across a fault do not automatically restart.
Prospective controller-only SESSION/ARM_REQ/ARMED/READY roles are GPIO14/9/16/15 at
DEVKIT.J1.20/15/9/8. READY reads conditioned CLR_N before a fresh arm edge. They are not yet implemented in firmware/profile. All three
TXU enables share the latch output; the existing seven AFE10k pulldowns remain.
No hardware or software review gate was enabled.

Do not claim unconditional brownout safety: detector30us is specified only at
5%overdrive; startup300us is typical, not a maximum. The5V window's calculated
UV range4.715-4.785V is not E1's4.75V guaranteed cutoff. Arbitrary fast shorts,
intermediate/unpowered control behavior, supervisor SENSE back-power and actual
loaded output/input margins remain explicit. In particular TXU's0.1mA near-rail
VOH row cannot qualify an existing10k load drawing up to0.36mA. The document
contains the fixed corner calculation and the concrete4.47925V overdrive
counterexample. Do not relabel these unknowns as closed by a truth-table pass.

**Next: native auxiliary C1+C2 schematic**, with all numbered cable landings,
actual rail feed/sense access, buffer/monitor/logic pin nets, bypasses and defined
passives. Resolve loaded DC margins and detector/sense limits while doing that
schematic; revise a part or passive explicitly if needed. AFE.C33.1/C32.1 are
net anchors, not approved physical wire attachments. J1.19 remainsCLKSEL and
J2NC staysNC. Distinguish buffer power-current feeds from remote sensing and
provide supported/keyed access. Any necessary AFE pad/connector change must be
coordinated across schematic/BOM/PCB/tests, not improvised wires or re-imported
layout. Then implement the matching guarded startup/fault firmware separately,
failure-first, with actual S3 compilation and no gate relaxation.

VCAP1 and completed clock qualification must remain downstream of bus enable:
first arm with all seven outputs low, then raise PWDN/CLKSEL, accumulate an
uninterrupted valid-clock interval and retain fresh VCAP1 confirmation before
reset. The current150ms wait starts after clock controls are raised. A fault
must invalidate timing/capture even inside a blocking wait. Digital buffering
does not protect analog inputs or qualify AVDD-loss/DVDD-alive operation.

C1's Adafruit5335/ISO7721DR separately powered console remains the target;
HOST/target returns must not be bridged. Existing INTERFACE aliases denote only
the ISO TARGET side. Permanent controller-tail service/programming restrictions
remain; neitherDevKitUSB is approved with accessories attached. C2 adds ten
unpriced auxiliaryICs and13bypass requirements, separate from C1'stwo/AFE's33.
Actual module/fixture/cable/rail-loss behavior and the delivered budget stayopen.

C2's executable ledger/corner/latch checks are source/data/Boolean analysis,
not native electronic simulation, installed interlock testing or addedproject
tests. The baseline99b ordinary gate passed1108+14subtests/86.31%branches; read
the C2 PR's actual final-head checks/review separately. A clean unchanged-board
DRC or a firmware compile does not validate a proposed auxiliary circuit.

## Previous work and still-open evidence

K2 editable solids are `hardware/rev_a/mechanical/view_k2.scad` and
`carrier_k2.scad`; read `REV_A_CARRIER_K2.md`. This is an initial fit prototype,
not a released print or arbitrary-tilt/force/material/insulation proof. Remove
bridges before PCB installation; release cable bars before withdrawing plugs.
Actual socket width<=5.30mm is an inspection requirement, not a manufacturer
maximum. Full seating, rivets/fasteners, liners, print tolerances, retention,
combined-axis tilt, controller support and terminated cable routes remain open.
PR72 added supported OpenSCAD2021.01 checks and retained failed-process logs;
56CAD cases are included in154native, not additional. Keep source-bound mesh
limits, not the earlier chat's unsupported102count.

K1 headers are HTSW-110-07-T-D; cable target IDSD-10-S-04.00-T-G-ST4. Bare sockets
remain unkeyed without validated capture. The header-field migration preserved
all old routing; no second migration is needed. Solder recipe and finished-hole
DFM remain open. Old M1/K1 hashes are historical records, not stale values to
rewrite. See `REV_A_CONNECTOR_K1.md` and `REV_A_MECHANICAL_ENVELOPE.md`.

Capacitor #48: `REV_A_CAPACITOR_E1_DECISION.md` maps33fitted capacitors.
Qualification shortlist is GRM21BR61C106KE15L (10uF), GRM188R61C105KA12D (1uF)
and GRM188R72A104KA35D (100nF), NOT substituted parts. Exact lifecycle/assembly
and guaranteed effective-C data remain open; all three minima stay unknown.
Four old bulk cores are discontinued;22old1uF/100nF positions have planned-stop
cores, not all already obsolete. InternalVCAProles and the1uF16Vcandidate need
pin-specific review. Typical curves/tolerance arithmetic are not guaranteed
biased-C minima. One future coordinated26-instance migration only after evidence
or a separately reviewed limited-pilot decision. Do not repeat catalog searching.

`REV_A_STACKUP_BENCH_REQUIREMENTS.md` selects JLC04161H-7628 as the design target,
not a confirmed factory stack. NP-155F availability, per-layer tolerances,
35/40.64um copper and4.6/4.43coreDk differences, viaDFM remain open. Prepared
supplier questions were not sent. Overall thickness+/-10% is not per-gap bounds.
E1 is limited person-disconnected1-10kohm calibrated dummy input,1-40Hz,
250SPS/gain24, noise<=0.50uVrms/coherent<=0.50uVpeak with explicit allocations
and uncertainty. High-Z/asymmetric cases are reported stress, not qualified
scalp use. Fixture capacitance, spectra and measurement floors remain unproved.
Do not inverse-filter/notch/cancel an error into a pass or relabel an E1failure.

The nine residual crossings remain ONE OPEN six-pair item, pending confirmed
construction and combined repair/pilot-risk review. Earlier mutual-C examples
are not PCB extraction or actualE1loading. AVDD1/MISO/DRDY/CH1N repairs are
merged; preserve longerVCAP3/C24 andAVDD56/C14 paths,44.132mmDRDY,
33.884mmCH1N and4.5mmDNPbranchimbalance. Read their detailed reports; don't
rerun authoring scripts over current source. A DNP footprint still has copper.
The distinct chat-local1689234/issue45variant76502e7 must not overlay main.

## Reproduce and finish

```sh
uv sync --locked --all-extras
uv run --locked --all-extras python -m tools.check
uv run --locked --all-extras python -m tools.check --native --schematic
uv run --locked --all-extras python -m tools.check --firmware
```

Install the declared native tools first; missing tools/network/cache are blockers,
not passes. OpenSCAD2021.01 is required for native; KiCad9.0.2/libraries are pinned
in the schematic workflow and Arduino in `firmware/toolchain.json`. Ordinary
checks stay renderer-free. Avoid concurrent environment resync. Local, hosted,
new, inherited, native CAD, target compilation and physical execution are distinct.
Publish each slice to a named PR; read back actual head, update this checkpoint
and roadmap, retain small durable evidence and commands/actualSHA/outcomes.
Keep unfinished source discoverable without chat artifacts. Merge only after
required checks and actual review. Report TLDR then category/remaining-turns/
status/next-slice table, useful evidence and one next bounded task.

User is an electronics beginner; favor explained bounded progress. Additional
parts objective$100 is NOT delivered/instrumentation budget. Planning$94.34
includes an unproven$3harness reserve; C1host module listed$5.95alone, with
isolator/auxiliaryboard/cables/fixture/tax/shipping still unpriced. No purchase
or compliance with$100 is established. Owned unspecifiedESP32/Arduino/electrodes
do not confirm the selected ADS/S3, actual revision or electrode properties.
Keep #45/#48 and all purchasing/fabrication/powered-connection/body-use flags
unchanged/false. No BIAS, lead-off or external acquisition is enabled. Pilot
release and later physical validation are separate; neither has been granted.
