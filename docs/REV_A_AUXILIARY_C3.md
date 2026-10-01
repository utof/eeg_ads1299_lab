# C3: native auxiliary schematic and coordinated bus-pull migration

Design draft, 2026-10-01. Base main `98362c6b6445ddb402ddf942b1c81af738eebe56`.
This implements the C1/C2 circuit in a **separate native KiCad project**, not an
assembled interface or an auxiliary PCB. Open
`hardware/rev_a/auxiliary/auxiliary.kicad_pro`. The four sheets are connections /
console, bus buffers, rail supervision, and arming. No importer replaces the AFE.

## What changed

The auxiliary contains **48 component instances and 212 numbered terminals**:
11 ICs, 15 capacitors, 16 resistors, one six-way service header, and five groups
of numbered solder lands. Its native BOM contains 43 component rows; the five
land groups are fabricated copper, not five purchased connector assemblies.
The Adafruit module, cable assemblies, opposite service-header half, remote STOP
switch, restraint, fabrication and labor are not silently included in that BOM.

The C1 ISO7721DR console boundary and C2 three TXU0304PWR buffers, four TPS3703
monitors, two SN74LVC1G97DBVR gates and SN74LVC2G74DCUR latch are now wired.
Every unused IC terminal is grounded or explicitly NC as appropriate. Host and
target returns remain separate. All 20 K1 conductors have separate landings;
the two regulated-5-V branches are not supplied through the AFE's DVDD output.
The external-port symbol types describe the **required external endpoint roles**,
not proof that those sources are always powered. This assumption is written
on the schematic; no PWR_FLAG or ERC severity/exclusion hides an absent source.

New auxiliary bypass selection: **C0603C104K5RACTU**, 100 nF, 50 V, X7R, 10%,
0603 [4]. There are 15 distinct bypasses: two console domains, six buffer supply
pins, four monitors and three logic packages. They are additional to the existing
33 AFE capacitors. Nominal part selection is not effective-C, assembly or lot
qualification; #48 remains open. Required local layout is not established by
connecting equal global labels. Resistors use the Yageo RC0603 1% family [3].

### Seven AFE components change, but no copper changes

`R_CS_DN`, `R_CLKSEL_DN`, `R_RESET_DN`, `R_PWDN_DN`, `R_START_DN`,
`R_SCLK_DN` and `R_DIN_DN` now specify **42.2 kohm, RC0603FR-0742K2L**.
Reserved CLK/GPIO pulldowns remain 10 kohm. The seven move from the old BOM
`straps` group to `bus_pulldowns`; their schematic and PCB Value/MPN/BOM_ID fields,
validators and actual native reference exports change together. All firmware
levels and sequences, physical pin map, AFE profile and approval flags remain
unchanged. The old 10-kohm minimum-load proof cannot be reused for C3.

Reversing just those seven components' three identity fields reconstructs the
ENTIRE previous AFE PCB and digital schematic byte-for-byte. No track, via, pad,
drill, footprint placement, outline, zone rule or cached ground fill changed.
Old PCB SHA256 `dfe893f958128ba28eb69188cf6debbbc9fcafa0ef5dd67bd58627d4b8a26842`;
C3 PCB SHA256 `f11c9651fb0cebb01bf2cc7d6ef1be0a0093664dfacc4f193f90aab14bdbd6c7`.
The AFE still has 68 footprints, 245 pads, 582 segments and 122 vias.
Native old/new AFE exports preserve all nets, pin functions and electrical types.

## Loaded-high calculation and the limited disabled-low budget

This choice addresses an actual specification gap, not an observed failed board.
TXU0304's near-rail VOH >= VCCO - 0.1 V is given at 0.1 mA output current [1,p8].
ADS1299 digital input current is at most 10 uA, with VIH=0.8*DVDD and
VIL=0.2*DVDD [2,p10]. A 10-kohm pull can exceed the cited light-load row; we do
not infer a stronger output guarantee from a typical curve or the 10-mA row.

Use a **declared steady 3.0-3.6-V digital-rail analysis envelope**, not a statement
that the supervisor guarantees it during transitions. Initial 1% resistance
plus 100 ppm/K over +/-5 K gives an additive 1.05% bound [3,p5]. Installed
resistance must be checked after assembly; long-term drift is not covered by
this short 20-30 C bench calculation. Allocate an additional <=1 uA of board/
fixture leakage per line, **a requirement to establish, not measured evidence**.

```text
Rmin = 42200 * 0.9895 = 41756.9 ohm
Rmax = 42200 * 1.0105 = 42643.1 ohm
Worst driven-high load budget = 3.6/Rmin + 10uA + 1uA = 97.213 uA
At DVDD=3.0 V: guaranteed light-load VOH 2.9 V; required VIH 2.4 V.
Conditional disabled-low budget = (10uA + 2.5uA + 1uA)*Rmax = 0.575682 V
Lowest VIL limit in the chosen analysis envelope = 0.600 V.
```

The disabled-low result has only about **24 mV budget remaining**. It is NOT a
universal guaranteed stopped voltage. The TXU Ioff 2.5-uA maximum applies under
specified zero-supply/other-supply and port-voltage conditions. Its powered IOZ
row tests output at ground or the rail; it does not bound every intermediate
output voltage, supply ramp, floating supply or damaged receiver [1,p8]. Those
limits cannot be extrapolated into an all-time guarantee. If the installed
leakage/resistance, receiver state or rail trajectory is outside this budget,
the corresponding state is unqualified and requires redesign or an explicitly
bounded experiment, not a relabelled pass. A larger 100-kohm pull fails even
this budget; merely weakening all pulls is not the strategy.

R114/R115 provide the same 42.2-kohm pull on MCU MISO/DRDY inputs. Their allowance
uses **10 uA as a receiver-leakage design requirement**, not a claim that the
ESP32-S3's 25-C table guarantees it over every supply/temperature trajectory.
The complete upstream MCU-to-TXU, ADS-to-TXU and control-gate timing/loading
checks still need actual specified rail/load/edge conditions before operation.
No measurement or absolute maximum protection follows from these calculations.

## Feed and sense are physically distinct connections in this project

J104 is a **JST B6B-XH-A(LF)(SN)** 2.5-mm six-way vertical header [5]. It is a
new dedicated service interface, not a reassignment of K1 pin 19 or a J2 NC pin.

| J104 pad | Auxiliary net | Required AFE-side origin |
|---:|---|---|
| 1 | TARGET_GND | Mechanically supported AFE return |
| 2 | AFE_DVDD | Feed from the actual AFE DVDD rail to all three buffer B supplies |
| 3 | AFE_DVDD_SENSE | Separate sense lead from that actual rail, not a local bridge to pad 2 |
| 4 | AFE_AVDD_SENSE | Sense from actual AFE AVDD |
| 5 | TARGET_GND | Second supported return |
| 6 | NC | Remains unused |

**The matching AFE connector/pads and reviewed cable are NOT added by this
slice.** C32/C33 identify the proper electrical nets in earlier reviews, not
acceptable unsupported flying-wire attachment points. The next AFE service-access
change must deliberately add an accessible, restrained feed/sense interface and
recheck routing, mechanics and all-pin connectivity. The current AFE and auxiliary
are not yet an electrically complete physical assembly. This native project
makes that missing connection explicit, rather than pretending J1 already
exposes DVDD or calling external connectors always-present sources.

The two sense inputs each have a local 100-kohm pulldown, so an OPEN sense lead
is not deliberately left floating. All monitor VDDs use MCU3V3. A separate
100-kohm DVDD feed bleed (R116) provides a defined resistive path; it is **not
fast discharge, a guarantee of zero voltage, or detection of every broken feed**.
Its three nominal 100-nF buffer bypasses alone give an ideal 30-ms RC time
constant; uncertain capacitance, buffer current and injected current change that.
No charge-storage/fault qualification is inferred.

Remote STOP uses a two-terminal normally open contact to target return. Its
exact switch, wiring and physical accessibility still require selection; this is
not a qualified emergency-stop or redundant safety channel. Both DevKit USBs
remain excluded with accessory wiring attached. Bare-board programming requires
complete accessory-tail removal under the existing C1 plan.

## Fault timing and arming: keep the real limits

The circuit preserves C2's fresh-edge latch. ARM_BUFFER is tied high at its
second AND input, **not gated with READY**, so rail recovery does not synthesize
an arm edge when ARM_REQ was left high. SESSION/RAILS_OK form the clear input;
READY observes that conditioned clear signal. The existing firmware does not
implement these GPIOs or the handshake. Startup requires seven parked outputs,
settled READY, a fresh ARM edge, and only then the existing uninterrupted clock/
VCAP/reset qualification. VCAP cannot be required before the clock-start controls
can propagate. Failure invalidates the whole capture, not only a sample.

TPS3703's 30-us maximum detection delay requires 5% overdrive; startup is a
300-us typical value, and release is 140-260 ms for the selected CT connection
[6,pp6-7]. For the conservative 5-V UV threshold, the 5%-overdrive point is
4.47925 V, already below E1's 4.75-V minimum. The monitor is not an E1 voltmeter.
As a conditional trajectory calculation, a fall from 4.47925 to 4.0 V at
1 V/ms takes 479.25 us; at 100 V/ms it takes only 4.7925 us, less than the
specified detector delay. Neither is an actual measured fault. Logic/disable
propagation, sense errors, MCU control-power validity, stored charge and receiver
limits must also be included before assigning a qualified deadline. No universal
pre-undervoltage shutdown or abrupt-short protection is claimed.

Monitor SENSE injection with VDD off, intermediate/floating rails, broken returns,
partial cable insertion, initial latch Q, analog J2 source exposure and
AVDD/DVDD asymmetry remain open. A clean schematic does not settle them.

## Native and failure-first evidence

Test-only `56b699d` first observed eight failures: seven 10-kohm loaded-current
checks and the absent auxiliary schematic. The native source and coordinated
pull migration followed in the next commit. One intermediate native test attempt
incorrectly applied the AFE's strict three-sheet ERC parser to the auxiliary;
it was corrected by a distinct four-sheet parser, not by weakening the AFE check.
Initial off-grid authoring/overlapping presentation defects were fixed in source;
no warning severity, exclusion, clearance or numerical threshold was relaxed.

The C3 checker validates the complete native pin partition and component identity,
including NC terminals, functions, BOM/population/board flags. One-at-a-time
moves of all 212 exported terminals are rejected by the software graph checks;
that is not 212 new full tests or exhaustive circuit proof. Native code can still
have defects; primary pin maps and independent critical-connection assertions
remain necessary alongside the manifest.

Eleven focused native cases cover four-sheet ERC/netlist/PDF/BOM, six deliberately
wrong but ERC-clean connections, two benign changes, and two native footprint
cases. The harmful connections include wrong buffer/supervisor supplies, local
feed substituted for remote sense, recovery-gated ARM, wrong-domain bypass and
an unused buffer input tied to activity. Native library pad inventories are
checked for all 12 selected footprint types, including exact local solder-land
hole/size/pitch checks and a wrong-drill control. This is NOT final pad/assembly
DFM, mechanical qualification or a routed auxiliary board. Label renaming and
reversal of a nonpolar capacitor remain benign.

`tools.check --schematic` now binds the authored auxiliary files, selected library
footprints, validator/tests and both native graph fixtures into its source
snapshot (74 entries at this checkpoint), and runs the auxiliary cases in the
same normal KiCad job. In-flight auxiliary source/contract/library/fixture edits
are rejected by gate controls. Native case outputs are retained under the gate's
schematic-test directory. Full gate/CI/review counts must always be read for the
actual final head; focused results or inherited AFE DRC are not a later-head pass.

## Recovery review corrections (PR #75)

The interrupted authoring turn published the complete native source before its
reply failed. Continue that source; do not regenerate the auxiliary or AFE.
The review correction's observed test-only commit is `4ac666f`: **22 failures
and 45 passes** in the focused ordinary auxiliary tests before implementation.
Two failures exposed ISO channel-letter drift; the remaining failures exposed
accepted ERC overrides, hidden dependencies, stale caches and linked libraries.

**ISO directions versus channel names:** TI SLLSEP3G printed p6, Figure 5-4 and
the **ISO7721 D/DWV column** specify 2=OUTA, 3=INB, 6=OUTB, 7=INA. Review
4157186342 proposed the opposite electrical directions; the actual figure does
not support reversing the existing UART wiring. C1's endpoints were already
correct. Only C3's channel-letter names were wrong. The local symbol, embedded
cache, contract and fresh native-export fixture now use the manufacturer names.
The exported nets, electrical types, pin numbers and component identities are
unchanged. Independent expectations cover both the manifest and native graph;
the existing UART wiring is deliberately retained. No zero-error report can
replace checking the selected part/package column in the primary drawing.

**ERC suppression and source closure:** finding 4157186361 was reproduced.
The snapshot now requires explicit empty ERC exclusions/severity overrides,
closed project settings and exact hierarchy/library resolution, and validates
local-symbol/embedded-cache equality before recording hashes. Extra CAD/local
land files, linked library directories and alternate URI/type/options cannot
silently introduce unsnapshotted dependencies. This extends the existing
project-specific boundary using its bounded S-expression reader, not a new
CAD generator. Expanding that boundary requires a deliberate reviewed change.

A new native control misconnects ISO pin2 to HOST_TX in a disposable copy.
Unmodified native ERC returns exit5 with output contention, an undriven input
and a dangling label. Suppressing those three rule types makes the same native
copy return exit0 and an empty report, as the review warned. The source snapshot
now rejects that policy even though the empty report alone passes its parser.
The invalid copy is never accepted as canonical source. A reordered/whitespace
changed empty policy remains allowed. No production rule was downgraded.

There are now **12 focused native auxiliary cases** (the initial11 plus this
suppression control), not12 physical experiments. The exact-head full gate and
independent re-review outcomes must be read from the live PR; earlier passes
and the initial reviewer completion are not acceptance of later source.

Primary pin reference for this correction, inspected as a page image:
https://www.ti.com/lit/ds/symlink/iso7721.pdf (SLLSEP3G, p6).

## Continuation and scope

**Next: the matching AFE service feed/sense access and its continuity/mating
review**, then the test-first C2 firmware handshake, auxiliary placement/routing
and system-level power-fault validation. Do not enable current firmware on this
circuit or call the auxiliary layout complete. Reuse the authored auxiliary
project; the temporary authoring helper is not a command to overwrite edits.

The AFE planning subtotal retains the old 0.06-USD-per-resistor allowance, now
split between five reserved and seven bus pulls. It is not a new supplier quote.
All added auxiliary ICs, bypasses, service connector/cable and production costs
are unquoted; the old $94.34 subtotal does not establish the $100 total target.
No old capacitor shortlist is implicitly adopted. #45/#48 and all purchasing,
fabrication, powered-connection and body-use gates remain open/false.

## Primary basis inspected

[1] TI TXU0304, SCES935A, pp4,7-8:
https://www.ti.com/lit/ds/symlink/txu0304.pdf
[2] TI ADS1299, SBAS499C, p10 (digital input/output conditions):
https://www.ti.com/lit/ds/symlink/ads1299.pdf
[3] Yageo RC_L, V14, 2025-11-14, pp2,4-5 (ordering, dimensions, TCR):
https://yageogroup.com/content/datasheet/asset/file/PYU-RC_GROUP_51_ROHS_L
[4] KEMET C1002 X7R SMD, 2025-02-20, p2 (full code):
https://content.kemet.com/datasheets/KEM_C1002_X7R_SMD.pdf
[5] JST XH, p5 (B6B-XH-A versus the distinct -XH-2 variant):
https://www.jst-mfg.com/product/pdf/eng/eXH.pdf
[6] TI TPS3703 SBVS249B, pp4,6-7,37 (six-pad DSE):
https://www.ti.com/lit/ds/symlink/tps3703.pdf
C1/C2 retain the other exact IC/host-module sources. Installed KiCad 9.0.2
footprints were loaded natively and their pins checked; source geometry and
primary drawings are not proof of a manufactured part's fit or solder yield.
