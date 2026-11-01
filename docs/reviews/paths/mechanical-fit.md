---
id: mechanical-fit
code: MECH
title: Mechanical fit
status: never
stage: before-fab
reviewed_at: null
reviewed_on: null
scope:
  - hardware/rev_a/mechanical
  - docs/REV_A_CARRIER_K2.md
  - docs/REV_A_MECHANICAL_ENVELOPE.md
  - tests/test_carrier_cad.py
  - tests/test_carrier_l5.py
---

# Mechanical fit

## Covers

K2 carrier and coded captures, AUX/DevKit/HOST supports, board thickness,
header and ribbon fit, probe access envelopes.

## Findings

| ID | Status | Summary | Where (at 652193d) |
|---|---|---|---|
| MECH-01 | open (not critical) | 1.6 mm board bottom is hard-coded; the Russian fab candidate offers 1.5 mm for 4 layers. Parameterise thickness or confirm 0.1 mm is absorbed by shimming | `hardware/rev_a/mechanical/carrier_k2.scad:80-109,188` |

## Not yet covered

Everything beyond MECH-01 (noted in passing by the remaining-work audit).

## Log

(none; MECH-01 came from the 2026-11-01 remaining-work audit, not a path review)
