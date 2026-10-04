# S1 supply-and-return DC budget: conditional, not a release

Source baseline: merged PR81 main `f6932ead58c1d02af145de405312a7f885dbb010`,
tree `a1bb3a16687c65f736de9c2634bb5ec2e4b990ac`. Both PCB byte hashes and the
native route inventory are bound in `studies/s1_supply_paths.json`. No copper,
component, firmware, cable selection, dependency or approval flag changes here.

**Decision:** do not widen traces or declare a supply pass merely from total
net length. Account for shared branch current, both boards, cable/contact loss
and the SIGN of the ground offset. Under the explicit 5 mA-per-buffer example,
the farthest digital-feed loss is about **3.56 mV**, not the **1.34 mV** obtained
by incorrectly loading every segment with that one sink's current. That does
not establish the actual load or voltage. The larger unresolved allowance is
the shared source/return and local ground distribution, not this small computed
feed loss alone.

The 0.5 A-controller example leaves only **95.0 mV** for all still-unmodeled
feed/return losses and errors before AVDD falls below the existing 4.75 V E1
minimum. Allocating that entire remainder to a common source/return pair would
allow at most **0.180 ohm**, with NOTHING left for other unknowns. That ceiling
is a sensitivity result, not a newly approved cable/ground specification.

## 1. The complete loop, and where sensing stops

The current source enters auxiliary J105.1. Its branches feed the MCU through
J102.21 and the AFE through J101.17, the K1 cable and AFE J1.17. On the AFE,
TPS7A20 supplies local DVDD and sends the auxiliary's B-side supply back through
J3.2, the C4 cable and J104.2. U102/U103/U104 share portions of that final feed.
The local analog rail is separately behind R11 (10 ohm). J3.3 carries DVDD sense
and J3.4 carries AVDD sense. They are not feedback regulators at the remote loads.

Ground is not one magic zero-volt wire. Ten K1 returns and two C4 returns provide
parallel AFE/auxiliary connections; MCU and source returns also share auxiliary
ground copper. Do not silently place all buffer current in the two C4 returns,
assume equal sharing across twelve wires, or calculate a plane's resistance from
its shortest drawn line. In a simplified two-ground-node DC model, the AFE's
net ground export is its LOCAL analog/digital consumption plus regulator ground
current: the remote-buffer current enters the AFE on 5 V and leaves on DVDD.
Spatial plane drops and other wiring complicate that useful KCL observation.

Define `dG = G_AFE - G_AUX`, with the AFE reference at the source/regulator ground:

```
V_DVDD_at_aux = V_DVDD_local + dG - forward_DVDD_drop
V_sensed_aux  = V_DVDD_local + dG - sense_wire_drop
V_AVDD_local = V_source - shared_loss - AFE_5V_feed_loss - dG - I_analog * R11
```

Use compatible reference points when supplying these terms; `shared_loss` must
not already include `dG`. A positive dG raises the auxiliary reading while
lowering local AFE voltage relative to the same auxiliary-referenced source.
A separately sensed source can therefore look acceptable while a downstream
feed has sagged. It does not continuously measure voltage at every buffer pin.
Broken feed/sense/return behavior and transient latch operation remain separate
C2/C3 physical questions, not solved by this arithmetic.

## 2. Native geometry versus a resistance hypothesis

The read-only `tests/supply_inventory_probe.py` runs only in the pinned KiCad
9.0.2 Python process. It traces 17 specified endpoint pairs along exact track
centerlines, split at incident endpoints, with native via/PTH links. It fails
rather than inventing a path when only a copper-width/pad-area connection exists.
The current selections are not general DRC or arbitrary-net path extraction.
No board is saved or refilled by this probe, and no ground-plane impedance is
extracted. Prior PR81's ERC/DRC results are not a new native DRC run here.

The selected supply paths are grouped by their downstream sinks. The same
oriented section must have the same root prefix; reconvergent/cyclic path sets
are rejected. Common segments then carry the sum of their downstream currents,
not each load separately. This is a **centerline-tree approximation**: it omits
parallel copper conductance, current spreading in pads and distributed load
locations. Local ADC DVDD current is explicitly lumped at C33.1. The two boards'
GND planes are not replaced by zero-ohm edges in that model.

| Selected path | Planar length, mm | Via transitions |
|---|---:|---:|
| AFE U2.5 to J3.2 | 14.088 | 0 |
| Aux J104.2 to U102.14 | 33.266 | 1 |
| Aux J104.2 to U103.14 | 50.500 | 1 |
| Aux J104.2 to U104.14 | 67.500 | 1 |
| Aux J105.1 to J101.17 (AFE 5 V) | 16.637 | 0 |
| Aux J105.1 to J102.21 (MCU 5 V) | 60.530 | 0 |
| Aux J105.1 to U108.1 (VIN monitor) | 38.573 | 1 |

PTH layer changes are counted separately in the JSON; zero via transitions does
not mean no barrel resistance. Planar lengths exclude vertical barrel length.
The VIN monitor lies on a path sharing MCU-feed copper: its sense pin is not
an ideal measurement of J105's source terminal under load.

### Explicit material/assembly assumptions, not vendor minima

Use rho20=0.0175 ohm mm2/m, alpha=0.00393/K, T=30 C; front/back copper35um and
inner copper18um; via full length1.6mm, finished bore0.30mm and plating20um.
These are illustrative parameters, NOT the unconfirmed factory stackup or
plating guarantees. Via resistance uses the annular cylinder area, not a solid
0.30mm copper rod. Model every traversed PTH transition with an additional
5 milliohm assumption; this is not inferred from a drilling diameter.

C4 uses its maximum target length155mm and an assumed24AWG copper area0.205mm2.
JST's catalog lists contact resistance10 milliohm initially and20 milliohm after
its environmental tests [1]. The example uses20 milliohm at EACH of two mating
interfaces per conductor, plus20 milliohm TOTAL additional unqualified series
allowance for crimps/solder/end effects. That extra allowance is not a supplier
bound. The catalog's3A rating is stated with22AWG, not evidence for arbitrary
24AWG assemblies. Neither cable nor actual crimp process is qualified.

```
R_trace = rho(T) * sum(length_mm / width_mm) / (1000 * copper_thickness_mm)
R_wire  = rho(T) * length_m / copper_area_mm2
R_via   = rho(T) * (length_mm/1000) / [pi*((bore/2 + plating)^2 - (bore/2)^2)]
```

## 3. Quantitative sensitivities, not a component-current prediction

The two cases use1mA or5mA for EACH of the three buffer B-side loads,36uA for
R116 and2mA for all other DVDD-related consumption lumped at C33,
INCLUDING the separate sense branch for this example (not2mA plus an omitted
sense bleed). These are assumed currents. TI's
microamp TXU quiescent-current entries are measured with no output load and
specified input states [2]; they cannot be used as an active switching/load
budget. Capacitor charging, reverse-channel output loads, pull currents,
frequency/duty/load capacitance and regulator dissipation need mode-specific
accounting before any maximum-current statement.

| Assumed B-side current per buffer | U102 feed loss | U103 feed loss | U104 feed loss |
|---|---:|---:|---:|
| 1mA | 0.643mV | 0.702mV | 0.732mV |
| 5mA | 3.112mV | 3.410mV | 3.557mV |

With nominal local3.300V and dG swept from-20mV to+20mV, the high-load farthest
pin becomes3.276443..3.316443V before other omitted effects. A source-sense wire
with an assumed0.1mV loss instead reports3.2799..3.3199V. This illustrative
signed-offset sweep is NOT a claim that the actual return drop reaches20mV.
The TPS7A20 DBV output tolerance is+/-1.5% under its stated voltage/current and
temperature conditions [3]; at3.3V that alone is49.5mV each way. Nominal3.300V
is not a guaranteed lower bound, and the regulator table is not a complete
board-level load/thermal/startup or stopped-state qualification.

### Existing 5 V and analog budget

Hold the source at the profile's4.95V lower target, analog current at its10mA
planning budget including AVDD-sense loading, auxiliary B-side current at3x5mA, all other DVDD-related consumption at2mA including its sense branch, and assume
50uA regulator ground current. Total assumed AFE5V current is27.086mA. The VIN
monitor and its bleed are modeled as1uA and52.5uA loads. These are scenario
allocations, not datasheet maxima or measured operation.

| Assumed MCU5V current | Aux drop toward AFE | Aux drop toward MCU | Loss at VIN monitor input | Remaining AVDD allowance* |
|---|---:|---:|---:|---:|
| 0.100A | 1.531mV | 12.122mV | 7.802mV | 96.867mV |
| 0.500A | 3.531mV | 60.053mV | 38.455mV | 94.867mV |

*After nominal100mV across R11 and a1.602mV lumped estimate for the AFE5V trace;
before source-lead drop, K1 contacts/wire, return distribution, ground offset,
R11 tolerance and all omitted errors. Loading the complete selected AFE input
trace with all AFE current overestimates its branch-only current **within the
chosen resistive-tree approximation**, not a physical upper bound including
missing effects. The source/input capacity is not a guarantee of MCU burst
behavior. These constant-current examples must not be conflated with the
conductance loads/transient model in `lab.rev_a_supply`, which is unchanged.

At0.500A MCU load,0.20ohm of hypothetical common source-plus-return resistance
would lose105.428mV, already exceeding94.867mV. The corresponding optimistic
AVDD example is4.739439V before the other omitted losses: below E1's4.75V.
This is a conditional counterexample, not an observed hardware failure. Reducing
only the short DVDD feed cannot recover that common-path loss. Specify and
measure the total source/return budget before deciding which copper or cable to
change. A local supervisor reading or DRC0 does not waive this requirement.

## 4. Reproduce, and keep assumptions visible

The small `tools.dc_budget` API does KCL/KVL accounting for explicit nonnegative
loads on rooted paths plus signed reference conversion; it does not silently
solve meshes or infer hardware assumptions. Unit cases use independently
calculated circuits, invalid inputs and shared-path controls. This complements,
not replaces, the existing conductance/transient study. No new orchestration or
dependencies were introduced. The shared schematic gate now snapshots the
inventory script, native test and geometry/assumption JSON and runs the native
snapshot check. Changing any during verification invalidates the evidence.

Run the ordinary/native selections through the existing locked environment:

```sh
uv run --locked --all-extras python -m pytest tests/test_dc_budget.py tests/test_supply_inventory.py -q
```

The second file requires native KiCad9.0.2 Python (`KICAD_PYTHON`, default
`/usr/bin/python3`). This snapshot test is not a fresh DRC or physical test.
The probe also requires repository Git history containing the pinned PR81
baseline. It reads that commit's actual tree and both original board blobs and
compares the current board bytes before and after capture. The JSON's
`source_commit`/`source_tree` identify that geometry baseline, NOT the current
study implementation or a new test run. A future intentional board change
requires a new, independently verified baseline and study review; regenerating
the JSON alone cannot attribute new geometry to this old source. A source ZIP
without the required Git history cannot supply this provenance and must fail.
The following accounting block uses only the recorded explicit assumptions:

```python
import json, math
from pathlib import Path
from tools.dc_budget import tree_drops, remote_voltages

m = json.loads(Path("docs/studies/s1_supply_paths.json").read_text())
a = m["assumed"]
rho = a["rho20_ohm_mm2_per_m"] * (1 + a["alpha_per_C"] * (a["temperature_C"] - 20))
via = (
    rho
    * a["via_length_mm"]
    / 1000
    / (math.pi * ((a["via_bore_mm"] / 2 + a["via_plating_mm"]) ** 2 - (a["via_bore_mm"] / 2) ** 2))
)


def resistance(g):
    return (
        sum(rho * g[layer + "_squares"] / (1000 * a[layer + "_mm"]) for layer in ("F", "In2", "B"))
        + g["vias"] * via
        + g["PTH"] * a["PTH_extra_ohm"]
        + rho * g["wire_m"] / a["wire_area_mm2"]
        + g["contact_pairs"] * a["contact_pair_ohm"]
        + g["extra_ohm"]
    )


Rs = {k: resistance(g) for k, g in m["dvdd"]["groups"].items()}
paths = {k: tuple(v) for k, v in m["dvdd"]["paths"].items()}
print("rho", rho, "via", via, "dvdd", Rs)
rows = []
for each in (0.001, 0.005):
    loads = {
        k: (0.002 if k == "local_at_C33" else 0.000036 if k == "R116.1" else each) for k in paths
    }
    d = tree_drops(Rs, paths, loads)
    wrong = {k: sum(Rs[e] * loads[k] for e in p) for k, p in paths.items()}
    rows.append(
        {
            "buffer_A_each": each,
            "local_AFE_DVDD_assumed_A": 0.002,
            "R116_A": 0.000036,
            "feed_losses_V": d,
            "wrong_per_path_load_only_V": wrong,
        }
    )
    print(rows[-1])
vinRs = {k: resistance(g) for k, g in m["vin5_aux"]["groups"].items()}
vinpaths = {k: tuple(v) for k, v in m["vin5_aux"]["paths"].items()}
print("VIN resistances", vinRs, "paths", vinpaths)
results = []
for imcu in (0.100, 0.500):
    iafe = 0.010 + 0.002 + 0.015 + 0.000036 + 0.000050
    loads = {"J101.17": iafe, "J102.21": imcu, "U108.1": 0.000001, "R108.1": 0.0000525}
    d = tree_drops(vinRs, vinpaths, loads)
    # All AFE input current through K1 5V cable/AFE route; R11 only analog10mA.
    r_analog = next(r for r in m["geometry"] if r["board"] == "AFE" and r["to"] == "R11.1")
    worst5trace = (
        rho
        * (
            r_analog["F_squares"] / (1000 * a["F_mm"])
            + r_analog["other_squares"] / (1000 * a["B_mm"])
        )
        + r_analog["vias"] * via
        + r_analog["PTH"] * a["PTH_extra_ohm"]
    )
    # Lump all AFE current on full path overestimates branch loading under tree hypothesis;
    # separate source harness/controller return losses are handled below, not hidden as0.
    d_local_allow = iafe * worst5trace
    r_shared_max = (4.95 - 4.75 - 0.100 - d["J101.17"] - d_local_allow) / (iafe + imcu + 0.0000535)
    results.append(
        {
            "MCU5V_A": imcu,
            "AFE5V_A": iafe,
            "aux_5V_losses_V": d,
            "AFE_input_trace_lumped_loss_V": d_local_allow,
            "headroom_V_for_ALL_other_feed_return_and_errors": 4.95
            - 4.75
            - 0.100
            - d["J101.17"]
            - d_local_allow,
            "shared_source_series_R_upper_if_all_other_losses_zero_ohm": r_shared_max,
        }
    )
    print(results[-1])
res = {
    "hypothetical_DVDD_load_cases": rows,
    "hypothetical_5V_load_cases": results,
    "rho_at_model_temp": rho,
    "via_resistance_ohm": via,
    "resistances_DVDD_ohm": Rs,
    "resistances_VIN_aux_ohm": vinRs,
    "no_qualification_result": True,
}
print(json.dumps(res, indent=2))
```

### Review corrections before acceptance

PR82 review found two real defects: the printed accounting block had an extra
indent, and regenerating the native inventory could keep old source identities
while measuring an edited board. Three new cases failed before correction: the
actual fenced Python block, and geometry-neutral byte edits to each of the two
boards in independent Git clones. The block now runs under an ordinary regression
and reproduces the reported numerical examples; the native probe verifies the
recorded commit/tree and original Git board bytes before emitting any inventory.
A rejected source does not produce replacement JSON. The baseline identities
remain the same because no board bytes changed. These are code/provenance checks,
not new physical measurements or approval of the assumptions.

A further review found that the selected AFE input-path calculation omitted its
one recorded PTH transition despite declaring a 5 milliohm allowance for every
such transition. A term-isolation regression sets trace/via resistivity to zero
ONLY in a disposable accounting input, leaving that 5 milliohm term. The old
calculation returned zero loss instead of 0.027086A * 0.005ohm = 0.13543mV.
The corrected expression includes the recorded PTH count; all reported headrooms
now include the additional 0.13543mV. The high-MCU example is94.866653mV, with
an optimistic shared-loop ceiling of about0.179965ohm, not the superseded
95.002083mV/0.180222ohm. The earlier original run/quoted intermediate values are
historical evidence, not an alternative accepted result. The initial new test
used a JSON-validation helper incorrectly; that harness error was corrected and
the actual omitted-term failure observed before the equation was fixed.

## Disposition and next bounded step

**Supply/return qualification remains open.** Next derive mode-specific currents
from the actual F1 waveform/duty and both sides' output loads, then allocate the
source/K1/C4/contact/return budget using factory copper and complete wiring.
Include four-wire resistance/contact inspection and simultaneous local/remote
voltage measurement in the future person-disconnected bench procedure, not an
instruction to energize now. A ground reference on a scope can change the return
network; C1 isolation and test-equipment grounding must remain explicit.

Keep the C3 disabled-low/leakage margin separate: the24mV calculation cannot be
freely assigned to all interboard offsets without following that signal's local
pull and receiver references. Rapid power loss, regulator/fault response, physical
latch behavior, analog-source exposure, #45/#48 and stackup/capacitor/mechanical
requirements stay open. No procurement, fabrication, powered-connection or body
permission changes. The two routed PCBs are untouched.

### Primary references inspected 2026-10-04

[1] JST XH catalog p1, contact-resistance and stated wire conditions:
https://www.jst-mfg.com/product/pdf/eng/eXH.pdf
[2] TI TXU0304 SCES935A p8, loaded outputs and conditional quiescent current:
https://www.ti.com/lit/ds/symlink/txu0304.pdf
[3] TI TPS7A20 SBVS338H p6, DBV voltage tolerance, load and ground-current conditions:
https://www.ti.com/lit/ds/symlink/tps7a20.pdf
The selected production process and operating currents are not established by
these component tables. Copper/temperature/current examples above remain
explicit assumptions and no vendor assembly quote is implied.
