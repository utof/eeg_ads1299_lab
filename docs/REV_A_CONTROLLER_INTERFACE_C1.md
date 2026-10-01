# C1 controller termination and split-powered application console

Decision record, 1 October 2026. Source main
`2b11ddec03a4fad97f6dbec2f00675fe5a48c09c`, tree
`8b9b175d35f652abe8867f6891827e99040c128d`. PCB SHA256
`dfe893f958128ba28eb69188cf6debbbc9fcafa0ef5dd67bd58627d4b8a26842`.

**Choose a captive, soldered controller fanout and an Adafruit CP2102N Friend
(product 5335) plus TI ISO7721DR, powered independently on its two sides, for
the application console. This is the C1 architecture target, not built hardware.**
It replaces the unspecified external UART adapter with a concrete design route.
The required auxiliary schematic/layout and assembly are not authored here;
no part has been added to the AFE BOM, ordered or connected. No firmware, circuit,
CAD, Python dependency or approval gate changes. The ledger and finite power-state
analysis are in `checkpoints/20261001_controller_interface_c1.json`.

**Important remaining blocker: the nine AFE-to-controller digital signals are
still direct connections between independently regulated 3.3-V domains.** This
USB-console barrier does not protect those signals during an AFE or MCU rail
failure. The next hardware decision must address that bus and analog-rail
startup, not declare the whole system safe because the console is isolated.

## 1. Controller cable termination, without another loose-pin harness

Retain the selected K1 cable `IDSD-10-S-04.00-T-G-ST4`, its AFE socket captured
in K2, all twenty conductors and the current electrical pin map. Select a fixed,
numbered solder fanout supported next to the separately supported DevKit.
Each identified conductor gets its own insulated landing `FAN.C01` through
`FAN.C20`; the number identifies the AFE contact proved by continuity, NOT a
color or an assumed ribbon ordering. The ten ground tails each have a separate
landing on the fanout's common return bus. Do not stuff ten wires into one
DevKit pad or leave uninsulated tinned ends loose.

Fanout signal leads terminate permanently at the specified DevKit header-tail
pads, with independent cable restraint and insulation from neighboring pads.
This choice eliminates a second loose, unkeyed plug from the initial controller
termination. It does not waive soldering/access/strain qualification or make
an unsupported solder joint a cable anchor. A small fanout/isolator board may
implement it, but its copper layout and mechanical mounting remain to be designed
with the rail-loss solution. No generic stripboard or breadboard is released.

| AFE.J1 contact / fanout landing | Function | Destination after fanout |
|---|---|---|
| 1 / C01 | SCLK | DEVKIT.J1.18 (GPIO12) |
| 3 / C03 | MOSI | DEVKIT.J1.17 (GPIO11) |
| 5 / C05 | MISO | DEVKIT.J1.19 (GPIO13) |
| 7 / C07 | CS | DEVKIT.J1.16 (GPIO10) |
| 9 / C09 | DRDY | DEVKIT.J1.4 (GPIO4) |
| 11 / C11 | RESET | DEVKIT.J1.5 (GPIO5), NOT DevKit EN |
| 13 / C13 | START | DEVKIT.J1.6 (GPIO6) |
| 15 / C15 | PWDN | DEVKIT.J1.7 (GPIO7) |
| 17 / C17 | AFE regulated 5-V feed | SUPPLY.+5V branch to AFE, not MCU 3.3 V |
| 19 / C19 | CLKSEL | DEVKIT.J1.12 (GPIO8), NOT a DVDD sense lead |
| 2,4,...,20 / C02,C04,...,C20 | Ten individual ground conductors | TARGET.GND_BUS; SUPPLY.RETURN and DEVKIT.J1.22 |

The power source branches separately to AFE.C17 and DEVKIT.J1.21. The MCU
current must not be routed through the AFE cable/feed resistor/regulator. Keep
signal/return adjacency to the fanout, minimize exposed fanout length, and record
actual length and routing for signal-integrity review. The logical ground-bus
membership is not a proof of its impedance or current rating.

AFE J2 remains a different, mechanically coded cable: contacts1-8 are the four
differential dummy inputs,9 is BIAS-after-1M,10 is return,11-20 are NC. Before
external-input release, cap each unused free end independently; in particular,
leave the BIAS output separately insulated and do not turn NC contacts into a
power/sense harness. No J2 conductor goes to the controller by this decision.
The earlier analog source/startup fixture requirements still apply.

Before permanent socket capture or soldering, inspect actual board revision and
contact numbering from both mating and solder views, then record a full
contact-to-tail continuity matrix and shorts check. Repeat after assembly and
an unpowered cable-retention test. Free ends, tails and exposed header pins need
insulation/guards; K2 only models the AFE end. Full socket seating must retain
K1's existing insertion margin. No live hot plugging or forced mating.

## 2. Exact console boundary and supply provenance

Select **Adafruit CP2102N Friend, product5335**, not the discontinued CP2104 or an
unspecified CP2102 clone [1,2]. Its published Eagle schematic at commit
`1c29f780bdc7503e18c8b6d29d1f8fb7cc1510bb`, blob
`62b31c86dc915b4632b9f943c0a2c92f8c3f4a17`, connects IC1 VIO/VDD and JP4.2
on the same 3.3-V net. JP1.4 is TXD, JP1.5 RXD, JP1.1 GND; **JP1.3 is USB
5 V, not the 3.3-V reference** [2]. Confirm the actual supplied revision and
labels before soldering. An assembled-board change invalidates this pin evidence.

`ISO` below means the selected **ISO7721DR, D-package 8-pin SOIC, non-F** [3].
The non-F default-high option is appropriate for an idle UART. Do not substitute
ISO7720, ISO7721F, a 16-pin package or a carrier with joined grounds/power.

| ISO pin, top-view pin numbering | C1 connection | Power domain |
|---|---|---|
| 1 VCC1 | HOST.JP4.2 (3V output; same net as USB bridge VIO) | Host USB only |
| 2 OUTA | HOST.JP1.5 (RXD) | Host |
| 3 INB | HOST.JP1.4 (TXD) | Host |
| 4 GND1 | HOST.JP1.1 (GND) | Host |
| 5 GND2 | TARGET.GND_BUS / DEVKIT.J1.22 | Target |
| 6 OUTB | DEVKIT.J1.10 (GPIO17 application RX) | Target |
| 7 INA | DEVKIT.J1.11 (GPIO18 application TX) | Target |
| 8 VCC2 | DEVKIT.J1.2 (MCU's own 3.3 V) | Target only |

Add local100nF bypass `CH` between pins1/4 and `CT` between8/5, following TI's
layout guidance [3]. These are two auxiliary requirements, not part of the
existing33-capacitor AFE count; exact bypass MPN/land/process remain unselected.
No isolated DC/DC is needed: each side is powered by the domain whose signals
it handles. Never power VCC2 from AFE DVDD or USB-derived power, and never join
HOST.GND to TARGET.GND on this interface. No supply jumper may leave a powered
UART driver attached to an unpowered/floating same-side isolator VCC.

The old `INTERFACE` endpoints in `REV_A_BENCH_HARNESS.md` now have a precise
interpretation: `TX_3V3=ISO.6`, `RX_3V3=ISO.7`, `GND=ISO.5`, all on the TARGET
side. That preserves the existing generated worksheet and firmware mapping.
It does **not** extend its common-ground row to the USB bridge's host ground.
VCC2 is an additional target-local bypass supply, not an adapter power output
being fed into the target. No production harness API changed.

Leave HOST5V,CTS,RTS,DTR,DSR,DCD,RI,reset/GPIO and both DevKit USB sockets out
of the target connection. Configure460800baud,8N1, no hardware/software flow
control, no automatic reset. The CP2102N's advertised3Mbaud is a nominal
capability, not tested460800-baud delivery, latency or absence of dropped frames
[1,4]. Do not repurpose GPIO43/44: the onboard DevKit bridge is already attached
there. Programming initially remains DevKit-only via its onboard USB-UART, with AFE,
external5-V supply and the entire C1 target interface disconnected [5]. The
permanent-tail choice has a service cost: program and inspect the DevKit BEFORE
attaching those tails. Later return to that bare-board programming arrangement
requires removing all accessory tails, not merely unplugging hostUSB. No
in-place USB programming of the soldered assembly is approved here. A future
removable full-row controller adapter may replace this laborious service path,
but needs its own orientation/retention/process review before changing C1.

The USB-C receptacle belongs to the HOST5335 module only. During a future reviewed
acquisition, use the existing external5-V source for the target, both DevKit USB
sockets disconnected/guarded. A VBUS-cut USB cable is not the selected workaround.
The interface must be supported outside K2, with controlled domain clearance,
no conductive mounting bridge, and independently restrained cables. A USB scope,
generator earth, shield or other accessory can create an external ground bypass;
review the whole bench. The component's isolation rating does not certify this
adapter or the EEG system for medical/body use, mains insulation or any safety
standard. No isolation voltage test or powered assembly is authorized here.

## 3. What happens when power is missing

TI Table8-2 calls a supply powered up at >=2.25V and powered down below1.7V;
the intervening range is undetermined [3,p25]. The following is a logic/domain
analysis at stable rail endpoints, NOT a transient/back-power simulation:

| Host-side supply | MCU/target-side supply | At MCU RX (ISO.6) | At host RX (ISO.2) |
|---|---|---|---|
| Up | Up | Host data or idle | MCU data or idle |
| Down | Up | Default high | Undetermined (own supply down) |
| Up | Down | Undetermined (own supply down) | Default high |
| Down | Down | Undetermined | Undetermined |

**Undetermined does not mean high impedance.** Do not claim that a powered-down
output is guaranteed Hi-Z or that brownout produces a clean UART frame. TI also
warns that a driven input can weakly power a floating local VCC through an input
protection diode. Shared driver/isolator supply provenance prevents intentionally
creating that local mismatch; it is not a proof against broken supply wiring,
decoupler discharge differences or internal failures. The galvanic signal
barrier avoids the intentional DC signal-wire path between host and target;
parasitic/transient leakage, installation errors and external ground paths
remain physical verification items.

USB disconnect/suspend/reset and target power loss invalidate capture. Stop,
retain the record and restart via the approved startup procedure; do not credit
a default idle level as proof of stable rails or a completed R/V acknowledgment.
USB suspend current/behavior and device configuration require actual module/host
verification. Host3V must remain within the validated operating range; no USB
bus-power or suspend compliance is inferred just from the module's regulator.

At a shared host3.1-3.6V rail, the published CP2102N VOH>=VIO-0.7 and VOL<=0.6
meet ISO input thresholds0.7VCC/0.3VCC; ISO VOH>=VCC-0.3 and VOL<=0.3 meet
CP2102N VIH>=VIO-0.6/VIL<=0.6 under their stated load conditions [3,4]. The
smallest calculated host high margin is0.23V; low margins are0.33/0.30V.
This is static same-rail compatibility, not edge/ringing, target-GPIO, cable or
brownout qualification. Reserve5mA per isolator domain for design budgeting;
TI lists3.4mA maximum DC-low and2.8mA at1Mbps with15pF loads under the3.3-V
conditions. The CP2102N regulator's100mA limit includes its OWN current [4,p12].
Check actual regulator load, capacitance and USB suspend budget before use.

### The separate AFE rail-loss blocker remains

There are seven MCU-driven signals: SCLK,MOSI,CS,RESET,START,PWDN,CLKSEL. MISO
and DRDY run the other way. They connect directly between the MCU's3.3-V rail
and the AFE TPS7A20's separate DVDD rail; sharing an upstream5-V source does not
make the regulators rise, fall or fail together. A high signal into an off rail
can exceed the receiver's input-voltage limit. A pulldown or software reset is
not an automatic isolation switch, and an operator's R/V acknowledgments do
not monitor later rail loss. AVDD failure with DVDD alive is a further ADC
power-state problem, not covered by isolating the console [5,6].

The checkpoint enumerates16 stable combinations of host/MCU/DVDD/AVDD presence.
It names the seven or two possibly driven-into-off-receiver paths and flags
mismatched ADC rails. This is conservative exposure accounting: it does not
assert that every named transmitter is actually high, model clamp current,
prove the other combinations harmless or cover partial ramps. Every row keeps
`powered_setup_permitted=false`. Host rail presence is not USB enumeration.

**Next hardware decision:** a fail-closed AFE bus/power-sequencing interface
covering all nine signals and the AVDD/startup conditions, or a separately
reviewed limited pilot-risk disposition. It must use the actual required rails,
not VIN as a proxy. AFE.J1.19 is CLKSEL, NOT DVDD; no DVDD sense lead is available
there. Adding a sense test point/lead, supervisor, isolation/buffering or any
new pad assignment requires an explicit coordinated electrical design review.
Do not hide a sense wire on J2 NC or rely on a normally ordered power switch to
handle an independent regulator failure. Do this before committing an auxiliary
fanout board layout; it may need to contain the eventual hardware interlock.

## 4. Reproduce the ledger and finite power-state checks

Run the following exact block from the repository root in the locked environment.
It uses the public harness API and a frozen exported schematic graph; that is
source consistency, not a fresh KiCad or physical continuity run. It compares
the C1 ledger with independently declared ISO7721 pins and stable-state rules.
Invalid-snapshot checks are analysis controls, not added project tests.

```python
import copy
import gzip
import hashlib
import json
from itertools import product
from pathlib import Path
from hardware.rev_a import bench_harness, load_documents, parse_schematic_xml

p, b, s = load_documents()
xml = gzip.decompress(Path("tests/fixtures/rev_a_netlist.xml.gz").read_bytes()).decode()
h = bench_harness(
    parse_schematic_xml(xml),
    p,
    b,
    s,
    Path("firmware/esp32_ads1299_bench/bench_console.h").read_text(),
)
c = json.loads(Path("docs/checkpoints/20261001_controller_interface_c1.json").read_text())
expected_groups = {
    "HOST_3V3": {"HOST.JP4.2", "ISO.1", "CH.1"},
    "HOST_GND": {"HOST.JP1.1", "ISO.4", "CH.2"},
    "HOST_TX": {"HOST.JP1.4", "ISO.3"},
    "HOST_RX": {"ISO.2", "HOST.JP1.5"},
    "TARGET_3V3": {"DEVKIT.J1.2", "ISO.8", "CT.1"},
    "TARGET_GND": {
        "TARGET.GND_BUS",
        "DEVKIT.J1.22",
        "SUPPLY.RETURN",
        "ISO.5",
        "CT.2",
        "INTERFACE.GND",
    },
    "TARGET_RX": {"ISO.6", "DEVKIT.J1.10", "INTERFACE.TX_3V3"},
    "TARGET_TX": {"DEVKIT.J1.11", "ISO.7", "INTERFACE.RX_3V3"},
}


def verify(data):
    assert (
        data["pcb_sha256"]
        == hashlib.sha256(Path("hardware/rev_a/layout/rev_a.kicad_pcb").read_bytes()).hexdigest()
    )
    assert not any(p["gates"].values()) and not p["afe"]["external_dummy_mode_enabled"]
    assert data["isolator"]["mpn"] == "ISO7721DR"
    assert data["isolator"]["output_when_own_supply_down"] == "undetermined"
    assert data["isolator"]["default_when_output_up_input_down"] == "high"
    assert not data["approval_changes"] and not data["hardware_tested"]
    groups = data["console_groups"]
    assert len(groups) == len(expected_groups)
    assert {g["name"]: set(g["endpoints"]) for g in groups} == expected_groups
    all_ends = [e for g in groups for e in g["endpoints"]]
    assert len(all_ends) == len(set(all_ends))
    assert data["logical_to_physical_alias"] == {
        "INTERFACE.TX_3V3": "ISO.6",
        "INTERFACE.RX_3V3": "ISO.7",
        "INTERFACE.GND": "ISO.5",
    }
    rows = data["fanout"]
    assert len(rows) == 20
    assert {r["contact"] for r in rows} == {f"AFE.J1.{i}" for i in range(1, 21)}
    for r in rows:
        pin = int(r["contact"].split(".")[-1])
        g = next(g for g in h if r["contact"] in g.endpoints)
        assert r["landing"] == f"FAN.C{pin:02d}" and r["net"] == g.name
        if pin % 2 == 0:
            assert r["destination"] == "TARGET.GND_BUS" and r["role"] == "return"
        elif pin == 17:
            assert r["destination"] == "SUPPLY.+5V" and r["role"] == "power_branch"
        else:
            assert r["destination"] in g.endpoints and r["destination"].startswith("DEVKIT.")
            assert r["role"] == (
                "AFE_to_MCU" if g.endpoints[0].startswith("AFE.") else "MCU_to_AFE"
            )
    toward_afe = {"SCLK", "MOSI", "CS", "RESET", "START", "PWDN", "CLKSEL"}
    toward_mcu = {"MISO", "DRDY"}
    assert len(data["power_states"]) == 16
    for actual, bits in zip(data["power_states"], product((False, True), repeat=4)):
        host, mcu, dvdd, avdd = bits
        assert [actual[k] for k in ("host_up", "mcu_up", "afe_dvdd_up", "afe_avdd_up")] == list(
            bits
        )
        expected = toward_afe if mcu and not dvdd else (toward_mcu if dvdd and not mcu else set())
        assert set(actual["possible_driven_into_off_receiver"]) == expected
        assert actual["adc_rails_mismatched"] == (dvdd != avdd)
        assert actual["powered_setup_permitted"] is False
        assert actual["console_at_mcu"] == (
            "undetermined" if not mcu else ("data_or_idle" if host else "default_high")
        )
        assert actual["console_at_host"] == (
            "undetermined" if not host else ("data_or_idle" if mcu else "default_high")
        )


verify(c)
bad = []
x = copy.deepcopy(c)
x["console_groups"][1]["endpoints"].append("TARGET.GND_BUS")
bad.append(x)
x = copy.deepcopy(c)
x["console_groups"][4]["endpoints"][0] = "HOST.JP4.2"
bad.append(x)
x = copy.deepcopy(c)
x["console_groups"][2]["endpoints"][-1] = "ISO.2"
bad.append(x)
x = copy.deepcopy(c)
x["fanout"].pop(1)
bad.append(x)
x = copy.deepcopy(c)
x["fanout"][18]["net"] = "DVDD sense"
bad.append(x)
x = copy.deepcopy(c)
x["isolator"]["output_when_own_supply_down"] = "high_impedance"
bad.append(x)
for i, wrong in enumerate(bad):
    try:
        verify(wrong)
    except AssertionError:
        continue
    raise AssertionError(f"corrupt C1 snapshot {i} was accepted")
print(
    json.dumps(
        {"AFE_contacts": 20, "ISO_pins": 8, "power_states": 16, "rejected_snapshots": len(bad)}
    )
)
```

The block checks only its explicit conditions; it is not a general cable or
circuit solver. The earlier ordinary gate on clean2b11ddec passed1108tests plus
14subtests; it did not execute new physical/interface tests. Read this C1 PR's
final-head runs separately. A failed preliminary FTDI-document download was not
used as evidence; the selected module above has inspectable primary pin/net data.

## 5. Cost and next deliverable

The selected host module was listed at$5.95 on1October2026 [1], not a delivered
quote. ISO7721, bypasses, auxiliary PCB, wiring, strain relief, shipping/tax and
K1 cables remain unpriced. The existing$94.34 planning subtotal with a historical
$3 harness allowance is NOT evidence of remaining within$100. No amount or
approval was silently changed in the BOM. Requote the complete build before
purchasing, and reconsider the architecture explicitly if the budget is binding.

The next deliverable is a finite nine-line AFE rail-loss/sequencing decision
with actual rail sensing and startup defaults, followed by the combined
auxiliary schematic/layout and terminations. Keep #45/#48, supplier stack and
capacitor facts, E1/fixture requirements, K2 physical fit and all purchasing,
fabrication, powered-connection and body-use gates unchanged. C1 defines an
interface; it does not authorize assembling or energizing it.

## Primary sources inspected on 2026-10-01

[1] Adafruit product5335 and pinout guide:
https://www.adafruit.com/product/5335
https://learn.adafruit.com/adafruit-cp2102n-cp2104-friend-usb-to-serial-converter/pinouts
[2] Manufacturer Eagle schematic, exact source revision given above; inspected
3.3V/VIO/VDD, VBUS, RXD/TXD and header pinref nets, not an actual-unit photograph:
https://github.com/adafruit/Adafruit-CP2102N-Friend-PCB/blob/1c29f780bdc7503e18c8b6d29d1f8fb7cc1510bb/Adafruit%20CP2102N%20Friend.sch
[3] TI ISO772x SLLSEP3G, pp6,15,25,31, pin/functions/electrical/mode tables and
layout diagram inspected as page images:
https://www.ti.com/lit/ds/symlink/iso7721.pdf
[4] Silicon Labs CP2102N Rev1.5, pp12-13 regulator/GPIO tables inspected as images;
100mA is total regulator output including the bridge:
https://www.silabs.com/documents/public/data-sheets/cp2102n-datasheet.pdf
[5] Espressif DevKitC-1 V1.1 schematic,2022-11-30,p2 and guide's exclusive power
alternatives; actual-unit revision is still to be confirmed:
https://dl.espressif.com/dl/schematics/SCH_ESP32-S3-DevKitC-1_V1.1_20221130.pdf
https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide_v1.1.html
[6] TI ADS1299 SBAS499C absolute maximum and power-up sequence; pin limits are
not a permission to inject current into a dead rail:
https://www.ti.com/lit/ds/symlink/ads1299.pdf
