# Continue from PR81: the R1 clock correction is imported

**Do not repeat recovery, publication staging, or clock routing.** The original
R1 correction has been imported into GitHub with its actual commit IDs intact:
`33a070a88aa680d1b511989948afe435ccf89bd9`,
`184e12c8996353a1b51d25f314c08b2918ca9abe`, and
`107d72c419149c7501ab4b3847b50c34e186e5da` (tree
`a278956c4f9e57d108a01a455c2cea7dcb81eb18`). Their parent is the already-published
P3 head `9d22a6c21eee1bd8983ba61fb4c459870182e734`.

This checkout integrates that engineering source with the documentation-only
`f7cb415ef5e7a4eb4ef6807bd861d92c0676bf99` history. Both histories are retained;
no force update, source reconstruction or test relaxation was needed. Source
outside docs is exactly R1. Read live main, PR81, its head/tree, check results
and review threads before deciding whether it is already merged. A successful
import is not CI or acceptance. Original findings are4174991282 (clock/MISO)
and4174991286 (stale handoff); inspect actual dispositions, not only the latest
review-summary badge. Main was70e8d41b at integration start.

## Working publication method and what not to repeat

Read `REPOSITORY_PUBLICATION.md`. PR77 used a normal GitHub Actions history
publisher separately from Codex review. The same bounded mechanism worked here:
run37204919737 verified the stored23575-byte R1 bundle and all14 source-data
files, imported exactly3commits, published only `recovery/pr81-r1-imported`, and
independently cloned that remote branch to check head/tree. It did not execute
project scripts, change main or run tests under its write permission. Its
single-purpose workbench workflow is NOT in this engineering tree.

GitHub's object API then integrates existing trees and both parents and advances
the existing PR branch without force. Codex is asked for review after real source
publication. A Codex editing-task environment is not a prerequisite for review
or for an independently authorized publisher. If a particular write is denied,
stop that operation: do not change permissions or route it through another API.
Do not retry the now-obsolete cloud importer or upload the stored bundle again.

## Current engineering source

Native auxiliary project: `hardware/rev_a/auxiliary/auxiliary.kicad_pro` and its
PCB. R1 changes only MCU_SCLK and resulting ground fill:71.875101mm planar length
instead of85.491637mm,4vias instead of5, minimum same-layer clock/MISO trace-edge
gap0.638848mm instead of0.230172mm. Inventory:52footprints/216pads/643segments/
157vias. All831 nonclock copper/footprint forms are unchanged from P3. These are
bounded routing improvements, not impedance, noise, ringing or timing proof.
The75mm/4via/0.60mm regression targets are not manufacturer SI limits. Actual
edges, packages, cables, return transitions and layer construction remain open.

Main AFE stays `hardware/rev_a/layout/rev_a.kicad_pcb`, SHA256
`60097ff4acf8408d5a172930de74bcd36aa50a379dd30a831e4bc64d3841c8a6`.
Its69footprints/251pads/593segments/122vias, J3, prior AVDD1/output/CH1N repairs,
circuit/BOM/profile, F1 firmware, C4 cable, K2 carrier, dependencies and rules are
unchanged. Never run the parking-grid importer or old authoring scripts over
either board. Read AGENTS.md, DEVELOPMENT.md and the hardware baseline first.

Keep all15P2bypass corridors,39P3terminal cuts, domain separation and mounting/
cable guards. The continuous central0.10mm global reference strip has declared
same-net through-contact exclusions; it is not full-width ground or an EM model.
The original20pending outlines/18records remain unapproved and may not expand
or move to accommodate a reroute. The reference fast path skips work only for an
EMPTY exact native group difference. The450s CAD batch budget, individual tool
deadlines and71%branch floor remain unchanged. Use current JUnit counts.

## Next bounded task

First finish exact-head hosted checks and renewed review of this actual R1 tree;
merge only after the original findings have explicit dispositions. After that,
review the AFE_DVDD feed AND return voltage-drop budget with bounded load,
copper, via, cable/contact and shared-trunk data, plus remaining channel/return
assumptions. Do not sum shared paths as independent wires or invent a generic
termination resistor. No further routine clock, J3, ground or F1 reconstruction.

Retained original R1 local evidence is1236ordinary+14subtests,291KiCad and49console
subset. Those counts are not a new hosted run. Bind all new results to their
actual SHA/tree; distinguish full native integration, target compilation, source
checks and physical experiments. Logs go under ignored reports; small durable
receipts and necessary source inputs belong in Git. Use locked uv and the same
`tools.check` entry point as CI. Missing native tools must fail, not be waived.

## Physical and release boundaries

C4 J3/J104 pins1/5 are return,2 is AFE DVDD feed OUT,3 separate DVDD sense,
4 AVDD sense after R11,6 NC. Feed/sense join at AFE, not auxiliary. Verify the
five-wire cable detached before intentionally common AFE nets hide swaps. Exact
wire/crimp, mounting and restraint remain unqualified; no hot mating. K2 support,
body/mate and cable checks are finite geometry, not force/tolerance validation.
Auxiliary H4 is intentionally offset, not a rectangular hole pattern.

F1 SESSION/ARM/READY/ARMED is implemented; BOARD_PROFILE_REVIEWED remains false.
Park outputs, require actual READY and fresh ARM, then clock/VCAP/reset. Faults
invalidate the entire session; software cannot preempt blocked I/O or retract
sent bytes. Real latched feedback and host recording invalidation need validation.
Both DevKit USB connections stay excluded with accessories; permanent tails must
be removed for bare-board programming. C1 HOST/TARGET supplies and grounds stay
separate. Digital buffering does not protect analog electrode inputs.

C3's42.2k pulls have a conditional24mV disabled-low margin, not measured leakage
qualification. Partial rails, SENSE injection, initial latch state, feed/ground
breaks and AVDD/DVDD asymmetry remain open. TPS3703's30us delay is conditional on
5%overdrive; no arbitrary-ramp or pre-E1 guaranteed shutdown has been established.

Keep #45/#48, JLC04161H-7628 manufacturer confirmation, E1 calibrated dummy-source
and measurement requirements, six-pair coupling disposition, capacitor lifecycle/
effective-C/assembly, physical fit and delivered budget open. The94.84USD AFE
allowance excludes the complete auxiliary/cable/carrier/tools/delivery and does
not establish the100USD objective. All purchasing, fabrication, powered-connection,
external-acquisition and body-use flags remain unchanged/false.

`REV_A_P3_CLOCK_REVIEW.md` records the original R1 rationale and experiments;
its historical publication-next-step is superseded by this handoff. Older
publication narratives in docs/archive are history, not current instructions.
Report a TLDR and category/remaining-turns/status/next-step roadmap. Never equate
source custody, a green badge or a merge with physical qualification.
