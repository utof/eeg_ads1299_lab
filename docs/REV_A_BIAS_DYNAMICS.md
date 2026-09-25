# BIAS amplifier-dynamics sensitivity (PR #21)

This increment asks whether the first linear BIAS result depends on the assumed
single-pole amplifier. It does not identify the ADS1299's real internal poles.
The default `extra_pole_hz=None` preserves PR #20's complete nominal model.

## Explicit alternative family

For a positive `extra_pole_hz`, the original assumed amplifier response is divided
by `1 + s/(2*pi*extra_pole_hz)`. The same additional time constant appears in the
full circuit state equations and an isolated RC stage in the generated SPICE
netlist. The state dimension grows from 12 to 13; the summing node and output
loading remain connected to the final output, not to the intermediate pole.
DC gain is unchanged. Infinite extra-pole frequency tends to the original
frequency response; the asymptotic test does not assert accurate state eigenvalues
for an arbitrarily ill-conditioned/stiff matrix.

**Important:** `gbw_hz` in this extension remains the original dominant-pole gain
product. Adding another pole lowers the total unity-gain bandwidth. These cases
are therefore not a fitted two-pole model satisfying the datasheet's typical
100 kHz unity-gain observation. They are sensitivity experiments about omitted
dynamics. No pole frequency or resulting range is a TI measurement/tolerance.

The normal study now also executes three nominal-load cases with extra poles at
100 Hz, 1 kHz and 100 kHz. They are kept separately under `dynamics/` and in
`amplifier_dynamics_cases`, not silently mixed into the original 108-point contact/
capacitance/GBW/gain grid. Six extra loop/closed ngspice comparisons bring the
study total to **16**; the existing five contact cases are unchanged.

## What was observed

With all other nominal assumptions fixed, an added 100 Hz pole changes the
rightmost modeled pole from about -749.67/s to -70.70/s. Both are stable in this
linear model, but their damping is materially different. Added 1 kHz and 100 kHz
poles give approximately -689.97/s and -749.09/s respectively. These values do
not establish actual amplifier bandwidth or a physical stability margin.

The correct conclusion is that unknown amplifier dynamics remain a model
uncertainty, not that the ADS1299 has a 100 Hz extra pole or needs new components.
The source record labels this separate assumption explicitly. No baseline part,
firmware behavior, body-use gate, dependency or generic solver was changed.

## Validation and evidence

Thirteen initial focused local cases failed on the absent `extra_pole_hz`
constructor argument before implementation. A separate remote test-only commit
`ec22270894cbb36d50fb6a943f33b6af4b655ac2` asserts that the assumption is exposed
in the model. Its CI is missing-feature evidence, not a pre-existing numerical bug.

Completed tests cover DC invariance, added state count, finite/positive validation,
the remote-pole limit, step/DC convergence, changed damping and six real ngspice
complex-transfer comparisons. The full locked gate and exact PR head's
Python 3.11/3.13/native jobs remain the merge evidence; do not confuse local dirty
source with a previously published Git commit. All study outputs include their
source/lock/baseline identities, copied source record and file-digest manifest.

No added pole implements rails, slew/current limiting, startup, nonlinear overload
or recovery. Issue #17 stays open for those questions and measured dummy-bench
calibration. Simulation agreement still means agreement about an assumed circuit.
