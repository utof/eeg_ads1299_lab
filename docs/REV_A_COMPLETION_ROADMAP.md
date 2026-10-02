# Rev A person-disconnected prototype roadmap

**Current checkpoint: P2 ground references and local bypasses routed.**
All59ground contacts and15local cap-to-IC paths now connect, reducing unfinished
connections from157 to85. Two separate In1 ground regions respect the existing
HOST/TARGET barrier. Placements, AFE/J3, F1, K2 and circuit selections are unchanged.
Native0parity/0other/85airwires is partial routing, not a release. Read the live
P2 PR/head and `REV_A_AUXILIARY_GROUND_P2.md` before continuing.

## Glanceable roadmap

Remaining substantial chat turns are estimates, not elapsed time or a safety
score. Categories overlap. Exclude supplier response, fabrication/shipping and
physical measurement time; do not sum these into a promised completion date.

| Category | Estimated turns remaining | Done / current status | Next slice or blocker |
|---|---:|---|---|
| Repository continuity | 0 for current milestone; maintain | C4/F1/P1 merged; P2 copper/proof in the current routing PR | Verify live PR/main, publish and review each actual head |
| Original AFE routing and scoped repairs | 0 for completed scope | All old copper preserved; J3 and11 service segments added | Preserve routing except explicitly reviewed service-access edits |
| Remaining input/supply coupling | 1 combined decision after confirmations | Nine locations remain one six-pair assessment | Confirmed construction/E1 inputs, then combined rework or separate pilot-risk decision |
| Stackup and bench envelope | 0 for targets; 1–2 plus outside evidence to close | Named construction and E1 numerical targets defined | Actual vendor drawing/tolerances and calibrated fixture/measurement floor |
| Capacitor decision/migration | 1 coordinated review after evidence | 33 AFE capacitors accounted; exact shortlist still not substituted | #48 lifecycle/effective-C/assembly conditions; new auxiliary bypasses separately |
| Carrier and cartridges | 0 for initial CAD; 1–2 plus physical fit/process | K2 solids plus C4 service backing and mating envelopes checked | Fit, retention, materials, cable and controller support |
| **C1+C2 auxiliary and rail access** | **1–2 for auxiliary routing/review; physical tests separate** | **C3/C4/F1/P1 complete; P2 grounds and15local bypasses routed;85airwires remain** | **Next: global supply feeds and remaining signals; then full return-path/interface review** |
| Real power/console faults | 1–3 plus physical checks | Circuit and steady-state budgets explicit; not qualified | Supply trajectories, actual leakage/edges, sense/feed breaks and disabled-state behavior |
| Fabrication package and delivered budget | 1–2 after prerequisites | Not ready for fabrication or purchase | Separate release review, coherent outputs and delivered quote |
| Person-disconnected bench verification | 2–4 guided turns plus bench work | Physical validation has not begun | Unpowered inspection, then staged dummy-source tests after prerequisites |

## Next bounded step

**Complete global supply and signal routing on the authored P2 auxiliary board.**
Preserve separate HOST/TARGET references, C4 distinct feed/sense, local bypass
paths and their continuously filled return corridors. P2 already joins all59
ground terminals and15local supply branches: do not regenerate those references
or repeat placement. Plan actual reference paths for any In2/B layer changes;
four layers alone do not guarantee a return plane under every trace. Refill and
check connectivity/clearance after each bounded group, then review completed
return paths and interface faults.85airwires remain; native exit5 is intentional.
Keep all6x6mount and wire/mate allocations, the asymmetricH4 coordinates, selected
lands and native isolation rules. Physical tolerance/process/force and supplier
construction are still unqualified.

F1's handshake and C4's J3 are implemented; do not reconstruct them based on an
old chat checkpoint. Firmware cannot retract an already delivered packet. Its
real-hardware timing and host recording invalidation are separate work. All
external-acquisition, release, purchasing and body-use gates remain false.
The 42.2k pull migration is explicitly conditional: disabled-low budget has only
24mV remaining under its stated assumptions. Unspecified intermediate-rail IOZ,
installed resistance/leakage and abrupt-fault timing remain open. No test passing
on nominal values converts those conditions into guaranteed hardware behavior.

## Three finish lines, not one checkbox

A **native schematic draft** is editable connectivity with reviewed component
identities, explicit external interfaces and reproducible checks. It is not a
manufacturing package or an assembled circuit. C3 reaches this source milestone.

A **pilot design ready for release review** additionally needs completed AFE and
auxiliary routing, power/sense and firmware integration, final stack/mating/
mechanical/assembly choices, coherent manufacturing files and a delivered quote.
Pre-pilot risk review can happen before the first PCB exists; actual performance
cannot be measured before assembly. Do not make that circular, or silently treat
a planned experiment as permission to order or energize it.

**Validated person-disconnected hardware** requires physical assembly, inspection,
calibrated measurements and explicit pass/fail scope. Simulations, CI and source
review cannot supply missing electrical or mechanical measurements. Body use is
another revision/review, not unlocked by this table or by a number of chat turns.

## Scope and budget discipline

Existing analog/BIAS/supply studies, portable/target firmware guards, native AFE
schematic/routing and K2 mechanical source should not be recreated. Read detailed
review files rather than applying their old authoring scripts. Keep the #45/#48
requirements specific; do not add a general risk registry for every unknown.

The AFE planning subtotal is now$94.84 including a$0.50 AFE service-header allowance. The
auxiliary's11ICs/15bypasses/16resistors/service header, cable mates, manufacture,
retention and labor are not priced in it. This does not establish the user's
$100 additional-parts target. Parts are choices, not proof of purchase. No
unsolicited supplier message, purchase, fabrication, powered setup or body
connection is authorized. Every such gate remains false.

Entry points: `LLM_HANDOFF.md`, `HARDWARE_BASELINE_REV_A.md`,
`REV_A_AUXILIARY_GROUND_P2.md`, `REV_A_AUXILIARY_PLACEMENT_P1.md`, `REV_A_AUXILIARY_C3.md`, `REV_A_BUS_INTERLOCK_C2.md`,
`REV_A_CONTROLLER_INTERFACE_C1.md`, `REV_A_STACKUP_BENCH_REQUIREMENTS.md`,
`REV_A_UPSTREAM_COUPLING_DISPOSITION.md`, K2/connector documents and open#45/#48.
