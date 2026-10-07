# Rev A roadmap — capacitor quotation schedule consolidated

100 nF decision PR87 merged at `890f76b1`; bench-first PR86 and S4 are merged. The user now confirms no power source is chosen
and authorizes reasonable planning assumptions. Read `REV_A_BENCH_FIRST.md` and
root `AGENTS.md`: engineering progress and justified architecture, not growing a
study/test count, are the objective. `REPOSITORY_PUBLICATION.md` remains mandatory.

Working source class: regulated 5.00 V, adjustable current limiting, at least 1 A
capacity. The documented 1 A / 0.050 ohm / 10 mA analog case is a hypothetical
sensitivity check, not proof of consumption, a source specification already met,
or an initial current-limit setting. No raw battery/custom charger is selected.
All original S3 physical terms remain unknown. Stop asking for a source identity
before doing independent manufacturing preparation; require it before power.

Remaining substantial turns below exclude quotes, shipping and physical work.
They overlap and are not a promised release date or safety percentage.

| Category | Turns remaining | Done/status | Next slice or blocker |
|---|---:|---|---|
| Architecture and agent continuity | 0 for this review | Small modular repo retained; practical direction in AGENTS/handoff | Refactor only to address a demonstrated obstruction |
| Supply method and provisional choice | 0 for planning | Reuse S1–S4; 5 V bench source class chosen | Actual source/leads/instruments and staged settings before power |
| 100 nF reuse decision | 0 for candidate choice | Prefer existing C0603C104K5RACTU for 7 AFE + 15 auxiliary quote sites; active BOM unchanged | Land/process acceptance, exact supply and effective-C or explicit pilot disposition before populated fabrication |
| Remaining capacitor selection | 0 for quotation choices | Existing 15 x 1 uF / 4 x 10 uF targets retained; full 48-capacitor schedule consolidated; no active migration | Internal-node/effective-C and assembly conditions explicitly retained |
| Complete pilot quote/DFM packet | 1 plus supplier response | Exact capacitor schedule, land dimensions and carrier allocation comparison prepared | NEXT: complete unsent two-board packet, full proposed BOM, stackup/interfaces and delivered costs |
| Coordinated engineering migration | 1–2 after applicable disposition | Active BOM and CAD unchanged | Reconcile responses or explicit pilot risk review, then update BOM/CAD/contracts and required regressions together |
| Remaining signal/reference decisions | 1–2 | Connected boards and scoped clock repair retained | Explicitly disposition pilot-relevant risks; no arbitrary meanders or relaxed guards |
| Quote and manufacturing release | 1–2 after required decisions | Not fabrication-ready | Complete delivered quote, exact parts/process and separate approval |
| Unpowered inspection and fixture | 1–2 plus hardware | CAD/contracts exist, actual fit unverified | Assembly inspection, keyed cables/retention and passive startup fixture |
| Controlled internal-test commissioning | 1–2 planning turns plus approved bench work | F1 and capture path exist; never operated | Source/ground/limit/abort review, then measured rail/current/startup and internal-test capture |
| Later characterization | Measurement-dependent | Not started | External dummy inputs, noise/coupling, full signal/rail-fault envelope; body use is a separate scope |

No calculator output, quote or roadmap edit closes an existing release condition.
Separate before-fabrication requirements, before-power requirements and empirical
characterization; do not demand impossible exhaustive measurements before a quote,
or power unreviewed hardware to bypass a known hazard. Preserve source/history and
necessary fault tests. The $94.84 AFE allowance is not a delivered system quote.
No ordering, supplier outreach, fabrication, powered connection, external-input or
body-use permission changes here. The next slice is the finite unsent quotation packet, not another
hypothetical source-current or capacitor-selection study.

The [100 nF decision](REV_A_100NF_REUSE_DECISION.md) closes candidate selection,
not physical qualification. Its 0.95 mm maximum body height is a conservative
family allowance; mounted height includes solder. The current 0603 lands are
not the exact KEMET density-B pattern. Obtain explicit process disposition for
all 22 proposed sites; do not change global stock footprints or widen guards.
No new code/framework or test-count growth was needed for this paper decision.

The [consolidated disposition](REV_A_PILOT_CAPACITOR_DISPOSITION.md) retains
GRM188R61C105KA12D and GRM21BR61C106KE15L for quotation, including separate
C8-C10 internal-node review (VCAP3 is boosted), local LDO effective-capacitance
conditions and all four bulk sites. The 1.35 mm body fits K2's existing 4 mm
allocation; this is not measured clearance or final assembly acceptance. Do not
redesign the carrier or pick a new capacitor family without a concrete rejection.
