# Continue PR98: R24 native API corrected; combined acceptance is next

Read root `AGENTS.md`, `REPOSITORY_PUBLICATION.md`, `DEVELOPMENT.md` and
`REV_A_BENCH_FIRST.md`. Read live main/PR98 heads and original review threads.
**Five SPI sites, C104/P3 repairs, S1-S4 reconciliation and the K2 nominal
review are already applied. Never reapply the archived candidate.**

Use the [hosted capability preflight](REPOSITORY_PUBLICATION.md#hosted-capability-preflight).
Connected GitHub publication and read-only hosted KiCad/CI are separate from this
chat's local tools. Missing local Git/gh/KiCad/pcbnew/DNS is not a global blocker.
Use the available authorized route; do not transfer setup to the user merely
because local dependencies are unavailable. Explicit denials must not be bypassed.

## Current correction and source identity

Continue `work/l5-spi-series`, PR98. Main was checked at c2f93ee3. The K2 source
review is at2888cede, followed by historical evidence at8307374f. The actual new
correction is `e0caa9b50cf8a28f8a3e378c0562f8d9b0bf8727`, complete tree
`6aaccba9a735703704613397cfc826feeed4fece`. Only `tests/test_carrier_l5.py`
changed in that commit; its Git blob is60462b03b26b727197d96009155ec9d2abcb10f1.

The unsupported `FOOTPRINT.GetProperty` calls now use the native KiCad9
`GetFields()` collection and each field's `GetName()`/`GetText()`. Population
and MPN remain mandatory dictionary keys, without permissive defaults. Native
DNP, value, orientation, land count/position/size/net and full courtyard checks
are retained. The required comprehension formatting is corrected in the same
file. No native test was disabled, emulated, or replaced by an exported-data pass.

The direct UTF-8 GitHub.create_blob correction succeeded; its blob and complete
tree matched local Git before a non-force expected-head branch update. No new
publisher, workflow, account, permission, dependency or hardware change was used.
The earlier formatter-only refusal and failing native run remain historical in
`checkpoints/20261012_l5_k2_gate.json`; do not rewrite that receipt. They do not
mean the corrected source is still unapplied. Local inspection used the verified
remote source tree with different local commit metadata; that local ancestry
was not published. Existing real historical input commits remain intact.

Official API reference:
https://docs.kicad.org/doxygen-python-9.0/classpcbnew_1_1FOOTPRINT.html
The prior actual KiCad9.0.2 run38177782530 is the fail-before evidence. Five local
installed-pytest source/entrypoint checks passed after the correction, with four
native/schematic cases deselected. The local locked gate did not start before
a bounded dependency-download timeout. Neither local result is a native pass.

## Next bounded task: combined acceptance, not more geometry

Read actual CI for the LIVE PR head, including all five jobs: Python3.11,
Python3.13, native integration, native KiCad and actual ESP32-S3 compilation.
Use existing `tools.check`, locked dependencies and unchanged450sCAD/71%floor.
Inspect the actual JUnits and source/artifact hashes, including the corrected
R24 native test and all existing fault controls. Do not borrow earlier d45acaaf
or2888 results, infer success from collection, or confuse one successful job
with full acceptance. Later documentation is not a separate code modification.

Request independent review of the exact combined head and inspect original
threads and any new findings. The last historical Codex request hit review quota
on October10; that was not a global GitHub or hosted-tool failure. Do not claim
review completion until a current response exists. Do not use another account
or an old approval. PR98 must stay draft/unmerged until complete gates and review
are accepted. Once accepted, use the guarded merge-commit path, verify live main
and its complete tree, and move to L4's remaining MCU-launch/control-channel
pilot disposition. No generic replacement study or duplicate RFQ is needed.

The PR conversation and exact-head artifacts carry acceptance results produced
after this handoff was authored. This document identifies the completed source
correction and verification procedure; it is not itself a green-gate receipt.

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
