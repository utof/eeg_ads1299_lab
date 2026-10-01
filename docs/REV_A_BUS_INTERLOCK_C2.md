# C2 nine-line bus interlock: pin-level architecture candidate

Decision, 1 October 2026. Base `99bafcea6b3fa518e76704061daf722aae539360`,
tree `1448f9179fffaa43431053b4383ba9cc80fa98f2`. PCB SHA256 remains
`dfe893f958128ba28eb69188cf6debbbc9fcafa0ef5dd67bd58627d4b8a26842`.
This is a candidate auxiliary circuit and prospective firmware contract, **not
an installed interlock, native schematic, actual rail-fault experiment or a
release of the unchanged directly connected AFE**. All current gates stay false.

## Decision and bounded next step

Use three **TXU0304PWR** dual-supply directional buffers, actual-rail window
supervision and a **fresh-edge arm latch** as the C2 architecture target. This
removes intentional direct driver-to-unpowered-receiver paths when implemented
with the specified supply provenance. It does not make every ramp or abrupt
short safe. A useful fault detector must not be advertised as a universal
brownout interlock merely because a Boolean table passes.

**Next: native auxiliary C1+C2 schematic**, including physical actual-rail feeds/
sense terminations, bypasses, passive values and the loaded logic/timing checks
below. Keep the current AFE copper intact until an explicitly reviewed sense-
access change is justified. Then implement the guarded firmware handshake in a
separate failure-first change. Do not enable the existing firmware on a proposed
C2 assembly: it does not implement these new controls. This is not another
unbounded component search or a permission to wire a prototype now.

## 1. Receiver-powered signal paths

Three TI TXU0304PWR devices (PW, TSSOP-14) provide three A-to-B lanes and one
B-to-A lane each [1]. **Every VCCA is MCU_3V3 from DEVKIT.J1.2; every VCCB is
actual AFE_DVDD**, not common VIN5, HOST3V3 or the controller's regulator. Their
common ground is TARGET_GND. This bus is not galvanically isolated; C1's USB
console barrier remains separate and unchanged.

| Auxiliary device | A1.2 -> B1Y.13 | A2.3 -> B2Y.12 | A3.4 -> B3Y.11 | B4.10 -> A4Y.5 |
|---|---|---|---|---|
| BU1 | SCLK | MOSI | CS | MISO |
| BU2 | RESET | START | PWDN | DRDY |
| BU3 | CLKSEL | Unused | Unused | Unused |

Pin1=VCCA, pin14=VCCB, pin7=GND, pin8=BUS_OE; pins6/9 are NC. Tie BU3's unused
INPUTS3/4/10 to ground and leave unused OUTPUTS12/11/5 unconnected. Do not ground
an output. Each rail pin gets local 100nF bypassing. All nine signal destinations
remain the existing physical AFE/DevKit assignments; insert the directional
paths rather than swapping endpoints. The JSON retains all 42 buffer pins and
nine routes. Keep all20 K1 conductors and C1's separate5V branches/ground landings.

TXU's OE-low state is high impedance. Its isolation and partial-power-down
specifications cover stated off-supply conditions; Ioff is at most +/-2.5uA
when one supply is0V, the other0-5.5V and the port0-5.5V [1, pp8,21-23]. The
floating-supply current row is tested with ports at ground: do not extend that
number to arbitrary driven/floating pins. A receiver-powered output avoids
intentionally driving from the opposite live rail; local bypass energy, a
broken rail wire, ground loss, supply overshoot, intermediate rails and clamp
currents still require review. Hi-Z is not an actively driven zero.

Preserve the seven existing AFE10k pulldowns. Add two auxiliary10k pulldowns on
MCU MISO/DRDY after the reverse buffers and a100k BUS_OE pulldown. No pullup on
the AFE controls: the existing parked state is all seven low. Pull resistors
establish a static tendency, not an instantaneous discharge deadline.
**Loaded output margins remain an explicit schematic-release check:** the
TXU VCCO-0.1V VOH row is at0.1mA, whereas10k draws up to0.36mA at3.6V. Do not
claim that row proves the existing ADC/MCU high thresholds. Account for actual
receiver leakage, pull loading, capacitance, edge rate and ringing, or revise
the driver/passive choice under coordinated review. No resistor substitution
is made here. The11ns data and42ns disable maxima at the3.3V table's test loads
are component conditions, not the assembled cable's SPI or shutdown guarantee.

## 2. Actual rails, common control power and a fault that stays stopped

Select four TPS3703 window supervisors [2]: MON_M/MON_D use
**TPS3703A4330DSER** (3.3V nominal, +/-4% window), MON_A/MON_V use
**TPS3703A5500DSER** (5V nominal, +/-5% window). All four VDD pins use
**MCU_3V3**, the same local supply as the control logic, NOT the rail being sensed
or HOST power. This avoids a still-powered latch losing supervision solely
because common VIN5 has gone away. It is not proof of behavior with a floating
or partly powered MCU rail; SENSE-powered injection into a dead supervisor
supply is not established by its absolute ratings.

| Monitor | Pin1 SENSE | Electrical anchor; not an approved physical solder instruction |
|---|---|---|
| MON_M | MCU_3V3 | DEVKIT.J1.2 |
| MON_D | AFE_DVDD | AFE.C33.1 on the actual regulator-output net |
| MON_A | AFE_AVDD | AFE.C32.1 after the analog feed resistor |
| MON_V | TARGET_VIN5 | Common regulated5V source branch |

Every supervisor pin2=MCU_3V3, pin5=TARGET_GND, pin3 connects through10k to
MCU_3V3 (A-series fixed200ms nominal release delay), pin4 joins RAILS_OK, and
pin6 joins STOP_N. RAILS_OK has10k to MCU_3V3. STOP_N has10k to MCU_3V3 and a
normally open local STOP switch to ground. This does not certify a broken
stop-switch wire or a single-fault emergency-stop function. Each SENSE gets
100k to ground at the monitor so a disconnected sense wire tends low; sense
loading, filters and wire resistance enter the eventual accuracy/response budget.
Each monitor has local100nF bypass. There is no default claim that a voltage
measured at the fanout equals voltage at the device during a broken lead.

**There is no AFE_DVDD feed/sense contact in the current J1 cable.** J1.19 is
CLKSEL; J2's NC contacts remain NC. C33.1/C32.1 are verified net anchors, not
permission to hang wires on tiny capacitors. The auxiliary schematic must
explicitly provide mechanically supported, keyed rail-feed/sense access and
return. Any required AFE test pads/connector change needs a coordinated native
schematic/BOM/PCB/test review. Sense-only thin leads may not silently become
buffer supply-current paths; distinguish feed from remote sense in the drawing.

### Edge latch, not an automatic restart or a slow CMOS clock

Choose **SN74LVC2G74DCUR** for ARM_FF and two **SN74LVC1G97DBVR** devices for
CLEAR_AND and ARM_BUFFER [3,4]. All use MCU_3V3 and local100nF bypassing. The
latch is a single D flip-flop despite the2G name. Its non-Schmitt CLR/clock
inputs must not receive a slow open-drain or RC edge directly.

- CLEAR_AND: pins1/2=GND,3=SESSION,6=RAILS_OK,5=MCU_3V3,4=CLR_N. This is the
  manufacturer's Figure4 AND configuration, using Schmitt inputs.
- ARM_BUFFER: pins1/2=GND,3=ARM_REQ,6/5=MCU_3V3,4=ARM_CLK. The same AND with
  one input high conditions the prospective arm edge.
- ARM_FF: pin1=ARM_CLK,2=D=MCU_3V3,3=/Q=NC,4=GND,5=Q=BUS_OE,6=/CLR=CLR_N,
  7=/PRE=MCU_3V3,8=VCC=MCU_3V3. BUS_OE drives all three OE pins and ARMED readback.

This adds **13 auxiliary100nF requirements**: six buffer supply pins, four
supervisors and three logic devices. They are not part of the33AFE capacitors
or C1's separate two bypasses. Exact capacitor/resistor ordering codes, package
lands, placement and assembly recipe are not selected by a nominal value.

Prospective controller-only roles from the V1.1 physical J1 table [6]:
**SESSION GPIO14/pad20**, **ARM_REQ GPIO9/pad15**, **ARMED GPIO16/pad9** and **READY GPIO15/pad8**. They do
not overlap the existing nine bus GPIOs or application console17/18; they are
not the Octal-PSRAM-reserved35-37 pins. SESSION and ARM_REQ each get10k to ground.
READY reads the conditioned CLR_N output, not an assumed elapsed timer.
These are requirements for later firmware, not edits to the current profile,
GPIO map or default review-stop behavior. Verify actual owned board revision.

With valid control power and detector outputs settled, any RAILS_OK fault or
SESSION low asynchronously clears Q. Merely restoring supplies or releasing
SESSION does not set Q; **a new rising ARM edge is required**. Holding ARM high
across a fault is insufficient. Firmware must park all seven outputs low,
force ARM low, obtain the fresh startup acknowledgment, raise SESSION, observe READY continuously high for
at least10us, pulse ARM for at least10us and verify ARMED.
These chosen software margins do not replace measured edge/clear-recovery
requirements. Only explicitly reviewed code may do this. Every fault invalidates
the capture and timing interval; restart the complete sequence, not the last
packet. Monitor ARMED through blocking waits and transport, not only at entry.
Power-on FF state before a valid asynchronous clear and behavior below minimum
logic supply are not proved by the Boolean model.

## 3. Clock startup is downstream of bus enable, not its prerequisite

Do **not** make VCAP1 qualification or the completed valid-clock interval a
condition for enabling every bus lane. The existing sequence must first drive
PWDN and CLKSEL to start/enable the internal clock, then count the valid interval.
The published startup specifies2^18 valid clock cycles and VCAP1>1.1V before
reset; at nominal2.048MHz the interval is128ms [5, p70]. Existing firmware waits
150ms after raising PWDN/CLKSEL, then requests fresh measured VCAP1 confirmation,
then applies its4us reset-low/20us wait. No VCAP sensor or guaranteed clock/
capacitor-settling time is added by C2. Requiring completed clock startup before
enabling the lines that start it creates a dependency cycle.

Future integration therefore has phases: parked and disarmed; rails qualified
and fresh arm; enable bus while outputs remain low; raise the existing clock/
control levels; accumulate uninterrupted valid startup time and confirm VCAP1;
reset/configure; acquisition. Fault or SESSION low clears the hardware latch
and invalidates every later phase, including a partly elapsed timer. Analog
J2 sources must still meet the existing low-before/stable-supply fixture rules;
**nine digital buffers do not isolate analog inputs or make loss of AVDD with
DVDD alive a qualified ADC state**. E1 and all operating gates remain unchanged.

## 4. What the supervisor can and cannot guarantee

The selected TPS3703A CT connection gives140-260ms reset-release delay, after
startup and acceptable sensing. Startup delay is300us TYPICAL, with no maximum
in that table. The30us detect maximum is specified at **5% overdrive**, not
arbitrarily close to the trip threshold [2, pp6-7]. Do not sum it with small
logic delays and advertise an unconditional board shutdown time. RESET is also
not specified normally below its power-on-reset region. Filters, pulses too
short to detect, load and rail collapse may change behavior.

Using conservative +/-0.7% threshold-error and0.8% hysteresis envelopes gives:

| Nominal window | UV trip envelope, V | OV trip envelope, V | Inside worst hysteresis envelope, V |
|---|---|---|---|
| 3.3V +/-4% | 3.1449-3.1911 | 3.407976-3.456024 | 3.2175-3.380328 |
| 5V +/-5% | 4.715-4.785 | 5.21325-5.28675 | 4.825-5.170956 |

The reproducer uses the larger nominal/trip value as the error base to avoid
understating a tolerance; these are calculated conservative intervals, not new
manufacturer-tested limits. Wire/sense loading errors are not included. The5V
trip window can extend outside E1's4.75-5.25V requirement, while a rail at its
allowed low endpoint may not permit rearm. **RAILS_OK is not an E1 voltmeter or
performance pass**. It detects selected out-of-window conditions and helps block
startup; it does not widen E1 or guarantee starting everywhere in E1.

A concrete limit: 5% below the lowest calculated5V UV threshold is
`4.715 * 0.95 = 4.47925V`, already below E1's4.75V minimum. Thus the specified
30us test point cannot prove disconnection before E1 is violated. C2 retains
`universal_shutdown_deadline_us=null`; abrupt-short/any-ramp safety is **not
qualified**. If release requires a stated maximum fault trajectory, derive it
from specified detector overdrive, sensing error, decoupling/load and all
logic/output discharge delays, then verify it. Add hold-up/current limiting,
different supervision or a combined circuit revision if that bound cannot be
met; do not hide it behind a preferred power-switch sequence.

## 5. Reproduce source and Boolean checks

The following exact block uses the public harness API and a frozen native graph,
not a newly run KiCad export. It checks86 proposed IC pins, nine current routes,
actual rail-net anchors, prospective GPIO separation,256 settled control truth
rows, held-arm/SESSION fault histories and threshold arithmetic. It rejects an
automatic-restart alternative and eight corrupt architecture records. These are
**source/data/Boolean checks, not transistor-level simulation, fault coverage
for all times/voltages, new project tests or physical experiments**. Every
hardware and firmware implementation claim stays false. Run from the repository
root with the locked environment; no hardware or simulator is accessed.

```python
import copy
import gzip
import hashlib
import json
import math
from itertools import product
from pathlib import Path
import xml.etree.ElementTree as ET
from hardware.rev_a import bench_harness, load_documents, parse_schematic_xml

profile, bom, sources = load_documents()
xml = gzip.decompress(Path("tests/fixtures/rev_a_netlist.xml.gz").read_bytes()).decode()
harness = bench_harness(
    parse_schematic_xml(xml),
    profile,
    bom,
    sources,
    Path("firmware/esp32_ads1299_bench/bench_console.h").read_text(),
)
net_nodes = {
    n.attrib["name"]: {(x.attrib["ref"], x.attrib["pin"]) for x in n}
    for n in ET.fromstring(xml).find("nets")
}
checkpoint_path = Path("docs/checkpoints/20261001_bus_interlock_c2.json")
c = json.loads(checkpoint_path.read_text())
expected_lanes = [
    ("BU1", "SCLK", 2, 13),
    ("BU1", "MOSI", 3, 12),
    ("BU1", "CS", 4, 11),
    ("BU1", "MISO", 10, 5),
    ("BU2", "RESET", 2, 13),
    ("BU2", "START", 3, 12),
    ("BU2", "PWDN", 4, 11),
    ("BU2", "DRDY", 10, 5),
    ("BU3", "CLKSEL", 2, 13),
]


def latch_step(q, previous_arm, arm, rail_flags, session, rule):
    # Settled, valid control-supply Boolean behavior AFTER detector response.
    # Delays, unknown voltages, transistor behavior and input pulse shape are not modeled.
    good = all(rail_flags) and session
    if not good:
        return False
    if rule == "follow_good":  # Deliberately rejected automatic-restart alternative.
        return True
    assert rule == "rising_edge_only"
    return True if arm and not previous_arm else q


def check_latch(rule):
    count = 0
    for rails in product((False, True), repeat=4):
        for q, previous, arm, session in product((False, True), repeat=4):
            actual = latch_step(q, previous, arm, rails, session, rule)
            # Independent positive-edge D=1, asynchronous-clear truth condition.
            expected = all(rails) and session and (q or (not previous and arm))
            assert actual == expected
            count += 1
    # Detected fault while ARM remains held high, then rails recover: no new edge.
    q = latch_step(True, True, True, (True, True, False, True), True, rule)
    assert not q
    assert not latch_step(q, True, True, (True,) * 4, True, rule)
    # SESSION low clears even with otherwise healthy rails; its release is not ARM.
    q = latch_step(True, False, False, (True,) * 4, False, rule)
    assert not q and not latch_step(q, False, False, (True,) * 4, True, rule)
    assert latch_step(q, False, True, (True,) * 4, True, rule)
    return count


def thresholds(v, w):
    # Conservative envelopes: larger of nominal rail and trip used as error base.
    # Deliberately no inference about unlisted delay versus overdrive or wire error.
    uv0, ov0 = v * (1 - w), v * (1 + w)
    uv = [uv0 - 0.007 * max(v, uv0), uv0 + 0.007 * max(v, uv0)]
    ov = [ov0 - 0.007 * max(v, ov0), ov0 + 0.007 * max(v, ov0)]
    inside = [uv[1] + 0.008 * max(v, uv[1]), ov[0] - 0.008 * max(v, ov[1])]
    return dict(
        conservative_UV_trip_interval_V=uv,
        conservative_OV_trip_interval_V=ov,
        conservative_inside_hysteresis_interval_V=inside,
    )


def verify(data):
    assert data["decision"] == "C2"
    assert (
        data["pcb_sha256"]
        == hashlib.sha256(Path("hardware/rev_a/layout/rev_a.kicad_pcb").read_bytes()).hexdigest()
    )
    assert not any(profile["gates"].values()) and not profile["afe"]["external_dummy_mode_enabled"]
    assert not data["approval_changes"] and not data["hardware_tested"]
    assert {
        (x["buffer"], x["net"], x["input_pin"], x["output_pin"]) for x in data["routes"]
    } == set(expected_lanes)
    assert len(data["routes"]) == 9
    expected_pins = {
        u: {1: "MCU_3V3", 6: "NC", 7: "TARGET_GND", 8: "BUS_OE", 9: "NC", 14: "AFE_DVDD"}
        for u in ("BU1", "BU2", "BU3")
    }
    for route in data["routes"]:
        n = route["net"]
        r = next(x for x in profile["spi"]["signals"] if x["signal"] == n)
        group = next(g for g in harness if g.name == f"{n} / GPIO{r['gpio']}")
        afe, dev = f"AFE.J1.{route['afe_contact']}", f"DEVKIT.J1.{route['mcu_header_pad']}"
        assert set(group.endpoints) == {afe, dev} and route["mcu_gpio"] == r["gpio"]
        reverse = r["direction_from_mcu"] == "in"
        assert route["direction"] == ("AFE_to_MCU" if reverse else "MCU_to_AFE")
        pins = expected_pins[route["buffer"]]
        pins[route["input_pin"]] = ("AFE_" if reverse else "MCU_") + n
        pins[route["output_pin"]] = ("MCU_" if reverse else "AFE_") + n
    expected_pins["BU3"].update(
        {3: "TARGET_GND", 4: "TARGET_GND", 10: "TARGET_GND", 5: "NC", 11: "NC", 12: "NC"}
    )
    assert len(data["buffers"]) == 3
    assert {b["ref"] for b in data["buffers"]} == {"BU1", "BU2", "BU3"}
    for b in data["buffers"]:
        assert b["mpn"] == "TXU0304PWR"
        assert {int(k): v for k, v in b["pins"].items()} == expected_pins[b["ref"]]
    expected_monitors = [
        ("MON_M", "TPS3703A4330DSER", 3.3, 0.04, "MCU_3V3", "DEVKIT.J1.2"),
        ("MON_D", "TPS3703A4330DSER", 3.3, 0.04, "AFE_DVDD", "AFE.C33.1"),
        ("MON_A", "TPS3703A5500DSER", 5.0, 0.05, "AFE_AVDD", "AFE.C32.1"),
        ("MON_V", "TPS3703A5500DSER", 5.0, 0.05, "TARGET_VIN5", "SUPPLY.+5V"),
    ]
    assert len(data["supervisors"]) == 4
    for m, (ref, mpn, v, w, net, anchor) in zip(data["supervisors"], expected_monitors):
        assert (
            m["ref"],
            m["mpn"],
            m["nominal_v"],
            m["window_fraction"],
            m["sense_net"],
            m["sense_anchor"],
        ) == (ref, mpn, v, w, net, anchor)
        assert {int(k): val for k, val in m["pins"].items()} == {
            1: net,
            2: "MCU_3V3",
            3: "CT_10K_TO_MCU_3V3",
            4: "RAILS_OK",
            5: "TARGET_GND",
            6: "STOP_N",
        }
    assert ("C33", "1") in net_nodes["DVDD"] and ("C32", "1") in net_nodes["AVDD"]
    assert ("J1", "19") in net_nodes["CLKSEL"] and ("J1", "19") not in net_nodes["DVDD"]
    expected_logic = {
        "CLEAR_AND": (
            "SN74LVC1G97DBVR",
            {
                1: "TARGET_GND",
                2: "TARGET_GND",
                3: "SESSION",
                4: "CLR_N",
                5: "MCU_3V3",
                6: "RAILS_OK",
            },
        ),
        "ARM_BUFFER": (
            "SN74LVC1G97DBVR",
            {
                1: "TARGET_GND",
                2: "TARGET_GND",
                3: "ARM_REQ",
                4: "ARM_CLK",
                5: "MCU_3V3",
                6: "MCU_3V3",
            },
        ),
        "ARM_FF": (
            "SN74LVC2G74DCUR",
            {
                1: "ARM_CLK",
                2: "MCU_3V3",
                3: "NC",
                4: "TARGET_GND",
                5: "BUS_OE",
                6: "CLR_N",
                7: "MCU_3V3",
                8: "MCU_3V3",
            },
        ),
    }
    assert len(data["logic"]) == 3
    assert {g["ref"] for g in data["logic"]} == set(expected_logic)
    for g in data["logic"]:
        assert (g["mpn"], {int(k): v for k, v in g["pins"].items()}) == expected_logic[g["ref"]]
    # Independent manufacturer J1 numbering; proposed roles are NOT current firmware.
    expected_roles = {
        "SESSION": (14, 20, "out"),
        "ARM_REQ": (9, 15, "out"),
        "ARMED": (16, 9, "in"),
        "READY": (15, 8, "in"),
    }
    assert set(data["prospective_controller_roles"]) == set(expected_roles)
    assert data["ready_readback_net"] == "CLR_N"
    for key, role in data["prospective_controller_roles"].items():
        assert (role["gpio"], role["header_pad"], role["direction"]) == expected_roles[key]
        assert role["gpio"] not in {x["gpio"] for x in profile["spi"]["signals"]} | {17, 18}
    policy = data["policy"]
    assert policy["clear_rule"] == "any_detected_rail_fault_or_session_low"
    assert policy["supervisor_supply"] == "MCU_3V3"
    assert policy["clock_interval_starts_after_bus_and_clock_enabled"]
    assert policy["universal_shutdown_deadline_us"] is None
    for key in (
        "recover_without_fresh_edge",
        "requires_vcap_before_bus_enable",
        "external_analog_startup_protected",
        "monitor_is_E1_voltage_acceptance",
        "fast_short_or_arbitrary_ramp_qualified",
        "sense_backpower_at_supervisor_VDD_zero_qualified",
        "hardware_installed",
        "firmware_implements_C2",
        "powered_setup_permitted",
    ):
        assert policy[key] is False, key
    assert check_latch(policy["arm_rule"]) == data["analysis"]["state_truth_rows"] == 256
    for v, w in ((3.3, 0.04), (5.0, 0.05)):
        actual = thresholds(v, w)
        for k, vals in actual.items():
            saved = data["analysis"][f"{v:g}V"][k]
            assert len(vals) == len(saved) == 2 and all(
                math.isclose(a, b, abs_tol=1e-12) for a, b in zip(vals, saved)
            )
    five = thresholds(5.0, 0.05)
    counter = five["conservative_UV_trip_interval_V"][0] * 0.95
    assert math.isclose(
        counter, data["analysis"]["five_percent_below_lowest_5V_trip_V"], abs_tol=1e-12
    )
    assert counter < profile["power"]["avdd_operating_min_v"]  # 30us spec cannot certify E1.
    assert data["analysis"]["conditional_reset_release_ms"] == [140, 260]
    assert data["analysis"]["detect_max_us_at_five_percent_overdrive"] == 30
    assert (
        data["analysis"]["startup_delay_typ_us"] == 300
        and data["analysis"]["startup_delay_max_us"] is None
    )
    assert math.isclose(
        2**18 / profile["afe"]["clock_hz_nominal"] * 1000,
        data["analysis"]["nominal_ads_clock_wait_ms"],
    )
    assert data["analysis"]["existing_firmware_wait_ms"] == 150
    assert data["local_bypass_requirements"]["count"] == 2 * 3 + 4 + 3 == 13
    assert data["local_bypass_requirements"]["value_F"] == 1e-7
    assert data["resistor_requirements_ohm"] == {
        "BUS_OE_to_ground": 100000,
        "SESSION_to_ground": 10000,
        "ARM_REQ_to_ground": 10000,
        "RAILS_OK_to_MCU_3V3": 10000,
        "STOP_N_to_MCU_3V3": 10000,
        "each_CT_to_MCU_3V3": 10000,
        "each_SENSE_to_ground_at_monitor": 100000,
        "MCU_MISO_to_ground": 10000,
        "MCU_DRDY_to_ground": 10000,
    }


verify(c)
# Reject the automatic-restart alternative against the same explicit truth requirements.
try:
    check_latch("follow_good")
except AssertionError:
    pass
else:
    raise AssertionError("automatic recovery wrongly accepted")
changes = [
    ("wrong_buffer_rail", lambda x: x["buffers"][0]["pins"].__setitem__("14", "MCU_3V3")),
    ("wrong_reverse_direction", lambda x: x["routes"][3].__setitem__("output_pin", 13)),
    ("CLKSEL_as_sense", lambda x: x["supervisors"][1].__setitem__("sense_anchor", "AFE.J1.19")),
    ("missing_session_clear", lambda x: x["logic"][0]["pins"].__setitem__("3", "MCU_3V3")),
    ("unconditional_30us", lambda x: x["policy"].__setitem__("universal_shutdown_deadline_us", 30)),
    (
        "monitor_as_E1_pass",
        lambda x: x["policy"].__setitem__("monitor_is_E1_voltage_acceptance", True),
    ),
    (
        "circular_VCAP_gate",
        lambda x: x["policy"].__setitem__("requires_vcap_before_bus_enable", True),
    ),
    ("grounded_spare_output", lambda x: x["buffers"][2]["pins"].__setitem__("12", "TARGET_GND")),
]
for label, change in changes:
    bad = copy.deepcopy(c)
    change(bad)
    try:
        verify(bad)
    except AssertionError:
        pass
    else:
        raise AssertionError(label)
print(
    json.dumps(
        {
            "routes": 9,
            "IC_pins": 86,
            "truth_rows": 256,
            "corrupt_snapshots_rejected": len(changes),
            "automatic_restart_alternative_rejected": True,
            "5V_corners": thresholds(5.0, 0.05),
            "scope": "architecture/data checks; not native electronics or physical qualification",
        },
        indent=2,
    )
)
```

## Evidence, boundaries and primary references

Source capture36864384757 verified exact99bafcea/tree and original bundle.
The clean baseline ordinary gate passed1108tests+14subtests,86.31%branches with
71%floor unchanged. Native electronics/KiCad/S3 were not run locally in this
slice. Read this PR's actual final-head CI and independent review separately;
a baseline result or a pending run is not a final-head pass. Current source
has no auxiliary circuit, new sense wiring or C2 firmware implementation.

Ten proposed auxiliary ICs, thirteen bypasses, resistors, actual-rail harness
and assembly add unquoted cost beyond C1. The old$94.34 subtotal/$3 harness
reserve does not establish the user's$100 target. No part is purchased, a
supplier contacted, or a print/PCB released. Keep #45/#48, all prior physical
fit/capacitor/stackup/coupling/fixture requirements and all approval flags open.

Primary sources inspected 2026-10-01, including the stated pin/function/timing
figures and tables; ordering variants checked against TI product information:

[1] TI TXU0304, SCES935A, pp4,6,8,14,21-23:
https://www.ti.com/lit/ds/symlink/txu0304.pdf
[2] TI TPS3703, SBVS249B, pp3-7,17,19:
https://www.ti.com/lit/ds/symlink/tps3703.pdf
[3] TI SN74LVC2G74, SCES203Q, pp3,5-7,9:
https://www.ti.com/lit/ds/symlink/sn74lvc2g74.pdf
[4] TI SN74LVC1G97, SCES416N, pp3,5-6,9-10:
https://www.ti.com/lit/ds/symlink/sn74lvc1g97.pdf
[5] TI ADS1299, SBAS499C, p70:
https://www.ti.com/lit/ds/symlink/ads1299.pdf
[6] Espressif DevKitC-1 V1.1, J1 table, power alternatives and Octal-memory note:
https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide_v1.1.html

Original four-PDF capture36866281796 includes early unselected HCS74 research;
that part is NOT the C2 latch. The selected LVC pin/function sources above were
inspected separately. Supplier datasheets are not an endorsement of this entire
candidate circuit. A native schematic and a firmware build likewise will not
replace the missing physical rail-fault, continuity, pulse/load and bench tests.
