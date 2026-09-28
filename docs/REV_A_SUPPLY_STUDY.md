# Rev A analog-feed supply sensitivity

This is an executable **shared-source / analog-feed hypothesis**, independent of
`lab.rev_a_power` and its unqualified TPS7A20 compatibility experiments. It is not
a regulator model, a complete board simulation, a sourcing recommendation, or
permission to purchase, fabricate, flash, or connect a person.

## Circuit and assumptions

```text
ideal source -- shared resistance -- bus -- selected 10 ohm feed -- AVDD
                                     |                            |
                               MCU conductance             analog conductance
                                     |                     and ideal capacitor
                                     0                            0
```

`run_supply_study()` first loads and validates the existing public hardware
contract. Source voltage is its low-tolerance endpoint: 5 V * (1 - 1%) = 4.95 V.
The feed is the selected 10 ohm component. The analog load is an **assumed
conductance**, calibrated to the 10 mA design budget at nominal 5 V: 0.002 S.
These inputs come from `hardware/rev_a/board_profile.json`; its operating window
is 4.75..5.25 V. No hardware document is changed by this study.

Shared resistance (0, 0.1, 0.5, 1 ohm), effective AVDD capacitance (10 or 100 uF),
and MCU conductances are unmeasured assumptions. At 5 V, 0.02 S corresponds to
100 mA idle, and the additional 0.08 S to 400 mA extra. The burst therefore means
0.10 S total, **not** 0.08 S total. These are neither measured radio traces nor
ESP32 current specifications. As voltage falls, these loads draw less current;
this is not a conservative substitute for constant-current or constant-power
loads in all operating conditions.

The capacitor is a lumped *effective* AVDD capacitance. Do not sum VCAP/reference
capacitors into it, infer it from BOM quantities, or confuse the 100 uF sensitivity
case with approving a new component. ESR, ESL, capacitance derating, regulator
response, source inductance, current limiting and signal/ground coupling are not
modeled. MCU load remains upstream of the analog feed; no MCU current is routed
through the ADS-only DVDD regulator.

## Independent analytical and native paths

For each constant-load phase, let `Rs` be shared resistance, `Rf` the feed,
`Gm` the total MCU conductance and `Ga` the analog conductance. The analytical
path reduces the bus to a Thevenin source:

```text
D = 1 + Rs*Gm
Vth = Vs/D
R = Rf + Rs/D
Vinf = Vth/(1 + Ga*R)
tau = C*R/(1 + Ga*R)
V(t) = Vinitial + (Vinf - Vinitial)*(1 - exp(-elapsed/tau))
```

The capacitor starts uncharged. Source turns on at 1 ms; added MCU load turns on
at 8 ms and off at 12 ms; the observation ends at 20 ms. The exact capacitor state
is carried between phases, independently of requested sample spacing. `expm1`
avoids cancellation near an event. Frozen input values reject nonfinite,
boolean, negative and inappropriate zero parameters; degenerate derived values
outside the floating-point domain are rejected rather than returned as results.

The ngspice exporter uses the **unreduced two-node circuit**, conductance loads
at their respective nodes, and explicit 1 ns source/load edges. A stiff shared
source uses a zero-volt source rather than a tiny-resistance approximation.
The existing public `lab.analog.run_ngspice_transient` owns execution and reading;
there is no second process runner or parser. It requires the named `v(avdd)`
column and fresh raw integration endpoints before any exported data are trusted.
The study additionally requires the whole observation window and samples in all
three active phases. Retained tables use the adaptive grid, not `linearize`.

The analytical edges are ideal and the native edges are finite. The declared
**100 uV absolute comparison tolerance** applies to these five fixtures at
native sample times, not to arbitrary parameter combinations or device accuracy.
The first local run on ngspice 42 compared 100,469 total samples, with maximum
absolute errors between 2.21 and 24.75 uV. Exact-head CI remains the authority for
which candidate was verified; these numbers do not imply a new silicon result.

## What the five cases demonstrate

Values below are analytical extrema in the explicitly defined **4..20 ms**
window, independently cross-checked against native traces. The first 3 ms after
source turn-on are excluded from the margin decision. That exclusion is a
fixture choice, **not an ADS startup time, sequencing guarantee or safety gate**.
Each first-order phase is monotonic, so evaluating its endpoints plus the start
of the margin window captures the continuous analytical extrema without choosing
a favorable sample grid.

| Case | Effective C | Minimum AVDD, 4..20 ms | Margin above 4.75 V |
|---|---:|---:|---:|
| Ideal stiff shared source | 10 uF | 4.852941 V | +102.941 mV |
| Shared 0.1 ohm | 10 uF | 4.803960 V | +53.960 mV |
| Shared 0.5 ohm | 10 uF | 4.617537 V | -132.463 mV |
| Shared 1 ohm | 10 uF | 4.403915 V | -346.085 mV |
| Shared 1 ohm, larger bulk | 100 uF | 4.411883 V | -338.117 mV |

Within this hypothesis, shared resistance matters and increasing capacitance
does not remove the final resistive voltage loss. The larger capacitor also slows
startup/recovery. Neither conclusion establishes the actual source resistance,
installed capacitance, load waveform or delivered board voltage.

## Tests and retained evidence

The saved test-only PR #35 scaffold was rerun with **34 software failures** before
implementation. Extended tests were committed and observed failing as well.
Independent tests include two-node DC KCL, instantaneous capacitor-current KCL
for the time constant (60 deterministic Hypothesis examples), zero-load and stiff
source limits, capacitance/source scaling, query-grid independence, an independently
computed shared-source exponential, and charge continuity. Native negative controls move the MCU load downstream or nearly
short the feed: both must disagree with the correct analytical circuit.

Publication tests inject missing/partial trajectories, sparse or truncated
observations, and finite but numerically biased traces. All five case attempts
are retained. `native_execution_complete`, `native_comparison_passed`, and
`model_margin_ok` are distinct: a completed correct comparison can demonstrate a
modeled margin breach, while a completed incorrect comparison must fail the gate.
Unexpected programming errors are not reclassified as simulator failures.

Nine hand-selected source mutations were executed and killed by test assertions:
wrong loading/burst interpretation, wrong burst time constant, erased capacitor
charge, ignored mismatch/failure, an incorrect margin window, MCU placement after
the feed, and conflated completion/comparison flags. This was a directed mutation
experiment, not a whole-project mutmut score. Mutated source was restored byte-for-byte.

Each invocation creates a new UUID directory containing netlists, raw tables,
logs, numerical comparisons, the baseline snapshot, `study.json` and a final
hash manifest. Reports record the model/parser/lock hashes and every input.
A failed execution or comparison returns an error **after** retaining the cases;
there is no latest-success pointer or overwritten historical result. Manifests
bind bytes, not simulator authenticity, filesystem durability, or physical truth.

```bash
uv sync --locked --all-extras
uv run --locked python -m lab.rev_a_supply --out reports/rev_a_supply
uv run --locked python -m tools.check --native
```

The shared native gate runs this study before native pytest, so a subsequent
native-test failure does not lose its supply reports. Normal CI needs no vendor
archive or online model download. A modeled rail breach does not make the command
fail; incomplete execution or a failed numerical comparison does.

## Next engineering step

Tie the source path, AVDD return, local bulk/decoupling and reference/VCAP
connections to the exact four-channel schematic and independent ERC/polarity
review. Obtain defensible source/load/effective-capacitance bounds before using
these predictions as board-design evidence. Keep the TPS7A20 enable-off issue
and unmeasured BIAS/contact assumptions open; neither blocks drawing the actual
schematic, and neither is silently repaired by this independent supply study.
