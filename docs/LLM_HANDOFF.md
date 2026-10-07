# Continue from Q1: one unsent two-board quotation packet

**Read `REPOSITORY_PUBLICATION.md` before any GitHub publication or recovery.**
Also read [the standing practical direction](REV_A_BENCH_FIRST.md).
Root `AGENTS.md`, README and DEVELOPMENT point there too. Read live main, open
PRs, recently merged PRs and original review threads before editing: failed
chat replies have followed successful publication/merges. Do not repeat them.
Publishing, Codex review, CI and merging are separate operations; obey actual
action schemas and stop explicit denials. Never regenerate authored copper.

## Current practical task and publication state

PR88 merged the complete capacitor quotation schedule at
`399677407a159ad10c766b4575b65aabc8bd3057`, tree
`a3306419b36226e6b233a42ca6a08a59664e872f`. PR85's S4, PR86's bench-first direction,
PR87's 100 nF choice and earlier S1-S3/P3/R1/C1-C4/F1/K2 work are already merged.
Q1 starts from that tree; inspect live PR status before calling Q1 merged.

**Read `REV_A_PILOT_QUOTE_PACKET.md` and `quote/`.** The full unsent RFQ now covers
both actual boards, 104 fitted board parts, 8 DNP sites, 5 copper-only landing
groups and 4 mechanical hole groups. The separate support/cost schedule includes
external modules, two K1 cables, one C4 cable, tails, carrier/supports, startup
fixture, assembly/setup/overage and delivered costs. It is NOT only a capacitor
BOM. One and five sets are reversible quote alternatives, not orders or MOQs.

`active_mpn` describes unchanged engineering source; `quote_mpn` contains the
26 proposed AFE ceramic replacements. Never assemble from their deliberate
mismatch. Q1 is a frozen quote snapshot, not a second live design contract.
Native CAD and libraries are in Git; the conversation ZIP is convenience only.
No release Gerbers, drill/stencil or pick-and-place outputs have been issued.

**Next decision:** obtain permission for a named recipient, destination and
1/5-set quote scope, then send only after explicit authorization. Record responses
against the packet's finite Q01-Q10 questions and keep exclusions/costs visible.
Do not repeat capacitor selection, create another worksheet, or re-upload source
because a final answer failed. While permission is pending, an independent
before-power inspection/passive-fixture plan is useful; vendor outreach is not
implicit in "next". No buying, fabricating, energizing or external/body inputs.

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
heads and original review dispositions; no prior green result proves Q1.

Read root AGENTS for TLDR + category/remaining-turns/status/next-step reports.
Separate quotation readiness, manufacturing release, before-power checks and
later dummy-source characterization. Purchasing, fabrication, powering,
external acquisition and person/animal use are still not authorized. Required
manufacturer, capacitor, stackup, fixture and physical fault decisions remain
open under #45/#48; a supplier's price is not their engineering acceptance.
