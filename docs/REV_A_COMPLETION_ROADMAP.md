# Rev A roadmap - K2 nominal review complete; combined validation and review

Continue draft PR98 from live head; main was checked at c2f93ee3. Hardware already
contains five SPI positions and the C104/P3 reference repair. Never reapply the
archived candidate. Read LLM_HANDOFF and the [hosted capability
preflight](REPOSITORY_PUBLICATION.md#hosted-capability-preflight). Use connected
publication and separate read-only hosted execution rather than local setup handoffs.

| Category | Remaining substantial turns | Done/status | Next slice or blocker |
|---|---:|---|---|
| S1-S4 source/topology reconciliation | 0 for this source repair | Fresh unchanged S1 geometry; explicit actual OPEN_DNP versus conditional S2-S4 examples | Exact d45 ordinary/CAD/firmware pass; independent acceptance pending |
| C104/P3 reference repair | 0 for this repair | Already applied; prior complete CAD passed all relevant reference/fault cases | Retain geometry and unchanged thresholds |
| K2 nominal fit/source binding and access | 0 for nominal review; physical evidence later | R24 allocation clears retained K2/B3 geometry; strict current-board binding and altered-R24 controls | Upper approach blocked when assembled; actual part/tool/joint/process acceptance remains before use |
| Independent review / PR98 merge | Review-availability dependent | Last Codex request returned review quota exhaustion; draft not merged | Complete exact-head gates and independent review; no old approval substitution |
| Other digital-channel disposition | 1 bounded decision plus evidence | MCU launch stages and DRDY/control paths remain separate | Source-end/channel evidence or explicit limited-pilot disposition |
| Components/manufacturing | 1-2 plus evidence | Existing proposals and frozen Q1 retained | Accepted stack/component/assembly decisions and actual SPI fit decision |
| Startup / internal capture | Assembly/equipment-dependent | Existing B1-B3 plans; all five SPI sites open; firmware gatefalse | Actual population/assembly/instruments and separately approved commissioning |
| Fabrication release | 1 after prerequisites | Not released | One consistent revision and acceptance of restricted pilot purpose/revision risk |
| External-input characterization | Later, measurement-dependent | Unqualified; another PCB revision possible | Existing E1 source/noise/coupling/uncertainty requirements |
| Prices/RFQ | Paused | Sole frozen unsent Q1 | No lookup, duplicate packet, outreach or purchasing |

Estimates overlap and exclude supplier/manufacturing/shipping waits and physical
measurements. They are not safety percentages. The supply repair leaves all
numerical assumptions, unknown bounds and qualification=false intact; current
examples require separately reviewed fitted receiver waveforms, not invisible
zero-ohm links across the actual DNP sites. No operating capture was performed.

Read `checkpoints/20261011_l5_supply_reconciliation.json` for exact source/run
identities. S1's five native cases pass after fresh extraction; the source-only
six-commit import preserves real input history. The formatter preserves both
executable-example ASTs and changes only S4's dependent document digest. Hosted
ordinary, CAD, native integration and target compilation are separate results;
no partial or old result is a full combined-source pass.

The existing hardware/reference checkpoints remain historical and unchanged.
No PCB, component, firmware, product workflow, dependency, frozen Q1 or physical
permission changed in the supply slice. Keep450s CAD/71% coverage, all15 SPI faults,
39 prior terminal cuts and the reference/domain/mounting guards. The K2 source-binding correction follows the documented nominal R24 review.
Next complete exact-head gates and independent review; do not repeat source
recovery, supply reconciliation or the already-completed reference repair.

Historical d45acaaf verification: both ordinary Python jobs pass;1399 ordinary tests
plus14 subtests in checked3.13 output; all309 KiCad cases pass in364.617s; actual
ESP32-S3 compilation passes. The native integration selection has186passes and
only the strict K2 board-binding failure. The whole PR is still blocked; do not
count later receipt-only commits as a new execution of those results. Read
`checkpoints/20261011_l5_supply_gate.json`. Next K2 review must retain its strict
altered-board protection and distinguish DNP nominal space from fitted-part access.

K2 continuation on58ebd9a9: source inspection retains68 raw footprint forms and
all old U1 geometry, with only its driver-pad net annotation changed. R24's
allocated3.2x1.6x4mm space is not a selected part maximum. Actual local OpenSCAD
shows no modeled allocation collision, but both upper approaches are obstructed
with the assembly/sense corridors installed. Removing the upper assembly is a
future unpowered-service condition, not present permission or tool-fit proof.
Read the L5 amendment in REV_A_CARRIER_K2.md and its20261012 checkpoint.
Latest combined hosted gates/review must be read against their exact source.
