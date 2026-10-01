# Rev A person-disconnected prototype roadmap

**Current checkpoint: native C3 auxiliary schematic and loaded bus-pull migration.**
C1/C2 are no longer only pin-map prose: the four-sheet auxiliary project and
all-terminal/native export checks exist. This is a schematic draft, not a routed
auxiliary board, implemented firmware handshake or qualified powered assembly.
The matching AFE service feed/sense access is the next bounded hardware change.

## Glanceable roadmap

Remaining substantial chat turns are estimates, not elapsed time or a safety
score. Categories overlap. Exclude supplier response, fabrication/shipping and
physical measurement time; do not sum these into a promised completion date.

| Category | Estimated turns remaining | Done / current status | Next slice or blocker |
|---|---:|---|---|
| Repository continuity | 0 for current milestone; maintain | Native sources, tests and current handoff are in the C3 branch/PR | Verify live PR/main, publish and review each actual head |
| Original AFE routing and scoped repairs | 0 for completed scope | All AVDD1/output/CH1N copper preserved; seven pull identities updated | Preserve routing except explicitly reviewed service-access edits |
| Remaining input/supply coupling | 1 combined decision after confirmations | Nine locations remain one six-pair assessment | Confirmed construction/E1 inputs, then combined rework or separate pilot-risk decision |
| Stackup and bench envelope | 0 for targets; 1–2 plus outside evidence to close | Named construction and E1 numerical targets defined | Actual vendor drawing/tolerances and calibrated fixture/measurement floor |
| Capacitor decision/migration | 1 coordinated review after evidence | 33 AFE capacitors accounted; exact shortlist still not substituted | #48 lifecycle/effective-C/assembly conditions; new auxiliary bypasses separately |
| Carrier and cartridges | 0 for initial CAD; 1–2 plus physical fit/process | K2 editable solids and geometry checks exist | Fit, retention, materials, cable and controller support |
| **C1+C2 auxiliary and rail access** | **2–3 for remaining source work; physical tests separate** | **Native four-sheet schematic, 212-terminal contract, 43-row BOM and conditional pull budget implemented** | **Next: matching AFE service feed/sense access; then firmware handshake and auxiliary layout** |
| Real power/console faults | 1–3 plus physical checks | Circuit and steady-state budgets explicit; not qualified | Supply trajectories, actual leakage/edges, sense/feed breaks and disabled-state behavior |
| Fabrication package and delivered budget | 1–2 after prerequisites | Not ready for fabrication or purchase | Separate release review, coherent outputs and delivered quote |
| Person-disconnected bench verification | 2–4 guided turns plus bench work | Physical validation has not begun | Unpowered inspection, then staged dummy-source tests after prerequisites |

## Next bounded step

Add mechanically supported **AFE service feed/sense access** corresponding to
auxiliary J104: ground, DVDD feed, separate DVDD sense, AVDD sense, ground, NC.
Use an actual placement and coordinated native all-pin/BOM/board checks. The
auxiliary header does not create the missing AFE connection by itself. Preserve
existing20-pin connector assignments, K2 clearances and prior routing guards;
do not authorize small-pad flying wires or assign J2NC/CLKSEL as a sense pin.

Then implement the actual firmware SESSION/ARM/READY/ARMED contract, followed by
auxiliary placement/routing and a separate power-fault review. Do not restart a
new architecture catalog search or call current firmware compatible with C2.
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

The AFE planning subtotal is still$94.34 with its old resistor allowance. The
auxiliary's11ICs/15bypasses/16resistors/service header, cable mates, manufacture,
retention and labor are not priced in it. This does not establish the user's
$100 additional-parts target. Parts are choices, not proof of purchase. No
unsolicited supplier message, purchase, fabrication, powered setup or body
connection is authorized. Every such gate remains false.

Entry points: `LLM_HANDOFF.md`, `HARDWARE_BASELINE_REV_A.md`,
`REV_A_AUXILIARY_C3.md`, `REV_A_BUS_INTERLOCK_C2.md`,
`REV_A_CONTROLLER_INTERFACE_C1.md`, `REV_A_STACKUP_BENCH_REQUIREMENTS.md`,
`REV_A_UPSTREAM_COUPLING_DISPOSITION.md`, K2/connector documents and open#45/#48.
