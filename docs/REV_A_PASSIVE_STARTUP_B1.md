# B1: passive J2 parking fixture and pre-power inspection

**DESIGN / INSPECTION PLAN ONLY. Not permission to build, connect or power.**
2026-10-07, based on main `4927b4c6cd312e40ee6a304e7083245e16d5440a`, tree
`192ba338a966d773c35cf58137fa67b6a2c1459c`. Neither PCB, active BOM, firmware,
model, protection rule nor approval gate changes. No physical result is reported.

## Decision: close the missing analog-startup termination

Use the existing **J2-coded K1 ribbon/cartridge** with an enclosed passive
termination at its free end. Join contacts **1 through 8 and 10** to one insulated
copper node. Leave contact **9** and **11 through 20** separately insulated and
unconnected. No extra PCB, active driver, battery, voltage divider, switch or
software feature is needed for this first internal-test fixture. It is the
previously budgeted startup-fixture scope, not another signal-generator project.

TI requires analog and digital inputs to remain low through supply stabilization
[1, section 11.1]. The current input R/C network cannot pull a floating cable low.
A firmware MUX selection made after reset cannot establish the pre-power state.
B1 provides a passive DC return for the eight routed channel inputs through their
EXISTING 4.99 kohm series resistors. It does not bypass those resistors or short
an IC pin with a test probe. Digital startup and rail supervision remain F1/C3.

Keep B1 connected throughout any separately approved internal-test run, shutdown
and discharge interval; never disconnect it to change modes while powered. The
internal signal uses the internal MUX path [1, section 9.3.1.1.2], so B1 need
not be switched out to observe it. This does not test the external electrode
path, input noise at a valid unipolar common-mode voltage, channel ordering or
BIAS operation. Do not use ground-parked external inputs as a general gain-24
external-signal/noise-test arrangement. BIAS and lead-off excitation stay disabled.

## Exact terminal schedule (contact numbers, not a mating-face picture)

Use contact-to-tail continuity to identify the actual numbered socket contacts.
Cable stripe, a mirrored drawing or wire order at the free end is not sufficient.
The independent return is **J2.10**; even-numbered J2 contacts are NOT all ground.

| AFE J2 contact | Native input net | Existing resistor / ADC endpoint | B1 free-end treatment |
|---|---|---|---|
| 1 | CH1P_DUMMY | R1 -> U1.16 (IN1P) | Join common node |
| 2 | CH1N_DUMMY | R2 -> U1.15 (IN1N) | Join common node |
| 3 | CH2P_DUMMY | R3 -> U1.14 (IN2P) | Join common node |
| 4 | CH2N_DUMMY | R4 -> U1.13 (IN2N) | Join common node |
| 5 | CH3P_DUMMY | R5 -> U1.12 (IN3P) | Join common node |
| 6 | CH3N_DUMMY | R6 -> U1.11 (IN3N) | Join common node |
| 7 | CH4P_DUMMY | R7 -> U1.10 (IN4P) | Join common node |
| 8 | CH4N_DUMMY | R8 -> U1.9 (IN4N) | Join common node |
| 9 | BIAS_AFTER_1M_DUMMY | R10 -> BIASOUT | Individually insulated; NOT part of the common node |
| 10 | GND / AVSS | Local AFE ground | Join common node; sole board-return conductor for B1 |
| 11-20 | Individually NC | No intended board connection | Each tail separately insulated; NOT tied together |

In words: eight input wires plus the one ground wire meet at the enclosed
termination. There is no connection to AVDD, DVDD, USB, chassis, bench earth,
AUX, a person, or an external generator. SRB/reserved/internal pins are outside
this fixture and retain their reviewed board connections; B1 does not claim to
verify every analog/internal pin or the complete power-up specification.

**J1 is forbidden:** pin 1 is SCLK, pin 17 is the 5 V feed, and even contacts
are returns. Correctly aligned on J1, B1 would ground SCLK/MOSI/MISO/CS; with
reversed contact order it can also join the 5 V feed to return. Neither is safe.
Use the captive J2 coding, full seating and independent restraint already defined
by K1/K2. A label is secondary protection, not a substitute for wrong-port and
rotation rejection. Actual keying/retention remains physically unqualified;
stop before mating if the coded carrier or seating is absent or uncertain.
Do not block/remove electrical contacts to add a key.

## Termination and inspection design

Use a small enclosed, insulating support for the free-end junction: separate
anchored wire entries and staggered soldered connections to a short common
copper bus. Support every wire before its joint; solder is not strain relief.
The support must cover all conductive bus/joint surfaces and secure the individually
insulated spare tails. No loose breadboard, twist-only join, exposed alligator
clip or nine unsupported wires hanging from a connector pin. Do not alter the
existing K2 carrier just to house this remote termination.

Label both ends **B1 / J2 ONLY / INPUTS PARKED / NO EXTERNAL SIGNAL**. Preserve
contact identity records and photographs before enclosing the joints. Insulation,
wire attachment process, bend relief, dimensions and a real assembly sample need
review before physical use; this topology is not a fabrication drawing, a tested
joint process, a released printed enclosure or a safety-rated fixture.

### Detached fixture checks: before and after joining

All tests in this subsection concern ONLY a loose, passive cable/termination,
with no board, controller, USB device, supply, battery, electrode or instrument
other than the selected resistance-test instrument attached. They are a proposed
acceptance plan, not authority to perform an unreviewed test on populated ICs.
Use an identified low-voltage resistance range and appropriate mating test adapter;
record its excitation/compliance and lead/contact resistance. No megger/hipot,
diode-test substitution, forced probe in a socket, or undocumented buzzer threshold.

1. **Before joining**, identify all 20 contact-to-tail paths one-to-one and check
   for unintended inter-wire connections. Record the mapping at the actual mating
   contacts, not just the loose ends. This establishes which conductors are used.
2. **After joining**, expect the partition `{1,2,3,4,5,6,7,8,10}` plus eleven
   isolated singletons `{9}`, `{11}`, ..., `{20}`. Measure every input contact to
   contact 10; check each isolated contact against the common node and against
   every other isolated contact. For a manual worksheet that is 8 closed-path,
   11 common-to-isolated and 55 isolated-pair observations. An appropriate passive
   harness tester can report the same partition without manual enumeration.
3. As provisional **workmanship screening** targets, use at most 1 ohm for each
   intended joined path and at least 1 Mohm for each intended open path, ONLY if
   the chosen instrument/range, adapters and uncertainty can distinguish them.
   Record raw values and lead zero; a marginal/uncertain result is HOLD. These
   are new planning screens, not vendor limits, insulation certification,
   allowable patient leakage, or proof of low voltage at the ADC input pins.
4. Inspect joints/insulation/anchoring and repeat the continuity screen under
   gentle handling of the supported cable. Any intermittent/open/extra connection
   is HOLD, not an average to accept. Mechanical pull forces and retention
   qualification require a separately specified procedure.

**Important blind spot:** permutations among the nine joined contacts produce
the same final connectivity partition. A completed B1 test cannot reconstruct
the original contact-to-tail map. In particular, a channel/P-N swap between
1-8 cannot be detected after commoning or by identical internal-test waveforms.
Preserve the pre-join map, and require separate pinout/external-channel verification
before repurposing the cable. Do not claim this fixture verifies channel order.

A broken contact-10 return leaves eight inputs joined to one another but floating
relative to the board. That is why the closed-path measurements reference the
actual socket contact 10. Their detached success still cannot prove the future
mated header contact, resistor solder joints or ADC-side DC level.

## Before-power hold points (one inspection sheet, no generic rail-ohms rule)

| Hold point | Evidence to record before releasing it | Failure or missing evidence |
|---|---|---|
| Assembly identity | Approved actual assembly revision/BOM and substitutions; photographs of both board sides | HOLD if the 26 quote-MPN proposals were populated without coordinated acceptance |
| Visual assembly | U1/U2/supervisor pin 1, tantalum C6/C7 polarity, D1-D8 absent, no bridges/debris/damage, accepted hidden-joint inspection | HOLD; a clear top photograph does not inspect WSON joints |
| Mechanical support | Actual J2-only keying/full seating, supported boards/tails, no pressure on capacitors, AUX offset H4 accommodated | HOLD if a wrong port/rotation can make electrical contact or cable loads reach joints |
| Detached passive items | B1 pre-/post-join records; original K1 and C4 pinout/no-shorts/empty-cavity records | HOLD if only assembled continuity was used or contact numbering is uncertain |
| Domain separation | Visual routing of shields, supply/meter returns and supports; no HOST/TARGET bridge | HOLD; B1 must not create a second return to another board or bench earth |
| Stored energy and instruments | Separately reviewed disconnect/discharge and probing plan with actual instrument identity | HOLD; a powered-off label is not proof of discharge; do not short capacitors with tools |
| Firmware/first power | Actual released fixture/source/probe plan, current-limit and abort settings, valid F1/VCAP observations and explicit approval | HOLD; BOARD_PROFILE_REVIEWED remains false and this document does not release it |

Do not publish a universal "rails must measure more than X ohms" acceptance rule:
semiconductor paths, capacitors and meter polarity/time matter. No assembled-board
resistance, diode or high-voltage test is specified by B1. Likewise, do not use a
successful detached shorting-plug test as measured compliance with low inputs
through a real rail ramp. Later commissioning must inspect the actual input-side
voltage/return behavior with a reviewed, non-bridging observation setup.

Copy the following record for the eventual assembly; all results start blank:

| Item | Record |
|---|---|
| Actual board / B1 / cable / assembly revision | |
| Inspector, date and photographs | |
| Pre-join 20-contact map and no-shorts report | |
| Instrument, range, excitation/compliance, uncertainty, lead zero | |
| Eight contact-to-10 values; common-to-isolated and isolated-pair report | |
| Gentle-handling repeat / insulation / restraint observations | |
| Wrong-port/rotation rejection and full seating evidence | |
| HOLD items and separate approval reference | |

## Scope, source and next bounded step

The table was checked against `hardware/rev_a/board_profile.json`, the validated
frozen native netlist `tests/fixtures/rev_a_netlist.xml.gz`, current authored PCB
terminal identities and existing K1/F1 documents. The unchanged board series
resistors are retained. This is source-derived wiring/inspection design, not a
new native CAD run, a physical continuity test or electrical qualification.
No calculator, production code, test harness framework or board redesign is
needed; existing project regression tests remain unchanged.

User update: **Moscow, Russia is the planning delivery region**; postcode and
recipient remain unselected. Price lookup is explicitly deprioritized. Q1 and
its 33-row/26-row schedules remain the sole, unsent, frozen quotation packet;
this update does not authorize outreach, ordering or assert delivery feasibility.
No availability, shipping, import or price searches were performed for B1.

**Next independent engineering task:** make the concrete before-power connection/
observation plan using existing source, rail, VCAP1 and ground test locations,
including instrument-ground isolation and staged HOLD/abort decisions. Reuse S3
and F1; do not enable firmware, invent a current maximum or repeat the RFQ. Obtain
actual instrument/assembly evidence before the corresponding powered stage.
The physical termination sample and keying need review before use. Keep #45/#48,
manufacturing and all purchasing/powered/external-input/body-use gates unchanged.

[1] TI ADS1299-x SBAS499C, sections 11.1 and 9.3.1.1.1-2, pp 70 and 21.
Page images inspected 2026-10-07; device-startup and MUX basis only, not TI
endorsement of B1 or its workmanship thresholds:
https://www.ti.com/lit/ds/symlink/ads1299.pdf
