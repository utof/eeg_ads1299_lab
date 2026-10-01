# Continue from this repository

**Current checkpoint: C4 routed AFE service access and carrier backing.**
Read root `AGENTS.md`, `docs/DEVELOPMENT.md` and the hardware baseline. Fetch live
main/open PRs, record SHA/tree and working-tree state. C4 is on
`feat/afe-service-access-recovered` until its actual checks/review/merge; after
merge use current main. Base is merged PR75 `10676fd14ffdeffe86f338342c9346c28f7cb1c8`.
An old chat progress message is not proof of published or tested source.

## Authored source and current scope

Canonical AFE PCB: `hardware/rev_a/layout/rev_a.kicad_pcb`; native project:
`hardware/rev_a/kicad/rev_a.kicad_pro`. Never regenerate the authored board with
the deliberately unrouted parking-grid importer. The auxiliary remains at
`hardware/rev_a/auxiliary/auxiliary.kicad_pro`, four sheets/48instances/212terminals.
No auxiliary PCB is routed and the firmware has no C2 handshake yet.

Read `REV_A_SERVICE_C4.md`, `checkpoints/20261001_service_c4.json` and the cable
target `hardware/rev_a/service_c4.json`. C4 adds AFE J3/J_SERVICE, matching C3's
six-way J104. Pin1/5 ground; pin2 actual AFE DVDD feed OUT; pin3 separate DVDD
sense; pin4 AVDD sense after R11; pin6 NC with no cable contact. Pins2/3 join
at the AFE rail, never at the auxiliary. No other regulator may drive pin2.
Existing20-position assignments, including CLKSEL/J2NC, remain unchanged.

J3 pin1 at75,15mm/180deg has11 new F segments, no new vias; final69footprints,
251pads,593segments,122vias. Every old68footprint/704track-via raw form remains
unchanged. The current board hash is
`60097ff4acf8408d5a172930de74bcd36aa50a379dd30a831e4bc64d3841c8a6`.
The new paths end at C33.1DVDD and C31.1AVDD. This is local rail sensing, not a
Kelvin connection at the ADC die. Native 0.95mm holes are not guaranteed
finished-hole dimensions. Exact assembly and process qualification are open.

Two carrier backing blocks brace the service connector at screened underside
regions without mounting holes. Nominal body/mate, solder-tail and northward
wire envelopes clear the existing frame/IDC parts in finite rigid checks.
K2 cartridges/bridges are unchanged; base support geometry and component
allocation changed. Real print/material tolerances, solder clearance, board
bending, pull retention, cable routing and tilted assembly still need unpowered
validation. Strict carrier/board binding was updated after this scoped review,
not weakened to accept arbitrary geometry changes.

Cable target: twoXHP-6 housings, tenSXH-001T-P0.6 contacts, fiveAWG24 wires,
150+/-5mm between wire faces, insulationOD0.9–1.9mm. Supplier wire/crimp process
is not selected or qualified. First test the detached cable1:1/isolation and
empty cavity6, then unpowered assembled continuity. The intentional on-board
DVDD and ground joins make assembled-only checks insufficient to detect every
cable wiring error. No powered mating; independent cable restraint required.

## Recovery and next bounded task

The failed turn retained its baseline source capture but not the uncommitted
service implementation. This continuation recovered recorded authoring operations
and reconstructed the design against exact main. New deterministic item UUIDs
and new red/fix recovery commits are intentional; no byte-identical restoration
of the lost uncommitted candidate or invented old ancestry is claimed.
Fresh missing-service and missing-support failures preceded the implementation.
Read the live PR's actual final-head evidence/review, not inherited counts.
The ground plane remains a single zone; its old mutation-order issue is
explicitly documented. No test or DRC threshold was relaxed.

**Next: implement guarded SESSION/ARM/READY/ARMED firmware integration test-first.**
Use the existing C2/C3 pin contract rather than a new pin-map redesign. Park
seven outputs low, wait for actual READY, create a fresh arm edge, and only then
start the existing clock/VCAP/reset sequence. A detected fault invalidates the
whole capture and requires a fresh sequence; restored rails alone must not
restart. Do not require the clock qualification before the control signals
which start the clock can propagate. Keep all external acquisition/release/body
use gates false. Then route the already-authored auxiliary schematic.

C3 review corrections are completed in PR75: ISO channel names2OUTA/3INB/
6OUTB/7INA were fixed without reversing valid electrical wiring; ERC suppression
and incomplete manifest/sheet validation were reproduced and closed. Preserve
those checks. C4 changes only the matching service-access assumption in the
auxiliary contract/validator, not its topology or previously selected pull values.

## Electrical limits that must survive continuation

Seven AFE control pulls changed 10k -> **42.2k RC0603FR-0742K2L**; five reserved
CLK/GPIO pulls remain10k. C3's loaded-high budget is97.213uA at the stated3.0-3.6V,
20-30C resistance/leakage conditions, fitting the cited0.1mA near-rail TXU row.
Its conditional disabled-low budget is0.575682V versus0.600V, only24mV margin.
This is not a blanket IOZ/rail-collapse guarantee. Installed resistance and
additional1uA board leakage are requirements to verify. IOZ/Ioff test conditions,
receiver validity, floating/partial rails and fast faults must not be extrapolated.
The reverse MCU lanes have a10uA input-leakage allocation, not a new datasheet
maximum. No old10k proof or nominal-R calculation alone qualifies this circuit.

Four monitor sense pulldowns and a separate100k buffer-feed bleed are explicit.
The bleed is not fast discharge or proof of detecting every broken feed. The
TPS3703 30us limit needs5%overdrive; its conservative5V test point4.47925V is
already belowE1min4.75V. No unconditional pre-E1 shutdown or arbitrary-short
protection exists. Analog source isolation, AVDD/DVDD asymmetry, monitor SENSE
backpower, initialQ, returned grounds and intermediate control-power behavior
remain unresolved physical conditions. RAILS_OK is not performance acceptance.

## Reproduce and verify

Use locked uv, not an alternate pip environment:

```sh
uv sync --locked --all-extras
uv run --locked --all-extras python -m tools.check
uv run --locked --all-extras python -m tools.check --schematic
uv run --locked --all-extras python -m tools.check --native
uv run --locked --all-extras python -m tools.check --firmware
```

Native KiCad9.0.2/libraries are pinned in the Schematic workflow; OpenSCAD2021.01
is needed by native mechanical tests. Arduino pins are in firmware/toolchain.json.
Missing tools/network/cache are blockers, not passes. Avoid simultaneous uv/hook
resyncs. A native ERC/XML/BOM/PDF export and all212-terminal partition check run
for C3 within `--schematic`, alongside the unchanged AFE native suite. Both
positive and wrong-but-ERC-clean auxiliary copies are tested. Gate source hashes
include the auxiliary, selected library lands, validator/tests and frozen graphs.
Keep transient output under ignored reports, never rewrite historical evidence.

The first observed red had8 failures. The implementation run found one facade
export-order mismatch after1155 tests passed; it was corrected rather than
relaxing the policy. Read the PR's final-head results for completed verification,
not the baseline or focused native run. Native fault copies/data perturbations
are not physical experiments. AI review is not professional qualification.

## Continue without private handoff dependencies

Publish source/tests and small necessary reference inputs to a discoverable PR;
read its remote SHA back, request independent review and verify actual exact-head
checks before merging. Preserve original failure-first history with merge commits.
Update this handoff and `REV_A_COMPLETION_ROADMAP.md`. Every report starts with
TLDR and a category/remaining-turns/status/next-step table; distinguish inherited,
new, local, hosted, unpublished and unexecuted work. Do not use test-count growth
as engineering progress. Tool-transfer helpers are not project dependencies or
commands to overwrite authored CAD. A missing chat reply may still have a merged
PR; inspect live GitHub before recovering anything from old attachments.

## Retained decisions and constraints

K2 carrier/cartridges exist as editable native CAD; physical fit/material/retention
is open. C1 uses permanent controller tails: returning to bare-board USB programming
requires complete accessory removal. Both DevKit USBs stay excluded with the
proposed acquisition wiring. No controller fanout/auxiliary board is yet built.

E1 remains a limited1-10kohm dummy-source,1-40Hz,250SPS/gain24 target, not electrode
qualification. JLC04161H-7628 is a design stack target, not a factory-confirmed
construction. The six-pair upstream coupling item, #48 capacitor qualification,
#45 vendor/fixture/mechanical/interface evidence and earlier supply/output-route
tradeoffs remain open. Fifteen new auxiliary bypasses do not count as the33AFE
capacitors or qualify their replacements. All costs for the auxiliary/cables/
service access remain unquoted; old$94.34 planning does not prove$100compliance.
The user is learning electronics; explain decisions plainly and keep slices finite.
All purchasing/fabrication/powered-connection/body-use flags remain false.
