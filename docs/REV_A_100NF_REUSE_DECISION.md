# 100 nF pilot decision: reuse the existing auxiliary identity

2026-10-07; inspected main `91857999f30f179d087e741a85d558a19b584a1e`,
complete source tree `6254649a8999fb70d6937bafed3d451558f281ac`.

**Decision: use KEMET `C0603C104K5RACTU` as the preferred quotation/qualification
identity for all seven AFE 100 nF sites.** Together with the 15 already-selected
auxiliary parts, this proposes 22 fitted instances of one orderable identity.
Do not add the previously shortlisted 100 V Murata family merely to replace
this role. This closes the candidate-choice question, not populated-fabrication
acceptance: land/process approval and applicable effective-capacitance evidence
or an explicit pilot-risk disposition are still required by #45/#48.

The active AFE BOM still specifies `GRM188R71H104KA93D`; no substitution is made
here. Keep that BOM, both authored PCBs, firmware, models and source contracts
unchanged until the coordinated ceramic migration is reviewed. The dated Murata
catalog evidence and earlier shortlist remain historical records, not overwritten.
No source-file hashes are being changed to conceal a component substitution.

## Electrical fit: same nominal requirement, not a proven identical response

KEMET's standard X7R ordering table decodes this identity as 100 nF, 10%, 50 V,
0603, matte-tin termination, TU unmarked 7-inch reel [1, p2]. These nominal
values match the current AFE `decap_100n` role without reducing voltage rating
or changing dielectric class. This is the standard termination, not FT-CAP.
It is not an assertion of identical biased capacitance, ESR, ESL or microphonics.

The existing validated native-netlist fixture and authored PCB agree on:

| Native ref / contract ref | Actual connection | Preserve this companion/network |
|---|---|---|
| C23 / C_VCAP1_HF | VCAP1 to GND | C6, nominal 100 uF; do not replace it with this 100 nF |
| C24 / C_VCAP3_HF | VCAP3 to GND | C9, nominal 1 uF, remains in parallel |
| C25 / C_REF_HF | VREFP to GND | C7, nominal 22 uF; VREFN is GND in this design |
| C26 / C_AVDD_HF | AVDD to GND | Existing analog-supply local bypass network |
| C27 / C_AVDD1_HF | AVDD to GND | Separate physical AVDD1 bypass/return, despite the same net name |
| C28 / C_DVDD_HF | DVDD to GND | Existing local regulator output/bypass network |
| C29 / C_VIN_HF | VIN_5V_AFE to GND | Existing local regulator input/bypass network |

TI's pin requirements and Figure 77 support keeping these parallel bypasses and
node-specific companion capacitors [2, pp6-7,71]. In particular, the reference
minimum is 10 uF for its network, not a requirement that this 100 nF alone meets.
The LDO effective-output requirement is likewise not a minimum for each 100 nF.
The 1 uF VCAP3 companion remains in the separate 1 uF migration decision.

**No guaranteed in-circuit minimum for this exact capacitor was established.**
A 50 V rating is not a DC-bias retention curve, and X7R's temperature class does
not bound combined bias, aging, initial tolerance and AC excitation [1, pp1,16].
Do not infer internal VCAP voltage/startup bounds from the 5 V supply label or
multiply separate typical curves into a guaranteed corner. This review supports
a same-nominal-value candidate, not an all-condition electrical equivalence.
No source simulation or acceptance threshold was recalibrated.

## Physical fit: measure the actual lands, not the package name

All seven AFE sites and C101-C115 use `Capacitor_SMD:C_0603_1608Metric`, with
identical local pad sizes/centres and courtyard dimensions in the authored boards.
KEMET's current family table selects thickness code **CJ** for C0603C / 104 /
50 V: body **1.60 +/- 0.15 by 0.80 +/- 0.15 by 0.80 +/- 0.15 mm** [1, pp3,5,9].
Use **1.75 x 0.95 x 0.95 mm maximum body** in the pilot envelope, not a nominal
0.80 mm height or an assumed 0.87 mm maximum. A tighter exact-part specification
can supersede this only when identified and reviewed. Mounted height must also
allow solder standoff; this body envelope is not a carrier-fit qualification.

The centred maximum body fits inside the existing 2.96 x 1.46 mm courtyard.
That observation excludes placement error, solder, PCB tolerances and neighbouring
body tolerances; it does not qualify assembly or the final mechanical fixture.

KEMET Table 3's dimension **C is half the pad-centre spacing**, not the gap:

| Local dimension (mm) | Existing authored land | KEMET density B [1, p12] |
|---|---:|---:|
| Pad centres from component origin | +/-0.775 | +/-0.800 |
| Pad length along body (Y) | 0.900 | 0.950 |
| Pad width across body (X) | 0.950 | 1.000 |
| Inner copper gap, 2C - Y | 0.650 | 0.650 |
| Outside copper span, 2C + Y | 2.450 | 2.550 |
| Courtyard length x width | 2.960 x 1.460 | 3.100 x 1.500 |

**The existing land is not KEMET's exact density-B recommendation.** Each pad
is 0.05 mm shorter and narrower; unchanged gap does not prove an equivalent joint.
Existing pads also have 0.225 mm rounded corners. At maximum body width, nominal
side protrusion is zero before alignment/process tolerances. Do not approve the
land by interpolating between density B and C or by quoting a clean native DRC.
KEMET calls for qualification before adopting minimum-land variations [1, p12].

Keep the current copper for the quotation. Ask the assembler to disposition the
actual lands, paste/mask, placement and reflow process at all 22 proposed sites.
If that land is rejected, make one reviewed, targeted footprint change during
ceramic migration; do not edit the global stock 0603 footprint or move all 0603
components. A native refill/DRC, bypass/return checks and mechanical review would
then be required on the actual changed source. Do not silently accept a new
courtyard collision. The present decision does not authorize that future change.

## The finite pre-fabrication questions

Include the following in the existing **unsent** pilot quotation/DFM request:

> Proposed 100 nF identity: C0603C104K5RACTU, 22 fitted per two-board set
> (AFE C23-C29: 7 proposed replacements; auxiliary C101-C115: 15 retained).
> Please quote this exact suffix, traceable supply/lot and applicable current
> product specification/status, not an unapproved substitute. Confirm maximum
> body dimensions and your assembled-height allowance. Review the actual
> rounded lands/courtyards above, stencil/mask, solder alloy and reflow process;
> either accept the deviation with process rationale or request explicit changes.
> Provide applicable capacitance-versus-bias/temperature/aging information and
> its status as typical or guaranteed. Record any unavailable information for
> explicit node-specific pilot disposition before populated fabrication.

KEMET supplies general reflow guidance [1, p13], not approval of our board/stencil
or other components. No manufacturer full-suffix lifecycle/PCN/stock/price audit
or lot-specific approval was obtained in this slice; table availability is not
stock confirmation. Exact-part web-sheet access did not succeed. Do not label
this identity newly lifecycle-qualified just because it is already in the
auxiliary contract. No vendor was contacted and no quote/order was placed.

## Next build decision, without another generic study

Finish the existing **15 x 1 uF and 4 x 10 uF** candidate disposition together:
internal-VCAP rating/retention for the former, and effective capacitance plus
1.35 mm maximum-height impact for the latter. Retain the current C0G and T491
identities. Combine those outcomes with this 100 nF decision in **one** coordinated
pilot BOM/CAD/assembly change or an explicit rejection—not three independent
BOM-string substitutions. Update the active BOM, schematic/PCB MPN fields,
applicable contracts/fixtures and targeted regressions together only after review.

That follow-through covers the 26 AFE instances with recorded lifecycle concerns;
it does not replace stackup, connector, delivered-cost or commissioning review.
#45/#48 stay open. Supplier confirmation is needed before the stage relying on
it, not a reason to block independent quote preparation or to start another
power-budget framework. No production code or additional validation framework is
needed for this decision. Existing regression suites remain in force.

## Source and verification scope

This was a read-only audit of current source geometry and the validated frozen
netlist, not a new local native refill, assembled inspection or electrical test.
Source identities: AFE PCB SHA256
`60097ff4acf8408d5a172930de74bcd36aa50a379dd30a831e4bc64d3841c8a6`;
BOM Git blob and both board identities are recoverable from the inspected tree.
The normal project gate and PR review validate the published documentation slice;
neither authorizes the proposed component migration or a physical procedure.

[1] KEMET, C1002_X7R_SMD, revision 2025-02-20. Ordering p2, dimensions p3,
selection p5, thickness p9, assembly lands p12, reflow p13, electrical conditions
p16. Relevant page images inspected on 2026-10-07:
https://content.kemet.com/datasheets/KEM_C1002_X7R_SMD.pdf

[2] TI, ADS1299-x SBAS499C, revised January 2017, pin table and Figure 77;
relevant page images inspected on 2026-10-07:
https://www.ti.com/lit/ds/symlink/ads1299.pdf

Purchasing, fabrication, powering, external-input acquisition and body-use gates
are unchanged. A source merge is not assembly or electrical qualification.
