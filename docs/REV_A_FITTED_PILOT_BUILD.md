# Fitted pilot build: selected proposal and the remaining migration conditions

2026-10-15. Source main `cabe26473a26421704d93210a465a8a3d24021d8`, tree
`ca2f1854abefb134e32a9258de7fc213fc34d2c1` (merged PR99).

**Select five 33-ohm RC0603FR-0733RL resistors as the proposed initial SPI fit,
retain the consolidated capacitor shortlist, and target the same named four-layer
construction for both boards.** This closes these design choices for the proposed
INTERNAL-TEST-ONLY pilot. The resistor is a replaceable starting fit, not a proven
matched termination. The active BOM/CAD still has five OPEN_DNP/NOT_SELECTED sites
and the legacy AFE capacitor identities. This note is not an instruction to
populate from mismatched files, release manufacture, buy parts or apply power.

Use this record for the current proposal and its delta from the sole frozen,
unsent [Q1 packet](REV_A_PILOT_QUOTE_PACKET.md). Do not create another quotation
CSV or replace Q1's historical hashes. Q1 remains the question/cost schedule;
B2 remains the commissioning run card. No new calculator or software layer is
needed. The changes below are selections for a later coordinated source revision.

## 1. Five identical starting parts, at five distinct drivers

| Board / site | Driver -> series position -> receiver side | Proposed fit |
|---|---|---|
| AUX R117 | U102.13 -> R117 -> AFE_SCLK / J101.1 | 33 ohm, RC0603FR-0733RL |
| AUX R118 | U102.12 -> R118 -> AFE_MOSI / J101.3 | Same |
| AUX R119 | U102.11 -> R119 -> AFE_CS / J101.7 | Same |
| AUX R120 | U102.5 -> R120 -> MCU_MISO / J102.19, with R114 downstream | Same |
| AFE R24 | U1.43 -> R24 -> MISO / J1.5, then AUX U102.10 | Same |

The manufacturer identifies the exact part as 33 ohm, 1%, 0603, 0.1 W at 70 C,
with +/-100 ppm/C TCR. Maximum stated body dimensions are 1.70 x 0.90 x 0.55 mm.
This is product identity/dimension evidence, not stock, price or assembly-process
acceptance. [Yageo exact-part sheet](https://www.yageogroup.com/component-documentation/download/specsheet/RC0603FR-0733RL)

**Why this starting fit:** it introduces finite source resistance with a small
incremental DC drop under the existing C3 load allocation, and a smaller RC
penalty than the 100-ohm comparison below. A zero-ohm link adds no deliberate
series resistance; leaving these five sites open prevents capture. Nothing here
establishes that 33 ohm is optimal or that all five paths will keep the same value
after measurement. No automatic tuning range or substitute is approved.

The following bounded comparison uses existing C3 assumptions: 20-30 C,
1% initial resistance plus 0.05% temperature allowance, and
`I = 3.6/(42200*(1-0.0105)) + 10uA + 1uA = 97.213296uA`.
R117-R119 drive the ADC pulls; applying the same allowance to R120 retains C3's
10uA MCU receiver-leakage **requirement**, not a guaranteed MCU specification.
For the RC column, 100 pF is S2's hypothetical lumped load and the driver is an
ideal voltage step. The expression is `-ln(0.2)*Rmax*100pF`: time to 80% of the
ideal final step caused by this resistor alone, not the actual receiver waveform.

| Comparison, nominal ohm | Rmax with that allowance, ohm | Conditional added DC drop, mV | Resistor-only RC time to 80%, ns |
|---:|---:|---:|---:|
| 0, ideal comparison only | 0 | 0 | 0 |
| **33, selected proposal** | 33.3465 | 3.2417 | 5.3669 |
| 100, comparison only | 101.05 | 9.8234 | 16.2634 |

The 97.213 uA is a conditional external-load ceiling from C3, not measured total
driver current. The drop does not establish receiver margin without local rails,
VOH/VOL, ground offsets and actual leakage. These comparisons do not bound flight
time, output impedance, overshoot, repeated crossings, setup OR hold. They do not
combine with L2's 5 pF-tested TXU delay as a new channel guarantee.

R24 has a different receiver: U102's data input, without R114 on that segment.
The TXU input-current table is tested at input supply or ground, so do not extend
it into an all-voltage/partial-rail bound. At a separately assumed 500 uA DC load,
R24 would add 16.673 mV; 500 uA is the ADC's output-voltage test current, not the
assembled load or an edge-current limit. Actual drive/loading remains part of
L2/L6 acceptance. [TXU0304 section7.5](https://www.ti.com/lit/ds/symlink/txu0304.pdf),
[ADS1299-x digital I/O table](https://www.ti.com/lit/ds/symlink/ads1299.pdf)

Retain L2's 1 MHz/mode 1 and receiver-local observations. The series parts do not
protect against arbitrary shorts, supply loss or a missing return. Retain L6's
separate MCU/DRDY/control disposition and staged interlock commissioning. Failed
or ambiguous waveform evidence requires a reviewed fit change or board revision;
it cannot be passed by changing firmware delays or interpreting good packets as SI.

The part's maximum body fits the nominal 0603 courtyard rectangle used by L4;
this does not qualify pads/paste, solder standoff, placement or tool access.
R24 stays inside K2's existing allocated box only subject to those assembly
conditions. Its upper access remains obstructed in the assembled model. Any
replacement must use the reviewed disassembly/access process; no in-situ soldering
under the ribbon or under-body trace surgery is assumed.

## 2. One capacitor proposal, with its unresolved conditions retained

Keep the exact [capacitor disposition](REV_A_PILOT_CAPACITOR_DISPOSITION.md):

| Proposed AFE migration | Count | Selected proposal |
|---|---:|---|
| C8-C22, 1 uF | 15 | GRM188R61C105KA12D |
| C23-C29, 100 nF | 7 | C0603C104K5RACTU |
| C30-C33, 10 uF | 4 | GRM21BR61C106KE15L |

AUX C101-C115 already use the selected KEMET identity. Retain the five C0G and
two T491 parts, including all original node-specific companions. D1-D8 remain
DNP. No alternative part family or larger capacitance is selected here.

**Do not apply the 26 substitutions yet.** Q1 Q03 still requires acceptance of
actual lands/paste/mask/process. The 2026-10-15 Q04 follow-through in the capacitor
disposition records node-specific pilot risks and remaining startup-critical
conditions. It retains the candidates without establishing joint minimum C,
impedance or transient bounds. The label INTERNAL-TEST-ONLY waives no condition.

## 3. Construction and assembly choices carried into the proposed build

Choose **JLC04161H-7628 for both AFE and AUX as the design target**: nominal 1.6 mm,
four layers, 1 oz outer/0.5 oz inner, with the existing NP-155F material target.
For AUX this resolves Q1's same-stack quotation alternative into the proposed
design choice. Each board still needs its own accepted job drawing; there is no
supplier confirmation or controlled-impedance acceptance. Preserve actual routing,
In1 returns, routed In2 and the AUX HOST/TARGET separation. The published table
still shows 0.21040 mm outer gaps and 1.065 mm core; E1's public copper/Dk discrepancies
remain Q01 questions, not substituted tolerance bounds.
[JLCPCB named stackups](https://jlcpcb.com/impedance),
[calculator material guidance](https://jlcpcb.com/help/article/user-guide-to-the-jlcpcb-impedance-calculator)

Retain Q1's ENIG/green-mask/white-legend proposal and depanelled delivery. Retain
HTSW-110-07-T-D, both differently coded IDSD cables and the C4 XH assembly exactly
as specified. Choose the existing assembly sequence: SMT first; then an accepted
selective through-hole/tail process; then supported harness/carrier assembly.
Sockets, ribbon and printed supports stay out of reflow. No hand-solder profile,
different hole diameter or undocumented connector substitute is introduced.
Q05/Q06 still cover finished-hole fit, exact process, harness tooling and tests.

K2 keeps 21 mm above-board working space plus 10 mm withdrawal allocation and its
existing support/contact regions. Material, manufactured tolerances, fasteners,
retention and measurement access remain Q07/L6 conditions. No AFE holes or
whole-system enclosure are added. L3/L6's possible replacement-board cost must
be accepted before release; this proposal does not commit the user's money.

## 4. Exact delta from frozen Q1; do not build from the old schedule

| Inventory per two-board set | Frozen Q1 | Current source | Proposed fitted revision |
|---|---:|---:|---:|
| Fitted AFE / AUX components | 61 / 43 | 61 / 43 | 62 / 47 |
| Total fitted board components | 104 | 104 | **109** |
| Physical footprint groups, AFE / AUX | 69 / 52 | 70 / 56 | 70 / 56 |
| Fitted capacitors, included above | 48 | 48 | 48, with 26 AFE identities migrated |
| DNP diode sites | 8 | 8 | 8 |
| Added SPI sites with no fit | 0 | 5 | 0, if the proposed fit is applied |

The current five positions were added by PR98 after Q1. Physical totals include
copper landings/mechanical holes; these are not additional purchased connectors
or fasteners. The DevKit is off-board and counted once in Q1's support schedule.
The five resistors are added fitted quantity, not replacements for R114 or any
other shunt. Order quantities, overage, delivery and prices remain unknown.

Q1's 18 input hashes still identify its original commit, and both quote CSVs
retain their recorded hashes. Do not replace them with current CAD hashes or
silently send old CAD with this new fit. An eventual authorized quotation update
must identify the current source and these deltas explicitly in the same packet;
no recipient, message, order or current stock/price claim is created here.

## 5. Assembly ownership decision, 2026-10-15

The user has no equipment at the current house. **Plan to outsource both PCB
assemblies, their through-hole/tail work and the C4 crimps to a capable assembler.**
Do not make purchase of a reflow oven, microscope, WSON soldering tools or a
specialized crimper a prerequisite for their first breadboard exercise. This is
a make/buy planning decision; no assembler is selected or contacted.

Retain the actual copper lands for the feasibility review. Do not enlarge all
0603 footprints speculatively. The assembler must answer Q03 with the actual
22-site KEMET deviation, 19 Murata sites, paste/mask/placement/reflow assumptions
and mounted envelope. If rejected, change only the affected footprints in the
coordinated revision and re-run native geometry/return checks. A nominal fit or
green DRC is not an assembly-process answer.

| Work package | Selected planning owner / next physical check |
|---|---|
| PCB SMT, then approved TH/tail process | Assembler: inspect polarity and orientation, T491 joints, WSON exposed-pad process and HTSW/XH finished-hole compatibility. Propose inspection coverage and report exclusions; no populated-board power/programming is included |
| K1/B1 cable work and C4 crimp assembly | Harness assembler: retain pre-join contact mapping, specified exact contacts/tooling, insulation and independent strain relief. Detached continuity uses the existing B1/C4 acceptance plans and an identified instrument |
| K2 and AUX/module supports | Mechanical supplier: quote the current complete source assembly and actual material/tolerances. User later performs documented unpowered fit inspection after fabrication approval; no printer purchase assumed |
| User's first electronics learning | Standalone AA-powered passive breadboard and DMM checks in BREADBOARD_FIRST_STEPS.md; no Rev A connection or fabrication needed |

The build handoff must supply one coherent final revision, placement/population
identities, process answers and inspection scope. Current mixed-stage Q1 is for
quotation only. Neither outsourced labour nor this ownership choice closes Q03,
Q05-Q07, or the possible replacement-board/access decision in L6.

## 6. The next bounded action and who can close it

The node-specific **Q04 design disposition is recorded**, with its remaining
startup-critical conditions. Do not repeat that review or present it as measured
acceptance. The next dependency is the actual manufacturing/process response.
Q03/Q05/Q06/Q07 need the relevant process/assembly evidence and remain open.
Q01 needs the actual job stack/DFM drawing; Q02/Q10 need sourcing/delivered scope.
Supplier contact remains paused until explicitly authorized.

After the migration conditions are resolved, make **one synchronized source
change** for the five SPI fits and 26 capacitor identities: AFE BOM/schematics/
PCB, AUX contract/schematic/PCB, validated native fixtures and affected validators.
Start with focused failing population/identity checks; preserve the independent
terminal, copper-cut/bypass, reference and geometry controls. Reconcile the existing
S1-S4 source bindings and distinguish new fitted behavior from their historical
open-state evidence. Keep numerical assumptions unknown where still unknown.
Use existing public hardware interfaces and `tools.check`; do not add a second
manifest framework or duplicate the canonical quote schedule to make this easier.

Only then assess one coherent revision for manufacturing/purchase release with
actual process answers, measurement access and delivered cost. Any powered
procedure still requires B2's source/fixture/current/abort approval; ADC bus enable
requires L6's prior interlock evidence from separately approved commissioning.
Body use and external-input qualification remain outside this pilot.

Evidence for this proposal: direct reads through existing hardware parsers,
frozen native graph/property checks, authored footprint counts, Q1 hash comparison,
standard-library arithmetic above and primary pages reread on 2026-10-15. No native
CAD regeneration, physical measurement, migration or source-code refactor occurred.
