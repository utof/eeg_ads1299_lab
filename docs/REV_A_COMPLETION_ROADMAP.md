# Rev A roadmap - B1 passive startup fixture, prices deferred

Q1 is merged in PR89 at main4927b4c6; PR90 is a closed duplicate. The sole RFQ
remains `REV_A_PILOT_QUOTE_PACKET.md` and `quote/`. The user now sets Moscow,
Russia as a provisional delivery region and asks to avoid deep price research.
No recipient/postcode, supplier acceptance, delivery guarantee or sending approval
is inferred. Continue non-price engineering. Read root AGENTS, the publication
runbook and `REV_A_BENCH_FIRST.md`; no new framework or duplicated packet.

| Category | Remaining substantial turns | Done/status | Next slice or blocker |
|---|---:|---|---|
| GitHub / practical direction | 0 for this slice | Main/closed PRs checked; standing no-price-diversion direction in AGENTS and handoff | Retain one canonical RFQ and exact-head review |
| Passive analog-startup fixture | 0 for topology/inspection design | B1 uses existing J2 cable: 1-8/10 commoned; BIAS9/NC11-20 isolated; pre-join identity and post-join checks specified | Actual termination sample, keying, instrument and workmanship acceptance before use |
| Before-power observation plan | 1-2 planning turns | F1, S3 and B1 exist; no actual hardware operated | NEXT: exact existing source/rail/VCAP1/return observation points and instrument-ground/abort plan |
| Quote / prices | Paused by user direction | Complete packet; Moscow planning region; prices unknown | No lookup campaign or outreach without explicit request/approval |
| Component / manufacturing disposition | 1-2 plus required external evidence | Candidates selected; active source unchanged | Apply accepted parts/land changes together; resolve required stackup/process/layout questions |
| Fabrication release | 1 after prerequisites | Not released; no production exports | Separate accepted manufacturing revision and order approval |
| Physical inspection / first internal test | Approved bench-work dependent | Blank B1 inspection record; firmware and capture path exist | Build/inspect only after approvals, then separately reviewed source/limits/observations and capture |
| Later characterization | Measurement-dependent | Not started | External dummy channels, noise/coupling/faults; body use remains separate |

These are overlapping estimates, excluding response/manufacturing/shipping and
physical measurement time. A nominal regulated 5 V source class and 1 A capacity
are planning choices, not first-power settings or actual current bounds. Do not
promote a missing specification or unperformed measurement into a pass.

Read `REV_A_PASSIVE_STARTUP_B1.md`. B1 grounds only the eight routed inputs via
their existing series resistors and J2.10; it is not a general unipolar external
noise-test fixture or body protection. J1 mis-mating is hazardous; actual K2
wrong-port/rotation/full-seating validation remains a HOLD. Pre-commoning wire
identity is needed because a final shorted partition hides input swaps. Keep
spare/BIAS tails individually insulated and no extra bench-earth return.

Next complete the before-power observation/connection plan, not a new RFQ, price
study, capacitor search or premature instrument-control layer. The real source,
instruments, fixture and measured limits remain prerequisites of later powered
work. Q1's frozen input/schedule records remain unchanged. None of this closes
#45/#48 or authorizes outreach, purchasing, fabrication, powering, external-input
acquisition or person/animal connection.
