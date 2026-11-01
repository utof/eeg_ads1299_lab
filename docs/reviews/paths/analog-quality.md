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

None yet.

## Not yet covered

Everything. Start with: model parameters versus SBAS499C and the schematic
values; whether model outputs are compared to independent expected results.

## Log

(none)
