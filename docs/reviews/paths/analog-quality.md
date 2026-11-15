---
id: analog-quality
code: ANALOG
title: Analog signal quality
status: never
stage: later
reviewed_at: null
reviewed_on: null
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

| ID | Status | Summary | Where (at 79d0c9f) |
|---|---|---|---|
| ANALOG-01 | suspected (decide before fab) | AVDD comes from the 5 V bus shared with the ESP32-S3 DevKit through only a 10 ohm RC feed, with no local analog regulator; radio/MCU load steps can reach AVDD. PiEEG-8 (below) instead uses dedicated low-noise LDOs (LT3042 +2.5 V, LM2662 + LT3094 -2.5 V) from a battery. Adopting a local analog LDO is a component change (reviewed change); not needed for internal-test-only first power | `docs/REV_A_SUPPLY_STUDY.md`; `hardware/rev_a/bom.json` line item `analog_feed`; `hardware/rev_a/board_profile.json` |

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
VCAP1 100 uF. Differences: 8 channels, Raspberry Pi host, battery-only, bipolar
+-2.5 V rails from LT3042/LT3094/LM2662, 3.2 V DVDD (LT3042), one 2-layer board
65 x 56 mm, no isolation, no published BOM, no independent noise measurement.

## Not yet covered

Everything. Start with: model parameters versus SBAS499C and the schematic
values; whether model outputs are compared to independent expected results.

## Log

- 2026-11-15: Opus review of goals A (defects vs SBAS499C, model values vs
  schematic) and B (PiEEG-8 comparison, adopt/skip verdicts) started at
  79d0c9f (first Fable attempt hit the usage limit). If no later entry
  exists, the run was lost: re-run with the brief template plus the PiEEG
  section above.
