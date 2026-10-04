# Rev A roadmap: published P3, R1 import still pending

P3 is published in PR81, originally at9d22a6c. This documentation-only update
does not replace its clock copper. The completed R1 correction and three-commit
history are now recoverable entirely from this GitHub repository: immutable
commit `ce2d891713a76bcaed300af8fb310d489e3c3479`, branch
`workbench/pr81-clock-source`, directory `recovery/pr81-clock/`.
The manifest recovers exact107d72c/treea278956. See `LLM_HANDOFF.md`.

The normal Codex publication task did not run because its repository environment
is absent. Do not mistake the durable archive for the active engineering tree,
repeat the upload, regenerate copper or merge the transport branch. The two
original review findings require explicit disposition; the stale handoff is
corrected here, while the clock correction remains pending actual import.

## Glanceable roadmap

Remaining substantial chat turns are estimates, not safety percentages. They
exclude supplier responses, fabrication/shipping and physical measurements;
categories overlap and must not be summed into a promised release date.

| Category | Estimated turns remaining | Done/status | Next slice or blocker |
|---|---:|---|---|
| Repository-only recovery | 0 for this checkpoint | Full R1 source/history stored on a named GitHub branch; live handoff corrected | No chat attachment or expiring link needed |
| R1 active publication/review | 1 after normal publisher is available | Correction preserved but not applied to the active PR board | Import/reconcile the three commits, exact-head CI and renewed review |
| Clock correction | 0 for local implementation | R1 reduces85.49→71.88mm,5→4vias; separation increased; prior local gate passed | Do not claim applied until actual tree is verified |
| Other auxiliary layout review | 1–2 | Full P3 routing and existing reference protections retained | Feed/return voltage-drop budget and full-channel/reference assumptions |
| Main AFE and F1 firmware | 0 for completed scope | Existing AFE/J3/guarded startup preserved | Physical-performance limits remain |
| Stackup, capacitors and analog coupling | 2–4 plus external evidence | Requirements and candidate choices documented | Vendor construction, capacitor evidence and combined six-pair decision |
| Mechanical assembly | 1–2 plus physical checks | CAD and mounting/access allocations preserved | Actual fit, materials, restraint and retention |
| Real power/console faults | 1–3 plus physical checks | Circuit limits and F1 response documented | Rails, leakage, broken feedback, analog exposure and recording validity |
| Release and delivered budget | 1–2 after prerequisites | Not fabrication-ready | Separate release review and complete delivered quote |
| Person-disconnected bench | 2–4 guided turns plus bench work | Physical validation not begun | Unpowered inspection then approved staged dummy-source testing |

## What must not be conflated

The old published P3 Quality/Schematic/Firmware workflows passed on9d22. Prior
R1 local ordinary/schematic evidence belongs to107d. Neither proves that R1 has
been published, independently accepted or tested by hosted CI. A documentation
run also cannot validate a different PCB. Keep291KiCad/1236ordinary+14subtests
as prior R1 evidence until another actual run establishes a new result.

R1 keeps all other copper, source rules,18pending reference records/20outlines,
15local bypass checks and the450s CAD deadline unchanged. Native DRC0 and
improved geometry do not qualify edge rate, impedance, noise, rapid power faults
or arbitrary return-path behavior. No generic termination value or meander is
selected. Independent review must inspect the corrected full channel.

An editable schematic/routed prototype is not a released manufacturing package.
A pilot release additionally needs closed or explicitly disposed stackup,
component, connection, mechanical, fixture and budget requirements. Physical
performance needs real assembly and calibrated measurements; body use remains
a separate scope. The94.84USD AFE allowance omits the auxiliary/cable/carrier and
delivery costs. All purchasing, fabrication, powered and body-use gates stayfalse.

Historical pre-publication narrative is preserved in
`archive/20261003_pre_publication_roadmap.md`; do not follow its stale publication
instructions or treat its old counts as current. This roadmap, the current
handoff and verified live branch state take precedence.
