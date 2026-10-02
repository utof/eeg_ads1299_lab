# Rev A person-disconnected prototype roadmap

**Current checkpoint: F1 guarded C2 firmware implemented.** C4 service access
remains the unchanged electrical baseline. Next is auxiliary PCB placement and
routing, not another connector or handshake redesign. Firmware depends on the
actual auxiliary latch and does not qualify power-loss or physical behavior.
Read the live guarded-firmware PR/head and `REV_A_C2_FIRMWARE.md`.


**Previous C4 checkpoint: C4 AFE service connection routed; cable target and backing defined.**
The six-way service header now exists on the AFE; all earlier copper and
placements are retained. C3 auxiliary schematic remains unrouted and the C2
firmware handshake is still unimplemented. Physical mating, crimp, process,
fault and measurement conditions remain open. Use current main/open PR source,
not a missing or stale chat reply.

## Glanceable roadmap

Remaining substantial chat turns are estimates, not elapsed time or a safety
score. Categories overlap. Exclude supplier response, fabrication/shipping and
physical measurement time; do not sum these into a promised completion date.

| Category | Estimated turns remaining | Done / current status | Next slice or blocker |
|---|---:|---|---|
| Repository continuity | 0 for current milestone; maintain | C4 source, tests and current handoff are in its recovery branch/PR | Verify live PR/main, publish and review each actual head |
| Original AFE routing and scoped repairs | 0 for completed scope | All old copper preserved; J3 and11 service segments added | Preserve routing except explicitly reviewed service-access edits |
| Remaining input/supply coupling | 1 combined decision after confirmations | Nine locations remain one six-pair assessment | Confirmed construction/E1 inputs, then combined rework or separate pilot-risk decision |
| Stackup and bench envelope | 0 for targets; 1–2 plus outside evidence to close | Named construction and E1 numerical targets defined | Actual vendor drawing/tolerances and calibrated fixture/measurement floor |
| Capacitor decision/migration | 1 coordinated review after evidence | 33 AFE capacitors accounted; exact shortlist still not substituted | #48 lifecycle/effective-C/assembly conditions; new auxiliary bypasses separately |
| Carrier and cartridges | 0 for initial CAD; 1–2 plus physical fit/process | K2 solids plus C4 service backing and mating envelopes checked | Fit, retention, materials, cable and controller support |
| **C1+C2 auxiliary and rail access** | **2–3 for remaining source work; physical tests separate** | **C3 schematic and matching routed AFE J3 now implemented in source** | **Next: guarded C2 firmware handshake; then auxiliary placement/routing** |
| Real power/console faults | 1–3 plus physical checks | Circuit and steady-state budgets explicit; not qualified | Supply trajectories, actual leakage/edges, sense/feed breaks and disabled-state behavior |
| Fabrication package and delivered budget | 1–2 after prerequisites | Not ready for fabrication or purchase | Separate release review, coherent outputs and delivered quote |
| Person-disconnected bench verification | 2–4 guided turns plus bench work | Physical validation has not begun | Unpowered inspection, then staged dummy-source tests after prerequisites |

## Next bounded step

Implement the actual **SESSION/ARM/READY/ARMED firmware handshake**, with
failure-first startup/fault/rearm tests and exact S3 compilation. The matching
AFE J3 is already implemented: do not repeat its placement or change the two
20-position headers. Retain the no-hot-mating and independent feed/sense cable
checks in `REV_A_SERVICE_C4.md`. Finish the auxiliary layout afterward and
review power-fault behavior separately. Current firmware is not automatically
C2-compatible merely because the schematic and service port exist.
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
`REV_A_AUXILIARY_C3.md`, `REV_A_BUS_INTERLOCK_C2.md`,
`REV_A_CONTROLLER_INTERFACE_C1.md`, `REV_A_STACKUP_BENCH_REQUIREMENTS.md`,
`REV_A_UPSTREAM_COUPLING_DISPOSITION.md`, K2/connector documents and open#45/#48.
