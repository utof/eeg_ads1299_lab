# S2: separate mode-dependent loads from return-current assumptions

Base main7325d659 (PR82), tree85b324a5445ca653afd16990311a04ccd9622ae5.
Source inputs and their byte hashes are in `studies/s2_current_return.json`.
**This is an accounting refinement, not current or power-fault qualification.**
No PCB, circuit, component value, firmware, cable, dependency or gate changes.

## Decision

Keep the existing copper. The fixed5mA/buffer S1 number is a sensitivity input,
not an established device maximum. First separate identifiable external loads,
internal switching, source/return distribution and peak/inrush behavior. S2 makes
those terms explicit and records UNKNOWN total-current ceilings, rather than
replacing the assumption with an equally unsupported precise-looking total.

Two practical corrections matter: a four-channel frame is15 bytes, not the27-byte
maximum allocated C array; and current exported on DVDD can re-enter the AFE on
its signal wires and return through AFE ground. Neither '1MHz continuously' nor
'all auxiliary current returns only on the C4 ground wires' describes the source.

## 1. What the current firmware actually schedules

For the reviewed hypothetical operating configuration, F1 reads3status bytes
plus3bytes per physical channel. ADS1299-4 therefore needs120clock cycles per
conversion. At nominal250SPS that is30000 rising clock edges/s, in1MHz bursts:
**3% clock-active time**, not continuous1MHz. With assumed equal clock phases,
SCLK is high1.5% of elapsed time. This is a healthy steady-state schedule, not a
startup, retry, glitch, overload, oscillator-tolerance or peak-current bound.

F1 clocks zero on MOSI during every frame read; physical START stays low because
commands control conversion. PWDN, RESET and CLKSEL are held high after startup.
CLKSEL is a static selection bit, NOT the2.048MHz internal oscillator output;
clock output is disabled. CS is high between frames; ignoring its additional
setup/hold/software-low time gives an upper high-time estimate of97% for this
ideal schedule. GPIO levels and the15-byte read are checked against the existing
source. The distributed BOARD_PROFILE_REVIEWED=false build stops before bus
setup; S2 does not run or enable an external acquisition.

For an ideal0/V output driving a resistor R and external capacitor C:

```
I_pull_mean = V/R * high_fraction
I_external_charge_mean = C * V * rising_edges_per_second
```

Use rising edges, not twice that number. Falling transitions dispose of charge
already supplied. These are average supply terms, not edge current or an RC/
transmission-line waveform model. A high static output draws resistor current
even without clock activity. Real VOL/VOH, cross-board ground shifts, receiver
leakage, internal switching and protection currents are separate terms.

The illustrative case uses3.6V high,42.2k-1%=41.778kohm and100pF external load
per used output. The100pF is NOT a measured or manufacturer maximum;3.6V is the
chosen across-load value, not a proof of voltage during a ground shift. Only
seven existing forward pulls are counted against the B-side source. MISO/DRDY
outputs atU102.5/U103.5 and R114/R115 are powered by the **MCU A-side rail**, not
another pair of B-side output loads. Their current must enter the MCU budget.

| Ideal scenario | Seven forward pull currents | External charging | Interpretation |
|---|---:|---:|---|
| Armed, quiet controls | 344.68uA | 0 | Four static highs; no frame clocks |
| Healthy nominal acquisition | 343.39uA | 10.89uA | CS/SCLK duty above,100pF assumed |
| During continuous SCLK burst alone | 43.08uA | 360uA | Clock only,50%duty; excludes other pins |

These do not include all supply current. In particular, the last row must not
be multiplied by3% and then used as a peak-current limit. Capacitor charging
has a much shorter time scale than the average over a burst or conversion.

## 2. What the datasheets do and do not bound

TI TXU0304 SCES935A p8 specifies6uA maximum per supply over-40..125C under
static rail-level input and zero-output-load conditions; its combined-current
row also has6uA maximum. Adding independent per-rail maxima would be conservative
but double-counts the combined bound. Neither row is an active loaded ceiling.
The p16 Cpd entries (at3.3V,13pF transmitting output side/2pF input side) are
TYPICAL at25C,10MHz,1ns edges and unloaded outputs. Do not promote them to
worst-case switching current in this cable/PCB. They are deliberately not added
to the example as a purported maximum. [1]

ADS1299-4's4.06mA analog and0.54mA digital entries are TYPICAL. The24mW maximum
power row has stated5V/3.3V, external-clock,250SPS,gain12 conditions; the selected
F1 gain24/internal-clock case is not that complete test condition. S1's10mA
analog/2mA digital allocations remain unqualified until coverage is established,
not replaced by those typical numbers. Startup/reference-cap charging is separate.
The digital-input +/-10uA entry also prevents omitting receiver-current terms. [2]

TPS3703 p6 has7uA maximum VDD current, but that is not its external bleed or
RESET-pull current: SENSE draws separately, and each asserted common pull is
counted once, not four times for four open-drain outputs. The four CT resistors,
manual-STOP pull/internal pulls, SESSION/ARM/OE pulls and two reverse-channel pulls
must also be allocated by state. [3] The DevKit total (CPU, memory, regulator,
LEDs/bridge and any enabled radio), ISO7721 side currents and digital switching
are not measured by this study. Host-side USB current must not be added to AFE
DVDD merely because both appear in the auxiliary schematic.

The JSON keeps total-operating, startup-peak, load-capacitance and internal-dynamic
maxima as null. A null is missing evidence, **not zero**. No mode is marked qualified.

## 3. Follow current through all boundary ports

S1's cancellation observation is useful only with its load-location assumption:
current going5V→AFE regulator→auxiliary supply cancels at the AFE boundary when
it is consumed and returns on the auxiliary. It does NOT cancel a static output
current which travels back to an AFE pulldown through an input signal wire.
For the simplified two-node steady-periodic example:

```
I_ground_export = I_5V_in - I_DVDD_feed_out + I_signal_DC_back
I_5V_in = I_AFE_local + I_DVDD_feed_out
=> I_ground_export = I_AFE_local + I_signal_DC_back
```

Any additional AVDD/DVDD sense export belongs in both incoming-source accounting
and the outgoing-port ledger; do not quietly count it as local AFE consumption.
The example's I_AFE_local=12.05mA explicitly means current returning locally on
AFE ground, not all loads on that rail. Its additional3mA auxiliary-local load is
arbitrary and cancels in this identity. Increasing that remote load changes
forward voltage loss but not this lumped ground-export result. In the ideal
capacitive steady state, net signal-lead charge over a whole cycle is zero;
charging and discharge currents must not be counted as a second DC ground load.
Distributed high-frequency returns, low-state sinking, leakage and incomplete
startup cycles are NOT described by this simplification.

Ten K1 returns plus two C4 returns are parallel only under an equipotential
endpoint approximation. For each branch R_j:

```
dG = I_ground_export / sum(1/R_j)
I_j = dG/R_j
```

The helper accepts a signed export. This is not a plane-resistance extraction,
and other shared-ground drops must not be included twice. It does not infer that
all twelve physical conductors share equally or that a broken return is safe.

At S1's30C copper hypothesis, C4's155mm/0.205mm2 wire is13.752mohm. Two mating
contacts at20mohm each plus the unchanged unqualified20mohm end-effect allowance
give73.752mohm **per conductor**, not per whole two-wire loop. JST's20mohm is after
its specified environmental tests; it is not a guarantee for an unqualified
crimp, board solder joint or different mating process. Its3A catalog rating uses
22AWG and does not certify the selected24AWG assembly. [4]

With ten K1 branches each ASSUMED0.1ohm and two C4 branches as above, KCL sends
about21.33% of net DC return through C4, not2/12=16.67%. The ground shift is
about0.0975mV for the example; this is not an actual-board bound. Four-wire cable
measurements and local plane/connector characterization must replace the assumed
branch resistances. The much larger shared source lead/ground loss from S1 still
needs its own current/tolerance budget; these tiny illustrative return values
do not close it or justify reallocating C3's24mV disabled-low margin.

## 4. Reproduce the source-bound example

Run this one block from the locked checkout root with its Git history. It checks
current bytes against the original committed input bytes and recorded hashes; no CAD, instrument or hardware is accessed. The output
is an accounting record with qualification=false, not an operating permission.


```python
import hashlib, json, re, subprocess
from pathlib import Path
from tools.dc_budget import switched_load, parallel_returns

m = json.loads(Path("docs/studies/s2_current_return.json").read_text())
assert m["qualification"] is False
assert all(value is None for value in m["uncertainty"].values())
assert re.fullmatch(r"[0-9a-f]{40}", m["source_commit"])
assert (
    subprocess.check_output(
        ["git", "rev-parse", m["source_commit"] + "^{tree}"], text=True, timeout=5
    ).strip()
    == m["source_tree"]
)
for name, digest in m["input_sha256"].items():
    current = Path(name).read_bytes()
    original = subprocess.check_output(["git", "show", m["source_commit"] + ":" + name], timeout=5)
    assert current == original and hashlib.sha256(current).hexdigest() == digest, name
f, output = m["firmware"], m["ideal_output"]
assert f["channels"] == 4 and f["default_review_gate"] is False
frame_bits = 8 * (f["status_bytes"] + f["bytes_per_channel"] * f["channels"])
clock_rises = frame_bits * f["sps_nominal"]
busy = clock_rises / f["spi_hz_nominal"]
rmin = output["pull_nominal_ohm"] * (1 - output["pull_tolerance_fraction"])
voltage, cap = output["high_v"], output["capacitance_per_output_F_assumed"]
# Healthy steady acquisition ONLY: no startup/configuration clocks, retries or glitches.
# Equal clock phases and nominal sample/bit rates are hypotheses. CS high time is
# an upper estimate because it omits the setup/hold/software time while CS is low.
quiet = {"SCLK": 0, "MOSI": 0, "CS": 1, "RESET": 1, "START": 0, "PWDN": 1, "CLKSEL": 1}
active = dict(quiet, SCLK=busy * f["sclk_active_high_fraction_assumed"], CS=1 - busy)
rises = {
    name: (clock_rises if name == "SCLK" else f["sps_nominal"] if name == "CS" else 0)
    for name in quiet
}
rows = {}
for mode, duty, frequency in (
    ("armed_quiet", quiet, dict.fromkeys(quiet, 0)),
    ("steady_acquisition", active, rises),
):
    per_pin = {
        name: switched_load(voltage, rmin, duty[name], cap, frequency[name]) for name in quiet
    }
    per_buffer = {
        ref: sum(
            sum(per_pin[name]) for name, row in m["forward_outputs"].items() if row["buffer"] == ref
        )
        for ref in ("U102", "U103", "U104")
    }
    rows[mode] = {
        "pull_A": sum(p[0] for p in per_pin.values()),
        "external_charging_A": sum(p[1] for p in per_pin.values()),
        "by_buffer_external_only_A": per_buffer,
        "total_operating_max_A": None,
    }
# Quiescent supply-current maxima do not turn the above switching model into a max.
a = json.loads(Path("docs/studies/s1_supply_paths.json").read_text())["assumed"]
h = m["return_example"]
rho = a["rho20_ohm_mm2_per_m"] * (1 + a["alpha_per_C"] * (a["temperature_C"] - 20))
c4 = (
    rho * h["C4_wire_m"] / a["wire_area_mm2"]
    + h["C4_contact_pairs_per_wire"] * h["C4_contact_ohm_each_after_catalog_tests"]
    + h["C4_end_effect_ohm_total_assumed"]
)
returns = {f"K1-{i}": h["K1_return_ohm_each_assumed"] for i in range(h["K1_return_count"])}
returns.update({f"C4-{i}": c4 for i in range(h["C4_return_count"])})
pull = rows["steady_acquisition"]["pull_A"]
charging = rows["steady_acquisition"]["external_charging_A"]
# KCL at the AFE BOUNDARY. Auxiliary B-side output pull current re-enters the AFE
# on the signal leads and goes to its ground. Ideal capacitor signal current has
# zero net charge over a complete periodic cycle; it is not a second DC ground load.
# Additional source-sense exports must be counted in BOTH 5V input and outgoing ports.
local = h["local_AFE_ground_load_A_assumed"]
remote = h["remote_internal_and_bleed_A_assumed"]
feed_out = remote + pull + charging
vin_in = local + feed_out
ground_export = vin_in - feed_out + pull
shift, branch_currents = parallel_returns(returns, ground_export)
result = {
    "frame_bytes": frame_bits // 8,
    "clock_rises_per_s": clock_rises,
    "spi_clock_busy_fraction": busy,
    "modes": rows,
    "return_example": {
        "C4_each_ohm": c4,
        "AFE_5V_in_A": vin_in,
        "AFE_DVDD_export_A": feed_out,
        "signal_DC_into_AFE_A": pull,
        "AFE_ground_export_A": ground_export,
        "AFE_minus_AUX_ground_V": shift,
        "branch_A": branch_currents,
    },
    "qualification": False,
}
print(json.dumps(result, indent=2, sort_keys=True))
```

## Disposition and next bounded task

No supply-qualified release follows from this slice. The deterministic F1/pull
terms and return KCL are now explicit; internal dynamic/peak loads and physical
series/ground terms remain unbounded. Next make ONE source/cable/return acceptance
worksheet: allocate the existing AVDD/DVDD limits to the current hypotheses with
unknown terms explicit, and specify de-energized four-wire checks plus future
simultaneous local/remote voltage/current observations needed to replace them.
Obtain a vendor bound or separately reviewed empirical operating envelope for
unknown mode/peak currents before using the worksheet for a release decision.
Do not buy a supply, energize an assembly, widen traces or insert generic parts
from this study. Keep #45/#48, stackup, component, mechanical and fault requirements.
All fabrication, purchasing, powered-connection and body-use gates are unchanged.

## Primary references inspected 2026-10-04

[1] https://www.ti.com/lit/ds/symlink/txu0304.pdf (SCES935A, pp8,16)
[2] https://www.ti.com/lit/ds/symlink/ads1299.pdf (SBAS499C, pp10,11)
[3] https://www.ti.com/lit/ds/symlink/tps3703.pdf (SBVS249B, p6)
[4] https://www.jst-mfg.com/product/pdf/eng/eXH.pdf (catalog p1)

TI table images were inspected from the fixed primary-download artifact after
web rendering failed for several pages; the PDF byte hashes and capture run are
recorded in the input JSON. JST p1 was inspected through the web page image.
The capture job is reference/source transport, not project tests. Copyrighted
manufacturer files are not project dependencies or redistributed source.
