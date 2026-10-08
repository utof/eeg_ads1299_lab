# Rev A roadmap - PR98 has fail-first tests; the scoped CAD edit remains

L4 merged in PR97 at c2f93ee3; L3/PR96, L1/L2, B1-B3 and Q1 are retained.
Draft PR98 (`work/l5-spi-series`) contains the unfinished fail-first stage.
Five missing-position failures and one preserved-shunt pass were observed locally
and in first-head hosted Python3.13 quality. This is not PCB progress, a green
full gate or native verification; inspect live-head results before continuing.
L4 rejects routine trace-surgery fallback and selects five custom-board SPI
series positions. It does not add them, choose damping values or release hardware.
Read live main/open/recent PRs, AGENTS, REPOSITORY_PUBLICATION and the handoff.
Moscow remains the planning destination; detailed prices/outreach stay paused.

| Category | Remaining substantial turns | Done/status | Next slice or blocker |
|---|---:|---|---|
| SPI provision method | 0 for decision | Five positions identified; four source escapes enter nominal package body boxes | No claimed solder/rework qualification or fitted parts |
| Five-position implementation | 1-2 source turns | PR98 has six topology tests; the five required positions still fail as missing. No CAD/BOM changes | NEXT: finish coordinated schematic/BOM/PCB/contracts/fixtures in PR98, then native both-side faults/refill/parity/access review |
| Other digital-channel disposition | 1 bounded decision plus needed evidence | Three MCU-driven stages and DRDY/control paths explicitly separate | Actual source-end access/channel evidence or bounded pilot disposition; not solved by five pads |
| Analog pilot choice | 0 for proposal | L3 retains six upstream pairs for internal-test-only purpose | Explicit scope/revision-risk acceptance at release; E1 unchanged |
| Components / manufacturing | 1-2 plus required evidence | Existing candidates and Q1 process questions retained | Accepted stack/component/assembly decisions and coordinated changes |
| B1-B3 physical setup | Assembly/equipment-dependent | Existing plans and B2 run card, no new framework | Actual contacts, insulation, restraint, instruments and approved limits |
| Fabrication release | 1 after prerequisites | Not released; Q1 remains a frozen quote snapshot | Consistent revision, restricted purpose, remaining dispositions and order approval |
| First power / internal capture | Approved physical-work dependent | Firmware gate false, no acquisition | Inspected real assembly and measured commissioning under separate permission |
| Prices / RFQ | Paused | One canonical unsent packet | No duplicate packet or price/stock campaign |

Estimates overlap and exclude supplier/fabrication/shipping/physical time.
Five positions cover the custom-board SPI drivers, not every output in the
system. The three MCU launch segments and DRDY/control/fault behavior remain
subject to their own conditions. No universal resistor, source-impedance value,
loop/edge budget or first-power setting is inferred from nominal geometry.

Next resume PR98 and implement AUX R117-R120 and AFE R24 as proposed in L4, not a further
paper provisioning exercise or a second red-test PR. Keep existing R114 on the receiver side, avoid
parallel bypasses and verify both sides of the added parts. No bare-IC lifting,
blind trace cuts, global footprint edits or enlarged reference allowances.
Keep the implementation separate from unrelated refactors and capacitor choices.
All #45/#48 and purchase/fabrication/rework/construction/mating/power/external-
acquisition/person or animal connection permissions remain unchanged.

Local Git network access, the locked Python environment and pinned KiCad were
unavailable in the starting session. GitHub source publication did work. Do not
claim a green revision or merge until the actual implementation and exact-head
checks/review are complete; keep the original 450 s CAD budget and safety gates.
