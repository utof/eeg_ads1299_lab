# Continue from B1: passive startup fixture, prices deferred

**Read `REPOSITORY_PUBLICATION.md` before any GitHub publication or recovery.**
Also read [the standing practical direction](REV_A_BENCH_FIRST.md).
Root `AGENTS.md`, README and DEVELOPMENT point there too. Read live main, open
PRs, recently merged PRs and original review threads before editing: failed
chat replies have followed successful publication/merges. Do not repeat them.
Publishing, Codex review, CI and merging are separate operations; obey actual
action schemas and stop explicit denials. Never regenerate authored copper.

## Current practical task and publication state

Q1 is merged in PR89 at `4927b4c6cd312e40ee6a304e7083245e16d5440a`, tree
`192ba338a966d773c35cf58137fa67b6a2c1459c`. PR90 is a closed duplicate; do not
revive `quote_draft/`. Keep `REV_A_PILOT_QUOTE_PACKET.md` and `quote/` as the
only RFQ. Earlier capacitor, S1-S4, P3/R1, C1-C4/F1/K2 decisions are already merged.
Read live main/PR state before claiming this B1 continuation merged.

**User update:** assume Moscow, Russia for delivery planning. Postcode/recipient
remain unknown; no sending permission or delivery-feasibility claim. Price research
is deprioritized. Do not ask the same country question, repeat stock/price searches
or block independent engineering while outreach remains unapproved.

**B1 closes the passive analog-startup topology decision.** Read
`REV_A_PASSIVE_STARTUP_B1.md`: existing J2-coded K1 cable, enclosed common node
for contacts 1-8 and 10; BIAS9 and NC11-20 each insulated and isolated. No new PCB,
active driver, battery, firmware or main BOM change. This is a design/inspection
plan, not permission for physical construction, mating or power. J1 is forbidden:
aligned contact order grounds driven signals; reversed order can short its 5 V
feed (J1.17, not J1.1) to return.
Actual keying, retention, joints and instrument limits still need review.

The pre-join contact-to-tail map is essential: once commoned, permutations within
1-8/10 become invisible to the final partition check. B1 cannot validate external
channel order. Post-join checks include the actual socket return contact 10,
BIAS/spare isolation and supported handling; provisional 1 ohm/1 Mohm screens
are workmanship assumptions, not voltage/leakage or medical-safety limits.
No rail-ohms rule or assembled-IC ohmmeter procedure is introduced. Physical
records remain blank; all existing firmware/hardware approval flags stay false.

**Next non-price step:** specify the before-power source/probe connection and
observation plan at existing rails, VCAP1 and local returns, with instrument-ground
separation, staged HOLD/abort criteria and actual-equipment prerequisites. Reuse
S3/F1 and the new B1 inspection sheet. Do not build another supply calculator or
quote packet. Actual instrument evidence is required before the stage using it,
not before independent paper/fixture work; no powered procedure is released yet.

Q1 remains a frozen quote snapshot with 104 fitted board parts, 8 DNP sites,
5 copper-only landing groups, 4 mechanical hole groups, all 48 capacitors and
26 explicitly unapplied AFE substitutions. Its source/cost hashes and blank
prices remain untouched. Vendor contact still needs explicit recipient/scope
approval; the Moscow update supersedes its original unknown-country statement
only, not postcode, availability, duties, price or production status.

After applicable supplier answers or an explicit limited-pilot risk disposition,
make ONE coordinated BOM/CAD/contracts/fixtures/regression update. Re-run exact-head
checks and review before a separate release. A quotation, green CI or a source
merge does not resolve #45/#48 or approve a component substitution.

## Standing user direction

No supply is selected; reasonable labelled assumptions are authorized. Use an
off-the-shelf regulated 5 V bench-source class with adjustable current limiting
and output-enable, not a raw battery or custom charger. Available 1 A capacity
is NOT an initial current-limit setting or guaranteed board load. Actual source,
lead/instrument identity and staged limit/abort review are required before power,
not before independent quote work. Q1's ENIG/green-mask/white-legend price basis
is likewise provisional, not a change to CAD or supplier process acceptance.

Each slice should close a build decision, repair a demonstrated defect or prepare
a specific physical check. Reuse existing pure calculators and `tools.check`;
no architecture rewrite or new framework for a document-only decision. Retain
necessary tests; test-count growth is not engineering progress. See
`REV_A_BENCH_FIRST.md`, `DEVELOPMENT.md` and `ADVERSARIAL_REVIEW.md`.

## Active source and preserved limits

AFE PCB: `hardware/rev_a/layout/rev_a.kicad_pcb`; SHA256
`60097ff4acf8408d5a172930de74bcd36aa50a379dd30a831e4bc64d3841c8a6`.
Auxiliary project: `hardware/rev_a/auxiliary/auxiliary.kicad_pro` and adjacent PCB.
Q1 changes neither. The current AFE has 69 footprints/251 pads/593 segments/122vias;
auxiliary has 52 footprints/216 pads/643 segments/157vias. R1's 71.875101mm clock,
4vias and 0.638848mm minimum MISO gap are already applied, not new tasks.
Keep all 15 bypass corridors, 39 terminal-cut tests, HOST/TARGET separation,
mounting/access guards and the 18 pending reference records/20 outlines. The
0.10mm central-reference check and own-contact exclusions are NOT full-width
reference continuity, impedance or safety qualification. In2 contains routed
signals/supplies. No enlarged envelopes, relaxed rules or arbitrary meanders.

The consolidated cap quote schedule is 15 x GRM188R61C105KA12D,
4 x GRM21BR61C106KE15L, 22 x C0603C104K5RACTU and seven retained C0G/T491 parts.
Active AFE MPNs still differ at 26 sites. Read `REV_A_PILOT_CAPACITOR_DISPOSITION.md`
and `REV_A_100NF_REUSE_DECISION.md` for internal C8-C10/VCAP3 voltage, local LDO
pairs, effective-C and lands. Typical curves are not guarantees. 1.35mm bulk and
0.95mm KEMET body allowances exclude solder; a4mm K2 allocation is not fit proof.
AFE's named stack target is not a supplier approval, especially not for auxiliary.

C4 exact wire/pin/crimp/empty-cavity contract is `hardware/rev_a/service_c4.json`.
Pin2 exports AFE DVDD; pin3 senses it separately; pin4 senses AVDD after R11;
pins1/5 return; cavity6 empty. Feed/sense join only on AFE. Inspect a detached
harness before common assembled nets can hide faults; no hot mating. K2 full
seating, supports, restraint and auxiliary H4 offset remain as authored.

F1 keeps BOARD_PROFILE_REVIEWED=false. S4 distinguishes that onboard-UART stopped
build from hypothetical reviewed C1-header acquisition (authorized_here=false).
Both DevKit USB ports stay excluded with accessories; permanent tails impose
bare-board programming/service requirements. HOST/TARGET supplies/grounds must
not be bridged by shields, instruments or fixtures. Digital buffers do not
protect analog electrode inputs. Polling cannot preempt blocked I/O or revoke
already-sent bytes; real latch/rail faults and recording invalidation remain open.

S1-S4 remain the existing accounting/evidence, not tasks to regenerate. The S3
21-term physical template remains null; no actual operating/peak/current/return
bounds were created by a planning choice. Conditional TPS7A20 accuracy requires
its stated load/input and other conditions; 500mA module supply capability is
not maximum consumption. Refer to their source-bound notes, not typical values
promoted to guarantees. The historical $94.84 allowance is not the delivered kit.

## Verification and reporting

Use the locked environment and the single `tools.check` orchestrator; retain
450s CAD batch/individual deadlines and71% branch floor. If local dependency
installation fails, retain the error and report that instead of using an
unlocked substitute as a project-gate pass. Bind new claims to actual hosted
heads and original review dispositions; no prior green result proves B1.

Read root AGENTS for TLDR + category/remaining-turns/status/next-step reports.
Separate quotation readiness, manufacturing release, before-power checks and
later dummy-source characterization. Purchasing, fabrication, powering,
external acquisition and person/animal use are still not authorized. Required
manufacturer, capacitor, stackup, fixture and physical fault decisions remain
open under #45/#48; a supplier's price is not their engineering acceptance.
