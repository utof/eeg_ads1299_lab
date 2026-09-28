# Rev A bounded linear BIAS study

First executable increment for issue #17 / PR #20, extended in PR #21.
See `docs/REV_A_BIAS_DYNAMICS.md` for optional amplifier-pole uncertainty. **Simulation and electrical
dummy loads only.** This is not a full ADS1299 model, a calibrated MCScap model,
a schematic release, or permission to enable BIAS in firmware.

## What it answers

BIAS senses the common voltage shared by the inputs and drives an inverted
correction through a feedback path. Negative feedback can reduce interference;
phase delay in the amplifier and load can instead make the loop oscillate.
This study asks how an explicitly stated linear circuit behaves before any
physical circuit is connected. It reports the full model, loop return ratio,
closed-loop poles, formal current-to-voltage response, and small linear steps.

It does **not** answer power-up sequencing, output swing/slew/current limits,
nonlinear saturation recovery, electrode polarization/noise, physical protection,
or actual body-interface behavior. Those remain separate work under #17.

## Sources and a corrected source discrepancy

The source record is `docs/references/ti/bias/source_record.json`.

* [TI SBAA188](https://www.ti.com/lit/pdf/sbaa188), printed pages 5-6, equation 3
  and figure 5: common-mode summing topology and the `Rf || Cf` feedback path.
  Its page 9 example uses 1 Mohm / 1.5 nF / 220 kohm. The independently checked
  two-selected-output limit has DC gain 9.090909 V/V and pole 106.103295 Hz.
* [ADS1299 Rev. C](https://www.ti.com/lit/ds/symlink/ads1299.pdf), printed page 9:
  BIAS gain-bandwidth is **typically** 100 kHz at a 50 kohm || 10 pF load, gain one.
  It does not specify a complete open-loop transfer function for this model.
* The same datasheet's figure 38 (page 33) says **220 kohm**, whereas equation 11
  (page 68) says **330 kohm**. [TI's explicit correction](https://e2e.ti.com/support/data-converters-group/data-converters/f/data-converters-forum/617532/ads1299-4-recalling-the-ways-to-get-a-clean-signal?keymatch=ADS1299-4&tisearch=e2e-sitesearch)
  identifies 330k as a typo and confirms 220k. The model uses 220k and preserves
  the discrepancy rather than silently picking a convenient value.

No TINA attachment or vendor silicon macro-model was retrieved/imported/executed.
This is a repository-owned reconstruction of the published topology and equation,
with disclosed simplifications. We did not reproduce TI's full EVM measurement
fixture or claim its published CMR measurements as our result.

## Selected facts versus assumptions

The existing validated hardware JSON supplies Rf=1 Mohm, Cf=1.5 nF,
BIAS output series R=1 Mohm, input series R=4.99 kohm, and four differential
capacitors of 4.7 nF. No baseline/BOM values are changed or duplicated as defaults.
The manifest/report identify the canonical baseline digest.

Eight buffered input outputs feed the summing node through individual 220 kohm
resistors. Both legs of every channel are included. The buffers approximate unity
common-mode transfer; they do **not** model PGA differential gain, finite bandwidth,
noise, offset or rail behavior. Summing resistors load the **buffer outputs**, not
the high-impedance input nodes. Pairwise differential capacitors remain explicit.
For both selected PGA legs, ideal differential components cancel in the sum;
that simplification becomes questionable when a real PGA rails after disconnection.

Unmeasured assumptions are deliberately exposed in `BiasModel`:

| Parameter | Nominal study assumption | What it is not |
|---|---|---|
| Amplifier open-loop DC gain | 100,000 V/V | A guaranteed ADS1299 specification |
| Amplifier dynamics | One dominant pole, derived from assumed gain and typical GBW | Complete internal amplifier dynamics |
| Eight input contacts | 10 kohm each | MCScap's component impedance specification or measured scalp contact |
| BIAS contact | 10 kohm | A measured owned electrode |
| Lead shunt capacitance | 100 pF | Known cable length, shielding, or distributed cable model |
| Each input-node capacitance | 100 pF | A fitted capacitor or calibrated cable capacitance |
| Input load | 1 Gohm per node | Full ADS input admittance over frequency |
| Dummy environment | 100 Mohm || 200 pF to the local midpoint | A person, room, protective earth, or isolation network |

Node zero is the small-signal analog midpoint, **not protective earth**. A one-amp
normalization in the equations defines volts per ampere (ohms); it is not an
instruction to inject an ampere. Native closed-loop AC uses a 1 nA source and
normalizes its result. The linear step is also 1 nA unless explicitly requested.

## Equations and independent checks

For `s=j*2*pi*f`, `Yf=1/Rf+s*Cf`, and `Gcm=1/220k`:

```text
A(s) = A0 / (1 + s*A0/(2*pi*GBW))       assumed single-pole family
K(s) = A(s)*Gcm / (8*Gcm + (1+A(s))*Yf)
vout = -K(s) * sum(vinput)

(G + s*C) * nodes = drive_column*vout + interference_column*I
L(s) = K(s) * sum(input response to unit vout)
vout/I = -K(s)*sum(input response to unit I) / (1+L(s))
```

The ideal infinite-amplifier-gain two-output limit is independently checked
against SBAA188's `2*Rf/220k / (1+s*Rf*Cf)`. A separate resistor-only reduction
checks the balanced DC closed-loop result. Another full 12-state circuit
formulation includes all passive nodes, the summing node and amplifier output;
its eigenvalues determine **this linear model's** stability. The matrix exponential
produces the zero-state step response without a time-step integration approximation.

`sampled_unity_crossings` interpolates crossings on 1,201 logarithmic frequency
samples from 0.1 Hz to 100 kHz. Its phase margins are estimates, not a proof that
all crossings were found. Pole classification, not one sampled phase number,
decides whether a settling trace is permitted. A stable linear pole set still
cannot certify the unknown physical amplifier or its load.

The five nominal cases are balanced, one 50 kohm contact, one disconnected input
(`None` means an actually omitted branch), disconnected BIAS contact, and a
10 Mohm-per-contact stress fixture. Even an open input retains the explicitly
modeled input load and pair capacitor. That is an electrical sensitivity case,
not the real disconnected-electrode rail/noise behavior.

There are **108 numerical sensitivity samples**: four contact values × three
capacitance settings × three GBWs × three assumed open-loop gains. Lead and
input-node capacitances vary **together** in this first sweep. These are neither
manufacturer tolerances, measured electrode ranges, a probability distribution,
nor exhaustive independent parameter bounds. Ten native comparisons cover five
nominal cases × loop/closed modes, not all 108 samples. PR #21 adds three separate
extra-pole cases and six more native comparisons; the original cases are unchanged.

## Run and retained evidence

```bash
uv sync --locked --all-extras
uv run --locked python -m lab.rev_a_bias --out reports/rev_a_bias
uv run --locked python -m lab.rev_a_bias --require-ngspice --out reports/rev_a_bias
uv run --locked python -m tools.check --native
```

The command returns one unique run ID and report path. `--run-id` accepts a
caller-chosen 32-character lowercase hex identity. It cannot be reused. Each
run directory contains the full parameter/results JSON, copied source record,
response CSVs, 16 AC netlists and seven stable-case step netlists, four
contact-case linear-step CSVs plus stable dynamics traces, and native
`ac.txt`/`transient.txt`/logs when requested. The transient tables use a uniform
interpolated observation grid; see `REV_A_BIAS_TRANSIENT_VALIDATION.md`. `manifest.json` is published **last**, hashing every
artifact. A failure has no completion manifest; previous directories are untouched.
There is no mutable `current` alias and no fallback to a previous run. The caller
must check command success and use that returned/requested identity. This is not
the passive study's separate `read_study` schema. There is no automatic historical
reader, authenticity, hostile-writer or fsync/power-loss guarantee.

Execution metadata records Python/NumPy/SciPy/ngspice versions, the model source
SHA-256 and uv.lock SHA-256. Exact Git commits and clean-worktree checks are
provided by the associated CI run. Local dirty-source checks must not be described
as execution of an unchanged Git commit.

Test-first CI commit `f18dd1b963ae374c74022e1e516111ce40bdf435` checks for the new
executable module; its failure records the **missing feature**, not a previously
existing numerical bug. Initial local equation tests likewise failed because the
module did not yet exist. The implemented tests then check published/DC limits,
common-mode symmetry, open paths, unstable stress rejection, amplitude/sign
linearity, input validation, source/netlist placement, unique publication,
failed native comparison, and ten real ngspice comparisons. Consult PR #20's
final exact-head jobs for completed source evidence.

## First observed numerical result and its meaning

In the nominal assumed circuit, the balanced case's rightmost pole is about
-749.67 per second and the sampled phase margin about 18.84 degrees. The 10 Mohm
stress fixture instead has a right-half-plane pole about +140.60 per second and
sampled margin about -6.09 degrees. The study retains that unstable result and
refuses to produce a misleading settling trace. AC algebra can still agree with
ngspice for an unstable circuit; its response is labelled **formal transfer only**,
not an attainable sinusoidal steady state.

These are values calculated for the documented assumptions, **not measured
ADS1299/MCScap performance**. The source parameters and retained run are the
reproducibility reference. Four traces span 0–0.1 seconds; that window does not
claim every stable mode has settled (an open contact can have a much slower mode).

## Remaining work

PR #21 adds an optional unmeasured extra amplifier pole consistently to equations,
state dynamics and netlists. Keep issue #17 open for physically justified dynamic
bounds, limited output swing/slew/current, nonlinear overload/recovery, and
dummy-bench calibration.
Do not fit uncertain poles or cable values just to obtain a comfortable margin.
No firmware BIAS or lead-off excitation was enabled. Power, schematic/ERC, S3
compilation, physical measurements and a separate body-interface review remain
independent gates.
