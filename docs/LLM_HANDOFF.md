# Continue with the standalone breadboard measurement

Read root `AGENTS.md`, `REPOSITORY_PUBLICATION.md`, `DEVELOPMENT.md` and
`REV_A_BENCH_FIRST.md`. Read live main, open PRs and original review threads.
Use the [hosted capability preflight](REPOSITORY_PUBLICATION.md#hosted-capability-preflight).
Local tool absence does not disable connected publication or hosted execution;
explicit denials must not be bypassed.

## Current accepted source and meter follow-up, 2026-10-15

PR101 is merged. Live main was read back at
`9d2fc299a348fd5b9c011f9493feab9d21f04658`, tree
`fa56722c1868d3624220a256450e717c40e13d2c`, identical to accepted head
`79606a49595077593f3e5fb49f379aaef8351839`. Its merge commit preserves full
verification/review receipts and artifact hashes. All five jobs passed:
Quality 38679107604 (1,411 cases plus 14 subtests on both Python versions,
86.954% branch coverage, 190 native cases), Schematic 38679107597
(49 harness-console and 310 CAD cases, 250.896 s), and actual S3 target
Firmware 38679107616. Hosted review 6184143883 found no major issues; all five
original threads were resolved. Do not repeat this completed acceptance work.

The user checkout was fast-forwarded cleanly and its locked environment/hooks
refreshed. The local full gate still reaches its unchanged 300 s ordinary-test
limit under concurrent host load; the failed two-worker ordinary trial was not
adopted. Complete hosted results are distinct from this local limitation.

This small documentation follow-up adds a checked UT139C manual-range example
to the existing breadboard guide, including its selected-range accuracy, lead
sockets and separate meter batteries. It is not the user's confirmed equipment.
The actual model/manual still needs checking on receipt; the manufacturer's
current PDF endpoint was unavailable, so the guide names and hashes the
manufacturer-authored distributor copy inspected. No new worksheet or code.

**Next bounded step:** receive the standalone kit, identify the actual meter,
and record the divider readings in `BREADBOARD_FIRST_STEPS.md`. Rev A still
needs the actual Q03 land/process answer and applicable manufacturing decisions
before coordinated BOM/CAD migration. Q1 is unsent; recipient/contact
authorization is absent. No fabrication, power or body-use gate changed.

## Shipping-window background accepted by PR101, 2026-10-15


The user authorized further bounded improvements while parts ship, with a
five-hour working window and a preference for visual results. This continuation
started from clean PR101 head `316ae0d4305c05f96cdf3c1bd793ace2bfbc057c`, tree
`3dfc9799d209e3f2ec546f9981854682ab242ee2`; main was still `e666fc0921197a857f1ea5c551d464ceb14358cb`.
Keep PR34/40's do-not-merge experiments untouched. Read live PR101 state before
continuing; the previous four preparation steps are published there, not yet
established as main by this note.

The demonstrated blocker was repeated 450 s CAD timeouts. The same-source hosted
comparison in `DEVELOPMENT.md` timed out serially, but executed the identical 310
cases in 251.031 s with two pytest-xdist workers. The change uses that existing
library's file scheduling, isolated temporary directories and failure reporting.
No fault selection, deadline or 71% branch floor was weakened. A separate local
failure probe demonstrated orphaned workers after a controller timeout; the
existing runner now terminates its POSIX process group on timeout or cancellation.
Independent reviews then reproduced cancellation gaps during active waiting,
process construction and timeout cleanup. Each was demonstrated failing before
correction; `DEVELOPMENT.md` retains the reviewed-head/failure table. The final
scoped standard-library signal context delivers default SIGINT/SIGTERM exceptions
only inside the cleanup-protected wait and defers them during construction and
cleanup. Custom/ignored handlers remain caller-owned. All 32 runner cases passed
locally; final-head checks/review remain the acceptance authority. Earlier green
heads do not verify later corrections. The lockfile is included in the CAD source
snapshot, with a focused changed-lock regression. The runtime comparison remains
diagnostic evidence, separate from final-head acceptance.

`BREADBOARD_FIRST_STEPS.md` now has explicit row layouts, a polarity/discharge
diagram, a labelled nominal charge curve and its single in-place measurement
record. These prepare the two-AA exercise; no Rev A board connection is implied.
The existing localhost capture rehearsal also ran: 2248 accepted synthetic
samples, two intentional omissions detected, one uninterrupted four-second
spectrum window, 10 Hz peaks on all four channels. Capture implementation was
unchanged from 316ae0d; the record is software transport evidence, not measured
ADC data. No new capture subsystem or hardware guard change was needed.

The ordinary local pre-change gate at 316ae0d again exceeded 300 s; it remains a
failure (`reports/cad-runtime-before/`). New focused runner and snapshot tests
were observed failing before correction. See PR101 for the current exact-head
full checks and review; do not borrow its earlier four passing jobs as acceptance
of the new execution behavior.

The independent local two-worker ordinary-test trial on 44c1609 also reached
300 s under concurrent host load, without a completed coverage/JUnit receipt.
It was not adopted: ordinary/native execution remains serial, with all tests
and deadlines intact. Profiling did not establish a small validator correction
that would resolve the whole timeout; no speculative validator cache was added.

The acceptance/merge step above supersedes this continuation's former open-PR
instruction. Preserve the recorded failures and corrections; continue from the
current physical dependency rather than reopening the completed paper probe study.

## Four-step continuation, 2026-10-15

Started clean from live main `e666fc0921197a857f1ea5c551d464ceb14358cb`, tree
`7dfbbf4d77f7ad0763086295b38421ba7a3c3732`, the verified PR100 merge.
PR100's accepted head was `fb7de0c580966068f0e8988b8f3dbf40f4d3043c`;
its merge message retains the five successful checks, review and artifact
identities, including failed attempts and independent hash-check limits.
PR34/40 remain open do-not-merge experiments. This work uses branch
`docs/pilot-four-step-disposition` in the attached internal-filesystem worktree.

Four bounded preparation steps were carried through together:

1. Q04 now has a node-specific conditional pilot design disposition in
   `REV_A_PILOT_CAPACITOR_DISPOSITION.md`. Candidates retained; functional
   uncertainty and replacement consequences are explicit. TI's EVM uses the
   legacy25V1uF part and does not validate our16V proposal. Guaranteed effective
   C/ESR/internal startup bounds remain unestablished; before-power review and
   final build-risk acceptance remain required.
2. The fitted-build record now selects outsourced PCB/TH/tail/crimp work and
   assigns the physical inspection responsibilities. Q03's land/process response
   remains a real migration hold. No active BOM/CAD edits were justified yet;
   do not call the planned26-capacitor/five-resistor migration delivered.
3. `BREADBOARD_FIRST_STEPS.md` provides the minimal standalone kit and divider/
   slow-RC wiring, independent equations, fault predictions and a measurement
   record. The user has no equipment at the current house and can buy. This
   learning kit can be bought without a Rev A release; no purchase was made.
4. Q1 now has a dated current addendum, and B2 records the actual equipment gap
   and prior-interlock requirement. The frozen quote CSVs/manifest are unchanged;
   no duplicate schedule, new calculator, software layer or tests-for-prose.

**Next dependency:** actual Q03 land/process disposition plus applicable
Q01/Q02/Q05-Q07 manufacturing responses. The user has not authorized supplier
contact or selected a recipient. Prepare no duplicate RFQ and invent no answers.
Once the migration conditions are disposed, apply the five SPI fits and26 AFE
capacitor identities coherently across BOM/CAD/contracts/native fixtures and
S1-S4 bindings, using focused failure-first checks and exact-head native review.
Active source still has five OPEN_DNP/NOT_SELECTED sites and legacy AFE capacitors.

Independent next user step: obtain the small breadboard kit, report the exact
meter model, and perform the standalone divider measurement. Rev A power still
requires the existing B1-B3/L6/Q04 conditions, source/probe selection, numeric
limits and prior interlock evidence. Body use remains outside the pilot.

The pre-change ordinary gate at `e666fc09` passed1402 cases plus14 subtests
in244.30s, with86.93%branch coverage. Three existing entrypoint checks and
changed-document local-link checks also passed. The unchanged frozen Q1 files
and both authored board hashes were independently compared with the starting
commit. Post-change/full hosted results must bind to the final source head.

Continuation is published as [PR101](https://github.com/utof/eeg_ads1299_lab/pull/101).
Its first reviewed head `f11088e1f33bf3880c1da9090a9501101bbee9b2` passed all
five hosted jobs (Quality38664887092, Firmware38664887015, Schematic38664887062).
Hosted review4278061190 identified an obsolete quote-preparation instruction;
that paragraph and its historical table are now explicitly superseded. Recheck
the final head and resolved review thread before merging; those earlier checks
are not execution of this wording correction. The post-edit local ordinary run
passed1402 cases plus14 subtests in263.16s/86.93%branch coverage during document
editing; final-head hosted evidence remains the acceptance authority.
The later local gate on `a47027557744ddd6109f1525a79dba0f63daf272` reached
the unchanged300s ordinary-test deadline (`reports/four-step-final/`), so it is
not a pass. A second hosted finding4278100520 required an explicit capacitor
discharge before every breadboard run. That step, removal of the discharge
resistor, and the nonzero-starting-voltage equation are now in the guide.
Retain both corrections and verify the final PR head; do not weaken deadlines.

The following repository/setup history is retained evidence, not the current
next-task instruction. Publication/verification of this continuation must name
its actual final head; do not borrow PR100 checks as execution of these edits.

## Verified repository state, 2026-10-15

Live main and the clean starting checkout are now PR99 merge
`cabe26473a26421704d93210a465a8a3d24021d8`, tree
`ca2f1854abefb134e32a9258de7fc213fc34d2c1`, identical to accepted head
`23d62e268d54f3906e764a98395ecffb8ad61115`. Its five hosted jobs passed:
Quality38656735973 (both Python versions and190 native cases),
Schematic38656736012 (49 harness and310 CAD cases,437.423s), and
Firmware38656735869 (actual S3 build). Hosted review comment6181114357 found
no major issues after the original stale-instruction thread was fixed/resolved.
The merge commit retains artifact identities and independent-hash-check limits.
PR99's ordinary local gate passed1402 cases plus14 subtests in231.76s.

Separate post-merge main runs Quality38658127643 and Firmware38658127735 passed.
Schematic38658127664 failed its unchanged450s schematic-tests deadline after
1402 ordinary cases plus14 subtests and49 harness-console cases passed. The
failed job log was inspected; this is not a new accepted main CAD run. Do not
substitute PR99's pass for it. A new local pre-change ordinary run for the fitted
proposal also hit300s; retain `reports/fitted-build-before/` in the attached
internal-filesystem worktree. Do not weaken deadlines or characterize either
timeout as physical evidence or an observed component defect. The post-change
ordinary run at `0c48845884508faa05f1d1b21985407b8469854f` also reached300s;
its evidence is in `reports/fitted-build-after/`. Fresh hosted results must bind
to the actual final proposal head; neither local timeout is a pass.

The PR98 state and setup receipts below are historical, not instructions to
repeat their completed repairs. The current fitted proposal is described below.

PR98 **merged on 2026-10-13**. Live main and the returning local checkout were
both `bab9f60f23c799c9da00fd531acd8a5b9ad1ecd7`, complete tree
`96afda406d9b0d7715d4fae4b2afa50d3f64b4a2`; the initial working tree was clean.
That tree equals accepted PR head `26d5ad903e1e48ce7fc435e3abef664a9812a9dd`.
The old combined-acceptance and guarded-merge task is complete. PR34 and PR40
remain open historical experiments explicitly marked do not merge.

Five SPI positions R117-R120/R24, C104/P3 repairs, S1-S4 reconciliation, K2
nominal review, R24 native GetFields correction, formatter and receipt-inventory
regression are active source. **Never reapply the archived candidate or repeat
these completed repairs.** The authored PCB remains
`hardware/rev_a/layout/rev_a.kicad_pcb`.

## Acceptance and separate post-merge execution

The [PR98 record](https://github.com/utof/eeg_ads1299_lab/pull/98) and merge
commit preserve durable source/run/artifact identities. Live checks were re-read
on 2026-10-15. These are historical results for exact `26d5ad90`, not fresh local
execution or physical evidence:

| Required job | Accepted result | Run |
|---|---|---|
| Python 3.11 and 3.13 quality | Both passed; 1402 cases plus 14 subtests each | 38396036350 |
| Native integration | 190 passed | 38396036350 |
| Native KiCad 9.0.2 | Attempt2 passed 310 cases in 345.975s | 38396036354 |
| Actual ESP32-S3 compilation | Passed | 38396036413 |

Exact-head Codex comment6145389281 reported no major issues. Both original
review threads were addressed and resolved. The merge record retains artifact
hashes and independent-check limitations. The first CAD attempt timed out and
remains a failure; no deadline or fault test was waived.

On merged `bab9f60f`, Quality38399520706 and Firmware38399520824 passed.
Schematic38399520579 separately **failed the 450s schematic-tests deadline**
after ordinary and 49 harness-console cases passed. Job115303238142 records the
timeout; artifact11815710029 has SHA256
`6c33342078241d1f4b897b9583102c78d22a2d1d1092a6210642103ef3f69423`.
This does not establish a new board defect or erase the accepted PR result.
The unchanged retry on 2026-10-15 **passed**: attempt2/job116145559750 ran
310 schematic cases in432.07s, within the same450s deadline. The job log records
artifact ZIP SHA256 `a255eed0e096b0b26e990513b8565dd018c036318f32941fc92d003831eb5fe9`.
This continuation inspected the job result/log, not every archived artifact hash.
The first failure remains recorded; one retry does not establish timing margin.
Do not substitute pre-merge execution for this separate post-merge result.

## Returning local environment

On2026-10-15, installed uv0.12.18, the locked Python3.13 environment with all
extras, both Git hooks, hash-verified ArduinoCLI1.3.1 and ESP32 core3.3.12.
The original checkout is on a FUSE filesystem. Its initial ordinary run and a
second run with only the environment/output moved to the internal filesystem
both exceeded the unchanged300s ordinary-test limit. The discovery case passed
alone; the full local gate must not be described as green from that result.
The app-managed copy on the internal Linux filesystem passed the unchanged
`uv run --locked python -m tools.check --firmware --out reports/setup` at
`abcd1e43da57c6b747c2693e3b09f2c733554d6e`, tree
`91cd7f3188e57e2dbbbfac02cacb19f276ae731d`: 1402 ordinary cases plus14 subtests
passed in285.27s, branch coverage86.931079%, followed by an actual ESP32-S3
compile with four fresh binary hashes. Total gate time was330.13s; the ordinary
test stage stayed within300s. The tracked source remained clean. This is local
ordinary/target-build evidence, not local native-simulator or KiCad execution.
The later documentation-only receipt does not constitute another full run.
Inspect the attached workspace and PR99; do not weaken timeouts or fault controls
to accommodate the original mount. Neither local nor hosted passes qualify power.

The user completed the system-package installation on2026-10-15. Package and
executable probes confirm ngspice42+ds-3build1 and OpenSCAD2021.01-6build4;
Node22.22.3 and g++13.3.0 are present. Do not ask for these packages again.

The subsequent unchanged `tools.check --native --out reports/native-setup` at
`d8c62936d32b6b6c41942e83f3015ee9f7f9f90a`, tree
`b533aad111f3e1cb7a10def07159f8ccd5e1182d`, **failed locally**: 1402 ordinary
cases plus14 subtests passed in293.77s, branch coverage86.931079%, and the
power/supply simulation commands completed, but native-tests reached its300s
deadline. Total gate time was598.82s; no complete native JUnit/pass is claimed.
An active OpenSCAD R24-probe render was observed late in the run; this is not a
complete performance diagnosis. Reports are retained in the internal worktree's
ignored `reports/native-setup/`; tracked source stayed clean. Keep the timeout.

The same `d8c62936` source has a successful hosted Native integration check,
run38652056137/job116153449588, re-read after the local failure. That hosted
result does not turn the local timeout into a pass. Use the existing hosted
route for complete native verification while local runtime remains unresolved.
Pinned KiCad9.0.2 also remains hosted. No missing package or physical release
follows from these results; the L6 decision and next build task are below.

## L6 channel decision and next bounded engineering task

Merged PR99 carries the [L6 disposition in L4 section3a](REV_A_SPI_PROVISION_L4.md#3a-l6-retain-remaining-paths-for-a-restricted-pilot-revision-is-the-fallback):
retain the three MCU-launched SPI paths and separate DRDY/control wiring for
the proposed INTERNAL-TEST-ONLY pilot. Add no further series sites in this slice;
accept a reviewed fanout/board revision as the fallback, not promised trace
surgery. The terminal map includes latch-local clock/clear, all three enables
and separate MCU feedback. Before fabrication release, the consolidated build
must explicitly accept possible replacement-board cost and establish supported
measurement access/commissioning feasibility. Startup-critical assumptions and
an independently bounded interlock commissioning arrangement remain before-power
work; actual interlock evidence must precede ADC bus enable. B2 is the sole run
card. No wiring, fitted part, firmware flag or release gate changed. This is a
paper decision, not electrical qualification. Do not repeat the disposition
or the earlier K2 review.

The pre-change ordinary gate at `d90109890fab042eb74ca04d6a7245f568c9f8ea`
passed1402 cases plus14 subtests in277.50s on the internal filesystem; branch
coverage86.931079%. Later review/CI must identify the actual L6 head rather than
borrowing this baseline pass. Source inspection included the actual C2/startup
firmware and frozen endpoint graphs; no physical channel evidence was produced.

The [fitted pilot proposal](REV_A_FITTED_PILOT_BUILD.md) selects33ohm
RC0603FR-0733RL at R117-R120/R24 as a replaceable initial fit, retains the
26-capacitor migration shortlist and targets JLC04161H-7628 for both boards.
It retains the existing connector/assembly arrangement and records the delta
from frozen Q1:109 proposed fitted board components, versus104 currently.
It does not prove matched termination, timing or assembly acceptance. The
active source STILL has five OPEN_DNP/NOT_SELECTED sites and legacy AFE caps.
No hardware, code, tests, firmware flags or Q1 schedules were changed by the
proposal. Do not silently populate parts from mixed-stage files.

**Historical PR100 next step (now superseded above):** Q04 disposition using the existing
evidence for C8-C10 internal nodes, local LDO pairs and reference companions.
State accepted limited-pilot uncertainty or the exact rejection; do not restart
a generic part-family search. Q03 process/lands and the other applicable
Q01-Q10 manufacturing conditions remain open. Once disposed, apply the five
SPI fits and26 capacitor identities in one reviewed BOM/CAD/contracts/native-
fixture change with focused failure-first checks and S1-S4 reconciliation.
Keep source ownership simple; no new framework or parallel quote schedule.

Preserve the sole frozen unsent Q1 in `docs/quote/`; later source deltas do not
rewrite its historical hashes. Before fabrication, accept one consistent build,
restricted purpose, possible revision cost and actual measurement access.
Any powered procedure needs actual inspection/fitting, fixture/source/instrument
checks and reviewed staged current/abort limits; interlock evidence precedes ADC
bus enable. CI cannot replace those conditions. Supplier contact remains paused.

The returning user wants practical breadboard learning too. A separate passive
R/C check can be planned from their equipment inventory without waiting for
fabrication. It is not the ADS1299 assembly or Rev A validation: the selected ADC
is surface-mount and the current prototype uses the designed two boards. Do not
reopen component selection or silently replace the boards as a setup task.

The following retained limits describe the already-merged work; references to
the API correction are historical, not instructions to repeat it.

## K2 conclusion and limits retained

R24 is the only added AFE footprint. Sixty-eight older raw footprint forms match;
U1 changed only its driver-pad net annotation. Original footprint geometry,
outline, carrier/view/B3 solids and the PCB are unchanged in this correction.
Keep the single strict AFE SHA256 binding
`7873928ea7118b9e39822c0c2b2a70f47df58b01c8b1696c16d343b2b7ec1b7a`
and both shifted-R24/land-size rejection controls.

The allocated x55.4..58.6/y28.6..30.2/z0..4mm box clears nominal installed
obstacles. It is allocated space, not a selected part or manufacturer maximum.
Both0.5mm straight upper probes are blocked assembled and clear in the specified
upper-assembly-removed model. Removing one cable is not assumed sufficient.
This does not qualify solder tools, joint-level access, thermal or insulation
conditions, workmanship, actual fitting or reassembly. No in-situ soldering under
the ribbon, blind-cut/flying-wire fallback, physical removal or rework is approved.
Read `REV_A_CARRIER_K2.md` and the historical K2 review/gate checkpoints.

## Other completed work and unchanged boundaries

S1's genuine recapture retained all17 selected supply paths and numerical terms.
S2-S4 distinguish OPEN_DNP/NOT_SELECTED from conditional fitted receiver-waveform
examples. R114 remains receiver-side; logical MOD1.GPIO13 remains downstream of
R24. Keep unknown current/voltage bounds and qualification=false. Preserve real
input history throughbcff4880, including S1 input6e4a207e and S2 input7bc15dcb.
All five active positions remain OPEN_DNP/NOT_SELECTED; the later fitted
proposal selects33ohm for coordinated migration. No active fit is implied.

Retain all39 prior terminal cuts,15 SPI cut/short cases,15 bypass corridors and
reference/domain/mounting controls. MISO/MISO_DRV retain combined whole-channel
budgets. No PCB, schematic, BOM, carrier/B3, firmware, product workflow or frozen
Q1 changes are part of this API correction.

L1-L4/B1-B3 and#45/#48 remain. Proposed first pilot is INTERNAL-TEST-ONLY with
six upstream analog pairs retained; E1 performance and possible revision cost
remain separate. Internal mux modes are not electrical isolation. MCU launch
stages and other controls retain L6's separate physical acceptance conditions.
B1 uses J2; B2/B3 contact, insulation, restraint, earth and uncertainty requirements
remain. Keep R -> fresh F1 arm -> wake/clock ->150ms -> VCAP1>1.1V -> reset, not
raised VCAP1 while parked in PWDN. BOARD_PROFILE_REVIEWED staysfalse; both DevKit
USB ports remain excluded. STOP is not a power disconnect.

Moscow remains a planning assumption; Q1 is the sole frozen unsent packet.
No price campaign, outreach, purchase, fabrication, construction/rework/mating,
powering, external-input acquisition or person/animal connection is authorized.
