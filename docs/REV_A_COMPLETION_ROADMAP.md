# Rev A roadmap - B3 sense-access method chosen

B2 merged in PR92 at8c08e012; B1 and the single Q1 packet are already merged.
B3 selects supported fine-wire sense pairs because the actual K2 cable/bridge
obstruct top-down access at C30/C33. No PCB, BOM, holder or firmware changed.
Read live refs, rootAGENTS and REPOSITORY_PUBLICATION before continuing.
Moscow remains the planning region; no detailed prices or supplier outreach.

| Category | Remaining substantial turns | Done/status | Next slice or blocker |
|---|---:|---|---|
| Startup fixture and observations | 0 for B1/B2 plan | Wiring, local pairs and R/V boundaries documented | Physical implementation and instrument coverage before use |
| Sense-access method | 0 for nominal method decision | B3 identifies blocked approaches and clear aerial lead corridors in existing K2 | Accepted fine-wire joints, insulation and outboard strain relief; no actual fixture qualified |
| Pilot layout/return-path disposition | 1-2 plus any necessary external evidence | Existing connected layouts and recorded pending regions retained | NEXT: concrete before-fabrication repairs/dispositions versus later characterization; do not widen guards |
| Component/manufacturing disposition | 1-2 plus necessary evidence | Preferred candidates and finite Q1 questions exist; active BOM unchanged | One coordinated accepted revision, including stackup/process and relevant electrical risks |
| Prices/quotation contact | Paused | Sole unsent packet; Moscow assumption retained | No repeated packet or lookup campaign |
| Fabrication release | 1 after prerequisites | Not released | Explicit approval of a consistent manufacturing revision |
| First-power settings and inspection | 1 after actual assembly/equipment inputs, plus physical checks | B1/B2 run card exists; firmware gate remains false | Numeric limits, accepted contacts, grounding, observation and shutdown/discharge review |
| Internal-test capture | Approved physical-work dependent | F1/capture path exists; not operated | Accepted assembly/fixtures/instruments, then authorized measured commissioning |
| Later characterization | Measurement-dependent | Not started | External dummy channels, noise, full channel/fault behavior; body use separate |

Estimates overlap and exclude fabrication, shipping and physical measurements.
The B3 SCAD is an inspection overlay, not a new printable fixture. Its seven
native intersections test nominal space: joint access below the 4 mm component
allocation, real wire/support compliance and electrical response remain untested.
No probe bandwidth/accuracy or waveform qualification follows from clearance.
Individual negative sense leads must not become a common instrument return.

B1-B3 are sufficient paper scaffolding for this stage. Do not make another generic
probe plan, RFQ, capacitor-family study or supply framework. Carry real attachment/
instrument acceptance into the existing run card and work on the next independent
build blocker. No broad architecture change is needed for this geometry decision.
Keep #45/#48, pending-reference records and stage-specific requirements explicit;
DRC0 cannot replace their engineering disposition. No purchasing, fabrication,
physical fixture construction/mating, powering, external acquisition or body use
is authorized. First-power values are not guessed from supply capacity.
