# B2: local voltage observation and startup hold points

**Connection/observation design only; not a released powered procedure.**
2026-10-08. Baseline main `f06f0bf8002386bcf24133215841e57caa72c163`, tree
`9cc21a19f42e738f53b1d063bf5f82fec0d017ce` (B1 merged in PR91).
No PCB, active BOM, firmware, source-current bound or approval flag changes.
Use B1's inspection record and S3's existing voltage worksheet; no new solver,
logging framework, test PCB or shopping exercise is needed.

## Decision: observe local pairs, without adding return wires

Plan a reviewed high-impedance differential/isolated voltage-measurement chain
at the EXISTING points below. A terminal name locates copper; it does not prove
that a probe can safely reach it in the assembled carrier. Use mechanically
supported insulated tips/adapters, installed while de-energized and discharged.
No handheld live probing of fine-pitch IC pins, unsupported wires soldered to
small capacitors, forced clips inside a mated header, or repurposed NC pins.
If a required contact cannot be held without slip/bridge risk, stop that stage
and resolve access; do not silently substitute a remote sense point.

### Source and wiring boundary

The planned regulated 5 V source connects positive to **AUX J105.1** and return
to **J105.2**. They are solder-wire lands, not ready-made banana terminals. The
source class, output-enable and current limiting are retained from BENCH_FIRST;
1 A capability is NOT a first-power setting. Keep K1, C4, the J2-only B1 fixture
and the separately powered C1 host console wired as already specified. Neither
DevKit USB is connected with accessories. B1 remains in place through shutdown
and verified discharge. Do not break a ground or feed while any rail is energized.
No additional supply is connected to J3/J104: pin 2 exports AFE DVDD, it is not
an external power input. Pins 3/4 are sense paths, not load or test-power outputs.

### Observation map (positive sense minus negative sense)

All numbers below are native component terminal numbers, not connector pictures
or GPIO labels. Never identify a tantalum terminal by left/right alone.

| ID | Positive / negative sense points | Meaning and limit of the observation |
|---|---|---|
| O0 | Actual supply output + / output - | Source terminal voltage; separate from the supply display/setpoint and delivered voltage |
| O1 | AUX J105.1 / J105.2 | Board-entry 5 V after BOTH common leads/interfaces; O0 minus O1 is a same-time common-loop loss |
| O2 | AFE C30.1 / C30.2 | VIN_5V_AFE before R11; local feed/return observation, not U2 input-pin certification |
| O3a | AFE C31.1 / C31.2 | AVDD bulk-pair landmark after R11; not proof of voltage at every U1 analog pin |
| O3b | AFE C32.1 / C32.2 | Separate physical AVDD1 bypass landmark; same net name as O3a does not eliminate local drop/transients |
| O4 | AFE C33.1 / C33.2 | Local DVDD bulk-pair landmark; U2.5/2 and U1.48/49,50/51 remain distinct endpoints |
| O5 | AFE C6.1 / C6.2 | VCAP1 versus its local return, related to U1.28; required observation at the later V boundary |
| O6 | AUX J102.2 / J102.1 | MCU_3V3 arriving from DevKit; not proof at the DevKit module itself or every auxiliary IC |
| O7a/b/c | AUX C104.1/2, C106.1/2, C108.1/2 | Three separate AFE_DVDD bypass pairs for U102/U103/U104; receiver pin14/pin7 drops remain to be accounted for |
| D1/D2 | AUX J104.3 / J104.1; J104.4 / J104.1 | Remote DVDD/AVDD sense-line diagnostics, referenced to AUX return; not replacements for O3/O4 or monitor-pin measurements |
| G1/G2 | AFE C31.2 / AUX J105.2; AFE C33.2 / AUX J105.2 | Signed local ground offsets, measured as VOLTAGES, never by joining the points with ground clips |
| F1 | AUX J102.20,15,8,9 each versus J102.1 | SESSION, ARM_REQ, CLR_N (READY feedback), BUS_OE (ARMED feedback), respectively; observed levels are not an independent rail measurement |

Capacitor notation C104.1/2 means positive on pad 1, negative on pad 2, not a
connection joining the pads. Optional post-configuration reference observation
is **AFE C7.1 / C7.2** (VREFP / GND; VREFN is tied to GND in this design).
Do not require the configured internal-reference voltage before its enable step.
J3/J104 pin 6 stays empty/NC; it is NOT a VCAP1 test pin or spare ground.

These landmarks were compared against both frozen native netlists and embedded
PCB pads. C6 pad centres are (52.20,49.38) and (52.20,55.62) mm, each 2.37 by
2.43 mm, in the authored AFE coordinate system. These are COPPER dimensions;
the fitted body/solder/carrier reduce accessible surface. C30-C33 pads are only
1.00 by 1.45 mm; the three O7 capacitor pads are 0.90 by 0.95 mm. No bare-pad
size is a promise of available clip area. Do not use U1's fine-pitch pins as a
hand-probing shortcut. All points require actual-access disposition before use.

### When a landmark is not enough

For S3 acceptance, local capacitor measurements cannot simply be relabelled
as ADC supply-pin, regulator-pin or buffer-pin readings. Account for the path
between the chosen contact and required endpoint, including its return, or
use a separately reviewed contact method at the endpoint. The board has multiple
analog and digital supply/return pins; one good bulk voltage does not prove all
of them. Before R, the B1 contact/joint/R1-R8 input-low condition and parked
ADC-side controls likewise need evidence, not only a photograph of the plug.
This map prepares access; it does not newly establish those physical conditions.

## Keep measurement equipment out of the return circuit

Ordinary scope channel commons are usually joined to each other and protective
earth. Two ground clips at different returns can add an unplanned parallel
conductor. Channel subtraction does not remove that conductor. Keep protective
earth intact; never float a mains scope by defeating its ground [2].

Prefer suitably rated isolated inputs or a documented differential chain for
the target-side observations. A differential probe is NOT automatically galvanic
isolation: inspect input-to-earth impedance, common-mode limits, bias current,
channel-to-channel connections and any required common lead. Include supply
negative/earth links, USB, chargers, shield/drain wires and communications leads
in one actual connection sketch. A portable/battery instrument can lose its
isolation when charging or USB-connected. No unreviewed path may bridge C1's
HOST/TARGET boundary or bypass the ground drop being measured.

High impedance is not zero load. Record resistance/capacitance of BOTH inputs,
range, attenuation, offset/uncertainty, common-mode rejection, bandwidth, trigger
and time alignment. VCAP/reference nodes are particularly sensitive to loading;
50-ohm scope termination and resistance/diode-test modes are not permitted for
these voltage observations. Probe loading and physical attachment can change the
observed signal [3]. No minimum probe impedance is declared universally adequate.

A floating battery DMM, with no charging/data connection and verified ratings,
may support static checks; it does not establish startup overshoot, fast dropouts
or the R-to-V timing history. Review enough simultaneous channels to establish
each claim. Separate stable-mode surveys may help troubleshoot, but readings
from different runs/times cannot close S3's instantaneous voltage-loss equations.
A common-ground logic analyzer has the same return-path problem; its input
thresholds must also match the target-domain signals.

For current, plan to record source total and any required branch separately.
The supply readout is not automatically fast/accurate enough. Do not insert a
shunt into a return or put an ammeter across a rail; shunt burden, added contacts,
bandwidth and changed current sharing require explicit review. No current-limit
value or component-temperature abort value is invented in this document.

## Match observations to the existing firmware boundaries

TI requires input-low/supply stabilization before the clock and a delay plus
VCAP1 > 1.1 V before reset [1]. The current F1 sequence provides two operator
acknowledgments; neither reads a voltage. This plan does not alter that sequence.

| Boundary | Required evidence before proceeding | HOLD / abort decision |
|---|---|---|
| H0: disconnected | B1 inspection complete; actual assembly/firmware identity, source/probe ratings, contact restraint, ground sketch, coverage and shutdown plan accepted | No mating/power if identity, isolation, polarity, energy or contact access is uncertain |
| H1: before first output-enable | Numeric current/compliance, permitted rail-ramp/settling time and temperature limits, source overshoot/energy, acquisition/trigger coverage and discharge criteria approved for the actual assembly | Blank settings mean no power; 1 A source capacity is not the current limit |
| H2: parked and awaiting R | Local rails meet the approved steady envelopes with uncertainty; analog inputs held low by accepted B1 paths; all seven ADC controls parked; SESSION/ARM_REQ and feedback low as F1 requires | Do not require VCAP1 > 1.1 V while PWDN/clock remain parked. Do not send R based only on J104 sense, READY, or a supply display |
| H3: after fresh R, at V prompt | F1 requires READY then a fresh ARM/ARMED sequence. Only then PWDN/CLKSEL/CS/RESET go high; the existing 150 ms wait occurs before V | Wrong feedback, rail loss, missing/invalid observation or failed arm means stop; no bypass or automatic retry |
| H4: V acknowledgment | O5's uncertainty-adjusted lower bound exceeds 1.1 V at acknowledgment; required rails stay valid through wake/wait/reset; retained timing and stable observations cover this interval | VCAP1 threshold alone is not a rail pass or substitute for clock-delay evidence; no reading copied from an earlier power cycle |
| H5: configuration/capture | Existing reset/SPI/ID/register checks and internal-test mode accepted; retain rail/current and event records for the same run | Fault, invalid frame/session, clipped measurement or exceeded approved bound invalidates the whole affected run; no noise/external-input claim |
| H6: shutdown | Use the reviewed source/host shutdown and verified-discharge sequence, keeping B1 and intended returns connected until discharged | STOP is logic, not a power disconnect. Do not unplug cables or short capacitors to force discharge; confirm all relevant rails/internal nodes, not just the source display |

**Actual firmware still has BOARD_PROFILE_REVIEWED=false** and stops before the
reviewed C1-header acquisition path. Seeing the distributed onboard-console
message is not evidence that H2-H5 ran. No instruction here grants permission to
change that flag. Preserve S4's distinction between these two states.

Existing stable analysis bounds are AVDD/AVDD1 4.75-5.25 V and C3 digital
3.0-3.6 V. They are not permission to spend a supply ramp below its lower limit
indefinitely, nor complete logic/ground-offset safety limits. H1 needs the allowed
ramp duration and energy before applying power; unknown or stalled ramps are
not excused as startup. Include measurement uncertainty in every comparison.
Unexpected current limiting, droop/restart, overvoltage, heating, unstable contact,
loss of rail/feedback or missing capture triggers the approved source-off action.
Do not keep increasing current/voltage to make the display or firmware pass.
A human response/STOP/polling is not guaranteed to outrun electrical damage.

## One run card, initially blank

Attach this to B1's existing inspection sheet; no separate instrument database.

| Record | Actual entry before the corresponding release |
|---|---|
| Assembly/BOM, firmware hash and enabled state, B1/K1/C4 identities | |
| Source model/serial; voltage/current/compliance; overshoot/energy review | |
| Probe/instrument/channel and + / - contact for each required observation | |
| Contact photographs/support; earth/USB/shield connection sketch | |
| Ranges, loading, uncertainty, bandwidth, sample/trigger/time coverage | |
| Numeric current/thermal/rail-ramp/settling/discharge limits and approver | |
| Raw rails/VCAP/current and R/READY/ARM/ARMED/V/reset event record | |
| HOLD/fault reason, full-run invalidation and shutdown/discharge result | |

## Next finite decision and evidence scope

Resolve **mandatory physical probe access**, starting with C6.1/C6.2 in the K2
holder and the O3/O4 rail contacts: pick a supported probe/contact arrangement
and confirm body, key, cable and mounting clearance. A net match alone is not
that decision. Use the existing CAD and actual available probe dimensions; do
not add a large universal fixture, new acquisition framework or blind test-pad
reroute. Then fill H1 with the actual equipment/approved commissioning limits.
An inaccessible essential point is a concrete fixture/CAD decision, not a reason
to waive the V observation or keep writing generic power studies.

This is a read-only source and firmware-order audit, not a native CAD execution,
electrical test or completed protection analysis. No pricing/outreach occurred.
Moscow remains the planning destination. Q1 source/schedules and all engineering
files remain unchanged. #45/#48 and buying, fabrication, power, external-input
and body-use restrictions remain open. A source merge approves none of those.

[1] TI ADS1299-x SBAS499C, pp7-8 and p70 (section11.1/Table30), page images
inspected 2026-10-08. Source: https://www.ti.com/lit/ds/symlink/ads1299.pdf

[2] Tektronix, Floating Oscilloscope Measurements and Operator Protection,
traditional channel commons and unsafe earth defeat; read 2026-10-08:
https://www.tek.com/fr/documents/technical-brief/floating-oscilloscope-measurements-and-operator-protection

[3] Tektronix, ABCs of Probes, physical attachment, loading and ratings;
read 2026-10-08: https://www.tek.com/en/documents/whitepaper/abcs-probes-primer
