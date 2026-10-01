# Continue from this repository

**Current checkpoint: C1 controller termination and split-powered console target.**
Start from live main/open PRs, root `AGENTS.md`, this file and `DEVELOPMENT.md`.
Record the actual SHA/tree and worktree status. Preserve unrelated edits. Base
for C1 is merged PR72 main `2b11ddec03a4fad97f6dbec2f00675fe5a48c09c`, tree
`8b9b175d35f652abe8867f6891827e99040c128d`. Use the live
`docs/controller-interface-c1` PR until merged, then current main. Do not repeat
K1's header migration or K2's carrier CAD because an old chat reply was missing.
Read actual exact-head checks/reviews before merge; preserve merge history.

Canonical PCB is `hardware/rev_a/layout/rev_a.kicad_pcb`; native project/sheets
are under `hardware/rev_a/kicad/`. Never rebuild the authored board with the
parking-grid importer. Current PCB SHA256 remains
`dfe893f958128ba28eb69188cf6debbbc9fcafa0ef5dd67bd58627d4b8a26842`, with
582segments/122vias/68footprints/245pads. C1 changes no CAD, BOM/profile,
firmware, production model, dependencies, old design rules or approval gates.

## Current result and next bounded task

Read **`REV_A_CONTROLLER_INTERFACE_C1.md`** and its source-bound
`checkpoints/20261001_controller_interface_c1.json`. C1 selects a numbered,
captive solder fanout for the existing K1 free-ended20-contact cable, with
individual ground landings, separate power branches and permanent controller
header-tail terminations. This is not a fabricated harness or auxiliary PCB.
Verify contact identity by continuity, never ribbon color or mating-view guess.

C1 selects **Adafruit CP2102N Friend product5335 + TI ISO7721DR (D8, non-F)**.
The HOST side uses the module's3V output/same VIO supply; TARGET uses the MCU's
own3.3V at DEVKIT.J1.2. No isolated power converter or host-ground connection to
target. ISO.3/2 are host TX/RX; ISO.6/7 connect targetRX17/TX18. Existing
`INTERFACE` worksheet names refer strictly to ISO's TARGET side, not hostUSB.
Both DevKit USB sockets stay disconnected in the proposed acquisition setup;
programming remains DevKit-only with all target accessories disconnected.
Program before permanently attaching controller tails; later bare-board USB
programming needs their removal, not merely unplugging HOST USB. A removable
controller adapter would be a later reviewed alternative, not existing hardware.
Actual module revision, auxiliary schematic/layout, assembly, USB configuration,
suspend/load/edge behavior and physical isolation remain unverified. ISO7721's
unpowered output is **undetermined**, NOT specified high impedance; its default
high requires the receiving side powered. Brownout is not covered by a binary
rail-state table. No component rating is whole-system/body-use qualification.

**Next: resolve the nine-line AFE bus and rail-loss/startup protection.** The
seven MCU outputs and two AFE outputs are still direct across separate3.3V
regulators. The console barrier alone does not protect them. Account for actual
AFE DVDD, MCU3.3V, AVDD and analog-source startup; software R/V acknowledgments
are not a later-fault interlock. AFE.J1.19 isCLKSEL, NOT aDVDDsense lead; no
silent J2NC reassignment. Choose one fail-closed hardware architecture with
actual sensing or a separate explicit limited pilot-risk disposition before
laying out the combined fanout/interface board. Any new sense lead/pad, buffer,
supervisor or circuit change needs coordinated review. Do not simply add a
power-up sequence and call independent rail loss solved.

C1's executed ledger/rejection controls are source/data checks, not native CAD,
electrical emulation or physical tests. They account for20AFEcontacts,8ISO pins
and16stable rail states; all states keep powered setup prohibited. Read the
C1 PR's final-head CI and review separately from inherited PR72 results.

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
