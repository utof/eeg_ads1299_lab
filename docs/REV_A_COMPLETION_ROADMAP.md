# Rev A roadmap - L5 source guards repaired; native integration remains

Continue draft PR98 (`work/l5-spi-series`) from the live head. Main was c2f93ee3.
The eleven-file candidate is still preserved, NOT applied to active hardware.
This slice repairs source population/inventory and exact-delta preservation
checks. It does not add or qualify physical resistor positions. Read AGENTS,
REPOSITORY_PUBLICATION and LLM_HANDOFF before publication or continuation.

| Category | Remaining substantial turns | Done/status | Next slice or blocker |
|---|---:|---|---|
| SPI provision method | 0 for decision | L4 selects five accessible positions, no trace-surgery fallback | No selected resistance or fit approval |
| Clock split coverage | 0 for selector repair | Both MCU_MISO segments remain screened | Native distance/edge evidence still required |
| DNP/inventory and preservation | 0 for this source repair; native confirmation pending | Field/native-bit/BOM guards and exact candidate delta; original snapshots retained | Independent review and pinned native run; remaining export consumers |
| Five-position hardware integration | 1-2 with working CAD and source transfer | Original candidate unchanged; still unapplied in PR98 | Ten native cuts/five bypass shorts, native exports/count updates, refill/parity/DRC and access review |
| Other digital-channel disposition | 1 bounded decision plus evidence | MCU launch stages and DRDY/control paths separate | Actual source-end/channel evidence or limited-pilot disposition |
| Analog pilot choice | 0 for proposal | Six upstream pairs retained for internal-test-only pilot | Restricted purpose/revision risk accepted at release; E1 unchanged |
| Components/manufacturing | 1-2 plus required evidence | Existing parts/process proposals and Q1 retained | Accepted stack/component/assembly decisions |
| B1-B3 startup setup | Assembly/equipment-dependent | Existing plans and B2 run card retained | Real contacts, insulation, restraint, instruments and approved limits |
| Fabrication release | 1 after prerequisites | Not released | One consistent reviewed revision and restricted-purpose acceptance |
| First internal capture | Approved physical-work dependent | Firmware gate false; no acquisition | Inspected assembly and separately approved commissioning |
| External-input characterization | Later, measurement-dependent | Unqualified; further PCB revision possible | Existing external-source/noise/coupling/uncertainty requirements |
| Prices/RFQ | Paused | Sole frozen unsent Q1 | No duplicate packet, detailed lookup or outreach |

Estimates overlap and exclude supplier, fabrication, shipping and physical work.
The new source checks require exact named DNP sites, reject contradictory fields
and retain the original P2/clock guard digests. The precise 21-before/41-after
comparison delta is not permission for arbitrary SPI edits or physical approval.
All 41 affected candidate records have corruption checks. Unrelated records
remain subject to the original preservation guards.

Local diagnostics are source/API-double checks, not native execution. Evidence
is bound to source identities in LLM_HANDOFF. The actual candidate now passes
the three existing source guards that previously rejected inventory/preservation;
that does not qualify its native DRC, geometry or electrical performance.

Do not repeat archive recovery or claim the hardware is applied. Pinned KiCad,
locked dependency access and complete active-file publication remain unavailable
locally. The blocked runtime workflow must not be retried or bypassed. Next finish
the native 10-cut/5-short regression source and coherent KiCad integration in PR98.
All manufacturing/startup/E1/#45/#48 requirements and purchase/fabrication/physical
work/power/external-input/body-use permissions remain unchanged. Do not merge red.
