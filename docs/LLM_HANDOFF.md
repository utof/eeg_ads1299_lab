# Continue from the complete UNSENT pilot quotation packet

**Read `REPOSITORY_PUBLICATION.md` before any GitHub publication or recovery.**
Read root `AGENTS.md` and `REV_A_BENCH_FIRST.md`: the user wants a safe working
prototype, not more generic studies, duplicate calculators or unnecessary layers.
For a failed reply, inspect live main, open AND recently merged PRs before work.
Publication, source review, hosted tests and merge are separate operations.

## Current checkpoint

Capacitor decisions are merged in PR88 at `399677407a159ad10c766b4575b65aabc8bd3057`,
tree `a3306419b36226e6b233a42ca6a08a59664e872f`. PR87/86/85 and S1-S3, P3/R1,
C4 and F1 are already merged. Do not redo them. The quotation continuation is
`review/two-board-quote`; read its live PR state, not this text, to establish merge.

Read **`quote_draft/REQUEST.md`** and **`quote_draft/ASSEMBLY_AND_INTERFACES.md`**.
The packet includes a 34-row current-versus-proposed BOM CSV, blank itemized
cost-response CSV and frozen-source manifest. The native source is already in
Git; no chat ZIP, workbook, old importer or expiring artifact is needed to continue.
The workbook/archive delivered in chat are convenient views, not extra project
requirements or manufacturing data. No production code or new framework added.

One provisional quote set means one AFE board plus one AUX board, with separately
costed external modules/cables/mechanics. Ask for one set and an optional five-set
price comparison, not an order. AFE has 61 fitted purchased parts and 8 DNP sites;
AUX has 43 fitted purchased parts, 5 non-purchased solder-landing groups and 4
non-purchased mounting holes. External MOD1 is counted once. The 48 capacitors
are only a subset of the whole assembly. Spares/MOQs/attrition are not fitted qty.

## Next bounded step — get actual quotation/DFM responses

The packet is **UNSENT**. No supplier/destination is selected or contact authorized.
Ask the user to authorize quotation-only contact and select a recipient; obtain
delivery country/postcode and confirm lot quantities before a delivered-price
request. Do not silently send messages, place orders or upload production files.
Do not create another packet, choose new capacitor families, reroute preserved
copper or repeat the source-model question as a substitute for that decision.

After authorization, request responses to Q1-Q9 and explicit inclusions/exclusions.
Keep supplier DFM/process responses separate from designer electrical-risk
acceptance. A missing item, borrowed instrument or supplier exclusion is not free
unless its actual cost/provision is established. Retain both one-time and recurring
costs, excess inventory, tax/shipping and shared equipment. Historical $94.84 is
not a complete delivered-system price or proof of the $100 objective.

Reconcile applicable responses or explicit bounded pilot-risk decisions. Then
make ONE coordinated BOM/CAD/contracts/fixtures/test update for accepted changes.
No isolated MPN-string substitutions. Only generate fabrication outputs from the
reviewed released revision; there are none in this quotation-only packet. Keep
#45/#48 open until their actual conditions have been explicitly disposed.

## Keep the existing engineering decisions

The proposed AFE replacements remain unapplied: 15 x GRM188R61C105KA12D,
4 x GRM21BR61C106KE15L and 7 x C0603C104K5RACTU. AUX retains 15 of the latter;
C0G/T491 remain. Read `REV_A_PILOT_CAPACITOR_DISPOSITION.md` and
`REV_A_100NF_REUSE_DECISION.md` for internal VCAP nodes, LDO-local effective-C/ESR,
reference companions, real land deviations and conservative body-height limits.
VCAP3 is boosted; a generic 5 V assumption is not its transient bound. Typical
curves and K2's 4 mm component allocation are not physical minimum-C or clearance
qualification. Apply the KEMET land/process question to all 22 quote sites.

Current authored source: `hardware/rev_a/layout/rev_a.kicad_pcb` (AFE, not an
importer output), and `hardware/rev_a/auxiliary/auxiliary.kicad_pcb`. AFE SHA256
`60097ff4acf8408d5a172930de74bcd36aa50a379dd30a831e4bc64d3841c8a6` is unchanged.
AUX R1 has 643 segments/157 vias and the scoped clock repair; AFE has 593/122.
Do not rebuild either board from a netlist. Preserve 15 P2 bypass protections,
39 P3 terminal-cut checks, 18 pending reference records/20 outlines, domain and
mounting/access guards. Reference checks are not an electromagnetic model.

Read `REV_A_STACKUP_BENCH_REQUIREMENTS.md`: the AFE named construction remains
a target needing supplier confirmation; it is not an approved AUX construction.
In2 is routed copper, not a continuous plane. Keep own-contact return transitions,
long channels and analog six-pair coupling in their existing review scope.

Read K1/C1/C4/K2 documents and current contracts for actual interfaces. K1 has
all 20 contacts and captive port-specific keys; C4 has separate feed/sense wires
joining only at the AFE, with cavity6 empty. J106 is STOP_N to TARGET_GND, not a
new safety-rated emergency stop. Keep independent support and no hot mating.
Older documents' pending placement/handshake statements are historical; current
source and handoff control. Do not connect DevKit USB with accessories attached
or bridge HOST/TARGET through shields, instruments or fixtures.

## Before power and later characterization

No actual supply was selected. The user permits reversible planning assumptions:
regulated 5.00 V bench supply with output enable/current limiting, >=1 A CAPACITY.
This is not consumption, a guaranteed source specification or initial current
limit. No raw battery, custom charger or new supply framework. S3's physical
input record stays unknown; S4's conditional regulator data remain conditional.
Actual equipment/grounding, staged current limits and abort criteria are required
before a powered procedure, not before independent quote preparation.

The first milestone is person-disconnected internal-test capture after approved
inspection/startup, not human EEG or exhaustive final noise/EMC qualification.
The analog startup fixture remains separate from the J2 cable. Detached passive
harness testing needs reviewed meter current/compliance; unpowered IC probing is
not automatically safe. Functional testing/energization requires separate approval.
F1 and the real distributed BOARD_PROFILE_REVIEWED=false gate stay unchanged.
Software cannot preempt blocked I/O, guarantee all rail-fault timing or recall
sent bytes; complete affected captures must be invalidated. Partial rails,
leakage, sense injection, clamps, ground breaks and real mechanical retention
still need their applicable checks. No body/purchase/fabrication/power gate changes.

## Verification and reports

Use locked uv and the existing `tools.check` orchestrator, all-file hooks and
actual-head CI/review. Keep the 450 s CAD deadline and 71% branch floor; missing
native tools are not a pass. No new project tests are needed solely to freeze
RFQ prose or spreadsheet formatting. Check derived schedules against source;
keep authoring/packaging checks distinct from project tests and physical evidence.
Report TLDR plus category/remaining-turns/status/next-step roadmap. Quote
preparation, supplier contact, a green badge and physical qualification are
four different milestones; never label one as the next.
