# Rev A roadmap - Q1 quotation packet, not a manufacturing release

PR88 consolidated all 48 capacitor quotation locations at main39967740. The
next slice Q1 packages the complete two-board inventory and support/cost scope.
Read live PR/main before assuming it is merged. Root AGENTS and
`REPOSITORY_PUBLICATION.md` remain mandatory; `REV_A_BENCH_FIRST.md` records the
user's preference for practical progress and reversible labelled assumptions.

| Category | Remaining substantial turns | Done/status | Next slice or blocker |
|---|---:|---|---|
| Source and agent continuity | 0 for this milestone | Existing GitHub guide; Q1 packet/CSV and current handoff in source | Check live heads and merged PRs; do not repeat failed-reply work |
| Component quotation selection | 0 | All48 capacitor sites covered;26proposed AFE replacements, not applied | Only revisit a choice after concrete rejection |
| Complete two-board RFQ | 0 for preparation after Q1 acceptance | 104fitted board parts,8DNP,5landing groups; external modules/harness/fixture/services and delivered costs separate | User approves recipient/destination and1/5-set quotation scope; no sending yet |
| Vendor/engineering disposition | 1-2 plus responses | Finite Q01-Q10 list identifies who decides and which stage is blocked | Enter evidence/exclusions; do not substitute a price for acceptance |
| Coordinated engineering migration | 1-2 after applicable dispositions | Active PCB/BOM/firmware unchanged | Apply accepted parts/land changes consistently and verify/review |
| Manufacturing release | 1 after prerequisites | Not released; no production exports in Q1 | Complete delivered quote and separate fabrication/order approval |
| Inspection and first internal-test capture | 1-2 planning turns plus approved bench work | Existing F1 and capture path; not operated | Unpowered inspection/passive-fixture plan; actual source/ground/limits then separately approved power |
| Later characterization | Measurement-dependent | Not started | External dummy signals, noise, coupling and fault envelope; body use separate |

Estimates exclude quote turnaround, manufacturing/shipping and measurements;
stages overlap and are not a countdown to safety approval. The working source
class remains regulated5V with adjustable current limit;1A capacity is not a
startup setting or consumption bound. Missing equipment does not prevent a
conditional RFQ. Q1's1/5-set quantities and finish/colour price basis are
provisional, not purchases or engineering-field changes.

The active/native and proposed quote MPNs are deliberately separate. No vendor
may assemble directly from their mismatch. Required capacitor effective-C/internal
node/land decisions, job-specific stackup and hole/process review remain open.
Preserve all current reference guards, C4 pin/cavity mapping, coded K2 seating,
auxiliary offsetH4 and separate HOST/TARGET domains. No generic framework,
arbitrary reroute or duplicate accounting worksheet is needed for quote work.

Next real action is permission to send the prepared packet to a named recipient
with a destination and quantity basis, then disposition actual answers. While
that decision is pending, prepare only an independent before-power inspection/
fixture plan; do not treat another "next" as outreach, purchase or power approval.
The historical94.84USD AFE allowance is not a complete delivered price. Keep
unknown amounts blank, with explicit included/N/A explanations for any zero.
All purchasing, fabrication, powered-connection, external-input and body-use
gates remain unchanged; source merges do not close #45/#48.
