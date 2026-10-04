# Rev A roadmap: R1 source imported, exact-head review next

The completed R1 clock correction is now imported into GitHub with its original
three commits through107d72c/treea278956. This checkout reconciles it with the
f7cb documentation history. It is the corrected engineering source, not an
encoded recovery package. Read live PR81/main and exact-head checks/review before
assuming merge or acceptance. No additional source recovery or clock reroute.

## Glanceable roadmap

Remaining substantial chat turns are ranges, not safety scores or a countdown.
Exclude supplier responses, manufacturing/shipping and physical measurements;
categories overlap.

| Category | Estimated turns remaining | Done/status | Next slice or blocker |
|---|---:|---|---|
| R1 source publication | 0 | Original correction imported and reconciled with current history | Read actual PR head; no more recovery transfers |
| PR81 CI/review | 1 including any concrete findings | Corrected source is available for exact-head checks | Resolve original clock/handoff findings, then merge if accepted |
| Auxiliary layout | 1–2 | Connected routing and shorter/separated clock | Feed/return voltage-drop budget and remaining full-channel/reference review |
| Main AFE and F1 firmware | 0 for completed scope | AFE/J3 and guarded firmware unchanged | Physical-performance limitations remain |
| Input/supply coupling | 1 after confirmations | Nine locations remain one six-pair item | Confirmed construction/E1 inputs; combined repair or separate pilot-risk decision |
| Stackup and bench requirements | 1–2 plus external evidence | Construction target and numerical limits documented | Vendor construction/tolerances and calibrated measurement floor |
| Capacitor migration | 1 coordinated review after evidence | Exact shortlist and33AFE roles accounted | Lifecycle/effective-C/assembly; auxiliary bypasses separate |
| Mechanical assembly | 1–2 plus physical checks | Existing CAD and mounting/access allocations preserved | Actual fit, materials, forces, retention and cable restraint |
| Power/console faults | 1–3 plus physical checks | Circuit limits and F1 behavior documented | Rail collapse, leakage, broken feedback and recording validity |
| Release and delivered budget | 1–2 after prerequisites | Not fabrication-ready | Coherent outputs, complete quote and separate release review |
| Person-disconnected bench | 2–4 guided turns plus bench work | Physical validation has not begun | Unpowered inspection then approved staged dummy-source tests |

## Next bounded engineering step

Complete actual corrected-head CI/review first. Then bound AFE_DVDD supply and
return drop using real shared-trunk geometry and declared current, copper, vias,
connector/cable and return assumptions. Keep complete-channel edges, own-contact
reference exclusions, sense coupling and18pending reference records explicit.
No automatic physical sign-off, generic termination or new meanders follows from
a shorter clock or clean DRC. All15local bypass checks,39netcut controls, pending
spatial envelope and450s CAD batch deadline remain unchanged.

## Publication lesson

The earlier successful path was ordinary GitHub history publication plus a
separate Codex review. It worked again in run37204919737 after exact bundle,
three-commit, file-scope and fresh-clone checks. The one-shot workbench importer
is not a product dependency or part of this PR's workflow diff. A missing Codex
editing-task environment does not disable review or authorize another execution
bypass. See REPOSITORY_PUBLICATION.md; do not repeat failed capability assumptions.

## Release boundaries

Editable/routed source, an approved pilot design, and physically validated
person-disconnected hardware are different milestones. Vendor stack, component,
mating, mechanical, fixture and budget evidence must be closed or explicitly
disposed before release. Measurements require real assembly; body connection is
a separate later scope. The94.84USD AFE subtotal does not include the entire
auxiliary, harness, holder, tools or delivery. No unsolicited supplier message,
purchase, fabrication, powered setup, external acquisition or body use is granted.

Use current handoff and live source over archived publication narratives. Prior
local107d results are not hosted results for this integrated checkout; every
new claim needs its actual source identity and run outcome.
