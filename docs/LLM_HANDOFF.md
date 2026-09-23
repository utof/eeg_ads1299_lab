# Handoff for the next assistant or engineer

## User goal

An electronics beginner wants to learn EEG through runnable simulation and hands-on experiments, eventually studying perception, meditation and consciousness. They own an Arduino Uno, an unspecified ESP32, breadboards, basic components and >10 electrodes. Additional spending target: **$100**, not the $300 in the older uploaded reports. Their existing ESP32 model, electrode type/connectors, and country-specific sourcing still need confirmation before physical work.

## Current hardware decision

Rev A selects a four-channel `ADS1299-4PAGR` daughterboard plus `ESP32-S3-DevKitC-1-N8R8`, internal ADS reference/clock, 5-V unipolar analog bench power, ADC-only `TPS7A2033PDBVR` DVDD regulation, and a 4.99 kΩ / 4.7 nF differential input network. Read `docs/HARDWARE_BASELINE_REV_A.md` and `hardware/rev_a/`. Do not reopen component selection for DX or simulation work. All hardware-review, purchase, firmware-port, schematic-release and human-connection gates remain false.

## Development workflow

Read `AGENTS.md` and `docs/DEVELOPMENT.md` before editing. The pinned project and development environment is installed with `uv sync --locked --all-extras`. Run `uv run --locked python -m tools.check` before and after changes. Install ngspice, Node, and a native C++ compiler to run `uv run --locked python -m tools.check --native`. Missing required tools must fail, not become a native-validation pass.

The shared check command enforces Ruff formatting/lint, strict Pyrefly (including warning-level diagnostics), cognitive complexity at most 15, Tach dependency/interface boundaries, the static hardware contract, unified pytest discovery, and actual branch coverage. New behavioral work and bug fixes start with a focused failing test; existing numerical behavior gets characterization tests before refactoring. Do not lower gates, add blanket suppressions, or refresh expected numerical results just to make checks pass.

`lab.analog` is now a package facade with `_model`, `_solver`, `_spice`, and `_report` internals. Preserve public imports such as `from lab.analog import InputNetwork, transfer`. Use the `hardware.rev_a` facade for hardware-contract functions. Cross-component imports go through public interfaces; internal modules must not import back through their own facade. Keep `__all__` and `tach.toml` aligned. Validate external data at entry points; array dtype annotations do not establish shape, units, or finiteness.

## What exists and what was verified

Read `README.md`, `docs/DX_VALIDATION.md`, `docs/RESULTS.md`, `VALIDATION.json`, and `docs/MODEL_SCOPE.md`. The latter historical results and validation file describe the original environment and are not silently overwritten by the new CI. Current quality logs and reports are generated under ignored `reports/` and uploaded as CI artifacts. `requirements-tested.txt` is historical; `pyproject.toml` and `uv.lock` define the current environment.

The package includes numerical passive-circuit analysis, ngspice exports/comparisons, a behavioral ADC, synthetic EEG-like sessions, quality/PSD/band-power analysis, a group-held-out toy classifier, custom binary transport, and actual localhost integration tests. The simulator is not a physiological brain model.

Unlike the original environment, the dated DX CI run in `docs/DX_VALIDATION.md` actually executed ngspice against the existing educational circuits and passed native C++ helper and localhost transport checks. Cite that specific run and scope. Do not imply that the next Rev A input-network model, BIAS loop, power circuit, or an ADS1299 silicon macromodel was thereby simulated.

## Hard boundaries to preserve

Do not call the entire ESP32 sketch compiled or hardware-tested because native C++ helper tests passed. No physical ADS1299 or ESP32 test was performed by the DX workflow. No body-use authorization is provided by this package.

Firmware remains bench-only and defaults to `BOARD_PROFILE_REVIEWED = false`. It uses only internal test/short mux modes, with bias and lead-off excitation disabled. Its current GPIO table is for original ESP32/WROOM-32, not the selected S3 or all ESP32 variants. `configs/board_profile.example.json` is a worksheet, not a live firmware configuration. The S3 port is separate work.

Do not provide invented power, reference, bias or electrode connections for an unidentified module. Do not fix saturation with only a digital high-pass filter. Do not call model resistor values safe patient protection. Battery/wireless operation is a precaution, not complete certification. Do not switch to AD8232, ADS1115 or a different architecture as a tooling change.

## Productive next work

After reviewing the DX change, implement the Rev A differential input network as its own feature commit. Preserve the current educational circuit as a regression fixture. Add explicit electrode/source impedance, P/N mismatch, resistor/capacitor tolerances, cable capacitance, 50/60-Hz common-mode excitation, bounded clamp leakage, an independent ideal-pole comparison, and numerical regression tests. Keep analytical checks and actual simulator results distinct.

Subsequent work is BIAS-loop simulation, power simulation, the exact four-channel schematic/ERC and independent footprint/polarity review, then the explicit ESP32-S3 firmware profile/compile tests with existing guards preserved. PCB/layout and an actual delivered build quote follow those gates. The planning subtotal is not a verified complete delivered under-$100 build.

Before physical work, obtain the exact board schematic/revision and header photographs, verify the actual MCU and electrode connectors, and review power/reference/clock/digital compatibility. Complete internal-test/internal-short bench recordings without anyone connected. External dummy inputs require their own board-specific input/common-mode/protection review; a wearable stage requires a competent body-interface review.

Keep raw counts, event metadata, transport gaps and quality exclusions. Any future real-data classifier needs an explicit importer/event/montage path and held-out sessions or days. Never describe synthetic 100% classification as demonstrated brain decoding. For meditation comparisons, hold eye condition constant and record subjective observations separately.

## Change discipline and review

Make one substantial change at a time; add a regression test; retain useful failing evidence. Do not overwrite committed historical reports during routine checks. Distinguish analytical checks, simulator runs, target compilation, physical bench evidence and physiological observations in every progress summary.

Hardware PR #1 and the DX review are separate. Until #1 is merged, review the DX branch against `hardware/rev-a-component-baseline`; retarget it to `main` afterward. Do not merge or change hardware gates without explicit authorization. The existence of CI workflows is not proof that required-status branch-protection settings are enabled.
