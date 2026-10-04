# Rev A completion roadmap — S1 supply/return budget

PR81's connected auxiliary board and R1 clock repair are merged at the S1 base
f6932ead. No recovery/publication of that old source is pending. S1 adds a
source-bound DC sensitivity review, not a circuit or gate change. Read
`REPOSITORY_PUBLICATION.md` before publishing this next branch.

Remaining substantial chat turns exclude supplier/assembly/shipping time and
physical measurements. Categories overlap; these are not safety percentages.

| Category | Turns remaining | Done/status | Next slice or blocker |
|---|---:|---|---|
| GitHub continuity | 0 for runbook discovery | AGENTS, README, DEVELOPMENT and handoff require the publication runbook | Inspect live refs/actions, publish actual engineering tree, separate CI/review |
| Supply/return accounting | 0 for S1 model; 1–2 for input bounds | Shared-current and signed-ground sensitivities computed; no hardware pass | Mode currents and real source/K1/C4/plane/contact bounds |
| Connected boards and F1 | 0 for completed source scope | R1 clock, P3 routing, J3 and guarded firmware retained | Physical validation remains |
| Other signal/reference review | 1–2 | Existing reference guards and recorded pending areas retained | Actual complete channels, layer transitions and loading |
| Stackup/capacitors/analog coupling | 2–4 plus external evidence | Candidate choices and requirements documented | Vendor information, effective capacitance and combined coupling decision |
| Mechanical/power-fault work | 2–4 plus physical checks | CAD and conditional circuit limits exist | Actual fit, restraint, leakage, rails and recording validity |
| Release and delivered budget | 1–2 after prerequisites | Not fabrication-ready | Complete quote and separate release review |
| Person-disconnected bench | 2–4 guided turns plus bench work | Physical validation not begun | Unpowered inspection then approved dummy-source procedure |

S1's illustrative5mA per buffer gives3.56mV at the farthest feed path. Under its
0.5A MCU example the remaining AVDD allowance is95.0mV before unbounded source,
return and connection losses;0.180ohm is an optimistic whole-shared-loop ceiling,
not a newly accepted design limit. Current, material and ground assumptions must
be bounded before changing hardware. Source sense is not delivered voltage.

Next derive the operating-mode current envelope and allocate a complete steady
loss/error budget. Keep transient/inrush and broken/partial-rail behavior
separate. The old94.84USD AFE allowance is not a delivered system quote. All
purchasing, fabrication, powered-connection and body-use flags remain false.
