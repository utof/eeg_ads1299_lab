# Rev A roadmap - breadboard kit ready; manufacturing responses block migration

Checked 2026-10-15: this continuation started from clean live main PR100 merge
`e666fc0921197a857f1ea5c551d464ceb14358cb`, tree
`7dfbbf4d77f7ad0763086295b38421ba7a3c3732`, identical to accepted PR100 head
`fb7de0c580966068f0e8988b8f3dbf40f4d3043c`. The merge message preserves its
five successful hosted checks and review, including failed local/hosted attempts.
Read `LLM_HANDOFF.md` and the [hosted capability preflight](REPOSITORY_PUBLICATION.md#hosted-capability-preflight).
Do not repeat recovery, integration, supply, reference or nominal K2 repairs.

| Category | Estimated remaining substantial chat turns | Done/status | Next slice or blocker |
|---|---:|---|---|
| Local development setup | 0 installation; runtime unresolved | Locked environment/native packages installed | Retain300s/450s deadlines; hosted route available |
| SPI provisions, reference/supply repairs, K2 nominal review | 0 for source/design work | PR98 merged; physical access/fit unqualified | Actual fitting/tool/joint inspection later |
| Remaining digital channels | 0 for paper choice | PR99 L6 retained paths with reviewed revision fallback | Before-fabrication access/revision-risk acceptance; interlock evidence before ADC enable |
| Proposed fitted components/stack | 0 for selection | PR100 selects five33ohm parts, capacitor shortlist, common stack target | Active source still OPEN_DNP/legacy caps |
| Q04 capacitor design disposition | 0 for this bounded review | Conditional pilot decision recorded; EVM does not validate16V substitution | Internal-node/startup and local LDO C/ESR conditions before power; final build-risk acceptance |
| Assembly ownership | 0 for make/buy choice | Outsource boards/TH/tails/crimps; no specialist tool purchase assumed | Actual supplier/process/hole/fixture responses |
| Coordinated BOM/CAD migration | 1-2 after conditions are disposed | NOT performed | Q03 land/process answer and applicable manufacturing decisions; preserve one coherent update |
| Fabrication/purchase release | 1 after prerequisites | Not released | Accepted revision, exact-part supply, restricted purpose and delivered quote |
| Standalone breadboard learning | 0 planning; 1 optional measurement follow-up | Kit, divider and slow-RC guide ready; user currently owns no equipment here | Buy/borrow listed basics, identify meter and record first readings |
| Rev A startup/internal capture | 1-2 planning turns plus assembly/measurements | B1-B3 plans exist; B2 equipment gap explicit; firmware gate false | Actual source/probes, numeric commissioning limits and prior interlock evidence |
| External-input characterization | Later, measurement-dependent | Unqualified; revision may be needed | Existing E1 requirements |
| Body-connected use | Outside this pilot | Not approved | Separately scoped hardware/safety engineering |
| Quote packet/outreach | 0 packet reconciliation; user/supplier dependent | Q1 current addendum added; frozen CSVs/manifest unchanged; unsent | Recipient/destination/currency/contact authorization and Q01-Q10 responses |

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

Four preparation steps in this continuation: node-specific Q04 disposition;
outsourced assembly ownership; the first breadboard kit/experiments; and current
Q1/B2 reconciliation. No BOM/CAD migration, new production code, framework,
physical measurement or supplier message occurred. All existing Rev A gates
remain closed, and a software check is not hardware qualification.

Keep the full ordinary/native/CAD/firmware selections and71%branch floor.
Local and hosted timing failures remain failures even if an unchanged retry
passes. Exact-head verification of this continuation is recorded in its PR;
previous accepted-head or main runs are not a substitute.

**Next bounded step:** obtain the breadboard kit and report the meter model/first
divider readings. In parallel, the next Rev A dependency is the actual Q03 and
related manufacturing response through the sole Q1 packet; send only when the
user supplies the recipient details and explicitly authorizes contact.
