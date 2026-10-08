# L4: provide replaceable SPI series positions; do not rely on trace surgery

2026-10-08. Inspected main `cc89a5b9cbdcdbd975109f75dd4a9d0587286384`,
tree `a211a23296f9981429dd162cf1501dfe1c7b5968` (L3 / PR96).

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

## 5. Next is implementation, not another provision study

Implement the five named positions as one scoped schematic/BOM/PCB/contracts
change, preserving history and the already-authored layout elsewhere. Start
with failing checks that require the new split driver nets and series paths.
With the resistor absent, the driver and external receiver must not remain
connected through copper; retain independent native connection/parity checks
and the relevant cut-track faults on both sides. Retain the receiver pulldown
branch and the false firmware/release gates. Existing connectivity contracts
must be updated deliberately, not worked around with schematic exclusions.

Update actual MPN/population fields, source fixtures and preservation expectations
for the exact edited scope; do not merely draw footprints on the PCB or refresh
hashes until tests pass. Keep the old Q1 packet as a dated frozen snapshot, with
any later approved parts/count delta made explicit rather than rewriting its
historical source hashes. Re-evaluate local decoupling, ground fill, unchanged
reference envelopes and K2/B3 access with the new source. No stock-library-wide
edit, ADC driver rewrite, resistor sweep framework or extra test rig is needed.

This five-site implementation is the next bounded source task. L3's internal-test
pilot proposal and possible later external-input revision remain explicit. A
series pad alone does not close component/stack/process, actual MCU/DRDY/control
channels or first-power approval. No price research or supplier contact occurs.

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
