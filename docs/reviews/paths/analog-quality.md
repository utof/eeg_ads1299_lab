---
id: analog-quality
code: ANALOG
title: Analog signal quality
status: partial
stage: later
reviewed_at: 01b8965
reviewed_on: 2026-11-15
scope:
  - lab/analog
  - lab/rev_a_bias.py
  - lab/rev_a_bias_overload.py
  - lab/rev_a.py
  - lab/signals.py
  - lab/dsp.py
  - hardware/rev_a/kicad/rev_a.kicad_sch
  - docs/REV_A_INPUT_STUDY.md
  - docs/REV_A_BIAS_STUDY.md
  - docs/REV_A_BIAS_DYNAMICS.md
  - docs/REV_A_P3_REFERENCE_REVIEW.md
---

# Analog signal quality

## Covers

Electrode input network (series R, C0G filters), BIAS drive and overload
behavior, reference/VCAP nodes, and whether the SPICE/analytic models in
`lab/analog` and `lab/rev_a_bias*.py` match datasheets and the schematic.
`stage: later` because the first pilot is internal-test-only; input-network
errors matter for external-signal characterization, not first power.

## Findings

| ID | Status | Summary | Where (at 01b8965) |
|---|---|---|---|
| ANALOG-01 | rejected as a PCB change; check at bring-up | Suspicion: AVDD shares the ESP32 5 V bus through a 10 ohm RC with no local regulator (PiEEG uses LT3042/LT3094). Review: ADS1299 PSRR ~96 dB (SBAS499C p.9) turns 1 mV ripple into ~0.016 uV, far below the 0.14 uVrms floor; a 5 V-to-5 V LDO cannot fix bus droop; PiEEG also takes 5 V from its host. Instead, at bring-up compare input-shorted noise with the ESP32 idle versus streaming | `hardware/rev_a/bom.json` `analog_feed`; `docs/REV_A_SUPPLY_STUDY.md` |
| ANALOG-02 | open, confirmed (later; before BIAS is enabled) | BIAS loop margin is thin with all 8 inputs sensed (model 18.8 deg; unstable with 10 Mohm contacts) and no BIAS_SENS selection is specified anywhere (no hit in firmware/lab/docs). Re-run of the repo model: 8 inputs 18.8, 4 -> 27.2, 2 -> 39.2, 1 -> 56.9 deg; 4.7 nF feedback only reaches 24 deg. Fix in firmware, not hardware: require <= 2 sense inputs (TI SBAA188 uses 2) and re-run the study for that count | `lab/rev_a_bias.py:222,250`; `docs/REV_A_BIAS_STUDY.md:153-156`; SBAS499C Fig 38 p.33 |
| ANALOG-03 | info | Generic `InputNetwork()` defaults (10 kohm / 1 nF / 100 pF to ground) are not Rev A values; they feed `circuit_report` and the pipeline plot, labelled "illustrative". Risk: misread as the Rev A response | `lab/analog/_model.py:17-23`; `lab/analog/_report.py:40`; `lab/pipeline.py:78`; `tests/test_rev_a_study.py:29-30` |
| ANALOG-04 | info | SRB1 has no pad or connector, so SRB1 common-reference mode is unavailable; referential montage still works by wiring the reference lead to all CHxN on the harness. No change | `hardware/rev_a/kicad/rev_a.kicad_sch` |
| ANALOG-05 | info (decide before a body-use revision) | No footprints for small RF caps to ground at the inputs; TI suggests them only for strong RF (p.68) | input network, `rev_a.kicad_sch` |
| ANALOG-06 | suspected (later, low) | VCAP1 tantalum leakage flows through the internal ~9.8 kohm and may shift the 4.5 V reference slightly (<1 %, irrelevant for EEG). Confirm by reading VREFP and VCAP1 at first power | SBAS499C Fig 25 p.24 |

Checked correct against SBAS499C (mirror, rev Jan 2017, sha256 `5855849f...`):
all 64 pins and unused-pin rules; per-pin 1 uF AVDD/AVDD1/DVDD decoupling;
VREFP 22 uF (>= 10 uF min even at -10 %); VCAP1-4 values and tantalum
polarity; BIAS 1 Mohm || 1.5 nF C0G plus 1 Mohm output R (<= 5 uA into the
body); BIASREF/BIASIN, SRB2, RESV1, DAISY_IN, GPIO, CLK/CLKSEL straps; input
filter 2 x 4.99 kohm + 4.7 nF C0G differential (corner 3.39 kHz, ~-50 dB at
fMOD), resistor noise ~0.10 uVrms vs chip 0.14 uVrms (total +24 %); AVDD feed
drop ~41 mV typ. Model values chain schematic -> BOM -> profile -> models;
outputs are checked against independent hand equations, TI SBAA188 and
ngspice (`tests/test_rev_a_bias.py`: 29 passed). No comparison with measured
data yet.

## Reference design: PiEEG-8 (2021 revision)

Open-source ADS1299 board for Raspberry Pi, GPL v3 (copying from it makes the
copied part GPL). Board files were deleted upstream on 2023-09-12 but remain in
git history; the user has a recovered copy in
`~/Downloads/EEG project files.zip` (`PiEEG-8 recovered board files/`:
schematic PDF, Gerbers, licence). Recover independently with:

```bash
git clone https://github.com/pieeg-club/EEGwithRaspberryPI
git show "4147845^:electrical_scheme/electrical scheme PIEEG.pdf" > pieeg8_schematic.pdf
```

Same TI reference core as ours: 5 kohm + 4.7 nF inputs, BIAS 1 Mohm || 1.5 nF,
VCAP1 100 uF. Differences: 8 channels, Raspberry Pi host (its 5 V comes from
the Pi header, J1.2), bipolar rails from LT3042/LT3094/LM2662, 3.3 V DVDD
(LT3042), input caps returned to SRB1 (TI Fig 73 referential), BIAS output
5 kohm, one 2-layer board 65 x 56 mm, no isolation, no published BOM, no
independent noise measurement.

**Verdict 2026-11-15: adopt nothing before fab.** Low-noise LDOs, split
supply, LT3042 DVDD and caps-to-SRB1 give no measurable EEG benefit for our
design at high cost. Its 5 kohm BIAS output resistor is rejected for safety
(up to ~1 mA DC into the body if BIAS saturates; ours limits to <= 5 uA).
Battery-powered host (no mains ground path) is recommended later, before any
body use, as a setup choice rather than a PCB change.

**Do not copy (schematic as drawn):**
1. U4 LT3094 R4 = 33.2 kohm gives -3.32 V, not -2.5 V: analog span 5.81 V
   exceeds the 5.5 V absolute maximum and AVSS is beyond -3 V vs DGND
   (SBAS499C p.7; LT3094 front-page example uses 33.2 kohm for -3.3 V).
   Orchestrator re-read R4/R2/R3 on the rendered schematic.
2. C30/C31 (+2.5 V bypass) bottom ends join only each other: AVDD has no
   real local bypass; no 1 uF per AVDD pin; other bypasses return to GND.
3. BIAS output only 5 kohm (above).
4. RESET/PWDN pulled up to the +2.49 V analog rail while DVDD is 3.32 V:
   below the 0.8 x DVDD logic-high minimum (p.10), and rise at power-up.
5. START floats; CLK goes to a single-use net label (floats).
6. GPIO1-3 shorted together to GND through 1 kohm (datasheet asks >= 10 kohm).
7. Suspected: 10 uF reference cap exactly at the minimum; DC-bias derating if
   ceramic.

## Not yet covered

Everything. Start with: model parameters versus SBAS499C and the schematic
values; whether model outputs are compared to independent expected results.

## Log

- 2026-11-15, 01b8965 (scope identical to 79d0c9f), one Opus review (a
  Fable attempt hit the usage limit). No critical defect. Rejected the
  orchestrator's ANALOG-01 supply suspicion; found ANALOG-02 (BIAS sense
  count); PiEEG verdicts and errors above. Orchestrator confirmed no
  BIAS_SENS hit and the 18.84 deg figure in the bias study.
  Not covered: PCB layout/placement (AVDD1 star, returns),
  `lab/rev_a_bias_overload.py` internals, `lab/dsp.py`, ngspice runs, PiEEG
  Gerbers and charge-pump detail, any measurement.
