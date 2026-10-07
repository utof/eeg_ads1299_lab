# Q1: two-board pilot quotation and assembly-review packet

**UNSENT - REQUEST FOR QUOTATION / DFM ONLY - NOT FOR MANUFACTURE OR POWER**

Prepared 2026-10-07 from source commit
`399677407a159ad10c766b4575b65aabc8bd3057`, tree
`a3306419b36226e6b233a42ca6a08a59664e872f`. Q1 adds documentation and quote
schedules only. It does not migrate components, regenerate either PCB, change
firmware or approve a process. Read this before using any attached CAD or BOM.

## 1. The request, ready for a named recipient after permission

Subject: **Quotation and DFM only: Rev A two-board internal-test pilot**

> Please assess the attached Rev A AFE and auxiliary designs for feasibility and
> a conditional quotation. Quote two alternatives: **one complete set and five
> complete sets**, each set containing one AFE board and one auxiliary board.
> These quantities are planning alternatives, not an order or assumed minimum.
> State any larger PCB/assembly MOQ and price the actual delivered quantity.
>
> Price the **quote_mpn** column of the assembly schedule, flagging its 26
> proposed AFE replacements. The CAD and **active_mpn** column deliberately
> retain the current engineering identities. Neither version is released for
> assembly. Do not populate from this mixed-stage packet, modify files, choose
> substitutes, start tooling or purchase non-cancellable materials. Return a
> deviation list and conditional price instead.
>
> Separate bare boards, components, SMT, through-hole work, setup/stencils,
> inspection, cable/fixture work, material overage, tax and delivery. State
> currency, lead time, validity, component sourcing basis, traceability,
> inspection scope, payment terms and exclusions. Identify any customer-supplied
> items and do not count them as free. One vendor need not supply every item;
> identify unsupported services so those costs remain visible.
>
> Return answers to Q01-Q10 below with evidence or an explicit exception.
> In particular, provide a job-specific stackup/DFM proposal for each board,
> capacitor-land/process disposition and connector-hole/soldering review.
> No energized board testing, programming, functional capture, external signal
> connection or medical/isolation qualification is requested. Ask before any
> test that injects voltage/current beyond a separately approved bare-PCB test.
>
> This request is for an unpowered, person-disconnected prototype quotation,
> not a patient-connected product. Nothing is to be built until a separate
> approved, internally consistent manufacturing revision is supplied.

**Recipient, quotation identifier, destination country/postcode and currency
are not selected.** Confirm them before sending. No private address, payment
information or vendor credentials are included. No vendor has been contacted.

## 2. Files and precedence

| Source or schedule | Use and limits |
|---|---|
| `quote/assembly_bom.csv` | Complete grouped board inventory, explicit active/proposed identities, fitted quantities and do-not-fit sites |
| `quote/support_and_costs.csv` | Separate modules, harnesses, fixture, services and equipment; vendor amounts intentionally blank |
| `quote/source_manifest.json` | Exact input identities for this frozen quotation snapshot; not a production release manifest |
| `../hardware/rev_a/layout/rev_a.kicad_pcb` | Actual 78 x 58 mm AFE board; do not regenerate with the parking-grid importer |
| `../hardware/rev_a/kicad/rev_a.kicad_pro` and three sheets | AFE schematic project and local symbol/passive libraries; PCB is in adjacent `layout/`, not a new board to seed |
| `../hardware/rev_a/auxiliary/auxiliary.kicad_pro` and adjacent PCB/four sheets | Actual 90 x 75 mm auxiliary board, local libraries, rules and contract |
| `../hardware/rev_a/service_c4.json` | Five-conductor service harness, exact pin identities and empty cavity |
| `../hardware/rev_a/mechanical/` | Editable K2 OpenSCAD fit-prototype source; not approved manufacturing drawings |

The optional conversation ZIP preserves these relative paths and includes the
relevant decision notes. All necessary source and schedules are also in Git:
the ZIP is convenient delivery, not a prerequisite for another agent. Use
KiCad **9.0.2** and OpenSCAD **2021.01** for the recorded source versions.
Installed stock libraries/tools and font files are not distributed. Embedded
PCB lands and project-local libraries are included, not a fresh-OS toolchain.

Precedence: pinned native CAD/contracts describe the **active** design;
`quote_mpn` describes the **proposed price basis only**. The consolidated
[capacitor decision](REV_A_PILOT_CAPACITOR_DISPOSITION.md) explains that delta.
Any conflict is a question, never permission to choose whichever file is convenient.
Historical notes' old next-step/count statements do not supersede this packet.

No Gerber, drill-production, paste/stencil or pick-and-place release is included.
For an initial quote, ask whether native KiCad plus these tables suffices. If a
vendor portal requires production formats, report that need before generating
separately labelled quote-only exports. Do not upload a draft to an order flow
as though a confirmed stackup, component migration or production review exists.

## 3. Reconciled assembly quantities

| Inventory per two-board set | AFE | Auxiliary | Total |
|---|---:|---:|---:|
| Board-mounted fitted components | 61 | 43 | **104** |
| DNP diode footprint sites (fitted quantity zero) | 8 | 0 | **8** |
| Copper wire-landing footprint groups, not purchased connectors | 0 | 5 | **5** |
| Mechanical NPTH footprint groups, not electrical parts | 0 | 4 | **4** |
| Physical footprint groups | 69 | 52 | **121** |
| Fitted capacitors, already INCLUDED in fitted components | 33 | 15 | **48** |

The native AFE schematic also contains external **MOD1**, the ESP32 DevKit.
It is excluded from the 61 AFE placements and costed once in the support list.
Do not count the auxiliary's 48 electrical footprint groups as 48 purchased
components: J101/J102/J103/J105/J106 are copper landings. H1-H4 are holes, not
four supplied mounting screws. All fitted components are on F.Cu; through-hole
tails and their backside clearance still matter.

The 33-row grouped CSV expands to every 69 AFE and 48 auxiliary electrical
footprint group exactly once. `site_count` counts footprints; `fitted_qty_per_set`
counts installed purchasable parts. DNP and LANDING_ONLY rows have zero fitted
quantity. Packaging/spares/MOQ are separate, not silently multiplied into either.

Quote the following **26 proposed AFE replacements**, leaving current CAD/BOM
untouched until one coordinated reviewed migration. All other identities in
the CSV are retained, not newly lifecycle- or process-qualified:

| Sites | Active MPN | Quotation MPN |
|---|---|---|
| AFE C8-C22, 15 x 1 uF | GRM188R61E105KA12D | GRM188R61C105KA12D |
| AFE C23-C29, 7 x 100 nF | GRM188R71H104KA93D | C0603C104K5RACTU |
| AFE C30-C33, 4 x 10 uF | GRM219R61A106KE44D | GRM21BR61C106KE15L |

Auxiliary C101-C115 retain that KEMET 100 nF identity, giving 22 proposed fitted
instances in all. Retain the five C0G and two polarized T491 capacitors and their
node-specific companions. **D1-D8 stay DNP**. Do not price/fit an optional diode
population as the default, substitute a different ADS1299 channel count, or use
an ISO7721F/other isolator package in place of ISO7721DR.

## 4. Board construction and assembly scope

| Item | AFE | Auxiliary |
|---|---|---|
| Edge.Cuts extents in native coordinates, mm | (10,10)-(88,68) | (0,0)-(90,75) |
| Nominal board size | 78 x 58 mm | 90 x 75 mm |
| Copper layers / nominal thickness | 4 / 1.6 mm | 4 / 1.6 mm |
| Actual minimum routed track width | 0.15 mm | 0.20 mm |
| Actual via pad/drill | 0.60 / 0.30 mm | 0.60 / 0.30 mm |
| Mounting | No PCB screw holes; use existing K2 contact/support regions | Four nominal 2.7 mm NPTH holes; see coordinates below |
| Populated faces | Front; SMT then approved through-hole attachment | Front; SMT then approved through-hole/tail attachment |

The AFE's selected **design target** is JLC04161H-7628, nominal 1 oz outer /
0.5 oz inner, with Nan Ya NP-155F proposed material. Its recorded nominal
outer dielectric gaps are 0.21040 mm and core 1.065 mm. This is **not** a factory
confirmation. The earlier stackup record identifies unresolved outer-copper/core-Dk
reference differences. Request actual pressed dielectric, finished copper,
registration, drill/plating/annulus and material values; nominal 1.6 mm thickness
is not a bound on each gap. No controlled impedance value has been qualified.
See [stackup requirements](REV_A_STACKUP_BENCH_REQUIREMENTS.md).

The auxiliary has four-layer source, but **no supplier-approved detailed stackup**.
Ask for a separately identified drawing; costing the same construction as the
AFE is a quotation alternative, not an implicit design or process approval.
Preserve the actual F / In1 / In2 / B routing; In2 has routed signals/supplies,
not an uninterrupted reference plane. Do not reroute or turn layers into pours.

Preserve the auxiliary all-layer no-copper strip x20.5-23.5 over y0-75 mm and
separate HOST_GND/TARGET_GND. No conductive fixture, mounting plate, shield or
instrument connection may bypass that boundary. The 3 mm separation is a
prototype geometry rule, not a mains/medical isolation certification.
Auxiliary H1-H4 centres: **(5,5), (85,5), (5,70), (86.5,70) mm**. H4 is offset;
do not replace this with a rectangular hole pattern. Fasteners/spacers are not
selected. Preserve mating/termination allocations in the existing P1/K2/C4 notes.

Ask the assembler to review U1 fine-pitch QFP, the auxiliary WSON exposed-pad
solder/paste requirements, VSSOP/TSSOP, the project-local T491 lands/polarity,
and the exact rounded MLCC lands. Ask for stencil strategy, mask registration,
cleaning/residue control and inspectability. **Planning quotation finish: ENIG**,
with green mask/white legend; this is a reversible quote basis, not a modification
of native finish fields or an accepted process. State alternatives/differences
explicitly. Do not alter board outline, hole counts, fiducials or panel tabs in
source; propose panel/tooling needs and keep the delivery depanelled unless agreed.

HTSW-110-07-T-D (AFE J1/J2): keep all twenty positions and 1.00 mm source drills;
manufacturer nominal hole is 1.02 mm. XH B6B-XH-A(LF)(SN) (AFE J3 / AUX J104):
keep six 0.95 mm source drills; manufacturer pattern is 0.9 +0.1/-0 mm. Source
drills are not guaranteed finished plated diameters. Ask for exact pin/hole fit,
plating and selective through-hole solder-process acceptance. Do not fit original
TSW parts or improvise a temperature/dwell from an operating-temperature rating.
Sockets, ribbon, plastic cartridges and fixtures stay out of board reflow.

## 5. Off-board kit and physical interfaces

`quote/support_and_costs.csv` is part of the request, not optional invisible cost.
It includes one ESP32-S3-DevKitC-1-N8R8, one Adafruit CP2102N Friend **5335**,
two K1 IDSD cables, one C4 service cable, fixed controller/HOST/power/STOP tails,
one K2 carrier set, independent auxiliary/module supports, and the still-unreleased
passive startup/dummy fixture. Lab equipment is priced separately from per-set parts.
An assembler may decline cable/fixture/tool work; record **excluded/TBD**, not zero.

**K1:** two IDSD-10-S-04.00-T-G-ST4 single-ended 20-conductor assemblies per set:
one for AFE J1, one differently coded for J2. Nominal 4 inches (101.6 +/-3.175 mm),
28-AWG ribbon, ST4 stripped/tinned free ends. Exact configuration orderability,
process, capacitance and physical seating remain open. Identify contacts by
continuity, not ribbon colour or mirrored drawings. J1 goes to the auxiliary
J101 contact-for-contact; the C3 buffers, not a direct unbuffered C1-era bus,
then interface to the controller. J2 is the separate passive fixture path:
unused 11-20 and initially disabled BIAS9 ends are individually insulated.

**C1/C3/F1 tails:** AUX J102 maps to the same-numbered DevKit J1 positions per
`auxiliary/contract.json`; positions 3,13,14 are unused. Keep 19 used positions,
including individual ground returns and SESSION/ARM/READY/ARMED. AUX J103.1 goes
to HOST5335 JP4.2 (3V3), .2 to JP1.1 GND, .3 to JP1.4 TXD, .4 to JP1.5 RXD.
HOST JP1.3 USB5V is **not** the 3V3 feed. J105 is the regulated target5V/return
pair; J106 is a remote normally-open STOP contact, not a generic power switch.
Exact wire grade, lengths, termination, insulation, strain relief and STOP-device
identity require a proposal; no loose-pin substitute or extra controller connector
is assumed. Never join HOST and TARGET grounds. Programming/service access needs
separate review; the current permanent-tail arrangement requires bare-DevKit
programming before attachment and removal of all accessory tails for that service.
No programming or energized functional testing is authorized by this quotation.

**C4:** one assembled cable uses two **XHP-6**, ten **SXH-001T-P0.6** contacts
(non-N suffix), five AWG24 conductors, insulation OD0.9-1.9 mm; length between
housing wire faces 150 +/-5 mm. Quote the complete assembly once, with breakdown
and tooling/setup, not the same ten contacts again in the board BOM.
J3 to J104 is 1:1 for pins1-5; cavity6 is empty at both ends. Pins1/5 return,
2 DVDD feed OUT from AFE,3 separate DVDD sense,4 AVDD sense after R11. Feed/sense
join only on AFE, never auxiliary. Both XH board headers are already counted in
`assembly_bom.csv`. Require a proposed detached continuity/shorts/retention check;
its test current/compliance and any assembled-board probing need later approval.
No hot mating and no claim of arbitrary power-loss protection.

**K2:** quote one complete fit-prototype set from `carrier_k2.scad`/`view_k2.scad`,
including both differently coded cartridges/bridges, covers, saddles, strain bars
and retainers. Material, tolerances, rivets/fasteners/shims and restraint process
are TBD for review; neither a PCB courtyard nor a coordinate allocation is physical
fit acceptance. Retain C4 support blocks and full socket seating without an inserted
mating-face spacer. Reserve K2's current **21 mm above-PCB working space plus
10 mm withdrawal allocation**; older K1 17/8 mm values are superseded. No AFE
holes may be added. Support auxiliary, DevKit and HOST module independently;
K2 is not an already-designed enclosure for the complete system.

## 6. Finite decision/response sheet

| ID | Question / required disposition | Owner and blocked stage |
|---|---|---|
| Q01 | Exact AFE material/stack drawing and separate auxiliary drawing; resolve nominal copper/Dk differences, via annulus/registration, finished holes and panel strategy | Fabricator proposal + engineering acceptance; before manufacturing release |
| Q02 | Current exact-suffix availability, traceability, lot, lead time, MOQ/overage and any proposed alternatives for ALL quote MPNs, including retained C0G/T491 | Assembler/supplier; procurement and fabrication |
| Q03 | Accept or reject the actual MLCC lands and paste/mask/reflow process at 22 KEMET sites and 19 Murata sites; state mounted-height/tolerance assumptions | Assembler process decision + engineer; populated fabrication |
| Q04 | Internal C8-C10 voltage/impedance and node-specific effective-C disposition; local LDO input/output pairs, reference and VCAP companions must stay intact | Engineer using applicable manufacturer evidence, or explicit limited-pilot risk decision; populated fabrication. Vendor is NOT asked to certify circuit performance |
| Q05 | HTSW/XH finished-hole/pin fit and approved post-SMT through-hole/tail process; WSON exposed-pad and T491 polarity/inspection requirements | Assembler/fabricator; populated fabrication |
| Q06 | Exact K1 configuration, cavity/conductor identification, C4 non-N crimp/tooling, free-end insulation, strain relief and proposed detached test parameters | Harness vendor proposal + engineer; harness build/acceptance |
| Q07 | K2 material/tolerances/complete subparts, full seating and retention; offset auxiliary hole supports and independent module fixtures without domain bridging | Mechanical supplier proposal + engineer; fabrication/use of the affected fixture |
| Q08 | Pilot disposition of remaining reference-edge regions, via/PTH return transitions, channel loading and unconfirmed stackup effects; do not widen guards | Engineer; affected manufacturing release. No assembler SI/medical sign-off inferred |
| Q09 | Regulated source, actual leads/grounding, passive analog-startup fixture, inspection and staged current/abort conditions, firmware/service state | Engineer/user; BEFORE POWER, not a reason to block a conditional quote |
| Q10 | Full delivered scope for 1 and 5 sets, MOQ, labour, setup, tooling, attrition/spares, tax, freight/import, destination and all exclusions | Quoting parties + user; before order approval |

All ten are **OPEN** in this packet. A quote may state conditions/exclusions
without closing them. Supplier answers inform engineering decisions; they do not
alone close #45/#48. In particular, typical MLCC curves are not guaranteed joint
corners: VCAP3 is boosted and expected near6.9V at5V AVDD, not a bounded5V node.
The 1.35mm bulk and 0.95mm KEMET maximum body allowances exclude solder standoff;
being below a4mm component allocation is not measured holder clearance.

## 7. Price accounting: no fabricated total

Use the support/cost schedule with the board BOM for **both quantity alternatives**.
For each vendor line obtain quantity actually charged, unit basis, currency,
extended price, included/excluded items and lead time. Quote finished bare boards
separately for the two designs, even when both share a panel/material. Count a
combined setup/stencil charge once when explicitly included, not once per board
and once again per set. Itemize overage/reel/minimum buys and ownership of excess.
Do not pay twice for headers, cable subparts or the externally listed DevKit.

Unknown prices remain blank/TBD. An explicitly included or not-applicable item
may be zero only with its explanation. The $94.84 historical AFE allowance
includes an external DevKit and excludes much of this kit; it is NOT a new quote,
a lower bound, a complete system total or evidence the user's $100 aim is met.
Keep hardware delivered cost separate from shared/borrowed lab equipment, while
showing any incremental equipment cost in the total cash required for first use.
No exchange rate, current price, stock or tax rate has been assumed.

## 8. Verification and the next real action

The inventory was checked against the current validated frozen AFE netlist,
its canonical PR88 export, auxiliary contract and actual footprint definitions.
This is read-only data reconciliation, not a new native CAD execution or physical
inspection. The complete source tree used for extraction matches the pinned tree.
One-off preparation checks stay evidence, not a new production-code framework.
Run the existing exact-head project CI/review for this documentation change;
report actual results separately rather than inheriting PR88's green badge.

**Next:** the user chooses/approves recipient, destination and this 1/5-set quote
scope; then send ONLY after explicit permission. A normal RFQ response should
be entered against Q01-Q10, not trigger another generic capacitor search. In
parallel, only an independent before-power inspection/fixture plan is useful;
no equipment model or fabricated price is needed to send a conditional quote.
After applicable answers or explicit limited-pilot dispositions, make ONE reviewed
BOM/CAD/contracts/fixtures update, rerun checks and issue a separate release.
Until then no order, supplier message, fabrication, powered connection, external
acquisition or person/animal connection is authorized.
