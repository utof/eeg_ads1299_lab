# Bounded BIAS rail/slew experiment

This experiment extends the already native-checked **linear** circuit. It asks
what happens under one explicitly assumed output-limiting rule; it does not
identify the ADS1299's internal overload mechanism. No hardware values, firmware
modes, selected parts, dependencies or body-use gates change.

## Source boundary

[TI SBAS499C](https://www.ti.com/lit/ds/symlink/ads1299.pdf), printed page 9,
section 7.5, gives **typical** BIAS slew 0.07 V/us and gain bandwidth 100 kHz
at 50 kohm || 10 pF, gain one. The 1.1 mA short-circuit current is also typical
and is **not** used as a current-limit/protection model. The AVSS+0.3 to
AVDD-0.3 entry is the amplifier's **input** common-mode range, not its output
swing. This table does not establish output saturation or overload-recovery time.
The exact distinctions and assumptions are in
`docs/references/ti/bias/overload_sources.json`.

The default output deviations of -2 to +2 V about a nominal 2.5 V midpoint
are **assumed**, not manufacturer bounds. A separate 100 V/s case deliberately
slows the output to test sensitivity; it is not a measured ADS1299 value or a
plausibility bound. Contact/capacitance values retain the existing unmeasured
electrical-dummy interpretation. They are not fitted MCScap/scalp parameters.

## Mathematical contract

The one-pole linear amplifier asks for

`d(out)/dt = -(2*pi*GBW/A0) * (out + A0*vm)`.

The hypothesis clips that requested slope to +/-slew and blocks only outward
motion at the assumed output rails. The output is released when its requested
slope points inward. **No additional recovery delay is invented.** This says
nothing about internal-node wind-up or actual transistor recovery. An optional
extra pole is explicitly rejected here because its nonlinear internal saturation
topology is unknown, rather than arbitrarily clipping multiple hidden states.

The feedback capacitor stores `Cf*(vm-out)`. When the output slope changes,
the summing-node slope must change by the same amount. This preserves the
capacitor's KCL and its stored charge. Clipping a completed linear trace would
not do so. Existing passive-node matrices and SPICE resistor/capacitor topology
have one owner in `lab.rev_a_bias`; only the amplifier law is replaced.

Python uses event-located hard-rail transitions and stiff Radau integration.
A separate ngspice behavioral-current integrator runs over the same passive
circuit. Seven cases include a small pulse, positive/negative overload,
asymmetric/open input, disconnected BIAS, and deliberately slow slew.
Each starts with zero capacitor voltages; this is **not supply startup**.
The input pulse rises from 0 at 1 ms to its requested current at 1.001 ms,
then falls between 6 and 6.001 ms. The observed window ends at 35 ms.

## Execution and numerical checks

```bash
uv run --locked python -m lab.rev_a_bias_overload --require-ngspice
uv run --locked python -m tools.check --native
```

Runs use unique, never-reused directories. The manifest is published last,
binds every output file, and is absent after a failed comparison. Source
records, model/lock hashes, package/tool versions, all twelve Python circuit
states, ngspice netlist/log/three voltage traces, explicit parameter values and
rail-event times are retained. The existing bounded ngspice process/trace
reader is reused; there is no second simulation runner. An exit code of zero
is insufficient: the requested time window and voltages must also pass.

Independent checks include a piecewise-linear-input matrix exponential in the
small-signal limit, positive/negative symmetry, output-slope bounds, an
integrated resistor-current/feedback-charge KCL check through saturation,
and native timestep refinement. Invalid values, sparse observation grids,
duplicate run IDs and failed native publication have explicit regressions.

Native tables are interpolated on a 2 us observation grid; integration uses
Gear, maximum step 100 ns, relative tolerance 1e-9. Coarser/looser exploratory
runs exceeded the original comparison criterion; tightening numerical
integration, not fitting the circuit or relaxing the criterion, corrected this.
All native samples are compared with rtol 2e-4 and atol 1 nV for the 1 nA pulse,
100 uV for the large-pulse cases. Native rail excursion is bounded to 100 uV
as a **numerical** tolerance. A separate balanced-case regression requires
both 100 ns and 50 ns runs to agree with the hybrid solution within 2 uV.
These numerical tolerances are not claims of physical hardware accuracy.

## Observed model behavior and remaining work

In the nominal balanced 5 uA pulse experiment the output hits the assumed -2 V
rail at about **1.2152 ms**, and releases at about **7.0154 ms**, after the pulse
has completely ended. The negative pulse gives the opposite signs. The
asymmetric/open-input cases are also modeled; with the BIAS path disconnected,
the output has **not** released by 35 ms. Neither a final value nor a finite
trace is labeled proof of global recovery or stability.

These are results of the stated projection hypothesis, not measured chip
recovery. Input/PGA clipping and output current limiting are absent, so large
node excursions are not literal predictions of real ADS1299 voltages. The
next physical constraints need source/measurement-backed output swing, overload
and load behavior. No firmware BIAS/lead-off/external-input enablement, purchase,
protection, schematic-release or human-connection approval follows.

## Independent-review corrections

The first Codex review found four numerical/evidence edge cases, reproduced by
focused regressions before correction. Native comparison now requires all
17,501 points of the declared 2 us grid, including interior spacing, rather
than merely accepting matching endpoints. Solver-reported events at pulse
segment boundaries are recorded before returning. Rail snaps shift both output
and summing voltage by the same correction, preserving `vm-out` charge.

Both rail deviations must be at least 1 mV from zero: a numerical supported-input
restriction relative to the 1e-10 V solver absolute tolerance, not a hardware
specification. Mode selection uses exact rail inequalities rather than a fixed
proximity band. Smaller rail hypotheses require a separately justified numerical
scale/tolerance contract; they are rejected instead of silently approximated.

A subsequent native regression shortened only the real integration to 25 ms,
leaving the interpolation request at 35 ms. ngspice padded the exported grid,
and the old check incorrectly accepted it. The exporter now records the actual
native stop before interpolation; the caller clears stale completion evidence
and verifies this stop independently of grid/voltage checks. The native
regression must reject that padded trace without publishing a manifest.
