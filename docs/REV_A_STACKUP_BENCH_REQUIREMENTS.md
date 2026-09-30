# Rev A stackup target and person-disconnected bench requirements

Decision record E1, 30 September 2026. Base source `8403c4eefc6fd6f1303a75510755f16f983e71c4`,
tree `4f5bebbc578c15f63c3463f2b3cef0bd28fbdfa9`; authored PCB SHA256
`5da65b4307f0336883da9aeae48711b28c1944ec587f5d3174f12db4e9921875`.

**Select JLCPCB JLC04161H-7628 as the design-stack target, and E1 below as the
first dummy-source performance target.** These are explicit engineering choices
made here, not measurements, previously supplied user requirements, an order,
or a claim that ordinary electrodes meet this envelope. The vendor's detailed
build tolerances and the actual bench fixture remain unconfirmed. No source
CAD, BOM, firmware, model, dependency or approval flag changes in this slice.

## 1. Named construction, without inventing factory tolerances

Use the named **1.6-mm, four-layer, 1-oz outer / 0.5-oz inner** construction [1].
Retain the authored F / In1 GND / In2 routed copper / B assignment. Do not rename
In2 a plane or imply that In1 shields the remaining B/In2 crossings.

| Layer or dielectric | Selected table value | Reference/design role |
|---|---:|---|
| F.Cu | 0.035 mm | Components and principal analog/digital paths |
| 7628 prepreg | 0.21040 mm, nominal effective Dk 4.4 | F to In1 |
| In1.Cu | 0.0152 mm | Existing connected GND fill |
| Core | 1.065 mm; stackup page Dk 4.6 | In1 to In2 |
| In2.Cu | 0.0152 mm | Existing routed supplies/signals, NOT a plane |
| 7628 prepreg | 0.21040 mm, nominal effective Dk 4.4 | In2 to B |
| B.Cu | 0.035 mm | Existing back copper |

The tabulated sum is **1.5862 mm before soldermask**, not a new nominal order
thickness. JLC's guide says finished thickness includes mask, prepreg values
are pressed thicknesses, and dielectric constants are process-derived [2,3].

The compared JLC04161H-3313 table uses 0.09940-mm outer gaps and a 1.265-mm core
[1]. It places F nearer GND but also places B nearer routed In2. Choosing 7628
is a compromise for the existing layout, not a proof of lower total coupling,
a cheapest delivered quote or an impedance guarantee. Do not estimate actual
mutual capacitance by treating the six trace-union areas as isolated plates.

**Material target: Nan Ya NP-155F**, the named 4-8-layer calculator material [2],
subject to written availability/build confirmation; do not accept an unspecified
FR-4 substitution on the strength of a stackup ID. The public sources need
reconciliation: the stackup page lists **35 um** outer copper / core Dk **4.6**;
the calculator guide uses **1.6 mil = 40.64 um** / **4.43 for cores >0.70 mm**
[1,2]. Those are distinct published reference values, not statistical limits.

JLC publishes **1.6 mm +/-10% overall thickness** and **+/-20% track width**
[4]. Neither is a guarantee of +/-10% on EACH dielectric gap, Dk, copper
thickness, registration or coupling. No such per-layer guarantee was found.
The existing 0.15-mm traces and 0.60/0.30-mm vias are not a substitute for DFM:
their nominal 0.15-mm annulus sits at the published multilayer PTH absolute
minimum, below its 0.20-mm recommendation [4]. Via-specific acceptance, drill
compensation and pad holes must be checked by the vendor; no automatic via resize.

### Factory confirmation needed before releasing build data

Request a dated job-specific drawing with the exact stack ID, laminate grade,
finished/pressed dielectric min/nominal/max, copper min/nominal/max, applicable
Dk/frequency/material ranges, layer registration and through-hole process.
Ask the vendor to resolve the two public-value differences above and to review
the existing fine-pitch copper, 0.60/0.30-mm vias and connector holes. Require
no substitutions without a new review. This is a prepared request, **not a sent
message or obtained confirmation**. The order price, finish, assembly and
material availability are not established by this record.

For a provisional sensitivity sweep only, examine outer gaps 0.17-0.25 mm and
Dk 4.0-4.8, as well as both published copper/core-Dk values. These are deliberately
chosen analysis intervals, **not vendor-supported bounds** and not sufficient
for worst-case sign-off. If the confirmed stack lies outside them, recompute.
Do not encode an unconfirmed stack into fabrication outputs or call it released.

## 2. E1 numerical target: a limited dummy-bench configuration

The purpose is to resolve a **10-uV-peak, 10-Hz reference stimulus** with useful
margin while retaining the current 250-SPS, gain-24 architecture. It is not a
clinical EEG specification. Existing internal-test/input-short modes remain
the only initially enabled modes; external dummy acquisition stays disabled.
Fixture/startup/interface review is required before any later powered test.

| Quantity | E1 requirement/definition |
|---|---|
| Environment | Person/animal disconnected; 20-30 degC; one reviewed bench-power arrangement; Wi-Fi/BLE, BIAS, lead-off and SRB routing off |
| Acquisition | Existing 4-channel, 250-SPS nominal, gain 24, internal 4.5-V reference, 2.048-MHz nominal clock; SPI mode 1, 1 MHz; no firmware changes here |
| Performance band | 1-40 Hz. Diagnose 50/60 Hz separately on the unnotched record. Do not claim a flat 65-Hz passband |
| Qualified-target source family | Calibrated resistive dummy sources 1-10 kohm per leg, P/N matching within 0.1%; verify endpoints 1k/1k and 10k/10k. This is NOT a scalp-impedance range |
| Fixture loading | At J2, no more than 100 pF to local return per leg, mismatch no more than 1 pF; measure including leads/adapters. Not a bound on ADS/PCB parasitics |
| Actual AFE load | Unchanged ADS1299 plus fitted R/C and DNP copper. TI gives 1-Gohm minimum DC input impedance without lead-off and 20-pF typical input capacitance [5]; 20 pF is NOT a maximum or a validated per-leg shunt model |
| Differential input | 10 uV to 10 mV peak AC; DC offset up to +/-50 mV; sum never exceeds 60 mV peak magnitude at the PGA. No overload/stimulation/body claim |
| Common mode | 2.5 V nominal; entire instantaneous excursion 2.40-2.60 V, including injected common mode; no source connected during unreviewed/unpowered startup |
| Rails | Existing AVDD operating range 4.75-5.25 V includes all ripple; DVDD nominal 3.3 V. Source remains the selected regulated 5-V topology, not DevKit USB power |
| Signal transfer | After one 10-Hz gain calibration, amplitude response at 1, 5, 10, 20 and 40 Hz must be within 5% of the declared passive network times sinc3 response NORMALIZED at 10 Hz; retain uncorrected data and calibration uncertainty |
| Total noise | At most **0.50 uV RMS**, integrated 1-40 Hz, each channel, all E1 sources quiet and terminated, normal SPI/UART activity; no notching or removal of in-band lines to pass |
| Internal-short diagnostic | At most **0.30 uV RMS** in the same band; additional troubleshooting criterion, NOT a replacement for the externally terminated test |
| Coherent error | At most **0.50 uV peak per victim/frequency**, with the component allocations below, including uncertainty. Broadband RMS noise is a separate condition |
| Record | At least 64 s AFTER 2 s of settling; measure actual sample rate, do not assume exactly 16000 samples or ideal clock frequency; no missing/clipped frames |

All error/noise voltages are ADC-input-equivalent values from calibrated code
scale (nominally Vref/(gain*2^23) per code, TI Equation 8), **without inverse-filter equalization**.
Coupling H includes the actual acquisition filtering; its denominator is the
measured aggressor node amplitude. Transfer-shape calibration above is separate
from noise/interference acceptance, not permission to rescale a failure away.

The core is intentionally a **low-impedance calibrated bench target**, not all
possible sources. Also characterize 100k/100k and 1k/100k with reversed legs,
plus fixture capacitance/mismatch excursions. These are **stress cases outside
E1 acceptance**, not omitted failures or qualification of high-impedance use.
Publish their actual curves/exceedances. Extending the supported range needs an
explicit requirement revision before claiming success; do not relabel a failed
E1 case as stress after seeing its result.

### Defined aggressors and allocations, in peak units

| Class at its actual node | Declared envelope | Allocation per victim/frequency |
|---|---|---:|
| Other input channels | Up to THREE simultaneous unwanted channels, each at most 10 mV peak, measured at the relevant J2 node; test CH2N -> CH3/CH4 and reciprocal directions, all E1 terminations | **0.20 uV peak total**, not 0.20 per crossing or aggressor |
| AVDD | At most 1 mV peak per test tone, measured on AVDD AFTER the feed resistor; sweep around a compliant DC rail without exceeding its operating range | **0.10 uV peak** including internal PSRR and shared paths, not geometry alone |
| Common mode | 10 mV peak applied equally to each victim's two source legs; test matched E1 sources at 50/60 Hz as well as band checkpoints | **0.10 uV peak** differential |
| Digital/console | Existing 3.3-V nominal, 1-MHz SPI bursts and UART acquisition traffic, Wi-Fi/BLE off; compare quiet/normal and supported worst-toggle patterns after fixture review | **0.10 uV peak** aggregate activity-correlated response; don't assign an invented pin edge rate |

For a class with multiple aggressors, use
`sum_j((abs(Hij) + U95_Hij) * Aj) + U95_fixture <= allocation`.
For simultaneous classes sum their upper error bounds; the allocations add to
0.50 uV peak. Unknown phases must not be credited with cancellation. Residual
fixture feedthrough must be measured, conservatively retained or bounded; do
not subtract an unmeasured blank. A floor-limited result is **inconclusive**,
not a zero transfer. DC gain/offset and broadband noise need their own checks.

Use actual node amplitudes, not unloaded generator settings. In-band checkpoints
are 1, 5, 10, 20, 40 Hz plus 50/60-Hz diagnostics. Out-of-band spot tests must also
meet the same class allocation for any component appearing in 1-40 Hz: use
`fs_actual +/- {1,10,40}` and `2*fs_actual +/- {1,10,40}`; include 1 kHz, then
`fMOD_actual +/- {1,10,40}` with `fMOD_actual=4096*fs_actual` in the existing mode.
Input tones remain 10 mV peak; AVDD perturbations remain 1 mV peak. These are
finite spot tests, **not continuous-frequency RF immunity or an accepted bound
on all real spectra**. Missing instrumentation leaves the corresponding test
open. Record actual rise/fall times, ringing and harmonics at the AFE header;
unsupported patterns or injected rail noise must not bypass interface/startup
limits. A 1-MHz clock setting does not characterize its edges.

Sinc3 notches cannot be used to assume zero aliases: internal-clock tolerance,
frequency drift and response repetition near the modulator frequency matter.
TI specifies `fMOD=fCLK/2`, **1.024 MHz nominal**, and decimation 4096 at 250 SPS
[5, pp25-26,46]. The published upstream model does not implement silicon,
digital filtering or aliasing; evaluate those with the raw recorded result.

## 3. Measurement floor and feasibility, not available-equipment claims

Require total expanded uncertainty **U95 <=0.03 uV peak** on each reported
class-level coherent bound, including source calibration, fitting/repeatability,
fixture feedthrough and clock error. For RMS noise require **U95 <=0.05 uV RMS**;
accept only `estimate + U95 <= limit`. Retain a traceable calibration record,
raw samples and PSD normalization/ENBW. For noise use a declared one-sided PSD
integral over 1-40 Hz; remove DC/linear trend only, not in-band tones. For tones
fit sine/cosine at the actual frequency with repeated drive-off/on and reversed
polarity runs. Do not average magnitudes into a fictitious zero-floor result.

As a feasibility calculation only, 0.5-uV independent white sample noise and
16000 samples gives `1.96*0.5*sqrt(2/16000)=0.01096 uV` for a phase-referenced
sine coefficient. ADC filtering correlates samples; systematic feedthrough
and unknown-phase magnitude confidence are not included. Thus this does NOT
establish the 0.03-uV floor: demonstrate it with repeated blanks and actual
uncertainty analysis, or hold the test. A normal oscilloscope trace is not a
sub-microvolt coupling measurement. A calibrated attenuator/low-noise source
and verified capture/analysis chain are required; none is selected, owned or
priced by this slice. The $100 extra-parts objective is not an instrumentation
budget or a delivered quote.

## 4. Consistency calculations and what they cannot establish

At 303.15 K, the simple unfiltered thermal estimate
`sqrt(4*k*T*2*(Rs+4990)*39)` is **0.08844 / 0.13991 / 0.37027 uV RMS** for
Rs=1k/10k/100k per leg. It is the resistor contribution only and ignores
attenuation, excess noise and correlations. TI's gain-24/250-SPS table gives
**0.14 uV RMS at 65-Hz -3-dB bandwidth** under its stated conditions [5,p17];
that is not a whole-board maximum. These scales motivate the E1 target and
separate high-Z stress case; they do not predict a passing prototype.

The normalized nominal sinc3 magnitude at 40 Hz is **0.880371**, so requiring
flat response there would be incorrect. With the selected differential R/C
and E1's 10k sources, the simplified passive-times-sinc3 response is **0.879819**
relative to DC, before AFE parasitics. Full-scale is nominal +/-187.5 mV;
for 60-mV maximum differential magnitude and AVDD=4.75 V, TI's PGA headroom
inequality gives `0.92 < Vcm < 3.83 V` [5,p23]. E1's 2.40-2.60-V envelope is
inside it, but this does not replace startup, clipping or actual-rail checks.

The prior restricted mutual-C example was rerun at 1k/10k/100k with an ASSUMED
1 pF. At 60 Hz with a stiff 10-mV-peak aggressor it gives respectively
**0.003769 / 0.037645 / 0.352868 uV peak** before the ADC. The 1T-ohm/100-pF
load is still that hypothetical example, **not the actual E1 load**. Three
parameter cases plus native reversed/balanced/zero controls are six unique
native cases (the 10k case was also repeated). A separately assembled four-node
KCL matrix agreed at723 parameter/frequency points. No geometry-to-pF mapping,
noise certification or added project tests is implied.

For scale only, assigning one third of the 0.20-uV channel budget to each of
three 10-mV aggressors gives conditional assumed-C thresholds **1.771 pF at10k**
and **0.1889 pF at100k**, evaluated at integer frequencies1-60Hz with the SAME
restricted model and no uncertainty allowance. These are NOT bounds on actual
capacitance or compliance. They explain why accepting high-Z performance from
crossing counts or a nominal stack thickness would be unjustified.

The second executable block below repeats the six native cases, independent
matrix check and the conditional-C bisection using the exact published `simulate` and `predicted` definitions
from `REV_A_UPSTREAM_COUPLING_DISPOSITION.md`. It imports only those definitions
and imports, not that earlier example's top-level cases, and verifies its source
hash first. This changes experiment inputs, not the model or repository defaults.

The checkpoint JSON records numerical results, source locations and unconfirmed
fields. The first block derives both stack sums, code scale, headroom, thermal
and filter values, and the illustrative white-noise sine-fit estimate. The
second derives conditional-C limits by an 80-iteration bracketed search and
challenges both sides, as well as repeating the native/KCL checks. Both compare
derived quantities against their retained records; low-level floating residuals
are printed and bounded, not required to match bit-for-bit across toolchains.
Neither block verifies live manufacturer data or physical performance.

Review comment4145311992 identified missing derivations in the first published
examples. Two disposable incorrect-snapshot probes (doubled LSB and conditional-C
limit) were silently accepted before correction and are rejected by these
blocks. They are software/data probes, not native circuit faults or new project
tests. The corrected exact blocks then completed the actual calculations and
six unique native cases again, without changing the requirements or PCB.

Follow-up4145477875 found that the nominal code-scale expression disagreed with
TI Equation8 and the existing `ADCConfig.lsb_v` contract. A direct comparison
failed before correction. The prose, derived value and checkpoint now use
`Vref/(gain*2^23)`, or22.351741790771484nV/code for4.5V/gain24; the first block
also checks agreement with the existing API. No production conversion changed.

```python
import json
import math
from pathlib import Path
from lab.adc import ADCConfig

p = json.loads(Path("hardware/rev_a/board_profile.json").read_text())
checkpoint = json.loads(Path("docs/checkpoints/20260930_stackup_bench_envelope.json").read_text())
saved = checkpoint["analysis"]
assert (p["afe"]["gain"], p["afe"]["sample_rate_sps"]) == (24, 250)
assert not any(p["gates"].values()) and not p["afe"]["external_dummy_mode_enabled"]
assert p["input_network"]["series_resistance_each_ohm"] == 4990
assert p["input_network"]["differential_capacitance_f"] == 4.7e-9
fs, n = 250, 4096
fmod = p["afe"]["clock_hz_nominal"] / 2
assert fmod == fs * n
sinc40 = abs(math.sin(math.pi * 40 / fs) / (n * math.sin(math.pi * 40 / fmod))) ** 3
rows = []
for rs in (1000, 10000, 100000):
    resistance = 2 * (rs + 4990)
    pole = 1 / (2 * math.pi * resistance * 4.7e-9)
    rows.append(
        {
            "Rs_ohm_each": rs,
            "thermal_unfiltered_1_40_uVrms": math.sqrt(4 * 1.380649e-23 * 303.15 * resistance * 39)
            * 1e6,
            "pole_Hz": pole,
            "sinc3_40Hz": sinc40,
            "passive_times_sinc3_40Hz": sinc40 / math.sqrt(1 + (40 / pole) ** 2),
        }
    )
selected = sum([0.035, 0.2104, 0.0152, 1.065, 0.0152, 0.2104, 0.035])
comparison = sum([0.035, 0.0994, 0.0152, 1.265, 0.0152, 0.0994, 0.035])
gain, reference, max_diff = p["afe"]["gain"], p["afe"]["reference_v"], 0.060
headroom = [0.2 + gain * max_diff / 2, 4.75 - 0.2 - gain * max_diff / 2]
chosen_cm = [2.40, 2.60]
assert headroom[0] < chosen_cm[0] < chosen_cm[1] < headroom[1]
assert max_diff < reference / gain
calculated = {
    "selected_nominal_stack_sum_mm": selected,
    "comparison_3313_sum_mm": comparison,
    "full_scale_peak_V": reference / gain,
    "LSB_nV": reference / (gain * 2**23) * 1e9,
    "max_diff_V": max_diff,
    "common_mode_allowed_at_min_rail_V": headroom,
    "selected_instantaneous_CM_V": chosen_cm,
    "white_independent_sine_fit_95_uV": 1.96 * 0.5 * math.sqrt(2 / (64 * fs)),
}
# Equation 8 must also match the established project's code-to-volts contract.
adc = ADCConfig(gain=gain, vref_v=reference, fs_hz=fs)
assert math.isclose(calculated["LSB_nV"], adc.lsb_v * 1e9, rel_tol=1e-12, abs_tol=0)
# Derived numbers are computed above independently of the retained result values.
for key, value in calculated.items():
    actual_values = value if isinstance(value, list) else [value]
    saved_values = saved[key] if isinstance(saved[key], list) else [saved[key]]
    assert len(actual_values) == len(saved_values)
    assert all(
        math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)
        for a, b in zip(actual_values, saved_values)
    ), key
assert len(rows) == len(saved["source_rows"]) == 3
for actual, retained in zip(rows, saved["source_rows"]):
    for key, value in actual.items():
        assert math.isclose(value, retained[key], rel_tol=1e-12, abs_tol=1e-12), key
allocations = checkpoint["bench_target"]["aggressor_allocations"]
assert math.isclose(sum(a["total_budget_uV_peak"] for a in allocations), 0.5)
print(json.dumps({"derived": calculated, "source_rows": rows}, indent=2))
```

Native/KCL reproduction (requires the declared locked environment and ngspice):

```python
import ast
import hashlib
import json
import math
import re
from pathlib import Path
import numpy as np

text = Path("docs/REV_A_UPSTREAM_COUPLING_DISPOSITION.md").read_text()
match = re.search(r"```python\n(.*?)\n```", text, re.S)
assert match is not None
code = match.group(1)
assert (
    hashlib.sha256(code.encode()).hexdigest()
    == "b87d7c32e9cb3f648c52b74038c82280807aa5c91300825bf91b037e2bf6b5fa"
)
module = ast.parse(code)
definitions = [
    node for node in module.body if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef))
]
namespace = {}
exec(compile(ast.Module(body=definitions, type_ignores=[]), "<reviewed model>", "exec"), namespace)
simulate, predicted = namespace["simulate"], namespace["predicted"]
checkpoint = json.loads(Path("docs/checkpoints/20260930_stackup_bench_envelope.json").read_text())
saved = checkpoint["analysis"]
rows, matrix_errors = [], []
for rs in (1000.0, 10000.0, 100000.0):
    frequency, native = simulate(rs, 1e-12, "p")
    error = max(abs(h - predicted(f, rs, 1e-12)) for f, h in zip(frequency, native))
    assert len(frequency) == len(native) == 241 and error < 2e-14
    for f in frequency:
        s, g, ys = 2j * math.pi * f, 1 / 4990, 1 / rs
        yc, yd, m = 1e-12 + s * 100e-12, s * 4.7e-9, s * 1e-12
        # Independent four-node KCL, order upstream P,N and filtered P,N.
        a = np.array(
            [
                [ys + g + m, 0, -g, 0],
                [0, ys + g, 0, -g],
                [-g, 0, g + yc + yd, -yd],
                [0, -g, -yd, g + yc + yd],
            ],
            dtype=complex,
        )
        v = np.linalg.solve(a, np.array([m, 0, 0, 0], dtype=complex))
        matrix_errors.append(float(abs(v[2] - v[3] - predicted(f, rs, 1e-12))))
    rows.append(
        {
            "Rs_ohm_each": rs,
            "native_error_V_per_V": error,
            "calculated_uV_at60Hz_10mV_peak": abs(predicted(60, rs, 1e-12)) * 1e4,
        }
    )
f, positive = simulate(10000.0, 1e-12, "p")  # Deliberate repeat, not a new unique case.
controls = {}
for mode in ("n", "balanced", "none"):
    f2, h2 = simulate(10000.0, 1e-12, mode)
    assert f2 == f and len(h2) == len(positive)
    expected = [-h for h in positive] if mode == "n" else [0j] * len(positive)
    controls[mode] = max(abs(a - b) for a, b in zip(h2, expected))
    assert controls[mode] < 2e-14
assert len(matrix_errors) == saved["independent_matrix_points"] == 723
assert max(matrix_errors) < 2e-14
assert len(rows) == len(saved["source_rows"]) == 3
for actual, retained in zip(rows, saved["source_rows"]):
    assert actual["Rs_ohm_each"] == retained["Rs_ohm_each"]
    assert math.isclose(
        actual["calculated_uV_at60Hz_10mV_peak"],
        retained["one_pF_10mV_peak_at60Hz_uV"],
        rel_tol=1e-10,
    )
# Residuals are numerical observations, not bitwise-portable reference outputs.
assert all(v < 2e-14 for v in controls.values())

# Solve the restricted model's single-pair limit, NOT an extracted PCB bound.
# The channel class has 0.20 uV peak total / 3 simultaneous 10-mV aggressors.
frequencies = range(1, 61)
budget_V, aggressor_V = 0.20e-6 / 3, 0.01
limits = []
for rs in (10000.0, 100000.0):

    def response(cm):
        return max(abs(predicted(hz, rs, cm)) * aggressor_V for hz in frequencies)

    lo, hi = 0.0, 100e-12
    assert response(lo) <= budget_V < response(hi)
    for _ in range(80):
        mid = (lo + hi) / 2
        if response(mid) <= budget_V:
            lo = mid
        else:
            hi = mid
    assert hi - lo < 1e-24
    # Challenge both sides of the computed crossing, not only a retained number.
    assert response(lo * 0.99) < budget_V < response(lo * 1.01)
    limits.append(
        {
            "Rs_ohm_each": rs,
            "conditional_Cm_pF": lo * 1e12,
            "allocation_peak_uV_per_pair": budget_V * 1e6,
            "tested_integer_frequencies_Hz": [1, 60],
            "uncertainty_allowance_included": False,
        }
    )
assert len(limits) == len(saved["conditional_cap_limits"]) == 2
for actual, retained in zip(limits, saved["conditional_cap_limits"]):
    for key in ("Rs_ohm_each", "conditional_Cm_pF", "allocation_peak_uV_per_pair"):
        assert math.isclose(actual[key], retained[key], rel_tol=1e-10, abs_tol=1e-12), key
    assert actual["tested_integer_frequencies_Hz"] == retained["tested_integer_frequencies_Hz"]
    assert retained["uncertainty_allowance_included"] is False
assert saved["native_runs_unique"] == 6 and saved["native_executions"] == 7
print(
    json.dumps(
        {
            "rows": rows,
            "conditional_cap_limits": limits,
            "controls": controls,
            "matrix_max_error_V_per_V": max(matrix_errors),
            "unique_native_cases": 6,
            "native_executions": 7,
        },
        indent=2,
    )
)
```

## 5. Exit and next action

The **design target is selected; the factory stack is not yet released**. Keep
the nine-location coupling group OPEN for the confirmed geometry and E1 result.
A pilot risk review may recommend retaining that copper for the LIMITED E1
experiment, but this document does not make that release decision or widen E1
into electrode/high-Z qualification. E1 failure, unresolved fixture floor or
unacceptable confirmed geometry triggers a combined rework/review, not nine
automatic edits. Existing targeted layout guards stay active.

Next independently actionable source work is **#48 capacitor lifecycle and
effective-capacitance closure**, while the prepared factory/fixture questions
remain on #45. Do not spend another slice merely restating undefined inputs:
use E1 and the named target. If a vendor response is unavailable, retain the
specific unknown tolerance fields and continue other finite design decisions;
never report them confirmed. Actual fixture design, firmware external-mode
review and physical tests follow their existing gates. No order, purchase,
fabrication, powered connection or body use is authorized.

## Primary references checked on 2026-09-30

[1] JLCPCB named stackups, 1.6mm/1oz/0.5oz table:
https://jlcpcb.com/impedance
[2] JLCPCB calculator guide (page states updated Sep16,2026), material and
calculation parameters: https://jlcpcb.com/help/article/user-guide-to-the-jlcpcb-impedance-calculator
[3] JLCPCB laminated structures (page states updated Apr24,2025), pressed versus
raw thickness and finished copper: https://jlcpcb.com/help/article/multi-layer-pcb-standard-laminated-structures
[4] JLCPCB rigid capabilities, thickness/trace/hole constraints:
https://jlcpcb.com/capabilities/pcb-capabilities/
[5] TI ADS1299-x SBAS499C, pp9,17,23,25-26,38,46 (tables/equations inspected as page
images): https://www.ti.com/lit/ds/symlink/ads1299.pdf

The stack page has no immutable revision/commit identifier. Its inspected
values and contradictions are retained in the checkpoint, not represented as
a dated factory drawing. Only public primary sources were used for technical
facts. Source-only changes in this PR require their own exact-head CI/review;
baseline and analysis passes do not validate a later head.
