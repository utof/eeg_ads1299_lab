# Rev A roadmap — practical pilot before more generic modelling

S4 merged in PR85 at `3324fc8c`. The user now confirms no power source is chosen
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
| Pilot BOM/assembly disposition | 1–2 plus vendor evidence | 33 AFE / 15 auxiliary capacitors inventoried and triaged | NEXT: check existing auxiliary 100 nF part for the seven AFE sites; retain/replace/needs-answer decision, then remaining ceramic/stackup/process conditions |
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
body-use permission changes here. The next slice is a build decision, not another
hypothetical source-current study.
