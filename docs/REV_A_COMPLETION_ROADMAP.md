# Rev A roadmap - L5 hardware candidate preserved, not yet applied or native-verified

Main was checked at c2f93ee3 (PR97). Draft PR98 remains the continuation branch.
An eleven-file LOCAL candidate adds all five DNP SPI positions to schematics and
PCBs, with BOM/contract guards and focused tests. Its exact patch is preserved at
[the L5 packet](recovery/l5_spi_candidate_20261008/README.md), NOT applied to active
hardware. No native export/refill/DRC or full locked candidate gate has passed.
Read live state, AGENTS, REPOSITORY_PUBLICATION and LLM_HANDOFF before continuing.

| Category | Remaining substantial turns | Done/status | Next slice or blocker |
|---|---:|---|---|
| SPI provision method | 0 for decision | L4 selects five accessible positions; no routine trace-surgery fallback | Retain scope; no chosen resistance or fitted parts |
| Five-position source integration | 1-2 with working pinned CAD | Real local eleven-file candidate preserved; not applied in PR98 | Recover exact bytes into PR98; native exports/refill/parity/DRC, both-side cut/short faults, access/driver-route review |
| Other digital-channel disposition | 1 bounded decision plus evidence | MCU launch stages and DRDY/control paths separate | Actual source-end/channel evidence or explicit limited-pilot disposition |
| Analog pilot choice | 0 for proposal | Six upstream pairs retained for internal-test-only pilot | Restricted purpose and possible revision cost accepted at release; E1 unchanged |
| Components/manufacturing | 1-2 plus required evidence | Existing parts/process proposals and Q1 retained | Accepted stack/component/assembly decisions and coordinated changes |
| B1-B3 startup setup | Assembly/equipment-dependent | Existing plans and B2 run card, not new worksheets | Real contacts, insulation, restraint, instruments and approved limits |
| Fabrication release | 1 after prerequisites | Not released | One consistent revision, restricted purpose and remaining approvals |
| First internal capture | Approved physical-work dependent | Firmware gate false; no acquisition | Inspected assembly and separately approved commissioning |
| External-input characterization | Later, measurement-dependent | Not qualified; possible additional PCB revision | Existing external-source/noise/coupling/uncertainty requirements |
| Prices/RFQ | Paused | Canonical frozen unsent Q1 packet | No duplicate packet, detailed lookup or outreach |

Estimates overlap and exclude supplier responses, fabrication, shipping and
measurements. The candidate uses accessible lands after retained source escapes;
R24 has about 10.85 mm driver-side track center-line and two vias, not a measured
SI pass. All existing footprints, including R20, stay in place. R114 remains a
receiver-side shunt. An unpopulated series position is open, not zero ohms.

Local diagnostics (104 installed-pytest passes plus 7 subtests and static route
checks) are not a native/locked pass. The published active fixtures still lack
five positions, so the original five red tests remain. Do not skip them, edit
XML by hand, or interpret old hosted review/CI as approval of this candidate.
No #45/#48, purchasing, fabrication, physical work/mating, power, external-input
acquisition or person/animal permissions changed. Next recover and natively
integrate the preserved candidate IN PR98, not another generic planning slice.
