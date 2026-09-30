# Remaining upstream coupling: one bounded disposition

Reviewed source: `b88d3746f5f2c72dd60ffbb201213ac9010b19a4`, tree
`54d8bb7df44d437626100ffa6da06fd65116c6a3`, after merged PR #66. Board SHA256
`5da65b4307f0336883da9aeae48711b28c1944ec587f5d3174f12db4e9921875`.
This assessment changes no source copper, circuit, dependency or approval gate.

## Decision: retain now, do not waive, resolve against requirements

**Retain the nine residual locations pending a chosen vendor stackup and a
quantitative bench-input/coupling envelope. Do not schedule nine independent
reroutes.** They are one upstream-coupling item with six electrical net pairs,
not nine independent noise sources. This is a design-work sequencing decision,
NOT acceptance of the geometry for manufacture or measured performance.

Next is the **four-layer stackup and person-disconnected input-test envelope**
decision: identify one manufacturable stackup, state supported source impedances,
aggressor spectra and error budgets, and then decide whether this group requires
one combined reroute or a deliberately accepted pilot-board experiment. Missing
inputs leave the item OPEN. Do not extend the previous hypothetical 5k/50k-ohm
examples into actual electrode specifications or accepted limits.

A combined reroute remains possible. The evidence here does not prove it is
impossible, globally inferior or unnecessary. What is not justified is exchanging
short upstream routes for large detours solely to improve a crossing counter
before setting dielectric geometry and performance requirements. Keep the
completed AVDD1, MISO/DRDY, CH1N and main R/C/U1 routes intact in the meantime.

## One group, six net pairs, nine projected locations

All remaining locations are **before** the four-channel series-resistor/filter
network. The filtered INn DNP branches implicated in PR65 are no longer part of
this residual group. Earlier DNP-branch asymmetry remains a separate unmeasured
parasitic issue, not something this disposition corrects.

| B-layer route | In2 counterpart | Distinct centreline locations | Union projected trace area, mm2 |
|---|---|---:|---:|
| CH3P_DUMMY | CH2N_DUMMY | 1 | 0.040000 |
| CH3N_DUMMY | CH2N_DUMMY | 1 | 0.040000 |
| CH4N_DUMMY | CH2N_DUMMY | 1 | 0.040000 |
| CH3P_DUMMY | AVDD | 2 | 0.120858 |
| CH3N_DUMMY | AVDD | 2 | 0.143831 |
| CH4N_DUMMY | AVDD | 2 | 0.144853 |

Native full-width Boolean unions remove overlapping authored segments before
area measurement (2 um polygon approximation). These are XY projections of
track copper only, NOT capacitances, physical contacts or proof of a parallel-
plate model. Do not multiply these areas by an assumed dielectric constant and
call the result a PCB extraction; edge fields, nearby copper, vias and spacing
matter. In1 GND is above both B and In2, not interposed between them. The prior
nine positions remain, with zero copper changes. Mutual coupling is reciprocal;
calling CH2N an aggressor is a test direction, not a one-way property.

The four-layer source declares only overall thickness 1.6 mm; it does not give
the three dielectric spacings, material tolerances or a vendor stackup identifier.
A nominal total thickness does not establish trace-to-plane or B-to-In2 spacing.

## What the simple reroute experiment did and did not show

In a **disposable copy**, moving all 18 B-layer segments of CH3P/CH3N/CH4N to F
without moving endpoints produces fresh native DRC **30 violations, 0 parity
mismatches, 0 airwires; exit 5**. Findings comprise 11 track-crossing, 9 shorting,
7 solder-mask-bridge and 3 dangling-via entries; these are report entries, not
30 independent faults. A separate unchanged copy freshly refills with DRC0/0/0.
This rules out a blind layer swap, not a carefully redesigned combined route.
The bad copy was never applied to tracked source.

## Conditional mutual injection, unlike the earlier ground-C example

Seven actual ngspice analyses investigate an **assumed capacitor from a stiff
aggressor to one upstream victim leg**: four Rs/Cm cases plus three native
controls. Both victim legs return through equal source resistances to small-
signal zero, then through the selected 4.99k-ohm resistors to a 4.7nF differential
capacitor. The illustrative load is 1T ohm ||100pF per ADC input. Zero is local
small-signal reference, not protective earth; there is no body or silicon model.

The numbers below use one hypothetical lumped Cm, NOT a measured value for any
crossing, not 1 or 10 pF per crossing, and not a PCB capacitance upper bound.
The stiff source suppresses aggressor back-action; a real high-impedance second
channel needs its own source/load network. Magnetic/shared-return coupling,
supply PSRR/internal paths, lead inductance, input mismatch, package, PGA,
digital filtering and aliasing are absent. They remain outside this model.

| Assumed Rs per victim leg | Assumed Cm to P only | Analog differential peak uV for 10mV-peak aggressor, 50 / 60 / 1000 Hz |
|---|---:|---:|
| 5k ohm | 1pF | 0.015701 / 0.018838 / 0.269827 |
| 5k ohm | 10pF | 0.157010 / 0.188375 / 2.698186 |
| 50k ohm | 1pF | 0.155006 / 0.184943 / 0.915524 |
| 50k ohm | 10pF | 1.550042 / 1.849400 / 9.151537 |

The table is evaluated by the exact reduced passive equation at those three
frequencies. The native comparisons use 241 logarithmic points, 0.1 Hz to
100 kHz; table frequencies are not represented as native samples. The 1-kHz
column is pre-ADC analog response, NOT a claim about a 250-SPS recorded signal.
An independent four-node nodal matrix agreed over 250 deterministic parameter
samples (seed20260930), max absolute error3.58e-17 V/V. Native/formula disagreement
was below1.04e-17 V/V for the four cases. Swapping injection to N reverses sign;
equal injection capacitances cancel in the symmetric model; zero coupling gives
zero response. None proves cancellation on the real, asymmetric board.

Reproduce the seven native runs and comparisons from the repository root with
the locked environment and ngspice installed. This calls the existing public
runner; it adds no production solver/dependency or permanent circuit change.
Assertions below are numerical consistency checks, not electrical acceptance.

```python
from pathlib import Path
import json
import math
from lab.analog import run_ngspice


def predicted(frequency: float, source_ohm: float, mutual_f: float) -> complex:
    # Exact reduction of this deliberately restricted passive, symmetric victim.
    s = 2j * math.pi * frequency
    yc = 1e-12 + s * 100e-12
    yd = yc + 2 * s * 4.7e-9
    ac, ad = 1 + 4990 * yc, 1 + 4990 * yd
    kc, kd = ac / source_ohm + yc, ad / source_ohm + yd
    m = s * mutual_f
    return m * kc / (kc * kd + m * (kc * ad + kd * ac) / 2)


def simulate(source_ohm: float, mutual_f: float, mode: str) -> tuple[list[float], list[complex]]:
    directory = Path("reports/upstream-mutual") / f"{source_ohm:g}-{mutual_f:g}-{mode}"
    directory.mkdir(parents=True, exist_ok=True)
    # P/N here are the two upstream victim nodes, not an electrode/body model.
    links = {"p": ["ep"], "n": ["en"], "balanced": ["ep", "en"], "none": []}[mode]
    coupling = "\n".join(f"Cm{i} ag {node} {mutual_f:.12g}" for i, node in enumerate(links))
    netlist = directory / "input.cir"
    netlist.write_text(f"""Illustrative upstream capacitive injection - no hardware approval
* small-signal nodes; local signal zero is NOT protective earth
Vag ag 0 AC 1
Rep ep 0 {source_ohm:.12g}
Ren en 0 {source_ohm:.12g}
Rsp ep inp 4990
Rsn en inn 4990
Rip inp 0 1e12
Rin inn 0 1e12
Ccp inp 0 100p
Ccn inn 0 100p
Cd inp inn 4.7n
{coupling}
.control
set wr_singlescale
set wr_vecnames
set numdgt=15
ac dec 40 0.1 100000
let h = v(inp)-v(inn)
let hr = real(h)
let hi = imag(h)
wrdata ac.txt hr hi
quit
.endc
.end
""")
    f, h = run_ngspice(netlist, directory)
    return f.tolist(), h.tolist()


rows = []
for rs in (5000.0, 50000.0):
    for cm in (1e-12, 10e-12):
        f, h = simulate(rs, cm, "p")
        error = max(abs(value - predicted(freq, rs, cm)) for freq, value in zip(f, h))
        assert len(f) == 241 and error < 2e-14
        rows.append(
            {
                "Rs_ohm_each": rs,
                "assumed_Cm_pF": cm * 1e12,
                "points": len(f),
                "native_formula_max_abs_V_per_V": error,
                "exact_H_magnitude_at_50_60_1000_Hz": [
                    abs(predicted(freq, rs, cm)) for freq in (50, 60, 1000)
                ],
                "peak_uV_for_10mV_peak_aggressor_at_50_60_1000_Hz": [
                    abs(predicted(freq, rs, cm)) * 10000 for freq in (50, 60, 1000)
                ],
            }
        )
# Three extra actual native controls, for the final 50k/10p case.
control = {}
for mode in ("n", "balanced", "none"):
    f2, h2 = simulate(rs, cm, mode)
    assert f2 == f
    target = [-value for value in h] if mode == "n" else [0j] * len(h)
    error = max(abs(a - b) for a, b in zip(h2, target))
    assert error < 2e-14
    control[mode] = error
print(
    json.dumps(
        {
            "scope": "hypothetical_lumped_mutual_injection_not_PCB_extraction",
            "rows": rows,
            "native_control_errors_V_per_V": control,
            "native_runs": 7,
        },
        indent=2,
    )
)
```

## Finite exit conditions: design release and hardware performance differ

| Stage | Required evidence | Outcome when missing or failing |
|---|---|---|
| Before a pilot fabrication decision | Vendor stackup ID/revision; dielectric and copper thickness/tolerances; supported source/load range; aggressor spectra at actual nodes; intended bandwidth/rate/gain; allocated coherent-tone and broadband-noise budgets | Keep #45 OPEN. Either one combined reroute against these inputs or explicit pilot-risk acceptance by the separate release review. A green DRC or this example is not that acceptance. |
| Before powered bench injection | Reviewed person-disconnected fixture, safe startup/rail sequence, exact interface and calibrated source/measurement method; all existing prerequisites | No powered experiment is authorized by this document. Do not bypass disabled acquisition/BIAS or connect a person. |
| Before claiming validated performance | Measured transfers with uncertainty/floor and source terminations, plus in-band noise/alias-sensitive tests under the chosen envelope | Reject/hold if a criterion fails or the floor cannot resolve it; review/reroute this group together if needed. No inferred pass from an unmeasurable result. |

This is not a circular demand to measure a physical board before the first test
PCB can exist: **pilot fabrication** requires a separately reviewed design and
bounded experimental risk; **validated hardware** requires the later physical
evidence. Neither authorization is granted now. Do not re-label bench checks as
a prerequisite already passed by simulation.

The finite future test matrix is:

- Drive CH2N through the intended source/load conditions, observe differential
  CH3 and CH4, then reverse relevant channel roles. Include baseline drive-off,
  swapped leads/polarity, grounded/low-Z and maximum-declared source-Z controls.
  Verify what actually reaches the aggressor node, not only generator settings.
- Observe AVDD ripple-to-CH3/CH4 transfer under a separately reviewed supply
  perturbation that stays within the allowed rails/startup policy. This measures
  the total board response, including internal supply sensitivity and shared
  paths; it does not isolate the six geometric supply crossings by itself.
- Repeat in the intended band and selected out-of-band/alias-sensitive conditions
  with the declared acquisition settings. Quantify fixture feedthrough and
  instrumentation noise before attributing a result to PCB coupling.

For declared simultaneous coherent aggressors, a conservative per-frequency
criterion is `sum_j((abs(H_ij(f)) + u_Hij(f)) * A_j(f)) + u_floor(f) <= B_i(f)`.
H is the measured differential transfer, A the declared aggressor amplitude,
and B the allocated coherent-error budget, all in compatible peak or RMS units.
Broadband noise needs its own integrated budget; this tone inequality is not
an RMS-noise qualification. Do not claim cancellation for unknown phases.
The actual spectra, impedance envelope, budgets and measurement floor remain
UNSET, not invented from the illustrative values above. Their definition is
part of the immediate stackup/test-envelope task, not deferred indefinitely.

## Evidence, source and limits

`checkpoints/20260930_upstream_disposition.json` records source hashes, six native
area measurements, the layer-swap control and all seven illustrative results.
Raw/native coordinates, nets, layers and straight lengths agreed for all704
track/via records. Native inventory read245pads; their coordinates were not
independently rederived again in this slice. Independent planar unions agree
within the stated0.0001mm2 analysis tolerance; no DRC rule was changed.

Source-capture36709023765 fetched exact publishedb88d, not the old chat ZIP.
Native9.0.2 refills were executed on separate canonical/trial copies. Tool/cache
captures only supplied the declared tools; they are not repository dependencies.
Initial local outer-timeout attempts and a missing native schema-path failure
are retained as failed attempts, not passing checks. Required resource placement
was corrected without source/test changes. Read this PR's live final-head checks
and review separately from baseline or analysis results.

Primary basis inspected, including relevant figures: TI SCAA082A pp8-9 explains
capacitive/inductive coupling and the need to establish signal specifications
and manufacturer layer spacing; TI ADS1299 SBAS499C pp68,72 describes the
input filter and application-specific layout. These are not per-crossing
picofarad values, a millimetre/noise guarantee, or a requirement to split GND.
https://www.ti.com/lit/an/scaa082a/scaa082a.pdf
https://www.ti.com/lit/ds/symlink/ads1299.pdf

Keep #45/#48 and all hardware/purchase/fabrication/body-use gates unchanged.
**Next: choose and document the vendor four-layer stackup and the bounded
person-disconnected input/coupling test envelope, with explicit unresolved
fields or one group reroute decision.** No new generic simulator or nine-step
routing loop is required. Component, mechanical and interface release decisions
then follow the roadmap.
