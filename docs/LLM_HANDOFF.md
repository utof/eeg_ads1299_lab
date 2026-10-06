# Continue from merged S1: S2 mode loads and return accounting

**Read `REPOSITORY_PUBLICATION.md` before any GitHub publication or recovery.**
Root `AGENTS.md`, README and DEVELOPMENT point there too. For interrupted replies,
check recently merged PRs as well as open ones: PR82 had already completed despite
its missing chat report. Do not repeat source publication or a failed Codex edit
request. Publishing, Codex review, CI and merging are different operations; use
actual available schemas and stop explicit denials.

S1 and the mandatory publication runbook are MERGED in PR82 at base main
`7325d659aeedf2628cf2a4430854e90ef1277785`, tree
`85b324a5445ca653afd16990311a04ccd9622ae5`. Its tested head was6a8fb444.
PR81's connected P3/R1, C4 service access and F1 firmware are also already merged.
This continuation is `review/current-return-s2` until its live PR is merged;
read actual refs/runs, not this base as a permanent main claim. No PCB, circuit,
BOM/profile, firmware, cable, carrier, dependency or release flag changes.

Read `REV_A_CURRENT_RETURN_S2.md` and `studies/s2_current_return.json`. The exact
executable block checks source/tree and eight original input byte hashes. It
models the selected four-channel15-byte frame:120clock cycles at250SPS gives
30000rises/s in1MHz bursts,3% activity. With ideal0/3.6V outputs,42.2k-1% pulls
and explicitly ASSUMED100pF external loads, it computes343.39uA mean forward-pull
and10.89uA external-charging contributions. These are NOT complete supply-current
ceilings; all operating/peak/internal-dynamic/capacitance maxima stay unknown.
MISO/DRDY output pull loads are on the MCU-side supply, not AFE DVDD.

A necessary KCL refinement: a forward buffer's static output current returns
via the AFE input pulldown, unlike a load consumed/returned locally on the auxiliary.
AFE net ground export is incoming5V minus outgoingDVDD plus incoming signal DC.
Only the auxiliary-local part cancels. In the two-equipotential-node example,
parallel returns share by CONDUCTANCE, not wire count. Ten ASSUMED0.1ohm K1 wires
plus two hypothesized0.073752ohm C4 wires carry21.33% of net return via C4, not2/12.
The0.0975mV example ground shift is not a distributed plane/fault guarantee.

TXU ICC is no-load/static; Cpd and ADS supply-current entries are typical. The
ADS1299-4 maximum-power test conditions differ from selected gain24/internalclock.
JST's contact figure has specific test conditions; crimps and shared returns are
not qualified by a gauge or catalog current rating. Preserve all unknowns and
mode/transient distinctions; no sense reading or calculator output grants power.

S1's5mA/buffer assumption and3.557mV farthest feed-loss example remain sensitivity
results, not replaced by the S2 partial load sum. The94.867mV common-path allowance
and0.180ohm optimistic ceiling still allocate unbounded errors, not accepted specs.

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

Build one source/cable/return acceptance worksheet using S1's existing AVDD/DVDD
limits and S2's mode/boundary accounting. Allocate known and unknown voltage-loss
terms explicitly, including shared source/plane return, K1/C4 contacts, source
accuracy, R11 tolerance and regulator behavior. Specify de-energized four-wire
cable checks and future simultaneous source/sink current/voltage observations
needed to replace the hypotheses; do not energize an assembly now. Obtain a
vendor bound or separately reviewed empirical envelope for unknown operating/
peak currents before using that worksheet for a release decision. Do not claim
an input current ceiling from no-load ICC, typical Cpd or an assumed 100pF load.
No speculative copper widening, generic termination or new component selection.

After publication inspect exact-head CI and every original review finding; merge
only after acceptance. S2's numerical/doc checks are ordinary software checks,
not added native CAD cases. The schematic gate binds its calculator, exact
executed documentation, model and tests into the input snapshot. Preserve the
450s CAD and individual native deadlines,71% branch floor and prior evidence.
All-file hooks and the same locked `tools.check` entry point apply locally/CI.
Distinguish source hashes, local/hosted execution, review and physical validation.

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
