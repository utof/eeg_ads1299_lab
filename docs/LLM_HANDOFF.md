# Handoff for the next assistant or engineer

## User goal

An electronics beginner wants to learn EEG through runnable simulation and hands-on experiments, eventually studying perception, meditation and consciousness. They own an Arduino Uno, an unspecified ESP32, breadboards, basic components and >10 electrodes. Additional spending target: **$100**, not the $300 in the older uploaded reports. Their existing ESP32 model and country-specific sourcing still need confirmation before physical work.

The user has now identified their electrodes as **MCScap with insulated DIN 1.5 mm connectors**. Read `docs/references/mcscap/README.md`, the complete supplied Russian manual transcription and `source_record.json`. The manual specifies Ag/AgCl passive electrodes and TouchProof; the 1.5 mm dimension is user-reported. The exact catalogue suffix, actual cable length/shielding and impedance/noise test conditions remain unknown. Do not map the manual's <=5 kΩ bound to a measured electrode-plus-scalp resistance, its <=20 µV noise to an RMS noise source, or its <=2.5 m cable bound to the user's actual lead length.

Build around this owned electrode family first. Keep a few bad-contact cases for the same hardware, but do not add generic electrode registries, DDD/state-machine frameworks or parallel solver wrappers speculatively. The user's priorities are YAGNI, DRY, functional calculations and explicit validated states. Selected ADS1299/S3 components are not evidence that the user has purchased them.

## Current hardware decision

**Rev A means hardware revision A**, the named first board-design baseline, not a temporary simulator stand-in or just a shopping list. It selects a four-channel `ADS1299-4PAGR` daughterboard plus `ESP32-S3-DevKitC-1-N8R8`, internal ADS reference/clock, 5-V unipolar analog bench power, ADC-only `TPS7A2033PDBVR` DVDD regulation, and a 4.99 kΩ / 4.7 nF differential input network. Read `docs/HARDWARE_BASELINE_REV_A.md` and `hardware/rev_a/`. Do not reopen component selection for DX or simulation work. All hardware-review, purchase, firmware-port, schematic-release and human-connection gates remain false.

## Development workflow

Read `AGENTS.md` and `docs/DEVELOPMENT.md` before editing. The pinned project and development environment is installed with `uv sync --locked --all-extras`. Run `uv run --locked python -m tools.check` before and after changes. Install ngspice, Node, and a native C++ compiler to run `uv run --locked python -m tools.check --native`. Missing required tools must fail, not become a native-validation pass.

The shared check command enforces Ruff formatting/lint, strict Pyrefly (including warning-level diagnostics), cognitive complexity at most 15, Tach dependency/interface boundaries, the static hardware contract, unified pytest discovery, and actual branch coverage. New behavioral work and bug fixes start with a focused failing test; existing numerical behavior gets characterization tests before refactoring. Do not lower gates, add blanket suppressions, or refresh expected numerical results just to make checks pass.

`lab.analog` is now a package facade with `_model`, `_solver`, `_spice`, and `_report` internals. Preserve public imports such as `from lab.analog import InputNetwork, transfer`. Use the `hardware.rev_a` facade for hardware-contract functions. Cross-component imports go through public interfaces; internal modules must not import back through their own facade. Keep `__all__` and `tach.toml` aligned. Validate external data at entry points; array dtype annotations do not establish shape, units, or finiteness.

Hypothesis is already installed. A scoped mutmut 3.8.0 pilot actually ran in a separate hash-locked Python 3.13 environment: 292 mutants, 207 killed, 60 survived, 25 with no associated tests in the focused selection. See `docs/MUTATION_PILOT.md` for exact run/artifact, elapsed time, failed setup attempts and interpretation limits. Survivors have not been individually classified. mutmut is not a permanent project dependency or mandatory CI gate. The disposable experiment PR #16 was closed without merging and its authoring workflow removed. See `docs/MODEL_REUSE_REVIEW.md` for the measured adoption decision.

## What exists and what was verified

Read `README.md`, `docs/DX_VALIDATION.md`, `docs/RESULTS.md`, `VALIDATION.json`, and `docs/MODEL_SCOPE.md`. The latter historical results and validation file describe the original environment and are not silently overwritten by the new CI. Current quality logs and reports are generated under ignored `reports/` and uploaded as CI artifacts. `requirements-tested.txt` is historical; `pyproject.toml` and `uv.lock` define the current environment.

The package includes numerical passive-circuit analysis, ngspice exports/comparisons, a behavioral ADC, synthetic EEG-like sessions, quality/PSD/band-power analysis, a group-held-out toy classifier, custom binary transport, and actual localhost integration tests. The simulator is not a physiological brain model.

Unlike the original environment, the dated DX CI run in `docs/DX_VALIDATION.md` actually executed ngspice against the existing educational circuits and passed native C++ helper and localhost transport checks. Cite that specific run and scope. The later Rev A passive input study has its own executed evidence in `docs/REV_A_INPUT_STUDY.md`; neither validates the BIAS loop, power circuit or complete ADS1299 silicon.

## Hard boundaries to preserve

Do not call the entire ESP32 sketch compiled or hardware-tested because native C++ helper tests passed. No physical ADS1299 or ESP32 test was performed by the DX workflow. No body-use authorization is provided by this package.

Firmware remains bench-only and defaults to `BOARD_PROFILE_REVIEWED = false`. It uses only internal test/short mux modes, with bias and lead-off excitation disabled. Its default GPIO table remains original ESP32/WROOM-32. PR #28 adds an explicit `EEGLAB_REV_A_S3` compile selection for the unchanged proposed S3 map; see `docs/ESP32_S3_TARGET_BUILD.md` and the exact-head Firmware job before claiming a target build. No automatic profile selection or physical port validation follows. `configs/board_profile.example.json` is a worksheet, not a live firmware configuration.

Do not provide invented power, reference, bias or electrode connections for an unidentified module. Do not fix saturation with only a digital high-pass filter. Do not call model resistor values safe patient protection. Battery/wireless operation is a precaution, not complete certification. Do not switch to AD8232, ADS1115 or a different architecture as a tooling change.

## Productive next work

PR #11 has been merged at `9400c797003fe7610e8710b5954bab2851bdd66d` after its final three checks passed. Its selected-component passive study is implemented; do not describe that bridge as still unstarted. Source/contact impedances and ADC-node parasitics remain illustrative, not measurements of the owned MCScap leads.

Read `docs/MODEL_REUSE_REVIEW.md` before expanding the models. Actual TI TINA subsystem examples were located: `ADS1299_BIAS_MEAS.TSC` and a four-channel electrode/lead-off example. Their attachment downloads failed; they were not imported or simulated here. Retrieve/inspect them before claiming reuse. Reuse TI's SBAA188 RLD/BIAS topology and analysis; TI specifically connects it to ADS1299. The TPS7A20 vendor PSpice transient model has an executable optional compatibility pilot, but shutdown remains unresolved; read `docs/TPS7A20_COMPATIBILITY.md` and its independent controls. Do not launch a full ADS1299 transistor/macromodel implementation. Keep BIAS and power studies focused, parameter-bounded, and separate from the passive transfer solver.

The guarded explicit ESP32-S3 target build is implemented in PR #28. Subsequent hardware work is the exact four-channel schematic/ERC and independent footprint/polarity review; target compilation does not replace those reviews. PCB/layout and an actual delivered build quote follow those gates. The planning subtotal is not a verified complete delivered under-$100 build.

Before physical work, obtain the exact board schematic/revision and header photographs, verify the actual MCU and the electrode catalogue/lead details, and review power/reference/clock/digital compatibility. Complete internal-test/internal-short bench recordings without anyone connected. External dummy inputs require their own board-specific input/common-mode/protection review; a wearable stage requires a competent body-interface review.

Keep raw counts, event metadata, transport gaps and quality exclusions. Any future real-data classifier needs an explicit importer/event/montage path and held-out sessions or days. Never describe synthetic 100% classification as demonstrated brain decoding. For meditation comparisons, hold eye condition constant and record subjective observations separately.

## Change discipline and review

Make one substantial change at a time; add a regression test; retain useful failing evidence. Do not overwrite committed historical reports during routine checks. Distinguish analytical checks, simulator runs, target compilation, physical bench evidence and physiological observations in every progress summary.

Hardware PR #1 and DX PR #2 were merged in order with merge commits. Audit #3 and child findings #4–#8 are implemented in merged PR #9; consult its final checks and `docs/ADVERSARIAL_REVIEW.md` rather than assuming a branch snapshot passed. Use Conventional Commits, uv-first commands, and merge commits without squash. `lab.recording` owns synthetic persistence/continuity, capture decoding streams into digest-bound artifacts, and `tools.check` owns verification. The existence of CI workflows is not proof that required-status branch protection is enabled. All hardware gates remain unchanged.

PRs #13 and #14 were merged into main, ending at `cdd901d5df8375e71eadefc99bdacc1056843410`; its post-merge Quality run `36134631550` passed. PR #13 addresses contradictory/mutable in-memory values; PR #14 preserves MCScap and reuse provenance. Issue #15 / PR #19 adds a separate generation-bound publication/reader contract in `docs/REV_A_RUN_IDENTITY.md`. Rejected/failed requests preserve historical success, but readers require the requested run ID and parameter set. Old flat report paths are not current evidence. Typed values and file digests still do not prove simulator authenticity, filesystem durability, model realism or hardware safety. Verify the latest PR/main state before continuing.

## Rev A passive input study (issue #10)

After the adversarial fixes in PR #9 were merged and main passed all three checks, the next addition was `lab.rev_a`, an explicit consumer of the public `hardware.rev_a` and `lab.analog` APIs. It does not change generic analog defaults, hardware JSON or firmware. Run it through uv and read `docs/REV_A_INPUT_STUDY.md`. The native quality gate includes its six real ngspice comparisons and keeps reports in the normal ignored evidence directory.

This closes the first executable selected-component/passive-input bridge, not the entire Rev A simulation plan. BIAS-loop stability, power/decoupling and input-fault analysis still need their own appropriate models; target-specific S3 compilation, schematic review and physical measurements are separate gates. Do not treat the illustrative ADC-node parasitics as a distributed cable model or the DC leakage sensitivity as qualified clamp protection.

## Bounded BIAS increment (2026-09-25)

PR #19 merged at `59cb94de2af9808b61a81d777e62a37538ac094a` after exact-head
Python 3.11/3.13/native checks passed in run `36165609993`. The first issue #17
BIAS increment is `lab.rev_a_bias`, PR #20: read `docs/REV_A_BIAS_STUDY.md`, its
TI source record and `docs/RESEARCH_APPLICATION_2026_09_25.md`. It reconstructs a
published summing topology, checks independent limiting cases and compares five
nominal dummy cases against actual ngspice. TI explicitly corrects the datasheet's
330k summing-resistor typo to 220k. Amplifier dynamics/contact/cable values remain
bounded assumptions; stress cases can be unstable. Linear steps are not power-up,
saturation/recovery or physical validation. No firmware BIAS is enabled. Keep #17
open for those remaining questions and verify PR #20's current exact-head checks.

## Independent BIAS step cross-check (PR #23)

Read `docs/REV_A_BIAS_TRANSIENT_VALIDATION.md`. The BIAS native study now adds
seven time-domain comparisons of dummy-common and amplifier-output voltages to
the existing 16 AC comparisons. Its transient reader shares the existing
ngspice subprocess boundary. Retained transient tables are uniformly interpolated,
not raw adaptive solver history. This is zero-state linear interference response,
not power-up, saturation/recovery or a physical safety gate. Verify PR status/CI
before assuming a development snapshot is merged.

## Continued BIAS work: linear transients and output-limiting hypothesis

PR #23 independently checks the linear BIAS time traces with actual ngspice;
read `docs/REV_A_BIAS_TRANSIENT_VALIDATION.md`. `lab.rev_a_bias_overload` adds
only a **one-pole output-state rail/slew projection hypothesis**, with preserved
feedback-capacitor charge and independent hybrid/native checks. Read
`docs/REV_A_BIAS_OVERLOAD.md` before describing it. The +/-2 V output deviations
are assumptions, not TI's INPUT common-mode range; typical 0.07 V/us is not a
guaranteed bound. There is no current limiter, internal recovery delay, PGA
clipping or supply startup. Unknown extra-pole nonlinear topology is rejected.
Disconnected BIAS can remain saturated throughout the reported 35 ms window.
All physical and human-use gates remain unchanged; issue #17 remains open.

## Resumed-session checkpoints

The failed-turn recovery retained merged PR #23 (independent linear BIAS transients) and PR #24 (bounded output rail/slew hypotheses). PR #27 merged the shared raw integration-window check and exact observation-grid checks, including the actual 25 ms integration / 35 ms interpolated-export false-positive regression. Read `docs/REV_A_BIAS_OVERLOAD.md`: these are unmeasured output-limit hypotheses, not ADS1299 recovery specifications.

The next compile-only increment is PR #28. `tools.check --firmware` requires the pinned Arduino CLI/core and creates a fresh, source/digest-bound target-build record. The dedicated Firmware workflow checks out the explicit PR head, unlike the normal integration checks that use GitHub's merge test checkout. Read the actual PR status before calling it merged or compiled. All hardware, wiring-review, purchasing and human-use gates remain false. PR #26 separately investigates TPS7A20 model compatibility; its retained failed probes are not regulator validation.

## Independent power shutdown controls (PR #33)

Read `docs/TPS7A20_COMPATIBILITY.md`. The optional pilot now uses four immutable
VIN/EN stimuli in the existing power module, report schema 2 and explicit
VIN/EN/VOUT columns; no new simulator runner or vendor patch was introduced.
Normalized-model EN deassertion fails near 0.895 V even with VIN held high;
supply-only collapse completes, without establishing physical output accuracy.
Five isolated four-pin comparator controls completed with the unmodified TI
library, so the comparator alone is not a reproduced failure. Investigate its
interaction with the full model or compare the same fixture in a reference
engine; do not treat a threshold correlation as proof of a comparator defect.
The 10 uF perturbation failed at startup, not at that falling threshold.

The six new software tests were observed failing before implementation in locked
CI; a separate native test uses only a synthetic algebraic wiring double. Actual
vendor results are optional retained investigations, never a normal online CI
dependency. PR #32's disposable workbench must close without merging. Check
PR #33's exact head, final review and CI before claiming it merged or validated.
Hardware, selected components, firmware guards and body-use gates are unchanged.

## Transient vector-identity candidate (2026-09-26)

Read `docs/TRANSIENT_VECTOR_IDENTITY.md` before accepting newly generated power
or BIAS evidence. The candidate adds exact named-vector contracts to the existing
shared reader and its three study consumers. Retained-output replay is not a new
simulation; local scoped tests are not a full locked gate. The original local
checkpoint was not pushed or merged. Verify the current GitHub state and require
fresh locked quality/native checks and review before adoption. This does not
repair or validate TPS7A20 shutdown and introduces no hardware approval.
