# Continue after merged PR98: remaining channels and pilot build decisions

Read root `AGENTS.md`, `REPOSITORY_PUBLICATION.md`, `DEVELOPMENT.md` and
`REV_A_BENCH_FIRST.md`. Read live main, open PRs and original review threads.
Use the [hosted capability preflight](REPOSITORY_PUBLICATION.md#hosted-capability-preflight).
Local tool absence does not disable connected publication or hosted execution;
explicit denials must not be bypassed.

## Verified repository state, 2026-10-15

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
An app-managed copy of the same source on the internal Linux filesystem was
prepared for full verification; inspect the attached workspace and PR99 results.
Do not weaken timeouts or fault controls to accommodate the original mount.

Local ngspice/OpenSCAD installation requires administrator authentication that
the chat does not have. The requested terminal install is pending; Node and a
C++ compiler are present. Pinned KiCad9.0.2 remains available through hosted CI.
These local setup limits do not block source publication or hosted verification.

## Next bounded engineering task

Complete **L4 section3**: disposition of the three MCU-launched SPI stages and
separate DRDY/control channels for the restricted pilot, using applicable
existing evidence or an explicit bounded-pilot disposition. The five new sites
do not cover those stages. No generic replacement study or repeated K2 review.

Then resolve the five sites' fitted values/MPNs and the consolidated component,
stackup, connector and assembly decisions. Every site is OPEN_DNP/NOT_SELECTED;
even zero ohms is unselected. An open SPI path cannot produce the planned
internal-test capture. Preserve the sole frozen unsent Q1 in `docs/quote/` and
carry later source deltas explicitly rather than rewriting historical hashes.
Before fabrication, accept one consistent build and its restricted purpose.
Before power, require actual inspection/fitting, fixture and source/instrument
checks, reviewed staged current limits and abort thresholds. Measurements are
not prerequisites for every paper decision, but CI cannot replace them.

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
No resistance, including zero ohms, is selected; all five positions remain open.

Retain all39 prior terminal cuts,15 SPI cut/short cases,15 bypass corridors and
reference/domain/mounting controls. MISO/MISO_DRV retain combined whole-channel
budgets. No PCB, schematic, BOM, carrier/B3, firmware, product workflow or frozen
Q1 changes are part of this API correction.

L1-L4/B1-B3 and#45/#48 remain. Proposed first pilot is INTERNAL-TEST-ONLY with
six upstream analog pairs retained; E1 performance and possible revision cost
remain separate. Internal mux modes are not electrical isolation. MCU launch
stages and other controls still need their separate limited-pilot disposition.
B1 uses J2; B2/B3 contact, insulation, restraint, earth and uncertainty requirements
remain. Keep R -> fresh F1 arm -> wake/clock ->150ms -> VCAP1>1.1V -> reset, not
raised VCAP1 while parked in PWDN. BOARD_PROFILE_REVIEWED staysfalse; both DevKit
USB ports remain excluded. STOP is not a power disconnect.

Moscow remains a planning assumption; Q1 is the sole frozen unsent packet.
No price campaign, outreach, purchase, fabrication, construction/rework/mating,
powering, external-input acquisition or person/animal connection is authorized.
