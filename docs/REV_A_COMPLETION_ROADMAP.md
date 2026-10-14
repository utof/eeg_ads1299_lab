# Rev A roadmap - PR98 merged; close remaining pilot build decisions

Checked 2026-10-15: live main is `bab9f60f23c799c9da00fd531acd8a5b9ad1ecd7`,
tree `96afda406d9b0d7715d4fae4b2afa50d3f64b4a2`, identical to accepted PR98
head `26d5ad903e1e48ce7fc435e3abef664a9812a9dd`. PR98 merged on October13.
Read `LLM_HANDOFF.md` and the [hosted capability preflight](REPOSITORY_PUBLICATION.md#hosted-capability-preflight).
Do not repeat recovery, integration, supply, reference or K2 repairs.

| Category | Estimated remaining substantial chat turns | Done/status | Next slice or blocker |
|---|---:|---|---|
| SPI provisions, reference and supply repairs | 0 | Merged in PR98 | Preserve accepted source |
| K2 nominal allocation/access | 0 for nominal review; physical evidence later | Merged; assembled upper access obstructed | Actual fitting/tool/joint/workmanship checks |
| PR98 acceptance and merge | 0 | Five required jobs and exact-head review passed; merge verified | Retain historical evidence |
| Post-merge CAD execution | 0-1, result-dependent | Main's later run timed out at450s; unchanged retry requested | Read run38399520579; diagnose if timeout persists, preserve limits |
| Remaining digital channels | 1 decision plus evidence | MCU launches and DRDY/control remain open | L4 section3 bounded-pilot disposition |
| SPI population, components/manufacturing | 1-2 plus supplier/user decisions | Five sites OPEN_DNP; candidate and Q1 work retained | Fit values/MPNs, capacitor migration, stack, connector and assembly disposition |
| Fabrication/purchase release | 1 after prerequisites | Not released | One accepted revision, restricted purpose and delivered quote |
| Startup/internal capture | 1-2 planning turns plus assembly and measurements | B1-B3 plans exist; firmware gate false | Inspection, equipment, reviewed first-power conditions and capture |
| Separate passive breadboard learning | 1 plan, equipment-dependent | Can be prepared independently | Inventory equipment; choose one passive R/C check |
| External-input characterization | Later, measurement-dependent | Unqualified; another PCB revision may be needed | Existing E1 requirements |
| Body-connected use | Outside this Rev A pilot | Not approved | Separately scoped hardware/safety engineering |
| Prices/RFQ | Paused pending user direction | Sole frozen unsent Q1 retained | No price campaign, duplicate packet, outreach or purchase |

**Planning estimate: roughly 3-5 focused turns to a purchase/build-ready Rev A
decision**, if remaining evidence can be obtained or explicitly dispositioned for
the restricted pilot. This is not a completion-date promise or a percentage of
safety. Rows overlap; supplier responses, delivery/manufacturing, measurements
and user decisions are excluded. First power and successful internal-test capture
follow actual hardware and equipment availability. Passive breadboard learning
does not need to wait for those board-release tasks.

The ADC is surface-mount in a two-board design, not a bare IC to plug into a
solderless breadboard. A passive exercise does not validate ADC noise, digital
channels, startup or body safety. Preserve the selected Rev A components.

All five positions remain open; no resistor value, including zero ohms, is
selected. R24's3.2x1.6x4mm allocation is not a part maximum. Both0.5mm upper
probes are blocked assembled and clear only in the specified upper-assembly-removed
model; actual solder tools, joint access and physical disassembly are unqualified.
Keep450sCAD/71%floor, all fault tests and frozen Q1 identities. No purchase,
fabrication, physical rework/mating, power, external acquisition or person/animal
use is authorized by this roadmap.

**Next bounded engineering step:** L4 section3's remaining MCU-launch and
DRDY/control-channel disposition, followed by the consolidated fitted build.
