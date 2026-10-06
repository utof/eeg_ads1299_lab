# Rev A completion roadmap — S4 named serial evidence

S3 merged as PR84 atde47a756. S4 now defines one named serial/internal-test setup,
records applicable component conditions and exercises the existing worksheet
with a conditional regulator interval. All physical template terms remainnull;
all8outputs stay indeterminate even in the partial scenario. Source model and
complete current/return bounds remain missing, not inferred from a1A target or
0.5A module supply-capability requirement. No engineering/permission changes.
Read REPOSITORY_PUBLICATION.md before writes/recovery; its entrypoint tests remain.

Remaining substantial chat turns exclude supplier/assembly/shipping time and
physical measurements. Categories overlap; these are not safety percentages.

| Category | Turns remaining | Done/status | Next slice or blocker |
|---|---:|---|---|
| GitHub continuity | 0 for runbook discovery | AGENTS, README, DEVELOPMENT and handoff require the publication runbook | Inspect live refs/actions, publish actual engineering tree, separate CI/review |
| Supply/return accounting | 0 for S1–S4 method/evidence review | Existing worksheet plus conditional regulator3.2505–3.3495V; all real bounds remain unknown | No further generic framework or duplicate worksheet |
| Actual source/current evidence | 1–2 after setup identity, plus external evidence | Named serial mode; current-capacity/typical-data traps documented | Next: user source model, lead identity and applicable specs; then matched current/ground evidence |
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

Next ask which regulated bench supply is actually available (or whether none is
chosen), then map its stated regulation/accuracy domain into the EXISTING S3
worksheet. The selected target voltage/current capacity is not a purchased or
measured source. S4 already reviewed the applicable regulator/module/DevKit rows;
do not re-run that evidence search as a substitute for the missing setup.
Keep total-current, contact, return and peak bounds unresolved until supported.
Do not reselect parts, widen copper or authorize measurements just to fill cells.

The retained helpers and S4 source/process checks are software evidence, not physical
experiments. Actual current/ramp envelopes, wire/crimp/contact resistance and
distributed return errors still require evidence before a release decision.
No supplier outreach or energization is authorized. The94.84USD AFE allowance
is not a delivered system quote. All purchasing, fabrication, powered-connection
and body-use flags stay false. Read actual PR head, CI and review before merging;
a missing chat reply is not a reason to recover completed work again.
