# Build and verification notes

## Initial implementation

Created the ADC model, passive circuit solver/exporter, synthetic signals, grouped analysis, custom transport, bench starter and tests. First regression run: **55 passed**. Log: `results/initial_tests.log`.

## Expanded checks and inspection

Added six/eight-channel and 500-SPS pipeline checks, a no-effect negative control, gap-safe capture inspection, and bench-gate regression checks. Improved the sketch's error halt to assert PWDN: keeping START low alone does not cancel command-started conversion.

The first expanded run had **one test failure and 62 passes**. The failing assertion was an overly literal whitespace-sensitive check of the existing `BOARD_PROFILE_REVIEWED = false` declaration, not an enabled hardware gate. The assertion was corrected to ignore spaces. The next expanded run passed all **63 tests**. Both logs are retained.

## End-to-end execution

Ran the default and null-control pipelines. An initial notebook-triggered run encountered output-directory permissions; permissions were corrected and the complete demo and figures were regenerated successfully. A notebook subprocess startup hook also emitted an unrelated spreadsheet-runtime warning; direct execution of the lab avoided that hook. These environment incidents are not presented as EEG-model validation.

Ran a real localhost receiver/replay/decode/inspection exercise. Sent a nine-second synthetic schedule with two deliberately missing sample sequences; received 2,248 valid packets and identified both gaps. No physical microcontroller or ADC was used.

## External tools

ngspice and the ESP32 target build toolchain were absent. Installation attempts did not succeed in this environment. The package retains explicit unexecuted statuses and strict commands that fail rather than silently treating those checks as passed.

The final test counts and tool statuses are in `VALIDATION.json`; later tests may increase the count beyond the intermediate logs above.
