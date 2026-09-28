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

Normal CI exercises handwritten switch fixtures, software rejection contracts
and a deliberately synthetic algebraic VIN/EN wiring double. The double is not
a regulator model or evidence of TI behavior. The vendor startup/shutdown experiment remains an explicit optional
pilot, not a dependency or required online-download gate. No noise/PSRR, current
limit, startup sequencing, delivered board voltage or safety qualification is
claimed. The control experiments below narrow the next reference-engine or
full-model interaction investigation; they do not repair shutdown.

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

## Independent shutdown controls (PR #33)

The optional vendor pilot now runs four fixed cases. VIN and EN share the same
0 -> 5 V startup at 1..1.01 ms. A falling input drops 5 -> 0 V at 15..15.01 ms;
the observation window remains 20 ms and the load step is unchanged.

| Case | VIN after 15.01 ms | EN after 15.01 ms |
|---|---:|---:|
| `startup_load` | 5 V | 5 V |
| `shutdown` | 0 V | 0 V |
| `enable_only` | 5 V | 0 V |
| `supply_only` | 0 V | 5 V |

Report schema **2** names every case, distinguishes `supply_collapse_requested`
from `enable_deassertion_requested`, and declares voltage columns
`[vin_v, enable_v, vout_v]`. Vendor `transient.txt` contains time followed by those
three voltages; schema 1 contained time, VIN and VOUT. A rejected case cannot
suppress its peers. Shutdown completion still checks execution, NOT output-decay
accuracy. These are diagnostic stimuli, not recommended physical sequencing.

Architecture: an immutable private stimulus value and one pure netlist generator
in `lab.rev_a_power` describe the fixed matrix. Existing archive validation,
private-library lifetime, shared analog process/trace reader and report publisher
remain the only owners of their jobs. No new module, process wrapper, dependency,
configurable experiment framework, hardware contract or simulator tolerance was
needed. Six new software regressions failed first against unchanged source in
[run 36203692580](https://github.com/utof/eeg_ads1299_lab/actions/runs/36203692580),
while the existing 500 tests and five subtests passed. The separate marked native
test checks wiring with a continuous algebraic double, not TI physics.

### Observations, including the hypothesis that did not reproduce

These investigations used Ubuntu's ngspice 42 in `psa` mode. The optional library
normalization was unchanged; reference-engine and physical comparisons were
**not** performed. The disposable workbench in PR #32 is not a production
workflow and must not be merged.

[Run 36203097578](https://github.com/utof/eeg_ads1299_lab/actions/runs/36203097578)
repeated both original and normalized baselines. With the normalized full model,
supply collapse while EN stays at 5 V completed 20 ms. EN deassertion at fixed
5 V VIN failed at about 15.00821 ms. Deasserting EN before a later supply collapse
failed at the same point. The completed supply-only trace reached about -43.8 mV
at its minimum; completion is not evidence that this undershoot is physically
accurate or acceptable. Four independent handwritten switch-plus-RC controls
completed; the inverse-switch wrong-state behavior remained visible.

[Run 36203367552](https://github.com/utof/eeg_ads1299_lab/actions/runs/36203367552)
varied one factor at a time. Falling ramps of 1, 10 and 100 us, and a 10 us ramp
moved before the load step, stopped with the last diagnostic EN sample near
**0.895 V**. This is an observed model/simulator boundary, not a device threshold
specification. Removing the external output capacitor, reducing it to 1 nF,
adding 0.1 or 1 ohm series resistance, and using trapezoidal instead of Gear
integration did not remove that falling-edge failure. The 10 uF test failed
**earlier at startup**, so it is not evidence for the falling-edge conclusion.
Partial traces remain rejected, even when their last values are diagnostically
useful. None of these perturbations changes the maintained 1 uF fixture.

The model's enable comparator reference and hysteresis inputs were observed at
0.92 V and 0.025 V in the full-model operating-point log. The helper interface is
`COMPHYS_BASIC_GEN INP INM HYS OUT`. Testing it in isolation using the **unmodified**,
hash-locked library in
[run 36204226480](https://github.com/utof/eeg_ads1299_lab/actions/runs/36204226480)
completed all five cases: the as-used values, rise-only, zero hysteresis, shifted
reference and smaller hysteresis. Its isolated rising/falling output reached the
expected logic endpoints. The comparator alone is therefore **not a reproduced
failure** under these controls. A preliminary metadata-only run found no selected
three-pin helper and ran no probes; an earlier ASCII-header decoding error also
ran no probes. Neither was counted as a successful electrical test.

**Next investigation:** reduce the full-model interaction around enable
shutdown, or compare this same fixture in the vendor's reference engine. Do not
replace the comparator or smooth its equations merely because the full model
fails at its falling transition. The inverse-switch endpoint mismatch and
full-model shutdown failure are still separate, unresolved compatibility limits.

### Retained evidence and exact reproduction

The disposable PR history retains the complete handwritten experiment
scripts. Retrieve each `tps7a20-disposable-workbench` artifact while available;
GitHub retention is finite. The downloadable archives were independently checked
against their GitHub digests and every manifest-listed file:

| Run | Artifact ZIP SHA-256 | Manifest files checked |
|---|---|---:|
| `36203097578` | `772ff7ceae29a1444adca0b73fa5b6099411bc9615c3168ba89408959f232e03` | 126 |
| `36203367552` | `c136d83e10bfeae3eaea739c31146b42dd0d7a49797a62f13c867153e36b3a08` | 53 |
| `36204226480` | `931a6cb4c749593711179826859afdee4557fb86f9cc91c58b1fd298547dfde7` | 27 |

The source commits are respectively `a95520455e94caccfd73e19f282daf3e2c004df6`,
`07a6e3c7b6f3413f0a45ab5643438758c3e183fb` and
`35d6301fb376553f05534c10a3680daa9c23ebcb`. The five-case helper script creates
only external sources, a load and an instance of the library's published
subcircuit interface; it does not retain the helper implementation. Reproduce
with the same hash-locked caller-supplied TI archive and initialization, rather
than treating an expired artifact URL or a plotted image as evidence.
