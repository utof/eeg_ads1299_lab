# Continue PR98: K2 nominal review published; new test corrections remain

Read root `AGENTS.md`, `REPOSITORY_PUBLICATION.md`, `DEVELOPMENT.md` and
`REV_A_BENCH_FIRST.md`. Check live main/PR98 heads and original review threads.
**Five SPI sites, C104/P3 repairs and S1-S4 reconciliation are already applied.**
Never reapply the recovery packet or recreate completed geometry/fault tests.

Use the [hosted capability preflight](REPOSITORY_PUBLICATION.md#hosted-capability-preflight).
Local missing Git/gh/KiCad/pcbnew/DNS is not a global blocker. Connected source
publication and separate read-only hosted native execution worked in this slice.
An explicit denied source write is a different condition: do not retry/bypass it.
No user local installation is required merely to restore those working routes.

## Current state and next bounded task

Main was checked at `c2f93ee30eb47f80a7702603f20ed22e6cce86af`. Draft PR98 is
`work/l5-spi-series`. K2 source is published at
`2888cede92df9c80fb2b0d294951d6db127b12c8`, complete tree
`4d708bd58651725ad8609f413d05d61bee8f7044`. Later documentation is not a new
execution of that source. The PCB and all carrier/B3 solids are unchanged.

The old strict K2 board identity is now reconciled after the nominal R24 review.
The remaining failures are in the NEW checking code, not that old identity:
1. Ruff requests one list-comprehension line wrap in `tests/test_carrier_l5.py`.
   The exact-head full gate stopped there before any later stage.
2. Read-only pinned KiCad execution found `FOOTPRINT.GetProperty` does not exist.
   The new placement/courtyard test fails at that call before geometry assertions.
   The existing native field API uses `GetFields`; do not invent an API double
   or accept collection, exported data, or the old green CAD run as a test pass.

A `GitHub.create_blob` attempt for the formatter-only replacement was explicitly
blocked by OpenAI safety checks. It returned no blob, was not published and was
NOT retried through a workflow, another API or another account. That is a real
operation denial, not a reason to ask the user to install Git or KiCad. The
separate read-only inspection of UNCHANGED published source was accepted.
Next needs a legitimately available authorized corrective source operation,
not a disguised retry of the denied operation. Preserve both known defects and
all acceptance predicates; do not relax formatting, disable the native test or
change gate selection. Then run exact-head combined gates and independent review.
Do not move to fabrication or treat this nominal review as full PR acceptance.

## K2 findings and limits

R24 is the only added AFE footprint. Sixty-eight old raw footprint forms match;
U1's only footprint change is its driver-pad net annotation. Original placement,
outline/top-level drawing and K2/view/B3 SCAD are retained byte-for-byte.
Current board SHA256:
`7873928ea7118b9e39822c0c2b2a70f47df58b01c8b1696c16d343b2b7ec1b7a`.
The strict one-hash check and altered-R24 rejection controls remain in source.

The allocated R24 box x55.4..58.6/y28.6..30.2/z0..4 mm fits the existing blanket
allocation and clears modeled installed K2/B3 obstacles. It is allocated space,
NOT a selected part or manufacturer maximum. Both 0.5-mm upper-approach probes
at the pad centres, z4.1..30 mm, are BLOCKED assembled and clear in the specified
upper-assembly-removed state. This is not a solder-tool envelope or joint-level
access proof. Removing only one cable is not claimed sufficient. Actual part,
height, solder/tool/thermal/insulation/workmanship and reassembly acceptance
remain before use. No in-situ soldering beneath a ribbon or blind-cut/flying-wire
fallback is supported. No physical removal, fitting, mating or power is authorized.
Read the L5 amendment in `REV_A_CARRIER_K2.md` and
`checkpoints/20261012_l5_k2_review.json` for the nominal source review.

## Actual evidence, not borrowed outcomes

`checkpoints/20261012_l5_k2_gate.json` retains exact source/run/artifact identities.
Local installed pytest plus REAL OpenSCAD2021.01: 65 carrier/service cases pass,
no errors/skips, 99.781s; 18 cases outside the native selection were deselected.
The original wrong-port, tilted insertion, cable, seating and support controls
remain. This is not a local locked gate or native KiCad execution.

Exact 2888 quality run38177492156 failed its formatter stage. Inspected artifact
11716705513 has no completed gate stages and no project-test result. Separate
read-only run38177782530/job114583722047 checked the same exact source with
KiCad9.0.2 and locked dependencies: 2 passes, 1 failure. The strict current-board
binding and existing C4 native placement pass; the NEW R24 test fails on the
unsupported API. Genuine native exported DNP/fields/lands/courtyard data agree
with the allocation, but that inspection does not convert the failed test to pass.
Tracked source stayed unchanged. ZIP hashes/CRCs, source identity and JUnit were
checked. No current complete native, firmware or overall green gate is claimed.

Source-only publisher run38177417350 verified the original patch digest, exact
seven-file scope and full tree, published only a temporary branch and independently
cloned it. Seven connector blob entries reproduced the full tree before the
non-force expected-head PR update. No project code executed with write privileges;
no synthetic materialization ancestry or workbench workflow entered the PR tree.
The one transport typo was repaired under the ORIGINAL complete digest before
this successful publication, not as a workaround for the later denied write.

## Retained completed work and historical verification

S1 recapture confirmed all 17 selected supply paths and original numerical terms
unchanged. S2-S4 explicitly distinguish OPEN_DNP/NOT_SELECTED from conditional
fitted receiver-waveform examples; no resistance is selected and acquisition is
false. R114 remains receiver-side; logical MOD1.GPIO13 remains downstream of R24.
Unknown current/voltage bounds and physical-qualification=false remain unchanged.
Preserve real input history through bcff4880, including S1 input6e4a207e and S2
input7bc15dcb. Do not replace committed input hashes or recreate those studies.

Historical d45acaaf/tree85d3da92 passed both ordinary Python jobs, 1399 cases plus
14 subtests, all 309 KiCad cases inside 450s, and actual ESP32-S3 compilation.
Its integration result was 186/187 with the THEN-old K2 identity failure. Those
results are in `checkpoints/20261011_l5_supply_gate.json`; they do not cover the
new test module. The older C104/P3 repair and all 15 SPI faults are retained.

Independent exact-source review remains outstanding. The last historical Codex
request returned quota exhaustion (comment6103095217); no new review is claimed.
Keep original review history. Do not use old approvals or another account as a
substitute. Keep PR98 draft and unmerged until combined gates and review pass.
Only after combined acceptance consider L4's remaining MCU-launch/control-channel
pilot disposition; no new generic study or duplicate quote campaign is needed.

## Retained engineering and physical boundaries

Keep 450s CAD/71% branch floor, 39 prior terminal cuts, 15 SPI faults, 15 bypass
corridors and reference/domain/mounting requirements. MISO/MISO_DRV retain combined
whole-channel budgets. PCB, schematic, BOM, carrier/B3 solids, firmware, product
workflows, dependencies and frozen Q1 were not changed by this K2 slice.

All five series positions remain OPEN_DNP, not zero-ohm links. L1-L4/B1-B3 and
#45/#48 remain. Pilot scope is INTERNAL-TEST-ONLY with six upstream analog pairs;
E1 performance and possible further PCB revision cost remain separate. Internal
mux modes are not electrical isolation. MCU launches/other controls remain separate.

B1 uses J2; B2 run card and B3 contact/insulation/restraint/earth/uncertainty rules
remain. Keep R -> fresh F1 arm -> wake/clock ->150ms -> VCAP1>1.1V -> reset, not
raised VCAP1 while parked in PWDN. BOARD_PROFILE_REVIEWED stays false; both DevKit
USB ports stay excluded. STOP is not a power disconnect. Moscow is a planning
assumption and Q1 remains the sole frozen unsent packet. No prices/outreach,
purchases, fabrication, construction/rework/mating, power, external acquisition
or person/animal connection is authorized.
