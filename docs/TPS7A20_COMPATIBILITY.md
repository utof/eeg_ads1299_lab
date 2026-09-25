# TPS7A20: a compatibility pilot, not a validated power circuit

The recovered disposable PR #25 had successfully *recorded* probe results, but
its requested trajectories had not completed. Some ngspice exits were zero even
though integration stopped early. The first fixture also demanded constant load
current before the output had powered up. Neither is a power-model pass.

`lab.rev_a_power` now makes the experiment reproducible through the existing
`lab.analog.run_ngspice_transient` boundary. It retains rejected probes and has
no `power_model_validated: true` outcome. A completed investigation is not a
successful regulator validation. Hardware, BOM, firmware and all false safety
gates remain unchanged. No dependency or second simulator process wrapper is added.

## Source and terms

TI's [SBVM961 archive](https://www.ti.com/lit/zip/sbvm961) contains the configurable
`tps7a20-adj_trans.lib`, Final 1.00, 21JAN2020, for PSpice 17.2-2016 S050.
Read `docs/references/ti/tps7a20/source_record.json` for exact raw hashes and pins.
The archive references an absent `SCHEMATIC1.net` plus Cadence libraries; this
work does not claim to reproduce the complete vendor reference fixture.
No affirmative redistribution grant was established. **Neither the original
nor adapted library is committed or included in our report artifacts.** The
caller supplies the exact archive; the code checks its SHA-256 before reading
or optionally modifying the library. No unverified vendor download happens in
normal CI. The explicit optional edit creates only a temporary private copy.

## Concrete failure isolated

On the exercised ngspice 42 build with `ngbehavior=psa`, a six-element handwritten
resistive-divider fixture isolates inverse `VSWITCH` behavior. With source 3.3 V,
load 1100 ohm, and specified low resistance 1 microohm, the expected output is
approximately 3.3 V. For `Roff=1e-6 Ron=1e6 Voff=0 Von=1m` at zero control, the
observed output is **0.003626 V** instead. The usual ordering works. This is a
local observed compatibility failure, not a claim about every ngspice release.

A separate original-macro-model DC investigation found an internal regulated
node near 3.30027 V but its external output near 0.003622 V. This supported
investigating the output switch rather than changing the regulator's setpoint.
The tiny reproducer contains no vendor implementation and is retained in every
pilot. The independent expected result is the resistor-divider equation.

## Explicit experimental edit and its limits

The optional `--normalize-switch` flag exchanges **both** resistance labels and
control-voltage endpoint labels in exactly one known `_S2` declaration. It does
not silently patch the source or claim an unmodified-vendor pass. Original and
executed library hashes and `library_edited` are recorded separately.

Endpoint tests then agree within a declared 10 microvolt numerical tolerance.
The finite low-resistance output differs by about 3 microvolts, consistent with
a simulator resistance floor; no continuous interpolation or PSpice parity has
been proven. Do not generalize the replacement to other models without tests.
The [upstream manual](https://ngspice.sourceforge.io/docs/ngspice-manual.pdf)
documents PSpice translation modes and its switch models; an endpoint match is
not proof that the entire macro-model shares Cadence's behavior.

The corrected startup fixture uses conductance loading: nominal 3 -> 10 -> 3 mA
at 3.3 V, but zero current at zero output. Both capacitors are an explicitly
assumed 1 uF. With the exact experimental library hash recorded in the source
record, the ngspice 42 startup/load probe completes **20 ms**, with plateaus near
**3.300048 V, 3.299540 V, 3.300050 V**. These are model outputs, not device accuracy
measurements. Its **shutdown trajectory still stops at about 15.00821 ms** and
is rejected. Unmodified startup and shutdown probes stop near **1.00184 ms**.
The supplied fixed windows and 2% plateau sanity threshold prevent those traces
from looking like completed regulation tests. That 2% is not a TI specification.

## Reproduce

```bash
# Only our handwritten switch fixtures; no vendor artifact needed.
uv run --locked python -m lab.rev_a_power

# Supply the exact SBVM961 ZIP from TI. No modification by default.
uv run --locked python -m lab.rev_a_power --vendor-archive /path/to/sbvm961.zip

# Explicit experiment, NOT qualified model adoption.
uv run --locked python -m lab.rev_a_power --vendor-archive /path/to/sbvm961.zip --normalize-switch
```

Read `pilot.json`, not just the command exit code. Exit zero means the requested
investigation was recorded, including failed/rejected probes. Each invocation
owns a new UUID directory. Digests bind visible logs, netlists, original source
record, initialization bytes, source/lock hashes and result tables. `spiceinit.txt`
records the exact bytes used as `.spiceinit`; restore that name for a manual run.
Vendor netlists contain a now-deleted temporary include path: reconstruct the
private library using the pinned archive/explicit edit before rerunning them.
The library itself is deliberately not an output artifact.

Normal CI exercises only the handwritten native fixture and software rejection
contracts. The vendor startup/shutdown experiment remains an explicit optional
pilot, not a dependency or required online-download gate. No noise/PSRR, current
limit, startup sequencing, delivered board voltage or safety qualification is
claimed. Next work is a reference-engine comparison or a justified compatibility
fix for shutdown, then a separate actual selected-board power study.

## Rejected switch-window semantics

The independent review identified that the original switch report collapsed an
incomplete integration and a completed endpoint mismatch into the same false
boolean. Each switch result now records `window_complete`, `last_time_s` and
`outcome`. An incomplete window has `outcome: rejected` and
`compatible_endpoint: null`, with a reason. Its observed voltage is diagnostic
partial output, not a completed compatibility measurement. Only a completed
10 us window can produce a true or false endpoint comparison. The voltage
threshold and all existing complete-case numerical behavior are unchanged.

The test-only `0bcc5f12` adds public-report regressions for complete/incomplete
cases. A separate local isolated-function check exercised all four combinations
of completed/incomplete and matching/mismatching endpoints before and after
the correction. That isolated check is software evidence, not a rerun of the
optional vendor model. Consult the final PR checks for integrated test evidence.
