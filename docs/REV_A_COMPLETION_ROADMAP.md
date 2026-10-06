# Rev A completion roadmap — S3 conditional supply worksheet

S2 merged as PR83 at188d954a. S3 now combines source/feed/return and local/remote
reference terms into one executable worksheet. All21 physical bounds startnull;
8output rows remain indeterminate. Even filled hypothetical scenarios do not
qualify operation. No board, circuit, firmware or permission changed. Read
REPOSITORY_PUBLICATION.md before writes/recovery; existing entrypoint tests keep
it linked from AGENTS, README, DEVELOPMENT and the handoff.

Remaining substantial chat turns exclude supplier/assembly/shipping time and
physical measurements. Categories overlap; these are not safety percentages.

| Category | Turns remaining | Done/status | Next slice or blocker |
|---|---:|---|---|
| GitHub continuity | 0 for runbook discovery | AGENTS, README, DEVELOPMENT and handoff require the publication runbook | Inspect live refs/actions, publish actual engineering tree, separate CI/review |
| Supply/return accounting | 0 for S1/S2/S3 source work; 1–2 plus external evidence for limits | One signed, source-bound worksheet now exposes all missing bounds; no physical pass | Next: close source/current evidence for one named steady-acquisition setup |
| Connected boards and F1 | 0 for completed source scope | R1 clock, P3 routing, J3 and guarded firmware retained | Physical validation remains |
| Other signal/reference review | 1–2 | Existing reference guards and recorded pending areas retained | Actual complete channels, layer transitions and loading |
| Stackup/capacitors/analog coupling | 2–4 plus external evidence | Candidate choices and requirements documented | Vendor information, effective capacitance and combined coupling decision |
| Mechanical/power-fault work | 2–4 plus physical checks | CAD and conditional circuit limits exist | Actual fit, restraint, leakage, rails and recording validity |
| Release and delivered budget | 1–2 after prerequisites | Not fabrication-ready | Complete quote and separate release review |
| Person-disconnected bench | 2–4 guided turns plus bench work | Physical validation not begun | Unpowered inspection then approved dummy-source procedure |

S1's illustrative5mA per buffer gives3.56mV at the farthest feed path. Under its
0.5A MCU example the remaining AVDD allowance is94.9mV before unbounded source,
return and connection losses;0.180ohm is an optimistic whole-shared-loop ceiling,
not a newly accepted design limit. Current, material and ground assumptions must
be bounded before changing hardware. Source sense is not delivered voltage.

Next close source/current evidence for one named steady-acquisition setup in
the EXISTING S3 worksheet; keep unknown terms and vendor/measurement prerequisites. Use S2's15-byte/3%-active nominal schedule
only for its stated average external-load scenario, not peak or total current.
Count forward output current returning into AFE pulldowns; only auxiliary-local
load cancels at that boundary. Parallel wire currents depend on conductance and
an explicit ground-node approximation, not the number of wires alone.

The new helpers and executable study are source/software checks, not physical
experiments. Actual current/ramp envelopes, wire/crimp/contact resistance and
distributed return errors still require evidence before a release decision.
No supplier outreach or energization is authorized. The94.84USD AFE allowance
is not a delivered system quote. All purchasing, fabrication, powered-connection
and body-use flags stay false. Read actual PR head, CI and review before merging;
a missing chat reply is not a reason to recover completed work again.
