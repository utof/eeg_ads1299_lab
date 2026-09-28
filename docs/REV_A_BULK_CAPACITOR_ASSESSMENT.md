# Rev A bulk-capacitor candidate decision — qualification target, not substitution

**Evidence date: 2026-09-27.** This advances issue #48 after the original
manufacturer snapshot in PR #50. The discontinued `GRM219R61A106KE44D` remains
in the current BOM. No component, schematic field, footprint, rail, firmware,
simulator assumption, dependency or release gate is changed by this assessment.

## Decision

Prioritize **GRM21BR61C106KE15** for the next exact-orderable and operating-envelope
qualification. It is an in-production manufacturer core and retains 10 uF,
±10%, X5R and the 0805 lateral size. Its 16 V rating is above the old part's
10 V rating, but that is **not evidence of better capacitance retention**.
This is a bounded first investigation target, not a declaration that it is the
best available part or an approved drop-in replacement. No packaging suffix is
invented, and no orderable replacement MPN is selected or purchasing authorized.

Reject **GRM21BR61A106KE19** as a lifecycle-resolution choice: the current
manufacturer snapshot marks it *To be discontinued*. Its familiar 10 V / X5R /
0805 description would not resolve the original sourcing concern. The two
other reviewed cores remain alternatives, not automatically equivalent parts.

## Four directly captured manufacturer cores

The public catalog [1] was fetched at 08:47:17 UTC; all three retained language
status columns agree. The raw channel is `jp`, and `#` is the catalog packaging
placeholder. This is not evidence of every commercial suffix, stock quantity,
last-buy date or worldwide availability. The current catalog ZIP and CSV hashes
are identical to the earlier same-day capture in PR #50; that historical record
has not been rewritten. The exact four rows and PDF receipts are retained in
`references/murata_20260927/bulk_candidate_assessment.json`.

All four cores are nominal 10 uF ±10%, 2012 metric / 0805. Dimensions and curves
come from their four distinct Sep. 2026 typical-characteristics PDFs [2], whose
identities, tables and plots were visually checked.

| Core | Status | Dielectric / rating | Body L × W × T, mm | Maximum height | Capacitance test |
|---|---|---|---|---:|---|
| GRM21BR61A106KE19 | To be discontinued (C) | X5R / 10 V | 2.0±0.1 × 1.25±0.1 × 1.25±0.1 | 1.35 mm | 1 kHz / 0.5 Vrms |
| GRM21BR61C106KE15 | In Production (B) | X5R / 16 V | 2.0±0.1 × 1.25±0.1 × 1.25±0.1 | 1.35 mm | 1 kHz / 0.5 Vrms |
| GRM21BR61E106KA73 | In Production (B) | X5R / 25 V | 2.0±0.15 × 1.25±0.15 × 1.25±0.15 | 1.40 mm | 1 kHz / 1 Vrms |
| GRM21BZ71C106KE15 | In Production (B) | X7R / 16 V | 2.0±0.2 × 1.25±0.2 × 1.25±0.2 | 1.45 mm | 1 kHz / 1 Vrms |

The old core's maximum height is 0.95 mm. Thus the three in-production candidates
increase the maximum body height by **0.40, 0.45 and 0.50 mm**, respectively.
An 0805 name does not establish identical height, terminal geometry, assembly
land compatibility or mechanical clearance. No exact termination/approved land
specification or assembly-process approval was obtained for these candidates.

### Voltage rating is not a substitute for bias evidence

At 5 V, the 16 V X5R and 25 V X5R plots each suggest roughly **5 uF**, using
coarse visual readings of typical curves. That does not demonstrate improvement
over the original part's roughly 5.5–6 uF at 5 V. The 16 V X5R uses the same
0.5 Vrms measurement level as the original; the 25 V X5R uses 1 Vrms. Their
separate typical plots are not a controlled cross-part performance ranking.

The X7R alternative's plot suggests roughly **6–6.5 uF** at 5 V under its stated
1 kHz / 1 Vrms condition. However, its generated PDF's temperature-characteristic
panel is blank. Do not report a complete temperature curve, interpret a blank
panel as flat response, or invent missing data from the dielectric label. It
also changes dielectric class and has the largest maximum height of this set.

These estimates are not manufacturer numeric exports, guaranteed minima,
production acceptance limits, or a calibrated in-circuit model. Temperature,
initial tolerance, aging, excitation, DC bias and manufacturing variation must
be addressed together for an operating-envelope requirement. Multiplying
independent typical curves is not a proof of a guaranteed lower bound. No
simulation expected value was changed to agree with this visual comparison.

## The four bulk instances are not one 40 uF capacitor

The existing validated schematic and BOM give the following node membership.
The ordinary consistency test checks each capacitor against independent U1/U2
package-pad anchors in the frozen native graph. The existing native suite
separately regenerates that graph from the current CAD.

| Existing reference | Actual node | Nominal operating context |
|---|---|---|
| C_VIN_BULK | VIN_5V_AFE | External regulated 5 V, before the 10-ohm analog feed |
| C_AVDD_BULK | AVDD | Analog rail after that feed |
| C_AVDD1_BULK | AVDD | Same electrical net as AVDD; local charge-pump supply decoupling role |
| C_DVDD_BULK | DVDD | TPS7A2033 output, nominal 3.3 V |

Therefore only **two** of these four parts are on AVDD. Summing all four nominal
10 uF values into an analog-rail effective capacitance would be wrong; their
voltages and intervening impedance differ. Equal net membership also does not
prove identical high-frequency behavior after placement and routing. The bulk
capacitors are not VCAP1's 100 uF or the reference's 22 uF tantalum capacitors.

For the selected TPS7A20, TI's recommended operating table [3, PDF page 5]
specifies effective output capacitance **0.47–200 uF**, nominal 1 uF, with
output-capacitor ESR at most **100 milliohms**. Its input-capacitor note identifies
0.47 uF as effective minimum, while clarifying that the input capacitor is not
required for LDO stability itself. These are LDO network requirements, not a
rule that each separate bulk capacitor must be at least 0.47 uF or that an
arbitrary parallel collection automatically satisfies stability. The two local
1 uF output parts and the DVDD bulk part share that output rail; their effective
capacitance, impedance and placement still need review. No regulator macromodel
compatibility result is used here as hardware validation.

`lab.rev_a_supply` already treats effective capacitance as an explicit lumped
hypothesis. Its historical 10/100 uF sensitivity cases must not be silently
relabelled as the sum of nominal BOM parts or as measurements of a candidate.
A later justified operating-envelope assessment can add separately identified
cases; it must not rewrite the original evidence.

## What the next component-change PR must establish

The first priority is the 16 V X5R core's exact orderable designation and packaging,
manufacturer approval/termination/assembly information, and actual height and
process constraints. Then establish acceptable effective capacitance at each
relevant node across the stated operating envelope, including the LDO output
network's impedance requirements. Finally verify sourcing and a delivered quote.
No current in-production catalog status guarantees future availability.

Only after those obligations are resolved should a separately reviewed change
update the four bulk BOM/CAD fields and their targeted regression expectations
together. Preserve the historical snapshots as dated facts rather than editing
them to assert that the old capture described a new part. Re-run the ordinary,
native schematic and target checks on that component-change head. Keep the
planned-stop 1 uF and 100 nF roles as distinct follow-through, not a simultaneous
unreviewed substitution of all 26 affected ceramic instances.

The current decision narrows the next qualification target and rejects a
misleading lifecycle alternative. It does not complete electrical, assembly,
cable/interface, purchasing or body-use qualification. Issue #45's land-pattern
and physical-interface decisions and issue #48 remain open.

## Tests and evidence boundary

Eight new offline tests were observed failing on the absent assessment before
it was authored. They bind the four dated core identities, all three status
languages, measurement conditions, exact open scope, and all four bulk nodes.
They also preserve the earlier catalog identity rather than becoming a live
network check or an alternative BOM. No production Python module is introduced.

Research transport is isolated in disposable read-only PR #51: no checkout,
secrets, login or repository write token. It retains bounded source receipts,
selected rows and exact PDFs, not the manufacturer's full catalog/coefficients
as product code. The branch must close without merging. The source record gives
run, artifact, file hashes and capture times; hash equality establishes integrity,
not manufacturer approval. Local review is not described as a separate subagent.
Independent @codex review and exact-head CI remain separate acceptance steps.

## Primary sources

[1] Murata public catalog and official status legend, fetched 2026-09-27.
https://ds.murata.com/simsurfing_data/data/mlcc.zip
https://ds.murata.com/simsurfing/img/supply_status/supply_status_info_en-us.png

[2] Four exact-core technical-characteristics PDFs, Sep. 2026; typical-only.
Their distinct URLs and SHA-256s are in the adjacent assessment record. Example:
https://ds.murata.com/simserve/characteristics?ReqType=TechPDF&partnumber=GRM21BR61C106KE15&techpdfname=technical_pdf_Capacitor01&lang=en

[3] TI TPS7A20 SBVS338H, recommended operating conditions and effective-C notes,
PDF page 5, visually checked. Regulator requirements, not candidate qualification.
https://www.ti.com/lit/ds/symlink/tps7a20.pdf
