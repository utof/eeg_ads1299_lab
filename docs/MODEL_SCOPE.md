# Model scope and assumptions

This release uses multiple small models. It does not claim an electrically complete end-to-end simulation.

| Layer | Implemented | Not implemented or validated |
|---|---|---|
| Electrode/input circuit | Linear two-node AC nodal solution; resistor/parallel-capacitor contacts; input loading; differential/common-mode response; 200 tolerance trials | Nonlinear electrodes, input clamp leakage, Johnson noise, PCB parasitics, active bias loop, supply ripple, fault analysis or person safety |
| SPICE | Ordinary passive `.cir` exports; subprocess runner; numerical comparison code | ngspice execution in this environment; full ADS1299 macro-model |
| ADC | Signed 24-bit ideal quantizer, physical gain/rate choices, datasheet-based scale and nominal range/common-mode checks | A transistor/device model, actual analog noise spectrum, reference drift or calibrated physical board |
| Digital filtering | Nominal sinc³ frequency-response equation; reduced-rate three-box time-domain surrogate | Actual 1.024-MHz modulator bitstream, exact internal startup timing or full RF alias behavior |
| Synthetic recording | Randomized balanced labeled blocks; 10/6/20-Hz components; colored noise; residual differential line noise; DC offset; artifacts; clipping flags | Neural sources, skull volume conduction, real EEG authenticity, individual meditation response |
| Transport | Native ADS frame parsing; custom CRC packets; uint32 rollover; gaps, duplicates and ordering; real localhost UDP | Actual ESP32 timing, radio interference, losses on the user's network or SPI electrical validity |
| Analysis | Raw quality heuristics, independent 4-s windows, 1–40-Hz offline bandpass, Welch PSD, band powers, grouped classifier and block permutations | Comprehensive artifact removal, clinical interpretation, causal real-time filtering, real-data experiment ingestion or consciousness inference |

## Separation that matters

`lab/analog.py` and `lab/signals.py` are **separate exercises**. The passive network is not applied automatically to the synthetic data. The synthetic 50/60-Hz component is a residual differential signal, not a numerically solved mains-to-body coupling circuit. Metadata includes `analog_network_applied: false`.

A quarter-microvolt RMS additive ADC noise term is an **illustrative assumption**, not a conversion of the datasheet's peak-to-peak noise figure and not a guaranteed chip or board specification. Colored signal noise and artifact parameters are also choices made for teaching.

The generator uses a 16-times-output-rate internal time grid. Three length-16 moving averages approximate a sinc³ shape before downsampling. At 250 samples/s their delay is 5.625 ms, versus approximately 5.858 ms for the nominal chip sinc³ filter's group-delay expression. This small low-frequency approximation does not validate precise event latency.

Known simulated headroom violations are checked before clipping and propagated as rejection flags. Real capture files have no equivalent omniscient “true input was invalid” flag. A rail-code check cannot detect every analog saturation or common-mode problem.

## Why still use this?

Each layer answers a testable question at an appropriate scale. You can verify code scaling without a PCB; learn common-mode conversion without a brain model; and expose leakage mistakes before any recordings exist. This is a foundation for measurement, not a substitute for measured board behavior.

When the exact board becomes available, add its real values and measured responses, keep this release as a baseline, and explicitly revise these assumptions. Do not silently rename the surrogate “validated ADS1299 hardware.”
