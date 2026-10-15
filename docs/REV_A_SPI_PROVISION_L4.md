# L4: provide replaceable SPI series positions; do not rely on trace surgery

2026-10-08. Inspected main `cc89a5b9cbdcdbd975109f75dd4a9d0587286384`,
tree `a211a23296f9981429dd162cf1501dfe1c7b5968` (L3 / PR96).

**2026-10-15 follow-through (L6):** PR98 implemented the five positions below;
all remain OPEN_DNP/NOT_SELECTED. Sections1/2/4/5 retain the original L4 design
basis, not instructions to repeat that implementation. Section3a now selects
the disposition of the remaining channels. This is a pilot design decision,
not an electrical pass or fabrication/first-power release.

**Later fitted proposal:** [the consolidated build decision](REV_A_FITTED_PILOT_BUILD.md)
selects33ohm RC0603FR-0733RL as an initial fit at all five sites, conditional on
the coordinated migration and its release conditions. Active source remains
OPEN_DNP/NOT_SELECTED. Earlier statements below about no selected value describe
the L4/L6 decisions; they do not supersede that later proposal.

**Decision: include five accessible series-component positions in the next
custom-board revision, rather than accepting cut-and-flywire rework as the SPI
fallback.** Four are at U102 outputs on AUX, one at U1 DOUT on AFE. This is the
selected implementation requirement, NOT already-added footprints, a selected
damping value or permission to manufacture/power. It does not certify all eight
driver-to-receiver segments in L2. The three MCU-driven segments remain distinct.

The source evidence below makes the choice concrete: four of those five launches
enter the nominal package-body projection before their first via. The schematic
contains no existing series part in any of the five paths. R114 is a shunt
pulldown, not a spare series resistor. No chip lifting, hidden-track cutting,
long aerial digital jumpers or connector-only resistor workaround is accepted.

## 1. What the authored geometry actually allows

Coordinates are native board millimetres; do not mix AFE and AUX origins. The
inspection follows F.Cu centreline segments from each driver-pad centre to its
first same-net via, then compares against the footprint's transformed F.Fab
body bounding rectangle. This is NOT a microscope inspection, exposed-metal
measurement, maximum package envelope or new native clearance/DRC execution.

| Driver / net | First via centre (x,y), mm | Surface path to via, mm | Via inside nominal body box? |
|---|---|---:|---|
| AUX U102.13 / AFE_SCLK | (39.050,24.900) | 2.791 | No |
| AUX U102.12 / AFE_MOSI | (38.100,28.450) | 1.379 | Yes |
| AUX U102.11 / AFE_CS | (39.000,28.450) | 1.313 | Yes |
| AUX U102.5 / MCU_MISO | (39.600,31.550) | 1.352 | Yes |
| AFE U1.43 / MISO | (51.375,35.225) | 2.505 | Yes |

U102's nominal body box is x=36.5..41.5, y=27.8..32.2; U1's is x=43..53,
y=32..42. The MISO launch from U1 has about 1.842 mm of the listed surface path
inside that nominal body box. Its first source segment is UUID
`d62dab04-82cb-5c0b-9d6f-c901c9d73358`, and first via is
`ac44305d-37c6-52b6-bfd7-d78f6c407686`. U102 clock's first via is
`34b78612-00ef-54da-b5eb-b1e05db9b0fe`. These locate the analysis, NOT cut points.

U102 pads have 0.65 mm pitch and 0.40 mm transverse copper width; U1 has
0.50 mm pitch and 0.30 mm transverse width. The relevant tracks are only
0.20 mm (AUX) and 0.15 mm (AFE) wide. A visible front-layer segment is therefore
not automatically a supported, inspectable place to scrape solder mask and
bridge a resistor. Even the clock's outward escape has no designed series lands.
No conclusion that specialist rework is impossible is needed: no such accepted
process exists, and the pilot need not depend on it.

The existing resistor footprint is `Resistor_SMD:R_0603_1608Metric`: two
0.80 x 0.95 mm pads with 1.65 mm centre spacing and a 2.96 x 1.46 mm courtyard.
Use that as the first placement candidate, not the different capacitor land.
It cannot simply be dropped between adjacent IC leads. Route the chosen launches
out to accessible lands; check final part lands, reference coverage and tool/body
access. Exact placement and solder-process feasibility are not established here.

## 2. Exact proposed series boundaries (not active schematic edits)

References below were unused in the inspected source. They are proposed for the
next coherent CAD change, not purchased parts or new entries in the active BOM.
Pad 1 is the driver side by convention; the resistor is electrically nonpolar.

| Proposed position | Driver-side net / only intended endpoints | Existing downstream net / preserve these destinations |
|---|---|---|
| AUX R117 | AFE_SCLK_DRV: U102.13, R117.1 | AFE_SCLK: R117.2 -> J101.1 -> K1 -> AFE J1.1 -> U1.40 |
| AUX R118 | AFE_MOSI_DRV: U102.12, R118.1 | AFE_MOSI: R118.2 -> J101.3 -> K1 -> AFE J1.3 -> U1.34 |
| AUX R119 | AFE_CS_DRV: U102.11, R119.1 | AFE_CS: R119.2 -> J101.7 -> K1 -> AFE J1.7 -> U1.39 |
| AUX R120 | MCU_MISO_DRV: U102.5, R120.1 | MCU_MISO: R120.2 -> J102.19 and existing R114.1 |
| AFE R24 | MISO_DRV: U1.43, R24.1 | MISO: R24.2 -> J1.5 -> K1 -> AUX J101.5 -> U102.10 |

Keep R114.2 at TARGET_GND and its 42.2k value unchanged. Putting the proposed
R120 upstream of this branch leaves the receiver-side pulldown with J102 when
the series part is absent. Replacing R114 with a low resistor would instead
load the data line toward ground; it is not a damping substitution. Preserve
all other default-control resistors and their existing electrical assumptions.

There must be **no parallel copper/solder-jumper bypass** around a proposed
series position. Its component-absent state is an OPEN connection, not the same
as a fitted 0-ohm link. A documented 0-ohm fit may be used as an *unpowered
continuity/configuration baseline* in the later design; it proves no damping
and is not automatically approved for first power. The actual fit, MPN and
allowed tuning alternatives require their own recorded electrical/process basis.
No numeric nonzero resistor is selected in L4. No resistor is inserted in ground,
power or the separate C4 feed/sense paths.

Prefer direct short driver-to-part routing before a long interconnect or fanout,
with the part accessible after assembly. Do not preserve an under-body meander
merely to reach a convenient distant resistor. If all five sites cannot fit
while retaining required bypass/return/clearance/access conditions, revise the
local placement explicitly; do not weaken those guards or silently add tiny
unserviceable packages. The existing 0603 choice is an implementation preference,
not a claim that final placement has passed.

## 3. Account for the other driven segments without pretending they are fixed

L2 contains **eight active driver stages**, not five: MCU SCLK/MOSI/CS drive
U102 inputs; U102 re-drives those three toward the ADC; U1 drives DOUT to U102;
U102 re-drives MISO to the MCU. The five proposed custom-board sites cover only
the last five of those stages. A resistor after U102 cannot damp a new edge
launched by the MCU before U102, or vice versa.

For the three MCU-driven stages, retain the existing commercial DevKit and
captive fanout contract. Do not add a resistor at AUX J102 and call it source
termination at the MCU. Any source-end inline provision would need a supported
attachment near DevKit J1.18/.17/.16 respectively, with the module's own trace,
lead/return geometry and received waveform included. No such attachment or
numeric value is qualified here. Close these stages with applicable channel
evidence or an explicit bounded pilot/rework disposition before their dependent
release; the five-footprint requirement does not waive them.

DRDY and the slower control/arming paths are outside this five-site SPI edit.
They are not presumed immune because they switch less often. In particular,
AFE U1.47's first DRDY via at (50.5,36.4) is also inside U1's nominal body box;
no later bare-track repair is promised there. Their edge/feedback/partial-rail
requirements stay open under F1/L2 and #45. If they require added provisions,
state that scoped change rather than quietly expanding this list or calling
all digital interfaces qualified. Keep all K1 returns and C1 HOST/TARGET
separation; the B3 high-impedance rail-sense leads are not digital signal jumpers.

## 3a. L6: retain remaining paths for a restricted pilot; revision is the fallback

Decision, 2026-10-15, against merged `bab9f60f23c799c9da00fd531acd8a5b9ad1ecd7`
(tree `96afda406d9b0d7715d4fae4b2afa50d3f64b4a2`), with the same hardware and
firmware in documentation head `d90109890fab042eb74ca04d6a7245f568c9f8ea`.
**Retain the commercial DevKit, captive fanout and existing DRDY/control paths
for the proposed INTERNAL-TEST-ONLY pilot. Add no further series sites in this
slice.** The explicit fallback is a reviewed fanout or board revision, possibly
including replacement fabrication; successful repair of an assembled board is
not assumed. This closes the paper choice requested by section3. It does not
close channel qualification, #45, or the user's later build-release decision.

The alternatives were extra sites on every remaining custom-board launch, or
an inline MCU adapter. Neither has a selected value, qualified attachment or
demonstrated need here. Existing L5 sites cannot cover independent MCU launches.
Retaining these paths avoids committing to an unreviewed adapter while making
revision cost and possible loss of the first pilot explicit. No resistor at
AUX J102 may be described as termination at the DevKit source. No under-body
cut, lifted pin or unsupported jumper is the fallback for DRDY or controls.

### Current terminal map and the evidence that matters

DevKit J1.n maps to AUX J102.n under C1. AUX J101.n maps through K1 to AFE J1.n.
These are electrical endpoints, **not approved probe attachment locations**.
Each arrow across a buffer is a separate actively driven segment.

| Path retained | Actual endpoints | Required receiver observation |
|---|---|---|
| MCU SCLK / MOSI / CS | GPIO12/11/10 -> J102.18/17/16 -> U102.2/3/4 | Both levels and single intended threshold transitions at U102; then L2's complete SCLK/data/CS setup AND hold checks downstream |
| RESET | GPIO5 -> J102.5 -> U103.2; U103.13 -> J101.11 -> U1.36 | ADC-local reset pulse, release and startup order |
| START | GPIO6 -> J102.6 -> U103.3; U103.12 -> J101.13 -> U1.38 | Remains low during command-started capture; no unintended transition |
| PWDN | GPIO7 -> J102.7 -> U103.4; U103.11 -> J101.15 -> U1.35 | Parked low, deliberate wake, and fault-state discharge/level |
| CLKSEL | GPIO8 -> J102.12 -> U104.2; U104.13 -> J101.19 -> U1.52 | Parked low and deliberate internal-clock selection, without glitches |
| DRDY | U1.47 -> AFE J1.9 -> J101.9 -> U103.10; U103.5 -> J102.4 -> GPIO4 | Both receiver edges, no extra/missing conversion indications, and complete frame timing |
| SESSION / ARM_REQ | GPIO14/9 -> J102.20/15 -> U109.3/U110.3 | Loaded levels/edges at the gates, including reset/boot and fault recovery |
| Clear / READY | U109.4 -> U111.6 and J102.8 -> GPIO15 | Local clear pulse/release at latch AND separate MCU readback |
| ARM clock | U110.4 -> U111.1 | Exactly the intended clock edge after valid clear release |
| BUS_OE / ARMED | U111.5 -> U102.8/U103.8/U104.8 and J102.9 -> GPIO16 | Each enable endpoint AND MCU feedback; no automatic rearm |

R115 remains a 42.2k shunt at MCU_DRDY, not a series position. U110's other
logic input remains tied high; gating it with READY would create an arm edge
on recovery when ARM_REQ was held high. The native contract and frozen netlists
agree on these endpoint partitions. They establish connectivity, not waveforms.

TXU0304 inputs are Schmitt inputs. Their hysteresis does not exclude repeated
crossings from ringing, nor prove the unknown fanout's loading. Apply the
manufacturer's thresholds for actual input supply and its stated output test
conditions; do not extrapolate a single 3V threshold row across all rail states.
The C3 conditional ADC-pulldown calculation does not cover these entire paths
or the arming fanout. [TXU0304, sections7.3/7.5/10.2](https://www.ti.com/lit/ds/symlink/txu0304.pdf)

U111's clock and clear inputs require particular attention. At 3.3V +/-0.3V,
the SN74LVC2G74 specifies input transitions no slower than10ns/V; its
-40..85C table requires clock and clear-low pulses >=2.7ns and inactive clear
setup >=1.2ns before the clock. These component conditions are **not assembled
margins**. Check loaded U109/U110 edges and latch-pin timing, with supply,
temperature and measurement uncertainty recorded. [SN74LVC2G74, sections6.3/6.6](https://www.ti.com/lit/ds/symlink/sn74lvc2g74.pdf)

F1 waits for sampled READY high for10us, then requests ARM high for10us.
Firmware sampling cannot certify a glitch-free interval at U111. READY and
ARMED use MCU internal pulldowns: include their actual loading together with
R109 and all three OE inputs; do not reuse an unloaded logic-output claim.
Keep the Schmitt conditioning provided by U109/U110 and assess their specified
loaded outputs. [SN74LVC1G97, sections6/8](https://www.ti.com/lit/ds/symlink/sn74lvc1g97.pdf)

DRDY is not merely a slow250Hz square wave. The ADC pulls it high on the first
SCLK falling edge, including command traffic. Capture both ends together with
SCLK; relate the firmware's falling-edge count to actual conversions and read
completion. Count/overrun/status checks can miss electrical faults and are not
a checksum. [ADS1299-x, sections9.4.4/9.5.2](https://www.ti.com/lit/ds/symlink/ads1299.pdf)

### Keep decisions at the stage they actually block

| Stage | Exit condition for these retained paths |
|---|---|
| Before fabrication release | Explicitly accept the restricted purpose and possible replacement-board cost in the consolidated build decision. Review actual fanout/return geometry, accessible supported measurement contacts and staged commissioning feasibility. If essential latch/receiver observations cannot be made, add designed access in a scoped revision before fabrication; a pin list is insufficient. Resolve the other manufacturing gates separately. |
| Before approving any powered procedure | Close startup-critical loaded-level, edge, partial-rail and fault assumptions for that procedure, including MCU internal pulls and actual source/instrument limits. Define a bounded auxiliary/interlock commissioning arrangement that does not depend on an unqualified latch to protect the ADC. This note supplies no power wiring or fault-injection approval. |
| Before first ADC bus enable | Obtain and review the actual interlock/feedback evidence from separately approved commissioning, including held-ARM recovery, SESSION/STOP clear, receiver parked levels and relevant rail trajectories. Follow B2's staged release; its H3 must not be the first test of an assumed-good interlock. No universal shutdown deadline follows from C2 or a passed software test. |
| During approved ADC commissioning, before accepting capture | Use B2 to record the mapped receiver waveforms, local rails/returns, reset/wake timing, complete SPI/DRDY frame and fault response. Keep 1MHz/mode1 and F1's R -> fresh arm -> wake ->150ms -> measured VCAP1 -> reset order. Any failed/ambiguous requirement stops acceptance and triggers disposition/revision. |

Use the **existing B2 run card**, with these endpoints in its contact map and
raw waveform references in its evidence fields. No second worksheet, simulator,
firmware API or test runner is needed. B3 sense tails are not logic probes.
The five L5 sites still need a coherent fitted-value/MPN decision; OPEN paths
cannot deliver the proposed capture. No resistance, including zero ohms, is
selected here. Firmware/release gates, BOM, copper, K1 returns and C1 isolation
remain unchanged. External-input performance and body use remain outside this
pilot. The [later fitted-build proposal](REV_A_FITTED_PILOT_BUILD.md) now carries
the five SPI fits, capacitor migration, stack/connector/assembly choices and
these revision/access conditions. It keeps the sole frozen Q1 packet intact.

Source inspection for L6 used current auxiliary pin contracts, both frozen
native netlists, `c2_interlock.h`, `rev_a_startup.h` and the sketch's call sites,
interrupt and fault paths. Primary datasheet sections above were reread on
2026-10-15. No assembled measurement, live KiCad export, electrical simulation
or electrical qualification was performed for this decision.

## 4. Why a replaceable position is useful, but not a resistor selection

Series source termination belongs near the relevant driver, with total source
impedance chosen for the actual interconnect. TI describes that topology in a
CMOS example [1]; the example's 22-ohm value and 50-ohm line are NOT specifications
for ADS1299/TXU0304 or this cable. TI also identifies resistors for long digital
input lines in the ADC layout example [2], without supplying our complete
buffered-channel solution. Neither example is copied as a universal value.

Retain L2's timing and load conditions. Series impedance can reduce excursions
but also delays threshold crossings and interacts with input loading, source
resistance and pulldowns. Check setup AND hold, edge monotonicity, pin excursions,
logic levels and actual clock/data/CS relationships at the receivers. Do not
replace these with a green packet counter. Use the existing B2 record and
reviewed high-speed probe method; long B3 rail-observation wires are unsuitable
as an assumed reflection-free logic measurement path.

## 5. Original L4 implementation requirement (completed by PR98)

**Superseded as a work instruction:** PR98 completed the five-site source change.
Do not implement it again. The original requirement was a coherent schematic,
BOM, PCB and contract change, including split driver nets, real OPEN connections
without copper bypasses, independent native parity/cut controls, the downstream
receiver pulldown and unchanged false release gates. PR98's acceptance record
and the current handoff identify the delivered source and its verification.

The original requirement also called for coordinated identity fields, frozen
native fixtures, local decoupling/reference review and K2/B3 access review.
Their delivered scope and remaining physical limits are recorded in the handoff;
this historical list is not a claim of assembled access or qualification.
The sole Q1 packet remains a dated snapshot, with later deltas carried separately.

The five-site source implementation is complete. The current follow-through is
the [fitted proposal's migration conditions](REV_A_FITTED_PILOT_BUILD.md#6-the-next-bounded-action-and-who-can-close-it),
starting with Q03/process responses after the conditional Q04 disposition. L3's restricted pilot and possible later
external-input revision remain explicit. Series pads alone do not close component,
stack/process, physical channel acceptance or first-power approval. No price
research or supplier contact occurs in this slice.

## Evidence and limits

Read-only audit matched all 251 AFE and 212 net-labelled AUX pads to the frozen
native netlists, traced the five launches in both segment directions, checked
R114's actual branch and proposed-reference availability, and verified Q1's
18 source plus two schedule hashes. Both PCB byte identities remain unchanged.
F.Fab geometry is nominal source evidence, not a fitted-package clearance model.
No new local native refill, assembled inspection, solder trial or powered test
is claimed. Full locked local dependencies failed to download; any hosted checks
must be tied to the actual PR head, not borrowed from PR96.

[1] TI CDCM61002 SCAS870F, June 2011, p25, LVCMOS termination/Figure24:
https://www.ti.com/lit/ds/symlink/cdcm61002.pdf . Text inspected 2026-10-08;
used for topology only, not this different driver's impedance or resistor value.

[2] TI ADS1299-x SBAS499C, January 2017, p73/Figure80:
https://www.ti.com/lit/ds/symlink/ads1299.pdf . Page image inspected 2026-10-08.

All #45/#48, purchasing, fabrication, physical rework/construction/mating,
power, external-acquisition and person/animal connection permissions are unchanged.
