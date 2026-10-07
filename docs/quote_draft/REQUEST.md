# Rev A two-board pilot — quotation / DFM only, UNSENT

**Do not fabricate, assemble, order parts, energize, or substitute from this packet.**
This is a feasibility and cost request, not production data or acceptance of a
manufacturing process. No supplier or destination has been selected; nothing has
been sent. Retain the NOT FOR FABRICATION markings in the native designs.

Source baseline: `399677407a159ad10c766b4575b65aabc8bd3057`, full tree
`a3306419b36226e6b233a42ca6a08a59664e872f` (merged PR88). See `source_manifest.json`.
All engineering files describe the CURRENT design. Only `Proposed_quote_MPN`
in `bom_current_vs_quote.csv` describes the requested capacitor quotation alternatives.
The actual BOM, schematic/PCB MPN fields, firmware and approval gates are unchanged.

## Draft message to the supplier

> Please provide a feasibility review and itemized quotation for one Rev A pilot
> set, with five sets as an optional price comparison. These quantities are
> planning assumptions, not a purchase commitment. One set is one AFE board and
> one auxiliary board, plus the separately listed controller, console, cables and
> mechanical items. Quote anything outside your scope as NOT SUPPLIED, not zero.
>
> Use the frozen native source for land/assembly review, and the proposed-MPN
> column for pricing. The 26 capacitor differences from the native source are
> deliberate, explicitly proposed, and not yet approved. Do not import this
> schedule as an assembly order. Please answer the numbered questions below,
> identify mandatory design changes and provide a dated job-specific stackup.
>
> Separate bare boards, fitted components, setup/stencils, assembly/inspection,
> harnesses, mechanics, minimum-order/attrition charges, spares, tax and delivery.
> State currency, quotation validity, lead time, minimum quantities and what is
> excluded. Destination and delivery terms are to be confirmed before any final
> delivered quote. Do not start work or buy material. No substitutions without
> written designer acceptance and a new released source package.

## What is in the packet

| Item | Use / limit |
|---|---|
| `bom_current_vs_quote.csv` | Complete grouped electrical schedule, actual PCB reference names, current/proposed MPN, population and quantities per set |
| `ASSEMBLY_AND_INTERFACES.md` | Both boards, landing/connector distinctions, cable and fixture scope, no-hot-mating and separate-domain constraints |
| `cost_reply.csv` | Blank itemized price-response template; empty price means unknown, never free |
| `source_manifest.json` | Frozen baseline, read-only source paths/hashes, counts and identity of the BOM export |
| Native source / referenced decision documents | Byte-preserved copies in the conversation RFQ archive; alternatively retrieve the exact paths at the baseline commit |

A spreadsheet companion is a convenience view of these schedules, not a second
engineering BOM or approval system. Fitted quantities exclude feeder loss, spares
and pack minimums. The controller is already listed once as EXTERNAL/MOD1: do not
add a second controller line when costing accessories. Board headers J1/J2/J3 and
auxiliary J104 are already in the board BOM; housings/contacts/cable are separate.

**Inventory check:** AFE has 61 fitted purchased parts and eight DNP diode sites.
Auxiliary has 43 fitted purchased parts, five wire-landing footprint groups and
four board-only mounting holes. Those landings/holes are not 9 purchased headers.
The two boards together contain 104 fitted purchased parts and 48 capacitors;
one external DevKit is additional. This is not the complete system's piece count.

## Numbered questions — answer each, or state the specific missing information

| ID | Question / required response | Decision owner and stage |
|---|---|---|
| Q1 | Quote AFE at its documented JLC04161H-7628 / Nan Ya NP-155F target, 1.6 mm nominal, four layers, 1 oz outer / 0.5 oz inner. Supply your actual material, finished copper, pressed dielectric, registration and finished-thickness tolerances. Reconcile the historical 35 vs 40.64 um outer-copper and 4.6 vs 4.43 core-Dk references. For AUX, quote a separate actual four-layer construction; matching the AFE is a cost option only, not an approved AUX stack. State finish/mask options and any panelization/support changes. | Supplier data, then designer stackup/return-path acceptance before fabrication. No unnamed FR-4 substitution. |
| Q2 | Review actual copper/drills/annuli, fine-pitch lands, mask/paste and thermal pads on BOTH boards. Inspect 0.60/0.30 mm vias, AFE 1.00 mm HTSW drills, 0.95 mm XH drills on each board, AUX U111's scoped 0.15 mm pad clearance, supervisor WSON pads and all numbered solder-tail holes. Report finished plated-hole ranges and any required changes. | Supplier DFM; designer approves any footprint/copper edit. Native DRC is not process acceptance. |
| Q3 | Confirm exact suffix, traceable authorized supply, current availability/lifecycle, packaging/MOQ and attrition for every proposed/retained MPN. Identify shortages without silently substituting. Quote the 26 proposed AFE capacitor changes, retaining 15 AUX 100 nF parts, five C0G and two T491 parts. DNP diodes are NOT purchased or fitted in the base quote. | Procurement information only; applicable evidence or explicit limited-pilot disposition before coordinated migration/populated fabrication. |
| Q4 | Give explicit land/process disposition for all 22 KEMET 100 nF sites: existing pads 0.900 x 0.950 mm at +/-0.775 mm, versus density-B 0.950 x 1.000 at +/-0.800, same 0.650 mm gap. Also disposition the existing 1 uF/10 uF lands, local tantalum patterns, stencil, reflow and solder standoff. Confirm body/assembled-height allowances; do not equate body-in-courtyard with process qualification. | Assembler for joints/process. Designer/manufacturer for node-specific voltage/effective-C/impedance; these are NOT tasks an assembly quote alone can certify. |
| Q5 | Quote SMT first, then unmated HTSW/XH and wire-tail attachment using an accepted alloy/profile/cleaning/inspection process. Keep IDC sockets and carrier pieces out of board reflow. Include polarity/pin-1 inspection, DNP verification and a practical inspection proposal for hidden WSON joints. No conformal coating, global stock-land changes or unapproved rework process. | Assembler proposal plus designer review before assembly. |
| Q6 | Quote the two distinct K1 cable/cartridge assemblies and C4 five-wire harness with exact contact suffix, wire dimensions, length, insulation and restraint. State continuity/short-test, crimp/pull and identification method. J104 pin 2 feed and pin 3 sense stay separate until the AFE rail; cable cavity 6 stays empty at both ends. No omitted/blocking K1 contact as a key. | Cable assembler data and designer acceptance; detached cable check before mating. |
| Q7 | Quote the K2/C4 mechanical parts separately from electronics. State proposed material/process, achievable tolerances, fasteners/rivets/liners and inspection/retention plan. AUX and DevKit require independent support; K2 is the AFE carrier, not an enclosure for everything. Do not change its coded ports or assume AUX holes form a rectangle. | Mechanical supplier proposal; actual fit/retention remains unqualified. |
| Q8 | Include bare-board electrical test and assembly optical/polarity inspection as separately identified services. State test access and coverage without powering populated boards. Functional or powered testing requires a later explicit procedure, settings and authorization; never bridge HOST/TARGET with fixtures or instruments. | Designer before powered commissioning; a supplier inspection report is not a whole-system safety sign-off. |
| Q9 | Return 1-set and optional 5-set prices with all `cost_reply.csv` categories covered: included, separate, not supplied or unknown. Separate unit charges, one-time charges, excess stock/spares, shipping/tax and lead times. Give a complete delivered total only after destination/currency/tax terms are known. | User decision before any order. Historical $94.84 allowance is NOT a quote or the whole-system total. |

## Electrical decisions that remain ours, not the assembler's

Capacitor choice was consolidated in `REV_A_PILOT_CAPACITOR_DISPOSITION.md`;
no new family search is requested. C8-C10 retain internal-node voltage/impedance
review (VCAP3 is boosted). Local LDO output effective-C/ESR, input source impedance,
reference/VCAP companion networks, bulk retention and startup energy remain
node-specific. Typical curves are not guaranteed minima. Manufacturer data or
an explicit bounded pilot-risk decision is needed before the affected build step.

The 18 pending auxiliary reference-edge records, own-contact return transitions,
complete signal channels, analog six-pair coupling and stackup implications remain
open. A quote, three-millimeter geometric separation, battery or green CI cannot
close them. No arbitrary meanders, generic termination value or enlarged guard
allowance is authorized. Keep #45/#48 open.

## Reply and next action

Return a question-by-question response and a cost sheet, not only a headline PCB
price. After user approval to contact a named supplier and provide delivery terms,
request the quote. Reconcile concrete responses and internal pilot-risk decisions;
then make ONE coordinated BOM/CAD/contracts/fixture/regression update where
accepted. Generate fabrication outputs only from that reviewed released source.
This packet intentionally contains no order-ready Gerber, drill or placement/CPL
package. Unchanged native CAD is for feasibility review, not manufacturing.

Actual regulated 5 V source/instruments and staged current/abort settings are a
before-power requirement; an unselected model does not block this quotation draft.
No supplier contact, purchase, fabrication, powered procedure, external acquisition
or body-use permission is granted here.
