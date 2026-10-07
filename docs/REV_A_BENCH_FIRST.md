# Bench first: provisional power and the shortest responsible pilot path

Decision basis: the user confirmed **no power supply is selected**, permitted
reasonable assumptions, and asked for practical engineering without needless
modelling or architecture. This supersedes S4's instruction to stop and ask for
a source model. S1–S4 remain historical evidence; their unknown physical inputs
are not overwritten. Baseline reviewed here: main `3324fc8c` (PR85).

## 1. Working choice: regulated 5 V, not a raw battery

For the first person-disconnected prototype, plan around an **off-the-shelf,
regulated bench supply set to 5.00 V**, with adjustable current limiting and an
output-enable control. Borrowing a suitable instrument is preferable to designing
a power supply. This is a source-class decision, not a purchased model, approved
instrument configuration, measured output or change to the hardware BOM.

| Quantity | Provisional planning choice | What it means |
|---|---|---|
| Source at its output terminals | 5.00 V; target 4.95–5.05 V over the intended steady load/temperature range | Procurement/test requirement; not established performance of an unidentified supply |
| Available continuous capacity | At least 1 A at 5 V | Capacity only, not board consumption or the initial current-limit setting |
| Shared-source load for sensitivity | 1 A total | Deliberately selected stress scenario, NOT a proven peak/operating ceiling |
| Source leads, both directions, including interfaces to J105 | At most 0.050 ohm total | Planning target at operating conditions; excludes board-local feed/ground terms |
| Analog-branch example | 10 mA through existing R11 | Same conditional example as S3, NOT a measured or guaranteed load |

Actual source identity, current-limit accuracy/response, startup overshoot, ripple,
output capacitance and instrument grounding must be checked before a powered
procedure is approved. A current limiter is not instantaneous protection against
stored energy and does not establish body safety. Do not set it to 1 A merely
because that is the capacity target. Do not raise voltage to hide cable loss.
The two DevKit USB ports remain excluded with accessories; use the existing
power-input/console contracts, not a new USB wiring arrangement.

**Why not a bare battery?** The ADS1299 analog supply requires 4.75–5.25 V [1].
A nominal 3.7 V cell is not a 5 V source; a 9 V battery is too high for direct
connection. Battery voltage alone is not a supply specification. Later battery
operation can use an enclosed commercial battery pack with a regulated 5 V
output, subject to the SAME input checks. Keep charging disconnected during any
future bench capture. Verify regulation/ripple, shutdown and low-load behavior;
do not assume every USB power bank satisfies this envelope. No cell, charger,
boost converter or battery-management circuit is being added to Rev A.

Bench supplies provide adjustable voltage/current for prototype investigation
[2]; choosing that capability avoids debugging a new battery subsystem alongside
the ADC. This is an engineering recommendation, not approval of an unnamed unit.

## 2. One budget check, using the existing method

At the stated hypothetical 1 A and 0.050 ohm, the common-pair loss is 50 mV.
At 10 mA and R11's initial +1% value (10.1 ohm), its loss is 101 mV. Therefore:

    4.950 V - 0.050 V - 0.101 V = 4.799 V
    4.799 V - 4.750 V = 0.049 V = 49 mV

**49 mV remains for ALL omitted analog-feed/local-return losses**, not 49 mV
per connector. The common source return was already charged once. At an assumed
20 mA through R11, the same partial calculation becomes 4.698 V: it would fail
even before the omitted losses. This exposes sensitivity to actual load; it
is not a prediction that the board consumes 10 or 20 mA.

The 5.05 V upper source endpoint does not by itself close signed ground-offset,
startup or transient checks. Do not call this a full eight-row worksheet pass.
Keep `docs/studies/s3_acceptance.json` unchanged. Reuse `tools.dc_budget` and S3
when real inputs arrive; no second calculator or instrument API is needed.

## 3. Architecture decision: keep the small modular repo

Targeted inspection covered `tach.toml`, `tools/dc_budget.py`, `tools/check.py`,
S1–S4 executable notes/tests, `lab/recording.py`, `lab/acquisition.py`, and the
existing architecture review. This is not an exhaustive audit of every subsystem.

- Keep pure supply calculations in the existing 189-line `tools/dc_budget.py`;
  keep scientific simulation separate from the standard-library hardware checks.
- Keep `tools.check` as the single orchestrator and `tach.toml` as the dependency
  boundary contract. Its long snapshot list is not a reason to build a plugin or
  service framework. Do not reorganize healthy code just to reduce file length.
- Keep synthetic recording persistence distinct from bench capture. Do not make
  the synthetic schema the owner of future measured-data semantics.
- Stop adding successive generic supply-study modules. S3 is already the solver;
  S4 is already the conditional source evidence. A small supported CLI may be
  justified when repeated actual measurements require it, not pre-emptively.
- Retain existing fault/provenance tests. Add a new test only for behavior, a
  defect, or an important discoverability contract—not to turn every sentence
  or hypothetical value in an engineering note into a software feature.

No production-code refactor is warranted by this inspection. The concrete change
is the decision/workflow, with a small link regression. No dependency, numerical
rule, CI deadline, source snapshot or existing test is removed or weakened.

## 4. Stop making bench evidence a prerequisite for every paper decision

The first useful hardware milestone is **a reviewed, person-disconnected pilot
that can produce the ADC's internal test signal**—not human EEG or final noise/
EMC qualification. Keep the current two-board design; do not reconstruct copper.

| Stage | Deliverable and exit evidence | Still prohibited without separate approval |
|---|---|---|
| Next: pilot build decision | One consolidated BOM/assembly disposition and quote-ready request covering the actual boards, exact parts, stackup, connectors and fixture | Ordering or fabrication; #45/#48 remain open |
| Before populated fabrication | Resolve or explicitly disposition each existing manufacturing gate, especially capacitor sourcing/effective-C/lands, stackup, connector process and delivered cost | Treating a quotation, this plan or DRC0 as release |
| Before first power | Approved assembled-board inspection and fixture, verified source/polarity/grounding, reviewed staged current limits and abort thresholds; resolve startup-critical assumptions | Flipping firmware gates or using a generic current setting |
| During separately approved dummy-source commissioning | Measure load/rail/ripple/return behavior, confirm F1 startup, then acquire and inspect internal-test data | Claiming unmeasured current/rail limits are guaranteed |
| Later | Full external dummy-source/noise/signal/fault characterization and separately scoped body-use engineering | Electrodes/person connection or safety certification by inference |

Do not require an impossible exhaustive vendor current maximum before preparing
a quote or assembly review. Equally, do not authorize power solely to discover
whether an unsafe unknown is acceptable: review bounded commissioning conditions
first. Classify each uncertainty by the stage it blocks. Existing gates require
explicit decisions; moving an item in this table never silently waives one.

## 5. Pilot BOM triage and dated follow-through

**2026-10-07 follow-through:** [the consolidated capacitor disposition](REV_A_PILOT_CAPACITOR_DISPOSITION.md)
now retains the existing 1 uF/10 uF targets and PR87's shared 100 nF quote identity.
It maps all 48 fitted capacitors, separates internal VCAP and local LDO conditions,
and checks the 1.35 mm bulk body against K2's existing component allocation.
No active BOM substitution or physical qualification occurred. The next task is
one complete unsent two-board quote/DFM packet, not another capacitor search.
The original triage below is historical prioritization, not an instruction to
repeat completed candidate decisions.

The current BOM and auxiliary contract were counted at the baseline above.
This is source inventory, not a fresh lifecycle/stock audit. The recorded concerns
and existing shortlist are in `REV_A_CAPACITOR_E1_DECISION.md` and #48.

| Current scope | Count | Disposition for the pilot decision |
|---|---:|---|
| AFE 10 uF, GRM219R61A106KE44D | 4 | Resolve recorded discontinuation; existing candidate GRM21BR61C106KE15L needs effective-C, land and extra-height disposition |
| AFE 1 uF, GRM188R61E105KA12D | 15 | Resolve recorded planned-stop issue; existing GRM188R61C105KA12D is not automatically equivalent at internal VCAP nodes |
| AFE 100 nF, GRM188R71H104KA93D | 7 | First check reuse of the existing auxiliary part below; otherwise retain GRM188R72A104KA35D as the previously researched candidate with its recorded status discrepancy |
| AFE C0G input/BIAS capacitors | 5 | Retain design choice; do not reopen selection just to consolidate the BOM |
| AFE T491 VCAP1/reference capacitors | 2 | Retain design choice and node-specific requirements; do not apply the LDO ESR rule to these nodes |
| Auxiliary C101–C115, C0603C104K5RACTU | 15 | Already the selected auxiliary 100 nF part; do not migrate these just because AFE Murata sourcing is open |

**Completed candidate-choice follow-through:** see
`REV_A_100NF_REUSE_DECISION.md`. The existing auxiliary identity is now preferred
for quotation at the seven AFE sites as well, subject to the recorded land,
height, exact-supply and node-specific effective-C conditions. The active BOM
and boards are unchanged. This does not grant assembly or electrical approval.
The pair decision is now in `REV_A_PILOT_CAPACITOR_DISPOSITION.md`. Carry its
consolidated schedule into the complete quotation packet, then one coordinated
engineering migration after the stated conditions are disposed.
Include total delivered-cost gaps; the historical $94.84 AFE allowance excludes
the complete auxiliary, cables, carrier, tools, tax, shipping and assembly.

The following is the unsent quote/DFM question set, not a fabrication order:

> For the current Rev A AFE and auxiliary boards, assess the specified four-layer
> construction, via/drill/land feasibility, and your assembly process for the
> exact proposed populated BOM. Flag unavailable parts and proposed substitutions;
> do not substitute without approval. Confirm capacitor effective-C/land/height
> evidence or identify what the manufacturer must supply. Include HTSW header
> and XH connector process, mating/support access, bare PCB/assembly/stencil/setup,
> minimum quantity, tax and delivery as separate costs. This request is for
> feasibility/quotation only; no production is authorized.

Do not send this message or choose paid services without authorization. Source
model selection remains a before-power task, not an excuse for another generic
analysis-only loop. If vendor evidence is unavailable, return the exact remaining
question/decision and move to another independent pilot blocker.

## References and status

[1] TI ADS1299-4 product specification, analog 4.75–5.25 V:
https://www.ti.com/product/ADS1299-4 (checked 2026-10-07).

[2] Tektronix, bench supply capabilities for prototyping:
https://www.tek.com/en/products/dc-power-supplies/bench-power-supply
(checked 2026-10-07; class-level explanation, not a selected product).

User-authorized planning assumptions only. No hardware, firmware, BOM, selected
component, physical measurement, supplier message or purchase/release/powered/
external-input/body-use approval changed. Historical studies retain their original
source identities; this note supersedes their next-task instructions only.
