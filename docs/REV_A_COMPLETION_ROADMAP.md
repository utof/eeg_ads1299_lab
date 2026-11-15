# Rev A roadmap - visual breadboard guide and bounded CAD runtime repair

Checked 2026-10-15: PR101 is merged at
`9d2fc299a348fd5b9c011f9493feab9d21f04658`, tree
`fa56722c1868d3624220a256450e717c40e13d2c`, identical to accepted head
`79606a49595077593f3e5fb49f379aaef8351839`. The merge message preserves all
five successful hosted checks, resolved reviews, artifact hashes and local limits.
Read `LLM_HANDOFF.md` and the [hosted capability preflight](REPOSITORY_PUBLICATION.md#hosted-capability-preflight).
Do not repeat recovery, integration, supply, reference or nominal K2 repairs.

| Category | Estimated remaining substantial chat turns | Done/status | Next slice or blocker |
|---|---:|---|---|
| Local development setup / CAD runtime | 0 installation/acceptance | PR101 merged; full CAD passed 310 cases in 250.896 s; cancellation cleanup reviewed | Local ordinary timeout remains recorded; no ordinary parallel speedup adopted |
| SPI provisions, reference/supply repairs, K2 nominal review | 0 for source/design work | PR98 merged; physical access/fit unqualified | Actual fitting/tool/joint inspection later |
| Remaining digital channels | 0 for paper choice | PR99 L6 retained paths with reviewed revision fallback | Before-fabrication access/revision-risk acceptance; interlock evidence before ADC enable |
| Proposed fitted components/stack | 0 for selection | PR100 selects five33ohm parts, capacitor shortlist, common stack target | Applied to active source 2026-11-15 (see migration row) |
| Q04 capacitor design disposition | 0 for this bounded review | Conditional pilot decision recorded; EVM does not validate16V substitution | Internal-node/startup and local LDO C/ESR conditions before power; final build-risk acceptance |
| Assembly ownership | 0 for make/buy choice | Outsource boards/TH/tails/crimps; no specialist tool purchase assumed | Actual supplier/process/hole/fixture responses |
| Coordinated BOM/CAD migration | 0 | Done 2026-11-15 on branch `fix/rev-a-review-fixes`, unpublished: five 33 ohm fits, 26 AFE capacitor identities, J102.1 no-connect, J105/tail silk, LVC1G97 names (commits 8644eea, d2f185f, 52c42d8, 33ef3fa) | Publish to a PR and pass hosted CI; Q03 assembler answer still open |
| Fabrication/purchase release | 1-2 after prerequisites | Not released; DO-NOT-FABRICATE marking kept | Todo item 3: hosted fabrication export and release marking; then accepted revision, exact-part supply and delivered quote |
| Standalone breadboard learning | 0 planning; 1 optional measurement follow-up | Kit, row layouts, charge curve and checked UT139C setup example ready | Receive the kit, identify meter and record first readings |
| Breadboard ADS1299 + ESP32-S3 prototype (separate from Rev A) | 0 for firmware/card; 1-3 follow-ups after measurements | 2026-11-16, branch `feat/breadboard-s3-target`, unpublished: breadboard firmware build (`-DEEGLAB_BREADBOARD_S3`) and [bring-up card](BREADBOARD_S3_BRINGUP.md); nothing built or measured | Publish to a PR; user builds steps 0-10; electrode mode (steps 11-12) waits for the user's decision |
| Laptop capture rehearsal | 0 for this rehearsal | Existing real localhost path:2248 synthetic samples, two intended gaps detected,10Hz peaks on four channels | Actual ADC capture waits for assembled-board commissioning |
| Rev A startup/internal capture | 1-2 planning turns plus assembly/measurements | B1-B3 plans exist; B2 equipment gap explicit; firmware gate false | Actual source/probes, numeric commissioning limits and prior interlock evidence |
| External-input characterization | Later, measurement-dependent | Unqualified; revision may be needed | Existing E1 requirements |
| Body-connected use | Outside this pilot | Not approved | Separately scoped hardware/safety engineering |
| Quote packet/outreach | 0 packet reconciliation; user/supplier dependent | Q1 current addendum added; frozen CSVs/manifest unchanged; unsent | Paused for budget (see current todo); then recipient/contact authorization and Q01-Q10 responses |

**Breadboard ADS1299 prototype (2026-11-16):** the user will hand-solder an
ADS1299-4 onto an adapter and wire it to an ESP32-S3-DevKitC-1 on a breadboard,
battery only. A separate firmware build (`EEGLAB_BREADBOARD_S3`: no C2
interlock, ID 0x3C or 0x3E, console-selected test signal or shorted inputs,
lead-off and bias off) and [BREADBOARD_S3_BRINGUP.md](BREADBOARD_S3_BRINGUP.md)
cover bring-up steps 0-10. The Rev A build is unchanged (identical loadable
sections). There is no electrode mode; adding one is the user's separate decision.

**Two separate practical paths:** the [breadboard kit](BREADBOARD_FIRST_STEPS.md)
is ready to obtain for the standalone passive exercises. It needs neither an
ADC purchase nor a PCB release. The selected ADS1299 is surface-mount and its
prototype remains the designed two-board assembly; it does not plug directly
into that breadboard.

For the Rev A purchase/build decision, allow roughly **2-4 substantial engineering
turns after the needed responses/decisions**, with overlap between rows. Supplier
responses, delivery/manufacturing, user decisions and physical measurements are
excluded. No date promise or percentage of safety is implied. Another planning
turn alone cannot create supplier acceptance or measured results.

Four earlier preparation steps: node-specific Q04 disposition;
outsourced assembly ownership; the first breadboard kit/experiments; and current
Q1/B2 reconciliation. No BOM/CAD migration, new production code, framework,
physical measurement or supplier message occurred in those steps. The shipping
continuation adds a bounded CAD execution repair, three breadboard figures and
an existing-tool capture rehearsal. All existing Rev A gates
remain closed, and a software check is not hardware qualification.

Keep the full ordinary/native/CAD/firmware selections and71%branch floor.
Local and hosted timing failures remain failures even if an unchanged retry
passes. Exact-head verification of this continuation is recorded in its PR;
previous accepted-head or main runs are not a substitute.

## Current todo, 2026-11-01: fabrication paused for budget

The user has no budget for fabrication yet. Quote outreach is paused (quotes
expire; send only when purchase is near and the user authorizes contact).
Domestic candidates noted: Rezonit (Moscow) and Elektrokonnekt (pselectro.ru).
Elektrokonnekt's public calculator (price list 25.09.2026, incl. 22% VAT), 4
layers, 35 um foil, ENIG, 5 boards each, offered 1.5 mm, not 1.6 mm: AFE
6060 RUB and AUX 7150 RUB standard (~20 days). ENIG is "non-standard" there
with a 6 dm2 minimum (13 AFE / 9 AUX boards), so real cost is higher. Bare
boards only; parts and assembly are unpriced. JLCPCB remains an option.

Two independent read-only reviews of main `652193d` (2026-11-01) found
computer-side work still blocking fabrication or first power. Unverified
review output until each item is fixed with a failing-first check:

Items 1-2 and WIRE-03/WIRE-04 were **done 2026-11-15** (base `f4c4294`,
commits `8644eea` S1-S4 rebinding, `d2f185f` WIRE-01/04, `52c42d8` WIRE-03,
`33ef3fa` FAB-01/02) on branch `fix/rev-a-review-fixes`, not yet published or
hosted-verified. Findings are recorded as fixed in `reviews/paths/`.

1. **Done 2026-11-15. Defect, before fab:** AUX J102.1 is TARGET_GND
   (`auxiliary/contract.json`, schematic, PCB pad), but it mates one-to-one
   with DevKit J1.1 = 3V3 (`harness.py` `_DEVKIT_J1`). As documented, tail 1
   shorts the DevKit 3V3 rail. Make J102.1 no-connect, keep ground on J102.22,
   re-point B2 O6/F1 to J102.22, and add a contract-vs-`_DEVKIT_J1` test.
2. **Done 2026-11-15. Before fab:** apply the coordinated BOM/CAD migration (five SPI fits,
   26 capacitor identities) now; the reviews judge Q03 not blocking because
   the same KEMET part/land is already active on AUX. Fold item 1 in.
3. **Next. Before fab:** add a reproducible hosted fabrication export (Gerber,
   drill, placement, designator BOM, fab notes) and the release marking
   that replaces the DO-NOT-FABRICATE silkscreen.
4. **Before power:** numeric B2 H1 limits from datasheets and load
   allocations, including supply setpoint versus TPS3703 window margin.
5. **Before power:** a console-selected firmware hold (C2 armed, ADC parked)
   for interlock evidence before ADC bus enable, plus late-ARMED and
   lost-READY test scenarios (two C2 guards survive deletion today).
6. Rough total budget estimate from public prices; no supplier contact.
7. Optional while saving: standalone breadboard kit (`BREADBOARD_FIRST_STEPS.md`).
8. When budget exists: choose fab, confirm 1.5 mm (K2 carrier hard-codes
   1.6 mm), prepare the Russian-language request.

Path reviews of 2026-11-15 (`79d0c9f`) added: **MECH-02**, the K2
cartridge cable window is closed so the ribbon socket cannot be loaded (fixed
2026-11-15, `87f81ef`: open-topped slot closed by the cover; quote item A05
must cite the new source); MECH-05 suspected, the J1
ribbon may not reach AUX J101 (paper mock-up); WIRE-03, add "+5V / GND" and
pin silk on J105/J102 together with item 1 (done 2026-11-15, `52c42d8`); ANALOG-02, the BIAS loop needs a
firmware rule of at most 2 sense inputs before BIAS is enabled (no hardware
change). Footprints, pinouts, polarity and analog values all matched the
datasheets. The PiEEG-8 comparison adopts nothing before fab (see
`reviews/paths/analog-quality.md`).

Reviews found nothing critical in firmware register/timing settings or the
capture/recording decode path. Review coverage, finding IDs and evidence are
tracked by path in [`reviews/`](reviews/README.md); continue reviews there.

**Next bounded step:** publish the 2026-11-15 revision to a PR and pass hosted
CI, then item 3: a reproducible hosted fabrication export (Gerber, drill,
placement, designator BOM with MPNs, fab notes incl. FAB-08 fills/holes) and the
release marking that replaces the DO-NOT-FABRICATE silkscreen (FAB-03/04).
