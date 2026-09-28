# Rev A capacitor evidence — manufacturer snapshot, 2026-09-27

This follows merged PR #47 and issue #48. No capacitor, BOM, schematic,
footprint, firmware, simulator assumption or approval gate changes here. The
highest-value result is no longer a distributor warning: the current public
Murata catalog and five exact-core electrical-characteristics PDFs were
retrieved directly from Murata. Their URLs, capture identities and SHA-256s
are in `references/murata_20260927/source_record.json`.

## What the manufacturer actually reports

| Existing BOM role / fitted quantity | Exact selected orderable MPN | Manufacturer core status |
|---|---|---|
| Input differential / 4 | GRM1885C1H472JA01D | In Production (B) |
| BIAS feedback / 1 | GRM1885C1H152JA01D | In Production (B) |
| 1 uF decoupling / 15 | GRM188R61E105KA12D | To be discontinued (C) |
| 100 nF bypass / 7 | GRM188R71H104KA93D | To be discontinued (C) |
| 10 uF bulk / 4 | GRM219R61A106KE44D | Discontinued (D) |

Source: the five exact `part_number` rows from the public `mlcc.csv` inside
Murata's catalog [1], captured 05:31:48 UTC, and its official status legend [2],
visually checked. The three language-specific status fields agree for these
rows. The raw rows carry `channel_code=jp`; this is not a worldwide stock audit.
The catalog uses a core designation and `#` packaging placeholder; the current
BOM selects suffix D. The record preserves both identities, without a generic
rule that all possible suffixes are commercially interchangeable.

**Planned discontinuation is not already-stopped production.** Murata's legend
separates these categories and says last-time-buy/discontinuation dates may be
listed elsewhere. No manufacturer PCN or exact last-buy/stop date was obtained.
The 100 nF distributor “obsolete” label therefore must not replace Murata's
more specific current core status. The 1.5 nF distributor Active/NRND difference
also does not override the captured manufacturer In Production category.

The new finding is the **1 uF part**, previously not flagged: its 15 instances
serve AVDD/DVDD decoupling, VCAP2/3/4, and the paired LDO input/output capacitors.
In total, 26 of the 31 fitted Murata ceramic instances use stopped/planned-stop
cores: four stopped and 22 planned, not “26 already obsolete capacitors.” The
five remaining instances are the two C0G types. Counts/roles come from the BOM,
not from the manufacturer catalog. None of this is an inventory or price quote.

## Exact-core mechanical and measurement evidence recovered

All five generated electrical-characteristics sheets [3] identify the exact
core, state Sep. 2026, and explicitly limit themselves to typical specifications
requiring an approved product specification before ordering. The dimension
sketches, tables and graphs were rendered and visually checked; a successful
PDF response alone was not accepted as a completed review.

| Core / nominal value | Body L x W x T (mm) | Capacitance measurement condition |
|---|---|---|
| GRM219R61A106KE44 / 10 uF | (2.0 ± 0.2) x (1.25 ± 0.2) x (0.85 ± 0.1) | 1 kHz / **0.5 Vrms** |
| GRM188R61E105KA12 / 1 uF | (1.6 ± 0.1) x (0.8 ± 0.1) x (0.8 ± 0.1) | 1 kHz / 1 Vrms |
| GRM188R71H104KA93 / 100 nF | (1.6 ± 0.1) x (0.8 ± 0.1) x (0.8 ± 0.1) | 1 kHz / 1 Vrms |
| GRM1885C1H472JA01 / 4.7 nF | (1.6 ± 0.1) x (0.8 ± 0.1) x (0.8 ± 0.1) | 1 kHz / 1 Vrms |
| GRM1885C1H152JA01 / 1.5 nF | (1.6 ± 0.1) x (0.8 ± 0.1) x (0.8 ± 0.1) | 1 kHz / 1 Vrms |

These close the missing exact-core body/thickness and typical-characteristic
source gaps recorded in the earlier footprint review. They do **not** supply
termination length/metallurgy, a qualified PCB land, or an assembly approval.
The 0.95/0.90 mm catalog thickness fields are maxima, not nominal thicknesses.
No dimensions were inferred from a GRM prefix or a neighboring part.

The 10 uF part is a concrete exception to the generic measurement table. Murata's
measurement document [4, printed p.8] includes a note that specified parts may
use different AC levels; use this exact part's 0.5 Vrms, not an automatic 1 Vrms
rule based only on nominal capacitance and rated voltage. AC excitation is not
the DC rail voltage and is not a stated ripple requirement for our circuit.

## DC-bias implications — typical evidence, not minimum capacitance

The exact 10 uF sheet's DC-bias plot at 1 kHz / 0.5 Vrms shows roughly 40–45%
capacitance loss near 5 V. A deliberately low-precision visual reading gives
about **5.5–6 uF**, computed as 10 uF times the remaining fraction. Near 3.3 V,
the same plot suggests roughly 7–8 uF. These are approximate plot readings of
typical data, not extracted vendor numeric tables or guaranteed lower bounds.

The exact 1 uF / 25 V part also has visible DC-bias dependence; it is not exempt
because its rating is much higher than the rail. Its typical curve is roughly
0.8 uF near 5 V under its stated 1 kHz / 1 Vrms condition. The 100 nF curve stays
near nominal in the 0–5 V region at that sheet's plotting resolution. The C0G
technical exports show flat typical AC/DC-bias curves. Murata explains the small
C0G bias effect in [4, p.7]; this is not proof of zero variation or a waiver of
initial tolerance, temperature or assembly effects.

For our design, VIN/AVDD bulk parts see approximately the 5 V condition, while
the DVDD bulk part sees approximately 3.3 V. The 1 uF parts have distinct rail,
VCAP and regulator roles. A part number's single typical curve must not become
a universal in-circuit capacitance across all those nodes.

`lab.rev_a_supply` already accepts **effective** capacitance as an explicit
hypothesis, separate from nominal BOM capacitance. Keep its historical cases
and results intact. These new plots motivate its lower-capacitance sensitivity
cases; they do not calibrate it or prove the chosen source/load waveforms.
Do not multiply independent typical AC-, DC-, temperature- and aging-curves
into a purported guaranteed minimum. The measurement method (including 60 s DC
hold and 25 ± 3 °C in [4, p.8]) is not our full operating envelope.

The public catalog's internal curve coefficients were not reverse-engineered
into a new capacitor model. The retained record contains selected factual
fields only; it is neither a new device registry nor a production lookup API.

## Land-pattern distinction that must not be lost

Murata's measurement document has a 1608/2012 land table [4, p.5]. It describes
the **S-parameter measurement fixture**, not an assembly recommendation. For
example, its 1608 drawing gives a=0.8, b=0.7, c=0.8 mm; its 2012 drawing gives
1.2/0.7/1.1 mm. The installed KiCad lands are not changed to those numbers.
A test fixture, body outline and soldering land strategy are different evidence.
The KEMET/SOT/header decisions under issue #45 are also untouched.

## What is now actionable, and what remains blocked

Before final manufacturing choices, prioritize a narrowly reviewed lifecycle
resolution for the 10 uF, 1 uF and 100 nF roles. Retained inventory may exist;
current core status does not establish stock exhaustion. No replacement is
selected here. Any proposed replacement needs its own exact lifecycle,
termination/body, land/height, voltage/dielectric/tolerance and effective-C
review at the relevant nodes, followed by synchronized BOM/CAD/evidence tests.
A distributor's substitute list is not equivalence proof.

Issue #48 stays open for manufacturer notices/dates where needed, exact approval
and termination/assembly information, actual operating-envelope/effective-C
justification, and any subsequent replacement decision. This step resolves the
primary-source access gap, not those physical/procurement decisions. All release,
purchasing, firmware-review and body-use gates remain false.

## Retrieval, verification and reproducibility

The initial old PDF links returned 403/404; an indexed page and retailer PCN
link were not accepted as a notice containing the selected parts. A disposable
read-only Actions branch/PR #49 captured the public catalog shell, then the
current normal public data URLs. No login, CAPTCHA solving, private catalog
mode, secrets, repository checkout or write-capable capture job was used.
The workflow is research transport only and must close without merging.

The raw catalog ZIP/CSV digests, capture runs and original PDF digests are in
the source record. Only the selected factual row fields are committed, not the
full catalog, model coefficients, manufacturer's JavaScript or a network CI
dependency. Original downloaded sheets and retrieval receipts are retained in
the conversation evidence package. Their hashes were checked after download.

Eight offline tests bind this dated snapshot to the five current BOM parts,
31 quantities, distinct status classes, exact measurement levels and explicit
unqualified scope. They do not poll Murata or authenticate a future website.
A later component change must supply/review fresh evidence rather than editing
this historical record to pretend the 2026-09-27 capture said something else.
No production Python module, simulator or firmware is added by this slice.

## Primary sources

[1] Murata current public catalog, exact core rows, fetched 2026-09-27.
https://ds.murata.com/simsurfing_data/data/mlcc.zip

[2] Official English status legend and icons B/C/D, fetched and visually checked.
https://ds.murata.com/simsurfing/img/supply_status/supply_status_info_en-us.png

[3] Five exact-core electrical-characteristics PDFs, generated Sep. 2026.
Complete per-core URLs and SHA-256s are in the source record. Example (not a
substitute for the other four distinct files):
https://ds.murata.com/simserve/characteristics?ReqType=TechPDF&partnumber=GRM219R61A106KE44&techpdfname=technical_pdf_Capacitor01&lang=en

[4] Murata SimSurfing measurement conditions, September 2022, printed pp.5,7–8.
https://ds.murata.com/simsurfing_data/pdf/en-us/mlcc/sim_mlcc_measuringcond_e.pdf
