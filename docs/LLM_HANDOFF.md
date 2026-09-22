# Handoff for the next assistant or engineer

## User goal

An electronics beginner wants to learn EEG through runnable simulation and hands-on experiments, eventually studying perception, meditation and consciousness. They own an Arduino Uno, an unspecified ESP32, breadboards, basic components and >10 electrodes. Additional spending target: **$100**, not the $300 in the older uploaded reports. Electrode type, connectors, country-specific sourcing and exact MCU are not confirmed.

## What exists

Read `README.md`, `VALIDATION.json`, `docs/RESULTS.md` and `docs/MODEL_SCOPE.md`. Run the tests before modifying code. The sources, generated figures and machine-readable evidence are in this ZIP. The old uploaded AD8232/alternative-ADC reports are background only; their historical ZIP links are not dependencies.

The new package includes numerical passive-circuit analysis, unexecuted ngspice exports, a behavioral ADC, synthetic EEG-like sessions, quality/PSD/band-power analysis, a group-held-out toy classifier, custom binary transport and an actual localhost integration test. The simulator is not a physiological brain model.

## Hard boundaries to preserve

Do not claim ngspice ran here. Do not call the entire ESP32 sketch compiled or hardware-tested because native C++ helper tests passed. No ADC or ESP32 was physically connected. No body-use authorization is provided by this package.

Firmware is bench-only and defaults to `BOARD_PROFILE_REVIEWED = false`. It uses only internal test/short mux modes, with bias and lead-off excitation disabled. The GPIO table is for original ESP32/WROOM-32, not all ESP32 variants. `configs/board_profile.example.json` is a worksheet, not a live firmware configuration.

Do not provide invented power, reference, bias or electrode connections for an unidentified module. Do not “fix” saturation with only a digital high-pass filter. Do not call model resistor values safe patient protection. Battery/wireless operation is a precaution, not complete certification. Do not quietly switch to AD8232, ADS1115 or a different architecture without explaining the change.

## Next inputs required

Obtain the exact ADS1299 board listing, complete schematic, revision and clear header photos; the model printed on the user's ESP32; and the electrode connector/type. Use those to review compatibility and total landed cost before recommending a purchase. No documented complete under-$100 ADS1299 build has been verified.

## Productive next work

First repeat `python run_lab.py verify` and `python tools/run_loopback.py`. Install ngspice and run the strict circuit comparison, preserving logs. Build the full sketch against a pinned Arduino-ESP32 core for the exact supported target. Treat failures as evidence to fix, not as reasons to declare success.

Then check actual power/reference/clock and digital pins on the selected board. Complete internal test and internal-short recordings without anyone connected. Compare rate, framing, voltage scale and spectra. External dummy-input mode requires separate board-specific input/common-mode/protection review. A wearable stage needs a competent body-interface review; it is not the next register edit.

Keep raw counts, event metadata, transport gaps and quality exclusions. Any future real-data classifier needs an explicit importer/event/montage path and held-out sessions or days. Never describe synthetic 100% classification as demonstrated brain decoding. For meditation comparisons, hold eye condition constant and record subjective observations separately.

## Change discipline

Make one substantial change at a time; add a regression test; retain the original failing output when useful; update the model-scope and validation reports. Distinguish analytical checks, simulator runs, target compilation, physical bench evidence and physiological observations in every progress summary.
