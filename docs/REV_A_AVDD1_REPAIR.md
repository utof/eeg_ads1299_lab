# AVDD1 local bypass repair: native draft, not electrical qualification

PR #62 follows the geometry finding in `REV_A_POWER_RETURN_REVIEW.md`.
Before source: `1e86c049c46b52b3f1889f6bef7941763f965f79`.
First published repair/test head: `a19bfc4514d7923aba33e8ee5c1d0009e3c5e931`.
Board after SHA256: `611218bae6559fb2488309fc80eee20ce2d6b5855977d52d600f947099179b43`.
Read the live PR for final exact-head CI/review and merge state. This document
and its geometry record do not certify a later edit.

## What changed

C16 (1 uF) and C27 (100 nF) now sit immediately above U1's AVDD1/AVSS1
pin pair. U1.54 reaches both positive pads on front copper; U1.53 reaches
both negative pads on front copper. Shared AVDD feed and GND plane entry
are beyond the capacitor cluster, not a substitute for these local paths.
C9, C24 and C14 also move to make room. All five remain front-side; no
part is under U1. No ferrite, split ground, new part or schematic net is added.

Native comparison of all 68 footprints and 245 pads found identical field
texts, values, footprint IDs, attributes/layers and relative pad definitions
(including net, drill, size, shape, pin function/type and orientation). Only
those five footprint positions/orientations change. The other 63 footprint
forms remain byte-identical. No signal tracks are added to In1. The board
now has 581 segments and 121 vias; new vias retain 0.60/0.30 mm geometry.
BOM, schematic, firmware, models, dependencies and approval flags are unchanged.

## Measured geometry and tradeoffs

Lengths below are specified trace-centre itineraries, not the shortest
conductive distance, pad spreading, via-barrel length, loop inductance, or
noise measurements. The JSON record lists the exact after-route UUIDs; the
previous review retains its before-route portions. Do not compare the old
9.325 mm GND-plane-entry separation with a new trace length as if they were
the same metric.

| Path | Before trace mm / vias | After trace mm / vias |
|---|---:|---:|
| U1.54 to C16.1 | 11.936 / 2 | 2.617 / 0 |
| U1.54 to C27.1 | 11.036 / 2 | 4.217 / 0 |
| U1.53 to C16.2 | Via/plane-dependent, no direct front path | 3.726 / 0 |
| U1.53 to C27.2 | Via/plane-dependent, no direct front path | 5.326 / 0 |
| U1.55 to C9.1, VCAP3 | 2.533 / 0 | 2.816 / 0 |
| U1.55 to C24.1, VCAP3 HF | 4.033 / 0 | 6.016 / 0 |
| U1.56 to designated C14.1 | 1.913 / 0 | 6.713 / 0 |
| U1.56 to shared C15.1 | Not tabulated here | 3.663 / 0 |

**Not every neighboring path improved.** C9 remains near its pin and both
VCAP3 paths stay front-only, but C24's path is about 1.98 mm longer. C14's
path is substantially longer; the nearer shared C15 path is explicitly an
alternative, not a changed capacitor ContractRef. U1.59's existing C15 path
and the DVDD C18 route are unchanged. Retain these tradeoffs in whole-board
supply/noise review; this repair does not establish their physical performance.

The pre-repair VCAP3 figures were summed from the original front-route
portions: U1.55 (48.75,31.3375) through its native bends to the C9 pad centre
(50,29.425), then the extra 1.5 mm to C24 (51.5,29.425). Both source boards
remain in Git. Use the explicit after UUIDs in the companion JSON to audit
these numbers rather than treating a printed rounded number as a constraint.

## Tests before repair, then connected-but-wrong faults

Test-only `cb11bb7a` produced four intended native failures for missing local
AVDD1 positive/return paths; both VCAP3 guards passed. `b2e11969` repairs copper.
Test-only `470ba37d` then exposed two accepted early plane joins despite intact
local paths. `a19bfc45` fixes that guard using native KiCad item types: connectivity
returns vias as generic track proxies, so Python isinstance is not sufficient.

Eleven added native cases passed locally: six bounded front-path checks, two
indirect reconnections, two additional upstream plane joins, and one benign
track subdivision/reversal. Each fault copy is freshly refilled and checked.
The four harmful controls still have zero ordinary DRC/parity/airwires; the
local guard rejects them. A globally connected supply is therefore not accepted
as evidence that the required local bypass connection remains present.

The test limits are project geometric guardrails chosen before repair, not TI
maximum-length or noise specifications. Native whole-contacted-item distance
can vary with subdivision near a pad; the benign control tests acceptance and
terminal identity, not an artificial invariant floating-point length. The
pre-bypass walk stops at capacitor-contacting track items, checking their vias
and foreign pads too. It is not exhaustive for arbitrary overlapping or long
boundary tracks. Such future geometry still requires direct review.

The canonical board and native fault tests remain in `tests/test_pcb_placement.py`.
The authored board keeps its fresh zone last so the existing removed-cache test
does not accidentally discard later tracks. No rule/severity/exclusion/threshold
was relaxed. Reproduce with the existing pinned environment:

```sh
uv sync --locked --all-extras
uv run --locked python -m tools.check --native --schematic
```

## Recovery and evidence boundary

The preceding failed turn left working tool artifacts but an incomplete source
transfer, not a recoverable published repair. This continuation recovered the
published main source and native tools from GitHub, reproduced the failures,
and published its four actual commits. Transfer run36622822760 verified the
14,068-byte Git bundle and a separate fresh GitHub checkout. Transfer code and
runtime binaries are not project dependencies and are not in the product tree.

An initial full local gate stopped because the transported ngspice runtime
lacked its stock initialization file. The exact distribution spinit was restored
outside project source; no model or expected result was edited to hide it.
Use the PR's final execution report for completed gate counts and outcomes.

Primary basis: TI ADS1299 SBAS499C, pp6,70,72, and Brian Pisani's TI E2E reply
recommend local AVDD1/AVSS1 bypass before the planes/pours, while recognizing
layout tradeoffs require performance judgment. Neither source gives the test's
millimetre limits or approves this board.
- https://www.ti.com/lit/ds/symlink/ads1299.pdf
- https://e2e.ti.com/support/data-converters-group/data-converters/f/data-converters-forum/462184/ads1299-98-does-avdd1-avss1-really-produce-significant-noise

Next: digital reference/layer-transition review on the live authored board,
then input P/N geometry/coupling. Keep #45/#48 open, including whole-board
supply tradeoffs, stackup, mechanics/assembly, component lifecycle/effective C,
and actual console/interface rail-loss behavior. No fabrication, purchasing,
power-up or body-use authorization; native CAD and source review are not
physical experiments or independent professional electrical qualification.
