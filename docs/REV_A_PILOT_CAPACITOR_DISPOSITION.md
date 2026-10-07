# Pilot capacitor disposition: one quotation list, no silent substitutions

2026-10-07; reviewed source main `890f76b14867fa606f32202d6af58e9b8732d085`,
tree `42817c22f687a3ed6c7245e09a865b4d546ea9aa`.

**Decision:** retain the existing shortlisted 16 V Murata identities for the
1 uF and 10 uF pilot quotation, alongside the shared KEMET 100 nF identity chosen
in PR87. Candidate selection for these three ceramic roles is now consolidated.
Do not search for another family or build another model without a concrete
rejection. This is a quotation/conditional pilot proposal, not an applied BOM
migration or acceptance of unresolved electrical/assembly conditions.

The active AFE BOM, both boards, firmware, scientific models and all gates are
unchanged. #45/#48 stay open. The 26 proposed AFE replacements must eventually
be applied together to the real BOM/CAD/contracts, not by editing this table.

## 1. Capacitor schedule for one two-board set

These are fitted quantities, not order quantities or spare/reel allowances.
Native references are board-specific. This schedule covers all 48 fitted
capacitors, not the complete populated assembly BOM or a delivered quote.

| Board / native references | Count | Exact proposed or retained identity | Disposition |
|---|---:|---|---|
| AFE C8-C22 | 15 | GRM188R61C105KA12D | Preferred 1 uF, 10%, 16 V, X5R, 0603; replace legacy GRM188R61E105KA12D only after the conditions below |
| AFE C30-C33 | 4 | GRM21BR61C106KE15L | Preferred 10 uF, 10%, 16 V, X5R, 0805; replace legacy GRM219R61A106KE44D only after the conditions below |
| AFE C23-C29 | 7 | C0603C104K5RACTU | PR87's preferred 100 nF, 10%, 50 V, X7R; legacy AFE identity remains active for now |
| Auxiliary C101-C115 | 15 | C0603C104K5RACTU | Retain existing selection; include these sites in the same land/process review |
| AFE C1-C4 | 4 | GRM1885C1H472JA01D | Retain differential input C0G 4.7 nF parts |
| AFE C5 | 1 | GRM1885C1H152JA01D | Retain BIAS feedback C0G 1.5 nF; not a ground bypass |
| AFE C6 | 1 | T491D107K016AT | Retain VCAP1 100 uF, with C23 in parallel |
| AFE C7 | 1 | T491B226K016AT | Retain reference 22 uF, with C25 in parallel |

The D suffix of the 1 uF target and L suffix of the 10 uF target are supported by
the existing manufacturer-authored orderable sheets [1,2]. Do not copy the old
bulk's D suffix onto the new part. Dated core-in-production evidence is retained
in `REV_A_CAPACITOR_E1_DECISION.md`; it is not a fresh full-suffix lifecycle,
stock, lot or price guarantee. Request current exact-part supply confirmation
with the quotation. C0G/T491 retention is not a new lifecycle clearance either.

## 2. The 1 uF decision is node-specific

The current frozen native netlist validates against the actual BOM/profile, and
the authored board agrees on all 19 sites reviewed in this slice:

| Actual node | Native references | Decision / condition |
|---|---|---|
| VCAP2, VCAP3, VCAP4 | C8, C9, C10 respectively | Keep three 1 uF nominal connections; C9 retains parallel C24. Do not qualify the 25 V to 16 V change from external rail voltage alone |
| AVDD, including the separate AVDD1 bypass | C11-C16 | Retain each physical local bypass, despite sharing one net name |
| ADC DVDD | C17-C18 | Retain both local digital bypasses |
| LDO input VIN_5V_AFE | C19-C20 | Retain the two local 1 uF parts; effective input capacitance >=0.47 uF is the source-impedance recommendation, not an unconditional LDO stability requirement |
| LDO output DVDD | C21-C22 | Retain the two local 1 uF parts; justify effective local output network 0.47-200 uF and ESR <=0.1 ohm under actual conditions |
| VIN_5V_AFE / AVDD / DVDD bulk | C30 / C31-C32 / C33 | Retain all four 10 uF nominal locations; do not substitute remote bulk capacitance for the local LDO pair |

**VCAP3 is not a 5 V rail.** TI's ADS129x debug FAQ lists VCAP3 as AVDD+1.9 V
and explicitly includes ADS1299-4 [3]. With AVSS=0 and AVDD=5 V, that suggests
approximately 6.9 V across C9; at the 5.25 V external analysis endpoint, the
same calculation gives 7.15 V. These are expected debug/sensitivity values, NOT
guaranteed startup or transient maxima. TI's ADS1299 support also identifies
VCAP3 as an internal boost supply [4]. This rules out using a generic 5 V cap
bias for all 15 sites; it does not close every internal-node voltage condition.

The 16 V candidate is therefore reasonable to keep for quotation, but C8-C10
require explicit internal-node voltage/impedance disposition before populated
fabrication, separately from C11-C22. Do not fall back to a 6.3 V part for C9,
change capacitance blindly, or infer permission to probe an assembled ADC.
Preserve the ADS1299 nominal VCAP arrangements and reference >=10 uF requirement;
neither is replaced by the LDO's 0.47 uF rule [5,6].

## 3. What the existing capacitance curves can and cannot decide

Re-read the retained manufacturer technical sheets, rather than rediscovering
the same shortlist [7]. Their DC-bias plots give useful order-of-magnitude
planning information: the 1 uF part is roughly 0.85-0.90 uF around 5 V and roughly
0.75-0.85 uF around 6.9 V; the 10 uF part is only roughly 4-5.5 uF around 5 V.
These deliberately broad visual estimates are typical plotted values, not
measured components, digitized specifications or minimum-capacitance bounds.
The test excitation is 1 kHz/1 Vrms for the 1 uF sheet and 1 kHz/0.5 Vrms for
bulk. Small-signal behavior, aging, temperature and initial tolerance still matter.

Thus a 16 V rating does not preserve 10 uF at 5 V. Retain the candidate without
pretending each AVDD bulk part stores its nominal charge. No transient energy
requirement or simulation expectation is adjusted to match these curves. If
first-power/load requirements need more guaranteed charge, that is an explicit
component/network decision before the affected procedure, not a hidden new cap.

For the LDO output pair, 0.47/1.8 = 26.11% compares the requirement with the two
parts' combined initial-tolerance low corner. It is NOT proof of joint retention,
and typical bias/AC/temperature curves must not be multiplied into a guaranteed
minimum. Keep effective-C unknown until applicable manufacturer information or
an explicit limited-pilot risk review disposes the actual network conditions.
The 100 nF and T491 networks keep their separate requirements [5,6,8].

## 4. Height does not require a new carrier on the present evidence

| Proposed body / current authored land | 1 uF, 15 sites | 10 uF, four sites |
|---|---:|---:|
| Maximum body length x width x height (mm) | 1.70 x 0.90 x 0.90 | 2.10 x 1.35 x 1.35 |
| Pad length x width (mm) | 0.90 x 0.95 | 1.00 x 1.45 |
| Pad centres from origin (mm) | +/-0.775 | +/-0.950 |
| Inner copper gap (mm) | 0.65 | 0.90 |
| Courtyard length x width (mm) | 2.96 x 1.46 | 3.40 x 1.96 |
| Smallest centred body-to-courtyard side allowance (mm) | 0.280 | 0.305 |

Both land patterns have rounded corners (radius 0.225 / 0.250 mm respectively).
These are actual source dimensions, not asserted Murata assembly recommendations.
Their source is the authored board, not an S-parameter measurement fixture.
Maximum bodies are from the dated manufacturer sheets [1,2,7].

All 19 centred maximum-body rectangles lie inside K2's existing component XY
allocation, outside its header-insertion and edge-contact cutouts. K2 already
reserves up to z=4 mm above the PCB for components at these locations, including
C33. The 10 uF candidate's 1.35 mm body is 0.40 mm taller than the old part's
0.95 mm maximum, but remains inside that allocation. There is no demonstrated
need to redesign the carrier just for this height increase.

This is a read-only box/coordinate comparison, not a new native 3D collision
execution or assembled fit qualification. The 2.65 mm difference to the 4 mm
allocation ceiling is NOT a measured cable/holder gap. Solder standoff, placement,
board/fixture tolerances and real cable motion must remain within the allocation;
no outer enclosure has been specified. Assembler land/paste/mask/reflow acceptance
is still needed. PR87's KEMET density-B deviation applies to all 22 100 nF sites.

## 5. One finite quotation/DFM request and stage-specific disposition

Unsent request, for feasibility and a quote only:

> Quote the exact capacitor schedule above for one AFE plus one auxiliary board,
> stating minimum order/spares, traceable lot and current applicable part status.
> Do not substitute without approval. Review the actual rounded copper lands,
> courtyards, mask/stencil/reflow process and assembled-height allowances; record
> acceptance or exact requested changes. For C8-C10 distinguish internal VCAP
> nodes from the external rails (C9 is a boosted node, about 6.9 V expected at
> 5 V supply, not a specified transient maximum). Identify applicable voltage,
> effective-C and impedance conditions; where only typical data exists, say so.
> Confirm the local LDO pair requirements separately from bulk and T491 roles.
> No manufacture, procurement or energized testing is authorized by this request.

| Stage | What this decision closes | Required follow-through |
|---|---|---|
| Quote preparation, now | One preferred capacitor schedule and existing geometry to assess | Assemble the complete two-board quote/DFM packet; keep active/proposed identities visibly separate |
| Before coordinated active migration / populated fabrication | No existing gate is waived | Record supplier/process responses or an explicitly reviewed limited-pilot disposition; identify each unresolved internal-node/effective-C risk, then update BOM/CAD/contracts and necessary regressions together |
| Before first power | No power procedure is released | Actual source/fixture, assembly/land inspection and bounded startup/current/abort review, including the changed capacitor networks |
| Later characterization | No final performance claim | Confirm settling, rail/ripple behavior and external dummy-source performance on the separately approved assembly |

**Next: prepare the single unsent, complete two-board pilot quote/DFM packet,**
using this capacitor schedule, the actual boards/stackup and existing connector/
carrier decisions. Include exact unresolved questions and total delivered-cost
items. Do not repeat capacitor selection, create a new acceptance framework or
perform an unreviewed BOM-string migration. Once the required conditions are
disposed, apply one synchronized engineering change. Asking permission to send
that finite packet is more useful than another generic capacitor study.

## References and evidence scope

[1] Murata-authored GRM188R61C105KA12# orderable reference sheet, 2023-12-20:
https://www.farnell.com/datasheets/4087892.pdf
[2] Murata-authored GRM21BR61C106KE15# reference sheet, 2023-03-19, pp1-2:
https://www.farnell.com/datasheets/3929902.pdf
These dated mirrors support identity/body data, not current production approval.
[3] TI ADS129x debug FAQ, internal voltage list and applicability:
https://e2echina.ti.com/support/data-converters/f/data-converters-forum/207224/faq-ads1298-ads129x-ads129x
[4] TI ADS1299-4 support, Ryan Andrews on VCAP3 boost behavior:
https://e2e.ti.com/support/data-converters-group/data-converters/f/data-converters-forum/1554969/ads1299-4-data-converters-forum
[5] TI ADS1299-x SBAS499C, pin table and Figure 77:
https://www.ti.com/lit/ds/symlink/ads1299.pdf
[6] TI TPS7A20 SBVS338H, recommended operating conditions and capacitor guidance:
https://www.ti.com/lit/ds/symlink/tps7a20.pdf
[7] Retained Murata technical PDFs captured 2026-09-30; source IDs and hashes in
`checkpoints/20260930_capacitor_e1.json`. Images re-inspected 2026-10-07. Bulk
hash `c047e4b3907bd1ff7caeefaaeb2f0d5f5e5b50d66bde277b585c09604c7e026a`
(Sep.2026 label); 1 uF hash
`6690c5ca56b8ca94854c929991572b1af1c3f2ba23bc9e2db522d0b67c2c4bce`
(Oct.2026 label despite Sept.30 capture). Fresh direct retrieval did not succeed;
do not relabel the restored PDFs a current catalog/approval or guaranteed curve.
The committed facts/hashes suffice to continue; expiring archives are not required.
[8] `REV_A_100NF_REUSE_DECISION.md` and `REV_A_CAPACITOR_E1_DECISION.md` retain
100 nF and T491-specific conditions. Earlier next-task wording is superseded here.

Read-only source/frozen-netlist audit only; no new local KiCad refill, native fit
execution, vendor contact or physical measurement. No production code/tests or
framework was needed. Active engineering files and all procurement/fabrication/
powered/external-input/body-use permissions remain unchanged.
