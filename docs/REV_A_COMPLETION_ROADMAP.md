# Rev A person-disconnected prototype roadmap

**P3 is published in PR81 at9d22a6c, not merged into main.** This checkout adds
R1 clock/handoff corrections; their publication/CI/review must be verified against
the actual remote head. Do not repeat original P3 publication, P2routing or F1.
Read `REV_A_P3_CLOCK_REVIEW.md` for the measured one-net change and its limitations.

## Glanceable roadmap

Remaining substantial chat turns are estimates, not a safety score. Categories
overlap. Exclude supplier response, fabrication/shipping and physical measurement.

| Category | Estimated turns remaining | Done/status | Next slice or blocker |
|---|---:|---|---|
| P3 publication | 0 for originalP3;1 for correction review | Actual routed source is onPR81; R1 source must be published separately | Exact corrected-head CI and renewed review, then merge if accepted |
| Verification runtime | 0 for scoped optimization; monitorCI | Exact native grouping fast path retained | No dropped cases or raised deadlines |
| Main AFE and F1firmware | 0 for completed scope | AFE/J3/guarded startup unchanged | Physical-performance restrictions remain |
| Auxiliary layout review | 1–2 | R1 clock71.88mm/4vias, MISOtrace gap>=0.60mm; no other copper moved | Independent acceptance, then supply feed/return budget and remaining full-channel assumptions |
| Input/supply coupling | 1 combined decision after confirmations | Nine locations remain one six-pair item | Confirmed construction/E1inputs and combined repair or separate pilot-risk decision |
| Stackup and bench envelope | 1–2 plus outside evidence | Named construction and numerical targets | Vendor drawing/tolerances; calibrated measurement floor |
| Capacitor migration | 1 coordinated review after evidence | Exact shortlist,33AFEcapacitor roles accounted | Lifecycle/effective-C/assembly; auxiliary bypasses separate |
| Carrier and assembly | 1–2 plus physical checks | CAD and mounting/access unchanged | Actual fit, materials, forces and cable restraint |
| Power/console faults | 1–3 plus physical checks | Circuit limits/F1response documented | Actual rails, leakage, broken feedback and recording validity |
| Release and delivered budget | 1–2 after prerequisites | Not fabrication-ready | Separate release review, coherent outputs and full quote |
| Person-disconnected bench | 2–4 guided turns plus benchwork | Physical validation not begun | Unpowered inspection then staged dummy tests after prerequisites |

## Next bounded step

Publish the R1 correction to PR81 and verify its actual head. The old9d22 CI pass
does not test this correction; the original review findings remain pending until
accepted on corrected source. Then bound AFE_DVDD feed/return voltage drop using
actual current, copper, vias, connectors and return paths. Retain long-channel,
reference-antipad and full-width pending-region review; no generic termination
or automatic physical sign-off follows from a shorter clock.

The original pending20polygons/18segment records are NOT expanded or approved.
All15P2bypasses,39terminalcuts, separation/mounting rules and450sCADbudget remain.
All external-acquisition, purchase/fabrication/powered/body-use gates stayfalse.

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
`REV_A_AUXILIARY_ROUTING_P3.md`, `REV_A_AUXILIARY_GROUND_P2.md`, `REV_A_AUXILIARY_PLACEMENT_P1.md`, `REV_A_AUXILIARY_C3.md`, `REV_A_BUS_INTERLOCK_C2.md`,
`REV_A_CONTROLLER_INTERFACE_C1.md`, `REV_A_STACKUP_BENCH_REQUIREMENTS.md`,
`REV_A_UPSTREAM_COUPLING_DISPOSITION.md`, K2/connector documents and open#45/#48.
