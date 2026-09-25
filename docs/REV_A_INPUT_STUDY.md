# Rev A passive input-network study

Tracking: issue #10 and PR #11. This is the first executable connection between the locked Rev A component contract and the existing analog simulator. It is intentionally one focused module, `lab.rev_a`, composing public APIs rather than adding board branches to the solver or a simulation framework.

## Run and inspect

Install/synchronize the uv environment described in the README, from the repository root:

```bash
uv sync --locked --all-extras
uv run --locked python -m lab.rev_a --out reports/rev_a_input
uv run --locked python -m lab.rev_a --require-ngspice --out reports/rev_a_input_native
uv run --locked python -m lab.rev_a --leakage-bound-na 2 --out reports/rev_a_input_2na
uv run --locked python -m tools.check --native
```

The first study command needs no simulator; its report explicitly says `not_requested`. `--require-ngspice` must execute and compare all six native cases or fail. The shared native gate also runs the study and retains its JSON, CSVs, netlists and simulator logs under `reports/check/rev_a_input/` for the normal CI artifact upload.

`runs/<run-id>/study.json` is the immutable-by-writer report for one generation.
`current.json` is published last and points to its digest-bound manifest. Use the
caller-known identity with `read_study`; current means last successful run, not last
attempt. See `docs/REV_A_RUN_IDENTITY.md` for the failure/reader contract.

The report records exact model parameters, canonical document digest, selected part numbers, nominal metrics, 24 tolerance-corner results (eight per scenario), simulator comparison errors, and limitations. Each scenario has a `response.csv` with frequency and real/imaginary differential/common transfer. Each drive has a self-contained `network.cir`; requested native runs also produce fresh `ac.txt` and `ngspice.log`. The terminal prints a compact summary rather than repeating every corner.

A failed new attempt preserves earlier generations without satisfying a new requested run identity. Analytic-only runs have their own directories and cannot inherit old simulator outputs. The current pointer is replaced only after the whole generation is complete. Same-root writers are explicitly excluded; different output roots remain independent. Committed historical `results/` remain untouched. This supersedes the flat-marker invalidation policy used in the dated PR #11 evidence below.

## Selected facts versus assumptions

The public hardware validator must accept the unchanged profile, BOM and sources before any model is built. Series resistance **4,990 ohms per leg**, differential capacitance **4.7 nF**, resistor tolerance **1%**, capacitor tolerance **5%**, and the selected part numbers come from `hardware/rev_a/board_profile.json` and `bom.json`. The snapshot digest hashes sorted-key JSON `[profile, BOM, sources]`; it is not represented as a hash of raw file bytes. No fitted common-mode capacitor or clamp is added to the baseline.

The source/electrode impedances and input loading below are **illustrative numerical assumptions**, not measurements or qualified ADS1299 input specifications:

| Scenario | Source resistance P / N | Source parallel capacitance P / N | ADC-node shunt capacitance P / N | Input load per leg |
|---|---|---|---|---|
| Ideal-source limit | 1 mOhm / 1 mOhm | 0 / 0 | 0 / 0 | 1 TOhm |
| Balanced | 10 kOhm / 10 kOhm | 100 nF / 100 nF | 100 pF / 100 pF | 1 GOhm |
| Impedance mismatch | 5 kOhm / 50 kOhm | 100 nF / 100 nF | 100 pF / 200 pF | 1 GOhm |

The nonzero shunt values represent assumed **ADC input-node parasitics**, not fitted capacitors or a claim that all real cable capacitance is located there. Upstream lead capacitance, distributed cable behavior, shielding and capacitive mains coupling require a different explicit topology.

## Independent checks and interpretation

For ideal zero-impedance sources and infinite input loading, the differential network has

```text
H(f) = 1 / (1 + j*2*pi*f*(Rp + Rn)*Cd)
fc = 1 / (2*pi*(Rp + Rn)*Cd) = approximately 3393.06 Hz
```

That is an analytic reference, not a measured bandwidth or the ADS digital filter response. The near-ideal finite-resistance model is tested against the reference. A second independent half-circuit equation checks a finite, purely resistive balanced source/load case. Symmetric common-mode excitation should cancel at the differential output; mismatch converts part of it into differential voltage. The reported common-mode transfer is V/V: multiply by an assumed common-mode amplitude to obtain differential amplitude.

Each scenario evaluates every combination of Rp at +/-1%, Rn at +/-1%, and Cd at +/-5%. These **eight deterministic corners are not a statistical distribution or proof of global extrema**: nonmonotone metrics may have interior extrema. The report preserves each corner instead of labelling an unproved global worst case. The six independent ngspice comparisons cover the three nominal scenarios with differential and common-mode drives; tolerance corners are evaluated by the numerical solver, not misrepresented as 24 additional native runs.

The optional leakage value is a **hypothetical independent DC current bound per input**, default 1 nA. With capacitors open at DC and independent opposite-sign currents, the differential bound is

```text
Ibound * (((RsourceP + RseriesP) || RinputP)
        + ((RsourceN + RseriesN) || RinputN))
```

The report uses amperes and volts internally; `--leakage-bound-na` takes nanoamperes. This sensitivity calculation does not fit or qualify BAV199 devices. Clamps stay DNP; there is no transient/ESD/fault-protection claim.

## Recorded execution, 2026-09-24

Concrete source commit `199065f84a42261cabce583d5f1c10a57247caeb` passed the complete locked Python 3.13 native gate in [run 35936794602](https://github.com/utof/eeg_ads1299_lab/actions/runs/35936794602). [The retained artifact](https://github.com/utof/eeg_ads1299_lab/actions/runs/35936794602/artifacts/10782439677) contains 54 evidence files, including the new study, numerical/native logs, coverage and localhost capture results.

| Check | Observed result |
|---|---|
| Ruff formatting and lint | Pass |
| Strict Pyrefly, including warnings | 0 diagnostics |
| complexipy | No function above 15 |
| Tach / unchanged static hardware baseline | Pass |
| Software tests | 222 passed; 5 subtests passed |
| Native/integration tests | 4 passed |
| Actual branch coverage | 331/442 = 74.89%; unchanged floor 71% |
| Rev A ngspice comparisons | All six executed and compared |
| Maximum absolute complex-transfer disagreement | 2.442502e-15 V/V |
| Existing localhost UDP replay | 2,248 accepted packets; two intentional omissions detected |

Before the final freshness fix, three regression cases reproduced stale success markers for negative, NaN and infinite leakage inputs. The same cases pass after the correction. This evidence is tied to the source commit above; final PR-triggered Python 3.11/3.13/native jobs are separate checks linked on PR #11. The longer-term 90% branch-coverage target is not achieved.

The run produced an ideal-source reference pole of **3393.06150795 Hz**. Nominal numerical metrics for the explicit illustrative assumptions above, with a hypothetical 1 nA per-input leakage bound, were:

| Scenario | Differential gain at 10 Hz (V/V) | Common-to-differential at 50 Hz (V/V) | At 60 Hz (V/V) | Hypothetical DC bound (microvolts) |
|---|---|---|---|---|
| Ideal-source limit | 0.9999956521 | 1.11e-16 | 1.11e-16 | 9.980002 |
| Balanced | 0.9995718646 | 1.24e-16 | 2.22e-16 | 29.979551 |
| Impedance mismatch | 0.9954639154 | 0.0016055888 | 0.0016671884 | 64.976876 |

The balanced residuals are numerical roundoff, not a physical common-mode rejection measurement. Agreement between two implementations of the same passive circuit supports numerical consistency, not the realism of every assumed component or parasitic.

## What remains outside the model

There is no ADS1299 silicon/PGA loading model, digital decimation, BIAS-loop stability, power supply/decoupling, PCB extraction, ESD, fault-current, target-firmware build or physical measurement here. The model cannot authorize purchasing, board manufacture or body connection. All original hardware safety gates remain false.

The next modeling work should address BIAS-loop and power integrity with their own justified models, then reconcile results with a reviewed schematic. Do not expand this passive transfer solver with unrelated safety or firmware conditionals.
