# Rev A roadmap — complete quotation packet, not fabrication release

PR88's capacitor disposition is merged at `39967740`. The complete UNSENT
quotation packet is `quote_draft/REQUEST.md`, with current/proposed BOM,
assembly/interfaces, cost response and source identity. Check the live
`review/two-board-quote` PR/main state for this continuation's publication.
Root AGENTS and `REPOSITORY_PUBLICATION.md` remain mandatory.

The user wants practical engineering and permits explicit reversible assumptions.
A regulated 5 V, current-limited bench-source class is the planning choice;
actual instrument and staged settings are needed before power, not before RFQ.
No new battery design, generic supply study or speculative code restructure.

| Category | Remaining substantial turns | Done / status | Next slice or blocker |
|---|---:|---|---|
| Architecture and continuity | 0 for this slice | Existing modular code, single gate and entrypoint instructions retained | Refactor only for a demonstrated obstacle |
| Capacitor quotation choices | 0 for selection | All 48 capacitor locations covered; 26 proposed AFE replacements not applied | Actual supply, process and node-specific electrical disposition |
| Complete pilot RFQ packet | 0 for preparation | Current/proposed full electrical CSV, interfaces, nine reply questions, cost sheet and pinned source | User authorization, recipient, delivery terms and confirmation of provisional 1/5-set quote quantities |
| Supplier replies and internal decisions | 1–2 plus response time | Finite questions separated by owner/stage | Request quotes only after permission; designer resolves electrical risks rather than delegating them to assembler |
| Coordinated engineering migration | 1–2 after applicable disposition | Active BOM, both boards and firmware unchanged | Apply accepted BOM/CAD/contracts/fixture changes together, then exact-head tests/review |
| Remaining layout/manufacturing decisions | 1–2 plus external evidence | Connected boards, clock repair and existing protections retained | Stackup, return/coupling and assembly acceptance; no arbitrary meanders or relaxed guards |
| Delivered quote and release | 1 after prerequisites | No whole-system quote or fabrication release | Include modules/cables/carrier/spares/setup/tax/delivery and equipment cash; separate order approval |
| Inspection and first internal-test capture | 1–2 planning turns plus approved bench work | Firmware/capture path and finite CAD exist | Actual assembly/fixture/source/current/abort review, then authorized measurement and internal capture |
| Later characterization | Measurement-dependent | Not started | External dummy inputs, noise/faults; body use remains a separate scope |

Times exclude shipping/manufacturing and physical measurements; rows overlap.
The 1-set request and optional 5-set comparison are assumptions, not purchase
quantities. Do not sum missing prices as zero or duplicate MOD1, board headers,
or the already-fitted isolator when costing accessories. The old $94.84 allowance
is not a complete delivered price. Quote exclusions need a separate provision/cost.

The packet deliberately carries no order-ready Gerber/drill/CPL files. Native
source is for feasibility/land review. A quotation cannot reconcile the 26
proposed identities into the active circuit by itself. Keep #45/#48, actual
stackup/process, electrical and mechanical requirements open until explicitly
resolved or subject to a reviewed bounded-pilot disposition.

**Next:** ask permission for quotation-only supplier contact, with recipient and
delivery details; then obtain Q1-Q9 responses. Do not prepare a second RFQ or redo
capacitor searches when the actual next dependency is the user's send decision.
Independent pre-power planning may continue, but it must not masquerade as a
newly obtained quote or manufacturing approval. No supplier contact, ordering,
fabrication, powered connection, external acquisition or body-use authorization.
