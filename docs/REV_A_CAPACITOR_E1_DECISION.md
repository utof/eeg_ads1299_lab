# Capacitors under E1: shortlist and node-specific requirements

**2026-09-30; base905347aa361669af0634fd84688b1ce7b3755e07,
tree998bc610dc5d956967dad697e5a0623495c94357.** Authored PCB SHA256
`5da65b4307f0336883da9aeae48711b28c1944ec587f5d3174f12db4e9921875`.
The dated facts and numerical comparisons are in
`checkpoints/20260930_capacitor_e1.json`.

## Decision: three qualification identities, not a BOM substitution

Retain the existing C0G and T491 design choices; this review finds no reason to
replace them merely to resolve the three legacy ceramic roles. Use this finite
shortlist for the next component qualification/migration decision:

| Role / fitted instances | Qualification identity | Decision and open condition |
|---|---|---|
| 10 uF X5R / 4 | **GRM21BR61C106KE15L** | Retain the previously identified16-V/0805 target; maximum height1.35mm versus old0.95mm, with effective-C and assembly still open |
| 1 uF X5R / 15 | **GRM188R61C105KA12D** | New16-V/0603 target, same nominal C, tolerance and dielectric; not an automatic replacement for a25-V part at internal VCAP nodes |
| 100 nF X7R / 7 | **GRM188R72A104KA35D** | New100-V/0603 target, same nominal C/tolerance/dielectric; reconcile the distributor NRND warning before claiming lifecycle closure |

The three manufacturer cores are currently B. The two new D suffixes are
explicitly listed in manufacturer-authored reference sheets, not copied from
old BOM suffixes:180-mm paper tape,4000 pieces per manufacturer reel [1-3].
Cut-tape sourcing need not require a whole reel; no price, stock or delivered
quote is established here. The bulk's L suffix remains the prior documented
embossed-tape target, not D.

**#48 stays OPEN.** No component, copper, schematic, BOM, firmware, model,
dependency, design rule or approval flag changes in this review. These targets
are neither already-qualified replacements nor an order authorization.

## Current lifecycle evidence and its boundaries

Fresh direct Murata catalog capture agrees with the historical September27
core statuses, without rewriting that historical record:

| Current BOM role | Current exact MPN | Fitted quantity | Captured core state |
|---|---|---:|---|
| bulk_10u | GRM219R61A106KE44D | 4 | D, Discontinued |
| decap_1u | GRM188R61E105KA12D | 15 | C, To be discontinued |
| decap_100n | GRM188R71H104KA93D | 7 | C, To be discontinued |
| input_c | GRM1885C1H472JA01D | 4 | B, In Production |
| bias_c | GRM1885C1H152JA01D | 1 | B, In Production |
| vcap1 / vref | T491D107K016AT / T491B226K016AT | 1 / 1 | Outside the Murata query; no exact-orderable lifecycle conclusion |

Thus **four instances are discontinued and22 are planned-stop**, not26 already
obsolete. All three catalog language-status fields agree; channel is `jp` and
public core identifiers use a packaging placeholder. This is not a last-buy
date, manufacturer EOL notice, stock-exhaustion claim or full-suffix guarantee.

The bounded GRM18/0603/1-uF/10%-tolerance X5R-or-X7R query found no B rows at
25/35/50V, but found GRM188R61C105KA12 at16V. It does NOT establish market-wide
unavailability of a25-V alternative. GRM185R61E105KA12 remains C; the checked
GRM188R61E105KAAD has raw N, not B. Neither passes the B-only screen. Active
GRM188D71H105KE01 is X7T, not the retained X5R/X7R class, and was not adopted.
The exact queried GRM188R71H104KA01 row was absent; that alone does not prove
discontinuation. No distributor substitute table is used as equivalence proof.

### Preserve the real lifecycle conflict

The100-nF core is B in the current manufacturer catalog and its2024 reference
sheet shows In Production. A current Farnell listing nevertheless carries
**Not Recommended for New Design** [4]. That is the retailer's own label, not
a manufacturer discontinuation notice. Do not ignore it, declare the part
obsolete on that basis alone, or pretend the full-orderable status is resolved.
Obtain the applicable current notice/approval and exact-suffix confirmation.

The two new manufacturer-authored reference sheets are dated2023-12-20 and
2024-12-19, hosted on Farnell [2,3]. They explicitly warn that they are typical
reference information and may be stale. They establish dated order identities,
not current detailed approval specifications. Current technical PDFs were also
captured directly for the three cores. The1-uF sheet says **Oct.2026** although
captured2026-09-30T15:00:01Z; retain both facts, not a backdated source label.
The bulk and100-nF technical sheets say Sep.2026.

The new0603 candidates have1.6±0.1 by0.8±0.1 by0.8±0.1mm bodies. Their reference
terminal dimensions are e0.2–0.5mm and gap g>=0.5mm. These are body/termination
facts, NOT production assembly-land, paste, solder or clearance approval. No
S-parameter measurement-fixture land table is adopted for assembly.

## Effective capacitance depends on the actual node

The existing public schematic validator checks the frozen canonical XML export
against the current BOM/profile. The reproduction below then derives all33
fitted capacitor instances and their actual networks. This offline graph check
is not a new native KiCad execution; final-head native CI is separate.

| Node / native references | Nominal sum | Applicable requirement or open question |
|---|---:|---|
| VIN_5V_AFE: C19/C20/C29/C30 | 12.1 uF | C19/C20 are the local2-uF input pair. TI recommends>=0.47uF effective against source R/L effects, although CIN is not required for LDO stability itself [5] |
| DVDD: C17/C18/C21/C22/C28/C33 | 14.1 uF | C21/C22 are the local2-uF output pair. Effective output network0.47–200uF and ESR<=0.1ohm [5]; remote same-net caps are not automatically equivalent local bypasses |
| AVDD: C11–C16/C26/C27/C31/C32 | 26.2 uF | C31/C32 are the TWO nominal10-uF bulk parts here. Preserve local bypass guidance/topology [6]; no actual load/timing-based effective minimum is established |
| VREFP: C7/C25 | 22.1 uF | TI requires minimum10uF. C7's nominal tolerance-only low corner19.8uF is not an all-condition in-circuit guarantee [6] |
| VCAP1: C6/C23 | 100.1 uF | TI specifies100uF; current parallel100nF remains. The LDO0.47-uF rule does not apply [6] |
| VCAP2: C8 | 1 uF | Preserve TI's1-uF nominal connection; review actual internal bias, startup and impedance [6] |
| VCAP3: C9/C24 | 1.1 uF | Preserve TI's1uF+0.1uF parallel arrangement and reviewed return [6] |
| VCAP4: C10 | 1 uF | Preserve TI's1-uF nominal connection; internal voltage is not inferred from external E1 rails [6] |

C1–C4 are differential4.7-nF input capacitors, not ground shunts. C5 is the
1.5-nF BIAS feedback element; BIAS remains disabled. Do not add these to supply
capacitance or remove their source requirements because a mode is off.

A2-uF local LDO pair needs23.5% of nominal capacitance to reach0.47uF. Relative
to its simple1.8-uF initial-tolerance corner, the fraction is26.11%. These are
requirement comparisons, NOT evidence that the proposed parts retain those
fractions. ESR and actual local network geometry still matter. The output
requirement is not an independent minimum for every capacitor on the board.

The current technical plots are **typical only**. Bulk is characterized at
1kHz/0.5Vrms; the1-uF and100-nF candidates at1kHz/1Vrms. Bias, excitation,
initial tolerance, temperature and aging cannot be multiplied as independent
typical plots into a guaranteed joint minimum. All three candidate minimum-C
fields remain null. No visual curve estimate recalibrates a source model.

E1's20–30°C room condition does not by itself bound capacitor self-heating or
aging since the last de-aging/reflow event. Its external rail limits do not
bound internal VCAP transients. Reducing25V to16V therefore needs a pin-specific
review, not simply a5V/16V ratio. The old ideal supply model's4-ms observation
window is not the physical startup requirement; the0.10-uV coherent supply-error
allocation does not by itself determine required stored charge.

## T491 decisions must not use the LDO's ESR limit

The current direct KEMET T491 PDF is revision2026-07-08 and has the same hash
as the existing land-pattern source. It lists the22-uF/16-V B and100-uF/16-V D
rating rows [7]. Their maximum ESRs at25°C/100kHz are respectively2.2ohm and
0.7ohm. Neither is on TPS7A20's output; rejecting them against its0.1ohm criterion
would be a network error. Actual reference/charge-pump performance and settling
still require their own evidence.

KEMET recommends application voltage50% of rating through85°C, or8V for these
16-V parts. C7's nominal4.5-V reference is below that recommendation; this does
not authorize reverse bias or unbounded startup/ripple. Rated-voltage leakage
limits at25°C after5minutes are16uA forC6 and3.5uA forC7, not asserted leakage
at their real operating bias or a guaranteed ADC startup time. Preserve the
already-reviewed density-B lands. A current family table is not a full-orderable
lifecycle, assembly-process or procurement clearance.

## One qualification request, then one synchronized migration

For the three named targets, obtain current exact-suffix status/notices, the
manufacturer approval specification, termination and permitted assembly/land/
paste/reflow information. Resolve the100-nF NRND discrepancy and check the
bulk's extra0.40mm maximum body height. Request effective-C/impedance evidence
with the actual DC bias, AC excitation, temperature, initial tolerance, time
since de-aging and intended operating interval stated. No supplier request
was sent, no current full approval sheet was obtained and no parts purchased.

Enforce the actual LDO network limits and reference minimum; preserve VCAP
nominal arrangements and justify their bias/impedance/startup behavior. When
only typical data is available, a **separately reviewed limited pilot-part risk
disposition and later person-disconnected measurements** are alternatives to
production qualification, not a way to mark the unknown minimum established.
Do not demand measurements of an as-yet unbuilt board, or infer pilot permission
from this shortlist. Existing firmware/release gates remain unchanged.

After applicable evidence or explicit limited pilot-risk review, make ONE
synchronized component-change PR for BOM, schematic fields, PCB fields and
targeted tests. Trace all26 affected instances individually; internal VCAP
roles may need a different decision from rail decouplers. Do not update only
BOM strings, transfer the old D suffix to the bulk-L target, or rewrite historical
snapshot tests. That migration is not performed here.

**Next independently executable slice: mechanical/assembly envelope review**
using these specific body/height candidates, existing T491 lands and headers/
mates. Keep #48's lifecycle/approval/biased-C requests and #45's factory-stack/
interface questions explicit while advancing that finite source work. Do not
spend the next turn merely rediscovering this catalog or declare #48 closed.

## Reproduce the source-bound accounting

Run this exact block from the repository root with the pinned environment.
It derives all33 instance nodes, eight nominal shunt totals, affected quantities,
local-bank and reference comparisons. It checks the retained open-state fields,
not real Ceff or live manufacturer status. Original captures' hashes and dated
factual extracts are retained in the checkpoint; an expired artifact is not
needed to continue from the named candidates and these requirements.

```python
import gzip
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path
from hardware.rev_a import load_documents, parse_schematic_xml, validate_schematic

record = json.loads(Path("docs/checkpoints/20260930_capacitor_e1.json").read_text())
assert (
    hashlib.sha256(Path("hardware/rev_a/layout/rev_a.kicad_pcb").read_bytes()).hexdigest()
    == record["board_sha256"]
)
profile, bom, _ = load_documents()
netlist = parse_schematic_xml(
    gzip.decompress(Path("tests/fixtures/rev_a_netlist.xml.gz").read_bytes()).decode()
)
assert validate_schematic(netlist, profile, bom) == []
assert not any(profile["gates"].values())
roles = [r for r in bom["line_items"] if "capacitance_f" in r["spec"] and r["population"] == "fit"]
anchors = {
    "VIN_5V_AFE": ("U2", "1"),
    "AVDD": ("U1", "19"),
    "DVDD": ("U2", "5"),
    "VCAP1": ("U1", "28"),
    "VCAP2": ("U1", "30"),
    "VCAP3": ("U1", "55"),
    "VCAP4": ("U1", "26"),
    "VREFP": ("U1", "24"),
}
ground = netlist.nets["U2", "2"]
totals, inventory, states = dict.fromkeys(anchors, 0.0), [], Counter()
for role in roles:
    assert role["quantity"] == len(role["references"])
    if role["manufacturer"] == "Murata":
        states[record["manufacturer_catalog"]["states_by_current_core"][role["mpn"][:-1]]] += role[
            "quantity"
        ]
    for ref in role["references"]:
        pins = {netlist.nets[ref, "1"], netlist.nets[ref, "2"]}
        found = [
            label for label, anchor in anchors.items() if pins == {ground, netlist.nets[anchor]}
        ]
        assert len(found) <= 1
        value = role["spec"]["capacitance_f"] * 1e6
        label = found[0] if found else role["id"]
        if found:
            totals[label] += value
        else:
            assert ground not in pins and role["id"] in ("input_c", "bias_c")
        inventory.append(
            {
                "native_ref": netlist.parts[ref].native_ref,
                "contract_ref": ref,
                "node": label,
                "nominal_uF": value,
            }
        )
assert states == {"D": 4, "C": 22, "B": 5}
counts = {
    "fitted_capacitors": len(inventory),
    "discontinued_core_instances": states["D"],
    "planned_stop_core_instances": states["C"],
    "C0G_core_B_instances": states["B"],
    "tantalum_instances": len(inventory) - sum(states.values()),
}
assert counts == record["counts"] and len(inventory) == 33 and len(roles) == 7
for key, value in totals.items():
    assert math.isclose(value, record["nominal_shunt_uF"][key], rel_tol=1e-12, abs_tol=1e-12), key
parts = {r["native_ref"]: r for r in inventory}
for name, refs, node in (
    ("LDO_input", ("C19", "C20"), "VIN_5V_AFE"),
    ("LDO_output", ("C21", "C22"), "DVDD"),
):
    assert all(parts[r]["node"] == node for r in refs)
    assert (
        sum(parts[r]["nominal_uF"] for r in refs)
        == record["node_requirements"][name]["local_nominal_uF"]
        == 2
    )
    assert list(refs) == record["node_requirements"][name]["refs"]
output = record["node_requirements"]["LDO_output"]
assert (output["effective_min_uF"], output["effective_max_uF"], output["ESR_max_ohm"]) == (
    0.47,
    200,
    0.1,
)
assert record["node_requirements"]["LDO_input"]["recommended_effective_min_uF"] == 0.47
assert record["node_requirements"]["VREF"]["minimum_uF"] == 10
ref = next(r for r in roles if r["id"] == "vref")
ref_low = ref["spec"]["capacitance_f"] * 1e6 * (1 - ref["spec"]["tolerance_fraction"])
assert math.isclose(ref_low, record["node_requirements"]["VREF"]["nominal_tolerance_only_low_uF"])
calculated = {
    "local_LDO_nominal_retention_for_0_47uF": 0.47 / 2,
    "local_LDO_tolerance_only_low_uF": 2 * 0.9,
    "retention_of_tolerance_corner_for_0_47uF": 0.47 / (2 * 0.9),
    "VREF_nominal_tolerance_only_margin_ratio": ref_low / 10,
    "T491_recommended_application_V_at_E1_temperature": ref["spec"]["rated_voltage_v"] * 0.5,
}
for key, value in calculated.items():
    assert math.isclose(
        value, record["arithmetic_not_effective_C_guarantees"][key], rel_tol=1e-12, abs_tol=1e-12
    ), key
assert len(record["qualification_targets"]) == 3
for target in record["qualification_targets"]:
    assert target["status_codes"] == ["B", "B", "B"]
    assert target["candidate_mpn"].startswith(target["core"])
    assert target["guaranteed_effective_min_uF"] is None
    assert not target["BOM_adopted"] and not target["assembly_qualified"]
assert not record["retailer_conflict"]["resolved"]
assert (
    not record["BOM_changed"]
    and not record["approval_changes"]
    and not record["physical_measurements"]
)
for item in (
    record["technical_sheets"]
    + record["order_code_references"]
    + record["capture_archives"]
    + [record["T491"]]
):
    assert re.fullmatch(r"[0-9a-f]{64}", item["sha256"])
print(
    json.dumps(
        {
            "instances": sorted(inventory, key=lambda r: int(r["native_ref"][1:])),
            "nominal_shunt_uF": totals,
            "counts": counts,
            "derived_context_not_Ceff": calculated,
        },
        indent=2,
    )
)
```

The accounting and wrong-data controls must be executed on the published final
head before claiming their completion. They are documentation-analysis checks,
not new project tests, native circuit faults or physical measurements. The
ordinary baseline gate on clean905347 passed1091tests+14subtests and86.06%
branches with the71%floor unchanged. Baseline success does not validate this
later source; consult the PR's actual final-head CI/review separately.

## References and provenance

[1] Murata direct public catalog and exact-core technical sheets. Full URLs,
recorded values, capture times, printed dates and original digests are retained
in the checkpoint. https://ds.murata.com/simsurfing_data/data/mlcc.zip
[2] Murata-authored1-uF reference,2023-12-20, mirrored byFarnell:
https://www.farnell.com/datasheets/4087892.pdf
[3] Murata-authored100-nF reference,2024-12-19, mirrored byFarnell:
https://www.farnell.com/datasheets/4459608.pdf
[4] Retailer label conflict, not technical approval:
https://at.farnell.com/murata/grm188r72a104ka35d/kondensator-0-1-f-100v-10-x7r/dp/1828921
[5] TI TPS7A20 SBVS338H,pp5,27:
https://www.ti.com/lit/ds/symlink/tps7a20.pdf
[6] TI ADS1299 SBAS499C,pp6–7,70:
https://www.ti.com/lit/ds/symlink/ads1299.pdf
[7] KEMET T2005_T491,2026-07-08,pp9–10,14:
https://content.kemet.com/datasheets/KEM_T2005_T491.pdf

Primary PDF tables/plots and both reference order-code/body pages were visually
inspected. Current KEMET bytes match the earlier land-reference hash; current
Murata bytes have their own recorded dates/hashes. No font or full catalog/model
archive is needed as a project dependency. Source capture36732187218 restored
the exact existing GitHub main; manufacturer captures36732577801,36732949793,
36733353894 and36734742508 are research transport, not physical qualification.
Temporary workbench/capture scripts are outside the product tree. No supplier
contact, purchase, fabrication, powered connection or body use was authorized.
