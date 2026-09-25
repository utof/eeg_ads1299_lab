# Independent BIAS transient validation (PR #23)

The earlier BIAS studies compared complex frequency-domain responses with
ngspice, but their step traces came only from Python matrix exponentials.
This increment checks the **time-domain implementation independently** before
adding any nonlinear overload behavior. It does not change the stated circuit.

## Experiment and reference

A 1 nA step is applied to the electrical dummy-common node. All capacitor
voltages start at zero relative to the local analog midpoint. This is a
zero-state interference experiment, **not supply power-up or a person test**.
`uic` prevents ngspice from initializing at the final DC operating point.

The existing full 12/13-state descriptor provides the independent solution
`x(t) = x_inf - exp(A*t)*x_inf`. Public `step_voltages` returns dummy-common
and amplifier-output volts; `step_response` retains its previous common-only API.
No differential-transfer, component or amplifier parameter was changed.

Seven stable configurations are checked: balanced, asymmetric, open input,
open BIAS, and the three existing extra-pole cases. The unstable high-impedance
stress case still has **no settling trace**. Existing 16 AC comparisons remain.

The generic `run_ngspice_transient` API shares the original bounded ngspice
subprocess implementation. It requires fresh output, finite real columns and
strictly increasing nonnegative times, retains timeout/error logs, and rejects
missing, stale, malformed, one-row or nonfinite tables. It does not itself
certify circuit correctness or that a requested time window was completed.

## Numerical controls and retained data

The generated BIAS transient uses trapezoidal integration, a 1 ns suggested
initial increment and a **200 ns maximum internal step**, over 0–100 ms.
Only common/output vectors are saved. ngspice `linearize` exports a uniform
**2 us interpolated observation grid**, limiting retained table size. That
50,001-row table is not the raw adaptive integration history. The netlist and
log preserve the integration/export instructions.

The completion gate compares selected early-time and whole-window rows against
matrix exponentials with fixed `rtol=1e-4`, `atol=1e-9 V`. It retains maximum
absolute errors, point counts and tolerances in `native_step_comparison`.
A successful comparison is not a claim about every unobserved instant.

Initial 2 us/Gear experiments failed these same tolerances, especially with the
slow extra pole. Refining the integration and initial increment corrected the
numerical disagreement without fitting the circuit or loosening acceptance.
A native regression additionally halves the maximum step to 100 ns for the
100 Hz extra-pole case, requires reduced error against the analytical trace,
and repeats the original accuracy check. A separate 1 kohm / 1 uF RC fixture
checks the process/reader path against `1-exp(-t/1 ms)` at a 1 mA input step.

The ngspice manual describes `.TRAN`/`uic`, transient integration options and
`linearize` in sections 11.3.10, 11.1.4 and 13.5.45:
https://ngspice.sourceforge.io/docs/ngspice-manual.pdf . The actual authoring
checks executed ngspice 42; compatibility was tested, not inferred from the
current manual alone.

## Failure and history evidence

Test-only commit `443fa40190728c1ea7ef184df7001a50b7f731b4` in PR #23 requires
an executable step export. It fails against the previous `loop|closed` exporter;
CI run `36172743628` retains that missing-feature evidence. This is not a claim
that the previous AC solver contained a numerical defect.

Software-only fixtures deliberately inject disagreement, late-start and
truncated-time traces. They cannot publish a completion manifest and never
claim native execution. Real native tests and the full study run are separate.
The final exact-head quality/native CI, not this description, is merge evidence.

Current complete study output has 16 AC netlists and seven step netlists;
seven step tables/logs exist only when native execution was requested. All
are bound by the existing last-published manifest. A transient failure leaves
partial evidence but no completed generation. Prior run directories are intact.

No output rails, slew/current limit, saturation/recovery, startup sequence,
physical contact measurement, firmware enablement or safety approval is added.
