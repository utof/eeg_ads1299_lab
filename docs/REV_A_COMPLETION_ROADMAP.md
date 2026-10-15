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
| Proposed fitted components/stack | 0 for selection | PR100 selects five33ohm parts, capacitor shortlist, common stack target | Active source still OPEN_DNP/legacy caps |
| Q04 capacitor design disposition | 0 for this bounded review | Conditional pilot decision recorded; EVM does not validate16V substitution | Internal-node/startup and local LDO C/ESR conditions before power; final build-risk acceptance |
| Assembly ownership | 0 for make/buy choice | Outsource boards/TH/tails/crimps; no specialist tool purchase assumed | Actual supplier/process/hole/fixture responses |
| Coordinated BOM/CAD migration | 1-2 after conditions are disposed | NOT performed | Q03 land/process answer and applicable manufacturing decisions; preserve one coherent update |
| Fabrication/purchase release | 1 after prerequisites | Not released | Accepted revision, exact-part supply, restricted purpose and delivered quote |
| Standalone breadboard learning | 0 planning; 1 optional measurement follow-up | Kit, row layouts, charge curve and checked UT139C setup example ready | Receive the kit, identify meter and record first readings |
| Laptop capture rehearsal | 0 for this rehearsal | Existing real localhost path:2248 synthetic samples, two intended gaps detected,10Hz peaks on four channels | Actual ADC capture waits for assembled-board commissioning |
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

**Next bounded step:** obtain the breadboard kit and report the meter model/first
divider readings. In parallel, the next Rev A dependency is the actual Q03 and
related manufacturing response through the sole Q1 packet; send only when the
user supplies the recipient details and explicitly authorizes contact.
