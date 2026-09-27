# Bulk qualification: exact orderable identity and inverse rail requirements

## Decision and new evidence

The next qualification target has a documented full designation:
**GRM21BR61C106KE15L**, not an invented `D` suffix carried over from the old part.
Murata's Product Search Data Sheet [1], mirrored by Farnell and dated 2023-03-19,
lists `L` (180 mm embossed-tape reel, 3,000 pieces) and `K` (330 mm, 10,000).
Those are manufacturer full-reel quantities, not a minimum prototype order or a
promise that a distributor will supply a particular cut-tape quantity.

Its drawing/table distinguish external terminal length **e = 0.2..0.7 mm** from
the gap between terminals **g >= 0.7 mm**. Body length is 2.0 +/- 0.1 mm;
width and height are each 1.25 +/- 0.1 mm. These are component dimensions, not
PCB copper dimensions. Do not turn the minimum gap into a land recommendation
or combine all independent extremes as if the drawing promised every combination.

The four-page manufacturer-authored mirror was downloaded, hashed and pages 1/2
rendered and visually checked. Its own warning says typical specifications only,
possibly out of date, and requires product/approval-sheet confirmation before
ordering. It is identity/geometry evidence, **not current assembly approval**.
The September 2026 core lifecycle/typical data in PR #52 remains separately dated;
this older sheet does not overwrite it. The factual addendum is
`references/murata_20260927/bulk_orderable_addendum.json`.

The old manufacturer reference URL [2] returned HTTP 404. The web parser had
older reference text, but its reflow table could not be visually verified, and
the attempted mirror returned non-PDF content. No reflow-land values from that
partial text were adopted. The retailer's linked 2015 PCN [3] concerns a factory
addition, not end-of-life; the exact target was not in its extracted MPN list.
A link labelled PCN does not close the lifecycle/approval question by itself.
The read-only capture run therefore has a retained **failure** with two useful
PDFs, not a falsely green all-sources retrieval. Its temporary PR #53 must never
merge. Stock/price snippets were inconsistent; no delivered quote is claimed.

The current BOM still contains the old 10 uF part. No package, land, capacitor,
rail, firmware or hardware/purchasing/body-use approval has been changed.

## What electrical requirement are we trying to satisfy?

The existing `lab.rev_a_supply` study answers a forward question: given a source,
shared resistance, conductance loads and effective AVDD capacitance, what voltage
appears on AVDD? The new `source_voltage_window(case, limits_v)` in that same
module answers the inverse: **which constant source amplitudes keep AVDD inside
the requested voltage limits throughout the study's existing 4..20 ms window?**

There is no new solver, model family, runner or network dependency. It reuses the
existing piecewise RC calculation. The source still turns on at 1 ms, the extra
upstream load starts at 8 ms and stops at 12 ms. The excluded startup interval
is the old fixture choice, not an ADS1299 reset time or a physically qualified
startup specification. Existing historical case inputs/results are not rewritten.

For this *linear conductance-load, ideal-capacitor hypothesis*, write
`V_AVDD(t) = V_source * f(t)`, where `f` is the response to a 1 V source. Within
each fixed-load phase the first-order response is monotonic. Therefore its exact
continuous-time extrema in the window occur among 4, 8, 12 and 20 ms. Let these
be `f_min` and `f_max`, and let the required rail limits be `L` and `H`:

```text
required source minimum = L / f_min
allowed source maximum  = H / f_max
```

The function returns that pair. **Lower > upper means no feasible source** in
this hypothesis; sorting the pair would manufacture a false solution. A source
range `[Vs_low, Vs_high]` meets the entire modeled window only if it is contained
in the returned interval. Positive finite ordered rail limits are required;
unrepresentable calculations fail instead of publishing infinity. `case.source_v`
is deliberately ignored by the inverse calculation, which normalizes to 1 V.

Both forward margin and inverse window use one shared extremum helper, avoiding
divergent sampling/window rules. Each existing five-case `study.json` now includes
`model_source_window_v` and `model_source_window_feasible`. The latter means that
*some* constant source amplitude could meet the modeled rail limits, not that the
selected 5 V supply range fits, and certainly not hardware approval. Existing
execution/comparison/margin flags retain their meanings. These are additive
report fields, with no new latest-success pointer or changed evidence runner.

## Quantitative consequences under the unchanged hypotheses

The following calculations use the existing 10 ohm feed, analog conductance
0.002 S, idle upstream conductance 0.02 S and **additional** burst 0.08 S. Required
AVDD is 4.75..5.25 V. Compare the result against the existing source tolerance
range **4.95..5.05 V**; this is not advice to raise a supply above that range.

| Shared R | Effective AVDD C | Required source min | Allowed source max | Entire 4.95..5.05 V range fits? |
|---:|---:|---:|---:|---|
| 0 ohm | 10 uF | 4.845000 V | 5.355000 V | Yes, in this model |
| 0.1 ohm | 10 uF | 4.894400 V | 5.366760 V | Yes, in this model |
| 0.1 ohm | 100 uF | 5.102062 V | 5.366773 V | No |
| 0.5 ohm | 10 uF | 5.092000 V | 5.413800 V | No |
| 0.5 ohm | 100 uF | 5.177884 V | 5.413884 V | No |
| 1 ohm | 10 uF | 5.339000 V | 5.472600 V | No |

For the 0.1-ohm hypothesis, individual 5/10/20 uF sensitivity cases all fit the
source range; the 100 uF case fails the 4 ms lower-rail requirement because it
charges more slowly. These discrete cases are **not** a guaranteed capacitance
range for an actual part. Likewise, when source resistance causes a settled
voltage loss, more capacitance cannot remove that loss. Under an unloaded,
1,000 uF / 10 ohm control, the required lower source exceeds the allowed upper
source: early charging and later upper-rail limits cannot both be met.

This sharpens the next measurement/qualification question: establish the actual
source impedance, load waveform, effective capacitance and required observation
interval, rather than select a larger nominal capacitor and assume the issue is
solved. Only two of the four bulk parts are on AVDD; do not sum the VIN/DVDD or
VCAP/reference capacitors into this lumped C. The new inverse is **not** a DVDD
regulator-stability check, nor a whole-board model. Constant-current/power loads,
ESR/ESL, supply control loops, temperature, aging and real startup are still absent.

No typical manufacturer plot has become a guaranteed minimum or calibrated
model parameter. The full orderable target and the conditional source requirement
are advances toward qualification, not a synchronized BOM/CAD substitution yet.

## Verification and use

```python
from lab.rev_a_supply import SupplyCase, source_voltage_window

lo, hi = source_voltage_window(SupplyCase(), (4.75, 5.25))
fits_selected_source_range = lo <= 4.95 and 5.05 <= hi
# Model calculation only. Do not enable hardware from this Boolean.
```

Run the unchanged entry point to retain the new metrics with the existing study:

```sh
uv run --locked python -m tools.check --native --schematic
```

The new API first produced the intended missing-import failure. The packaging
record had four observed missing-record failures. A separate pre-change replay
also demonstrated that the old native study lacked the new report fields.
Tests cover an independently derived unloaded RC solution, two-node DC KCL,
empty windows, source normalization, invalid numeric/limit inputs and 40
deterministic property examples against dense queries plus event endpoints.

Four native boundary cases execute eight unreduced two-node ngspice runs: at
each computed lower/upper boundary and 20 mV outward. A boundary must agree
within 100 uV; the outward source must violate its corresponding rail limit.
The original forward-study native checks still run. Software-record checks are
not counted as native execution, and native agreement is not physical accuracy.

## Remaining concrete decisions

Obtain the applicable current approval/termination/assembly information for the
now-identified `L` part and confirm actual height/process constraints. Establish
node-specific effective-C/impedance requirements over the intended environment,
using the real source/load/timing envelope rather than this demonstration fixture.
Then make the separately reviewed BOM/CAD change and verify delivered sourcing.
The planned-stop 1 uF and 100 nF roles remain distinct follow-through. Issues #45
and #48 stay open; no layout/fabrication or body-use release is implied.

[1] Murata, Product Search Data Sheet GRM21BR61C106KE15#, updated 2023-03-19;
manufacturer-authored copy hosted by Farnell, pages 1/2 visually checked.
https://www.farnell.com/datasheets/3929902.pdf

[2] Historical Murata reference URL, parsed text dated 2016-03-07; direct PDF
returned 404 in this session. Reflow-table visual verification did not complete.
https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM21BR61C106KE15-01.pdf

[3] Murata HEMCG2-2560, 2015-11-05, factory-addition notice; not a target-specific
current approval or discontinuation notice.
https://www.farnell.com/datasheets/2006461.pdf
