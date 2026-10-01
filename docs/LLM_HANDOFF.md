# Continue from this repository

**Current checkpoint: C3 native auxiliary schematic and coordinated AFE bus pulls.**
Read root `AGENTS.md`, `docs/DEVELOPMENT.md` and the hardware baseline. Fetch live
main/open PRs, record SHA/tree and `git status --short`, and preserve unrelated
changes. Start from the C3 PR on `feat/auxiliary-c3` while open; after merge use
current main. The parent is `98362c6b6445ddb402ddf942b1c81af738eebe56` (PR74).
Do not assume an old chat report or a queued check describes the current head.

## Authored source and current scope

AFE board: `hardware/rev_a/layout/rev_a.kicad_pcb`; its existing three-sheet
project lives in `hardware/rev_a/kicad/`. **Never regenerate this board from the
parking-grid importer.** C3 changes only seven existing bus-pull component
Value/MPN/BOM_ID fields in the board and digital schematic; reversing those
fields recovers both original files exactly. All copper, pads, placement and
zone fill remain intact. The new board hash is
`f11c9651fb0cebb01bf2cc7d6ef1be0a0093664dfacc4f193f90aab14bdbd6c7`.
The 68-footprint/245-pad/582-segment/122-via inventory is unchanged.

**Auxiliary native project:** `hardware/rev_a/auxiliary/auxiliary.kicad_pro`.
Four editable sheets, separate local symbol/land tables and a complete
`contract.json`: 48 instances, 212 terminals, 43 native BOM component rows.
Five numbered solder-land groups are PCB copper, not purchased connectors.
No auxiliary PCB has been placed or routed. Read `REV_A_AUXILIARY_C3.md` and
`checkpoints/20261001_auxiliary_c3.json` for exact scope, changed references,
primary sources, source-only calculations and unresolved physical conditions.

The console ISO7721DR remains split-powered HOST versus TARGET. Three TXU0304PWR
buffers use actual MCU3V3/AFE_DVDD. Four monitors use MCU3V3 for VDD, not the rail
each senses. ARM_BUFFER is not READY-gated, so recovery cannot manufacture an
arm edge from held ARM. Existing firmware does NOT implement this handshake.
The native schematic has zero ERC findings under explicit external endpoint
role assumptions; this is not installed power-loss protection or bench approval.

## Next bounded task

**Add the matching, mechanically supported AFE service feed/sense access.**
The auxiliary now selects J104 `B6B-XH-A(LF)(SN)` with pins1/5 return,2 actual
AFE DVDD feed,3 separately carried DVDD sense,4 AVDD sense,6 NC. The matching
AFE connector/pads and cable were deliberately NOT added by C3. Identify a
real placement with access/clearance and power-return review, then migrate
AFE schematic/BOM/profile/board/contract/native fixtures together. Preserve all
existing K1/K2 contacts and route guards. Do not repurpose CLKSEL or J2 NC,
join remote sense to its feed locally, or authorize wires on tiny C32/C33 pads.
The existing board is not yet the complete physical C1+C2 assembly.

After service access, implement the C2 firmware handshake test-first and then
auxiliary layout. Seven MCU outputs start parked low; firmware requires settled
READY and a fresh ARM, then starts the existing clock/VCAP/reset sequence.
Do not require completed VCAP/clock qualification before the control signals
that start that clock can pass. Detected faults invalidate the whole session.
Do not enable acquisition or body use as part of these edits.

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
