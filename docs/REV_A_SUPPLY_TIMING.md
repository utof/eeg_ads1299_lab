# Explicit supply timing and source-tolerance coverage

**2026-09-27.** This continues PR #54 without changing its circuit or promoting
its demonstration timing to a hardware requirement. The source and load events,
integration stop and observation interval are now explicit in the existing
`lab.rev_a_supply` API, command and retained reports. The old defaults, five
cases, conductances, ideal capacitor, rail limits and comparison tolerance stay
unchanged. No capacitor substitution, BOM/CAD/firmware change or approval follows.

## Why this matters before a capacitor decision

The previous inverse correctly answered the question encoded by its fixed
4..20 ms observation interval. That interval was a study fixture, **not** the
ADS1299 reset or supply-settling requirement. A 100 uF effective AVDD capacitor
could fail at 4 ms because it had not charged sufficiently, even when the later
pulse and recovery would meet the same voltage limits. Conversely, observing
only after a pulse can hide an actual modeled voltage failure during the pulse.
Neither choosing more capacitance nor moving the observation window is an
engineering fix without a justified operating requirement.

The supplied external research explicitly left burst duration and edge rate
unmeasured. Espressif's module data characterize specified RF modes and test
conditions; they do not supply the actual user's DevKit/source/cable waveform.
The existing conductance pulse therefore remains an **unmeasured hypothesis**,
not a calibrated radio trace. This change makes its time assumptions inspectable;
it does not replace missing measurements with a new arbitrary "real" envelope.

## One immutable schedule, used by every calculation

`SupplyTiming` contains the following quantities in **seconds**:

| Field | Preserved default | Meaning |
|---|---:|---|
| `source_on_s` | 0.001 | Ideal source turn-on, from an uncharged capacitor |
| `burst_on_s` | 0.008 | Added upstream MCU conductance begins |
| `burst_off_s` | 0.012 | That added conductance ends |
| `stop_s` | 0.020 | Native integration and available response horizon |
| `observation_s` | (0.004, 0.020) | Closed interval whose rail limits must hold |

Events must be finite, nonnegative and strictly ordered. Each physical phase
must be long enough for the existing native 1 ns edge to be representable and
finish before the next event. Observation must have positive duration, begin
strictly after ideal source-on and end no later than the integration stop. It
may be before, during, across or after the pulse. These checks are numerical
and experiment consistency rules, not minimum physical timing specifications.
A representable schedule can still fail the existing bounded native execution,
resolution or comparison checks; such failures are retained, not waived.

Changing **only observation** does not change the source/load netlist or the
voltage trajectory. It changes the question asked of that same trajectory.
`rail_response`, `supply_netlist`, `source_voltage_window` and
`run_supply_study` all accept the same keyword-only `timing` object. Omitting it
preserves existing calls and calculations. No new solver, runner or dependency.

```python
from dataclasses import replace
from lab.rev_a_supply import SupplyCase, SupplyTiming, source_voltage_window

case = replace(SupplyCase(), capacitance_f=100e-6)
timing = SupplyTiming(observation_s=(0.006, 0.020))
required_min, allowed_max = source_voltage_window(case, (4.75, 5.25), timing=timing)
```

## Exact reduction to event/window endpoints

Within each phase the circuit has one first-order state:

`v(t) = v_final + (v_initial - v_final) * exp(-(t - phase_start) / tau)`.

It is monotonic within that phase and continuous at the ideal load events.
Consequently its minimum and maximum on a closed observation interval occur
at its two endpoints or at a load event **inside** it. The inverse now uses
exactly that set. Excluded earlier events do not constrain the observation,
but their effect on capacitor state is still propagated; the state is never
reinitialized when observation begins. A dense grid is only a test oracle,
not the algorithm used to find extrema.

Linearity in the constant source amplitude is unchanged. For unit-source
extrema `a_min` and `a_max`, the required interval is still
`[rail_min / a_min, rail_max / a_max]`. Lower greater than upper means **empty**;
never sort it. The forward case's `source_v` is still ignored by the inverse.

## Separate three conclusions in the report

The existing `model_margin_ok` tests the forward trace at the case's source
setting (the baseline's low source endpoint). `model_source_window_feasible`
means that **some** constant source amplitude could satisfy the model.

The new `model_source_range_covered` instead requires the calculated interval
to contain the **whole** baseline source range. With the unchanged baseline,
that is 4.95..5.05 V. Both endpoints must fit, not merely intersect the allowed
interval or pass at 4.95 V. The top-level `configured_source_range_v`, `timing`
and `margin_window_s` record the actual question. Existing per-case fields and
native execution/comparison status remain separate.

This coverage concerns the configured constant-source-amplitude family within
this ideal model. It is not a measurement of source regulation, current limit,
transient behavior or actual supply tolerance. It also is not a proof for a
continuous range of unexamined load, resistance, capacitance or timing values.
All physical and body-use flags remain false regardless of any model pass.

## Reproducible native experiment, not a changed startup policy

The command remains the existing entry point. CLI timing values are in
**milliseconds** and are converted once to the API's seconds:

```sh
uv run --locked python -m lab.rev_a_supply --out reports/timing-example \
  --source-on-ms 2 --burst-on-ms 11 --burst-off-ms 19 --stop-ms 30 \
  --observe-ms 7 28
```

It runs the same five cases, preserves a fresh run directory and records the
specified schedule. The native PWL sources, true integration-stop expectation,
phase-observation checks, analytical comparison and inverse all use it. Invalid
CLI timing is rejected before creating a run. Missing native tools or an
incomplete/wrong trajectory remain failures, not analytical-only successes.
The ordinary `tools.check --native` still runs the unchanged default study.

### Conditional results from the same old conductance hypothesis

Here C is **total effective AVDD capacitance**, not one part's nominal value.
Source turns on at 1 ms, the pulse is 8..12 ms and integration ends at 20 ms.
Rail limits are 4.75..5.25 V; the source range is 4.95..5.05 V.

| Shared R | Effective C | Observation | Required source minimum | Whole source range covered? |
|---|---:|---|---:|---|
| 0.1 ohm | 10 uF | 4..20 ms | 4.894400 V | Yes |
| 0.1 ohm | 100 uF | 4..20 ms | 5.102062 V | No |
| 0.1 ohm | 100 uF | 6..20 ms | 4.893787 V | Yes |
| 0.5 ohm | 100 uF | 6..20 ms | 5.088036 V | No |
| 0.5 ohm | 100 uF | 14..20 ms | 4.924454 V | Yes, but the pulse was excluded |

The last row is a diagnostic counterexample, **not** an acceptable qualification
shortcut: it discards the very activity that caused the earlier failure.
Changing observation does not repair the circuit. Likewise the third row does
not authorize a 6 ms firmware wait, adding a 100 uF part, or raising the source.
Real startup depends on actual rail/clock/VCAP behavior and the existing guarded
firmware procedure. It is not inferred from this one-capacitor experiment.

## Test evidence and preservation

Tests begin with the missing public timing API. Independent unloaded-RC cases
exercise observation endpoints; dense traces exercise intervals before, inside,
across and after the pulse. A case with acceptable-looking window endpoints but
a lower internal pulse voltage requires the internal event to be considered.
Thirty deterministic property examples translate the schedule and scale both
time and capacitance, preserving the response. Distinct checks protect frozen
values, invalid numeric/order/window requests and query-range enforcement.

Actual ngspice cases use nondefault source-on, pulse and stop times and check
both inverse boundaries before/during/after the pulse against the unreduced
two-node circuit. An actual CLI run checks that the requested schedule and full
source-band coverage reach the fresh study report. A software-only publication
fault shows that feasible-window/low-endpoint success must not be confused with
coverage of the high source endpoint. Doubles are not counted as native runs.

A pre-edit replay retained default traces, netlists and inverse outputs for
three representative cases. They remain byte-for-byte/numerically identical
under the default schedule after the change. Existing fixed-case numerical
checks remain in place; no expected historical result was refreshed.

## Next physical evidence, without expanding scope

Use `GRM21BR61C106KE15L` only as the already-documented qualification target.
Current assembly/termination/process approval, actual effective capacitance,
ESR/ESL and delivered sourcing remain open. Before a component-change PR,
state the intended source/load/timing envelope and observe the corresponding
hardware, including the *whole* activity interval that must meet the rail limits.
Keep the two AVDD bulk parts distinct from VIN/DVDD/VCAP/reference capacitors.
No BOM, footprint, firmware, circuit topology or approval flag changes here.

Sources and prior evidence: `REV_A_SOURCE_VOLTAGE_WINDOW.md`,
`REV_A_BULK_CAPACITOR_ASSESSMENT.md`, `REV_A_STARTUP_SEQUENCE.md`, and the current
`hardware/rev_a/board_profile.json`. TI ADS1299 electrical limits and startup:
https://www.ti.com/lit/ds/symlink/ads1299.pdf
Espressif module RF-mode/test-condition information (not a DevKit burst trace):
https://documentation.espressif.com/esp32-s3-wroom-1_wroom-1u_datasheet_en.html

## Independent review correction: initial observation versus early turn-on

The first candidate retained the old absolute 10 ns allowance for the first
observed sample. With an explicitly earlier source event, that could accept a
trace starting after source-on and its finite edge. Two process-double regressions
reproduced this false completeness claim before correction; five controls
preserved earlier/at-event samples and the historical bound. These doubles
isolate completeness and are not actual simulations.

The first observed sample must now be no later than the smaller of 10 ns and
source-on. A source starting at zero therefore requires a zero-time sample.
This preserves the default near-zero rule while binding it to the requested
schedule. Two real ngspice study controls, at source-on zero and 2 ns, still
pass with their initial samples intact. No event, trajectory, model parameter
or physical startup policy was changed to make those controls pass.


## Hosted-engine correction: no repeated zero-time source vertex

The first strict initial-observation correction passed the local ngspice 44.2
runs but failed the actual ngspice 42 CI zero-time-source case. The retained
per-case diagnostics showed NaN node voltages during initialization, zero
transient rows and a warning about non-increasing PWL times. The source exporter
had emitted the origin twice when source-on was zero: `(0, 0), (0, 0), ...`.
Local 44.2 accepted that input with the same warning; that did not establish
portable validity. No artifact was treated as a successful run after failure.

A separate structural regression failed for the repeated timestamp while the
early/default controls passed. The exporter now emits that origin only once
when source-on is zero. All positive-source-on netlists, including the historical
defaults, are byte-unchanged. Source amplitude, ramp duration, ideal trajectory
and the stricter first-sample requirement are unchanged. The native zero/early
cases remain required; no exception, invented sample or larger tolerance hides
the failure. This is a correction to our generated input, not a vendor model
patch, a solver upgrade, or proof of a general ngspice defect. The test now prints
retained per-case failures and bounded log tails because CI does not upload
pytest's temporary directory.
