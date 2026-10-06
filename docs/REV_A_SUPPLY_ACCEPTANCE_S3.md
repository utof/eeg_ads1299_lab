# S3 supply acceptance worksheet — conditional arithmetic, not a release

**Decision:** collect bounded evidence for the complete source/feed/return loop
before choosing a supply, widening copper or approving operation. The editable
worksheet is `studies/s3_acceptance.json`; the exact executable block below
reports voltage intervals, lower/upper margins and missing terms. All 21 physical
terms start **unknown**, not zero. The eight output rows are consequently
indeterminate. There are no physical measurement records in this template.

S2 is merged as `188d954a4546d945f825008a723e4ad345e96fc3`. The worksheet's
immutable input baseline is its reviewed head `319f685439fa5ed7c34eeabf44537d48fbddcd90`,
tree `b17c00d67a95594ddfeda4d6973d78173dd5f4b5`, identical to that merge.
Nine committed inputs, including BOTH boards, are checked against their original
Git bytes and SHA256s. Source history is required; a bare ZIP is not provenance.
S1/S2 sensitivity examples remain historical hypotheses, not accepted limits.
No circuit, PCB, firmware, BOM, cable, component, dependency or approval change.

## 1. Use explicit measurement reference points

Let P0/G0 be the selected external source's output terminals; P1/G1 are auxiliary
J105.1/J105.2 at a specified metal reference surface. Never silently use chassis,
USB/computer ground or an arbitrary plane point as G1. The following path terms
are **end-to-end intervals**, not sums of every conductor visible on a net.
Account for uncertainty, temperature, mode, loading and contacts in their bounds.

| JSON term (all volts) | Physical definition / evidence boundary |
|---|---|
| `source_error` | Actual P0-G0 minus the 4.95–5.05 V target envelope; signed accuracy, regulation and observation uncertainty not already included elsewhere. The target is a requirement, not a supply measurement. |
| `common_pair` | (P0-G0) minus (P1-G1): both common source leads and defined interfaces, including the common RETURN once. Source internal regulation belongs in source_error, not here too. |
| `afe_5v_feed` | P1 minus AFE R11.1: auxiliary branch copper, K1 5-V conductor/interfaces and AFE pre-R11 feed. No K1/C4 return term in this row. |
| `r11` | AFE R11.1 minus R11.2 under the actual analog-plus-sense branch current. Initial 1% resistance tolerance alone does not bound temperature or load. |
| `avdd_distribution` | R11.2 minus the relevant ADC analog-supply pin; bound every required pin, including AVDD1. One capacitance pad is not all supply pins. |
| `g_analog` | Relevant ADC analog-return potential minus G1: K1/C4 sharing AND distributed ground offsets. Positive subtracts from delivered analog voltage. |
| `regulator` | AFE U2.5 minus U2.2: actual TPS7A20 output range with valid input, load, temperature and regulation conditions. Not an ideal fixed 3.3 V. |
| `dvdd_local_feed`, `g_digital` | U2.5 minus ADC DVDD pin; ADC DGND minus U2.2, respectively. Both subtract. Check both DVDD pins and relevant digital returns. |
| `dvdd_feed_U102/3/4` | U2.5 minus the named buffer pin14, including AFE feed, C4.2 contacts/wire and shared auxiliary supply copper. Each endpoint includes its common upstream loss; do NOT add the three complete path losses together. |
| `g_U102/3/4` | U2.2 minus that buffer pin7. Positive ADDS to its supply relative to its own ground. Not necessarily equal to g_analog with opposite sign. |
| `mcu_3v3` | MCU-side actual local 3.3-V range from its own regulator, including its 5-V branch and load/return effects. The ADC regulator does not supply it. |
| `dvdd_sense`, `g_dvdd_sense` | U2.5 minus U106.1; U2.2 minus U106.5. Sense loss subtracts, ground conversion adds. Neither is the downstream buffer supply. |
| `avdd_sample` | AFE J3.4 minus the selected AFE analog reference point. Distinct from worst ADC pin voltage; document that reference point. |
| `avdd_sense`, `g_avdd_sense` | AFE J3.4 minus U107.1; the same selected AFE reference minus U107.5. Include monitor/bleed and instrument loading. |

The exact analog identity is:

`V_AVDD = V_target + source_error - common_pair - afe_5v_feed - r11 - avdd_distribution - g_analog`

The exported digital identity is:

`V_buffer_i = regulator - dvdd_feed_i + g_i`

Every ground quantity is signed. A common-return loss already inside common_pair
must not be charged again to g_analog. Conversely, g_analog must not vanish merely
because source ground and board ground have the same schematic net name. S2's
boundary rule remains `I_G = I_5Vin - I_DVDDout + I_signal_DC` under its declared
DC port accounting. Parallel returns need actual conductances; distributed nodes
and transient return currents are not solved by that two-node approximation.
No fixed "two of twelve wires" split is accepted here.

## 2. Acceptance rows and honest results

| Worksheet output | Window / interpretation |
|---|---|
| AVDD at the ADC | Existing E1 requirement **4.75–5.25 V**, across all required analog pin pairs. Use encompassing intervals, not an average over pins. |
| Local ADC DVDD | Existing C3 **3.0–3.6 V analysis envelope**, with local feed/ground losses included. |
| DVDD at U102/U103/U104 | Three separate **3.0–3.6 V analysis-envelope** checks. |
| MCU local 3.3 V | Same C3 analysis-envelope screen; not a new DevKit operating specification or regulator model. |
| U106/U107 sensed rails | **Diagnostic only; no acceptance window.** The TPS3703 threshold is not the E1 limit or a meter at every load. |

For a predicted interval [L,H] and required [A,B], report margins [L-A,B-H].
Both nonnegative means ONLY that the supplied interval is contained in that
window. A negative margin means containment is not demonstrated; it need not
prove a particular physical unit fails. An unknown term makes the voltage and
margins unknown and lists the missing ID. Invalid/nonfinite/reversed bounds fail,
even when some other term is unknown. Correlation is not assumed away: summing
independent endpoints can be conservative; shared-path double-counting is still
a modelling error, not "extra safety". Measurement uncertainties must be included
once in the input intervals. No root-sum-square reduction without a justified
statistical measurement model.

**A filled worksheet never changes physical_qualification=false.** The template
accepts only unreviewed hypotheses and contains no measured-data approval path.
A later evidence-backed revision needs source, test conditions, uncertainty,
assembly identity and review; a positive margin alone cannot certify evidence.
C3's logic-high/low budgets also depend on the DIFFERENCE between the transmitting
and receiving grounds, not merely each supply being inside 3.0–3.6 V. Preserve
its conditional 24 mV disabled-low margin and unresolved leakage assumptions.
The default-disabled firmware, startup, partial rails, peak excursions and
power-loss response remain separate blockers. Mean S2 current is not peak current.

### Useful allowance, before inventing missing values

At the source target's low end (4.95 V), the E1 lower limit (4.75 V) leaves
200 mV. At an ASSUMED analog branch current of 10 mA and R11's initial +1%
value (10.1 ohm), 101 mV is consumed: **99 mV remains for ALL other signed losses
and errors**. A hypothetical 110 mV common-pair loss alone yields 4.739 V,
even with the other losses optimistically zero. This is a counterexample to
"the source says 5 V, therefore the ADC gets enough voltage", not a measurement
or a new maximum cable-resistance specification. It is distinct from S1's
94.867 mV example, which also charged specific illustrative board-trace losses.

Do not assign all 99 mV to the source cable: K1 contacts, board losses, ground
shifts, source error and current/tolerance uncertainty still need allocations.
Do not copy the 5 mA/buffer S1 assumption or S2's external-only mean current into
a field labelled operating maximum. Regulator load/thermal/headroom evidence,
full-mode current envelopes and the shared-source MCU peaks are still missing.

## 3. Evidence collection plan — no assembly is to be energized now

| Required record | What must be bounded / retained |
|---|---|
| Source and common pair | Source model/serial and settings, allowed modes/temperature, source-terminal accuracy/load regulation; total MCU+AFE+auxiliary current range; common outgoing and return lead/interface resistance with exact sense surfaces. Do not confuse the profile's 1 A source capacity with measured current. |
| Detached K1 cable | Identify all 20 conductors by continuity; independently record the pin17 feed and EACH of ten ground conductor resistances, including the specified mated interfaces. Keep signal identity/shorts checks. No conductor-count sharing assumption. |
| Detached C4 cable | Five 1:1 conductors, cavity6 empty at both ends. Record each conductor/interface resistance separately; label pin2 feed, pin3/4 sense, pin1/5 return. Test while detached: common board nets conceal swaps and parallel paths. |
| Board feed and return | Vendor copper/plating bounds and temperature plus current partition. Existing centerline squares are a geometry approximation, not a plane resistance extraction. Bound ground-node DIFFERENCES or record them with simultaneous local/remote observations later. |
| Regulator and modes | Check U2 input headroom, output tolerance, dissipation and load conditions; separately bound MCU branch. Enumerate parked, startup/configuration, steady acquisition and fault/shutdown; retain mean, peak and bandwidth/time context rather than one timeless scalar. |
| Measurement chain | Instrument ID/calibration, range, resolution, total accuracy/uncertainty, input loading, offset compensation, test current/compliance, temperature, fixture/contact boundary, mating cycles and raw repeated readings. Resolution is not accuracy. |

A four-wire resistance meter applies current through force leads and observes
voltage with separate sense leads, reducing lead-drop error [1]. It still injects
a test signal and can alter contact conditions or heat the specimen. **"Unpowered"
is not permission to put a low-ohms tester across assembled IC rails.** Initial
resistance work is a proposed detached-passive-harness method only: disconnected
from BOTH boards and every power/USB/source, with absence of stored voltage
verified and fixture/test current/open-circuit compliance reviewed first. No
numeric test current or voltage is selected here; do not assume a meter's default
range is compatible. No hipot, megohmmeter or high-voltage insulation test.

Place sense connections so the intended mating contact/crimp resistance is
included, while unintended fixture leads are excluded or independently budgeted.
Record both polarities/offset compensation where supported and meaningful [1];
do not use current reversal across semiconductor paths. Characterize contact
repeatability and temperature under the selected procedure, not just one best
reading. A detached conductor's resistance is not a distributed return network.

For later, separately approved person-disconnected powered validation, record
**simultaneously** P0/G0, P1/G1, ADC analog/digital pin-pair voltages, local regulator
output, each buffer pin14/pin7, MCU rail, and the monitor inputs versus their own
grounds. Record source/branch current and ground shifts in the SAME mode and time
window. Different sequential readings across changing loads cannot close KVL.
Fast peaks need a specified instrument bandwidth/trigger/uncertainty plan; DC
windows do not qualify transients. Differential/isolated instrumentation and
its common-mode ratings/loading require review: a scope/USB/shield return must
not bridge C1's HOST/TARGET isolation. Test shunts can add burden and change the
very current sharing under study. No actual powered protocol is authorized here.

## 4. Reproduce the worksheet

Run the block from the repository root through the locked environment. With no
argument it reads the committed template; an optional JSON path supports
labelled hypothetical scenarios. Input-source hashes and fixed circuit recipes
still apply. It neither runs native CAD nor accesses instruments. The executable
block and its JSON/tests are bound into the existing schematic-gate snapshot.

```python
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from tools.dc_budget import voltage_bounds

path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("docs/studies/s3_acceptance.json")
m = json.loads(path.read_text())
assert m["schema"] == "S3-conditional-windows-v1"
assert m["scope"] == "conditional_signed_DC_intervals_not_a_release"
assert m["physical_qualification"] is False
assert m["evidence_status"] == "unreviewed_hypotheses_only"
assert m["measurement_records"] == []  # this template contains no physical results
assert m["source_commit"] == "319f685439fa5ed7c34eeabf44537d48fbddcd90"
assert m["source_tree"] == "b17c00d67a95594ddfeda4d6973d78173dd5f4b5"
assert (
    subprocess.check_output(
        ["git", "rev-parse", m["source_commit"] + "^{tree}"], text=True, timeout=5
    ).strip()
    == m["source_tree"]
)
inputs = {
    "hardware/rev_a/board_profile.json",
    "hardware/rev_a/bom.json",
    "hardware/rev_a/auxiliary/contract.json",
    "hardware/rev_a/service_c4.json",
    "hardware/rev_a/layout/rev_a.kicad_pcb",
    "hardware/rev_a/auxiliary/auxiliary.kicad_pcb",
    "docs/studies/s1_supply_paths.json",
    "docs/studies/s2_current_return.json",
    "docs/REV_A_AUXILIARY_C3.md",
}
assert set(m["input_sha256"]) == inputs
for name, digest in m["input_sha256"].items():
    current = Path(name).read_bytes()
    original = subprocess.check_output(["git", "show", m["source_commit"] + ":" + name], timeout=5)
    assert current == original and hashlib.sha256(current).hexdigest() == digest, name
p = json.loads(Path("hardware/rev_a/board_profile.json").read_text())
assert not any(p["gates"].values()) and not p["afe"]["external_dummy_mode_enabled"]
a = p["power"]
v, tol = a["external_source_nominal_v"], a["external_source_tolerance_fraction"]
source_target = (v * (1 - tol), v * (1 + tol))
avdd_required = (a["avdd_operating_min_v"], a["avdd_operating_max_v"])
digital_analysis = (3.0, 3.6)  # existing C3 ANALYSIS envelope, not complete logic acceptance
# A correction factor -1 reverses BOTH endpoints; all quantities are signed DC intervals.
specs = {
    "AVDD": (
        source_target,
        {
            "source_error": 1,
            "common_pair": -1,
            "afe_5v_feed": -1,
            "r11": -1,
            "avdd_distribution": -1,
            "g_analog": -1,
        },
        avdd_required,
    ),
    "DVDD_AFE": (
        (0.0, 0.0),
        {"regulator": 1, "dvdd_local_feed": -1, "g_digital": -1},
        digital_analysis,
    ),
    "MCU_3V3": ((0.0, 0.0), {"mcu_3v3": 1}, digital_analysis),
    "DVDD_SENSE": ((0.0, 0.0), {"regulator": 1, "dvdd_sense": -1, "g_dvdd_sense": 1}, None),
    "AVDD_SENSE": ((0.0, 0.0), {"avdd_sample": 1, "avdd_sense": -1, "g_avdd_sense": 1}, None),
}
for ref in ("U102", "U103", "U104"):
    specs["DVDD_" + ref] = (
        (0.0, 0.0),
        {"regulator": 1, "dvdd_feed_" + ref: -1, "g_" + ref: 1},
        digital_analysis,
    )
assert set(m["bounds_V"]) == {term for _, terms, _ in specs.values() for term in terms}


def window(base, terms, required):
    signed = {}
    for name, sign in terms.items():
        raw = m["bounds_V"][name]
        assert raw is None or (isinstance(raw, list) and len(raw) == 2)
        pair = None if raw is None else tuple(raw)
        voltage_bounds(pair, {})  # validate original ordering/type, before applying sign
        signed[name] = pair if pair is None or sign == 1 else (-pair[1], -pair[0])
    bounds = voltage_bounds(base, signed)
    margins = (
        None
        if bounds is None or required is None
        else (bounds[0] - required[0], required[1] - bounds[1])
    )
    return {
        "voltage_V": bounds,
        "margins_V": margins,
        "required_V": required,
        "missing_terms": [key for key, value in signed.items() if value is None],
    }


# An independently stated sensitivity, NOT a new bound or substitution into the ledger.
bom = json.loads(Path("hardware/rev_a/bom.json").read_text())
r = next(row["spec"] for row in bom["line_items"] if row["id"] == "analog_feed")
rmax = r["resistance_ohm"] * (1 + r["tolerance_fraction"])  # initial tolerance ONLY
remaining = source_target[0] - avdd_required[0] - 0.010 * rmax
print(
    json.dumps(
        {
            "windows": {name: window(*spec) for name, spec in specs.items()},
            "hypothesis_only": {
                "remaining_before_all_other_losses_V": remaining,
                "with_assumed_110mV_common_loss_V": source_target[0] - 0.010 * rmax - 0.110,
            },
            "physical_qualification": False,
        },
        indent=2,
        sort_keys=True,
    )
)
```

## Next bounded task

Resolve the source/current evidence for ONE named steady-acquisition setup:
create the exact vendor/measurement questions needed to bound total MCU and
exported DVDD loads, source regulation/common-pair loss, and ground offsets.
Do not rebuild this worksheet or reselect hardware. Obtain actual specified
conditions or a separately reviewed empirical envelope before allocating the
remaining voltage margin. Keep peak/startup/fault and physical qualification
open if evidence cannot bound them. No supplier messages have been sent.

No purchase, fabrication, powered-connection or body-use flag changes. Keep
#45/#48, unresolved reference regions, stackup, capacitors, fixture, mechanical
fit and delivered-budget requirements open. The 94.84 USD AFE planning figure
is not a delivered auxiliary/cable/carrier/instrumentation total.

[1] Keithley/Tektronix, Low Level Measurements Handbook, sections 3.3.1–3.3.4:
four-wire low resistance, offsets, non-ohmic contacts and self heating. Official
web text inspected 2026-10-06; no instrument settings inferred from this guide.
https://www.tek.com/en/documents/product-article/keithley-low-level-measurements-handbook---7th-edition
The circuit limits and initial resistor tolerance come from the nine bound
repository inputs and their existing primary-reference records, not new limits.
