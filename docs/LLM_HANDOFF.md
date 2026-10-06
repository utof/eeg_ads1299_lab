# Continue from S3: S4 serial source evidence and actual setup blocker

**Read `REPOSITORY_PUBLICATION.md` before any GitHub publication or recovery.**
Root `AGENTS.md`, README and DEVELOPMENT point there too. For interrupted replies,
check recently merged PRs as well as open ones: PR82 had already completed despite
its missing chat report. Do not repeat source publication or a failed Codex edit
request. Publishing, Codex review, CI and merging are different operations; use
actual available schemas and stop explicit denials.

S3 and its optimized-Python validation fix are merged in PR84: mainde47a756,
reviewed/tested heada88c5377, tree740889dc8b2318af1490ec29d8f2810a7f31ed21.
S1/S2, P3/R1, C4 and F1 are already merged. S4 is on `review/steady-source-s4`
until its live PR is merged; inspect actual refs and any original findings.

**S4 is a named serial evidence supplement, not another worksheet.** Read
`REV_A_STEADY_SOURCE_S4.md` and `studies/s4_serial_evidence.json`. The selected
future mode is internal-test,4channels,gain24,250SPS,1MHzSPI and C1 header UART.
That hypothetical branch requires a separately reviewed true profile gate; it is
NOT the current distributed false-gate build, which uses onboard UART and stops
before acquisition. The two states are explicitly separate in the record and
hypothetical authorized_here=false. No actual gate changed or acquisition ran.
The profile/console headers are included in the nine-file input fingerprint.
No CPU/radio/memory power state or real source model was measured.
TI's conditional TPS7A2033 DBV accuracy yields3.2505–3.3495V only with its
specified input/load/temperature and other conditions: importantly VIN>=3.6V
and IOUT>=1mA. The145mV dropout row is NOT the accuracy headroom requirement.
The default S3 record remains allnull. Temporary scenarios fill only regulator
and reuse the original worksheet; all8outputs stay indeterminate and unqualified.
Espressif's0.5A is minimum SUPPLY CAPABILITY, not a current maximum; modem-sleep
columns aretypical. The v1.1 drawing uses SGM2212, with CP2102N/LED/RGB loads still
connected without USB. Real board revision and total MCU/exported current bounds
remain unknown. Do not sum unrelated typical rows as an operating ceiling.
Nine input hashes and three schematic snapshot entries bind the evidence.

**S3 creates one conditional supply worksheet**, `REV_A_SUPPLY_ACCEPTANCE_S3.md`
and `studies/s3_acceptance.json`. All21 physical voltage terms startnull; all8
output rows are indeterminate. The executable block checks9original input files
against319f's Git bytes/hashes, including both boards. The small interval helper
adds signed endpoint bounds, validates all inputs even when one is unknown, and
never replaces missing information withzero. No hardware/firmware/circuit/BOM,
cable, dependencies, rules or approval changes. GitHub guide entrypoint tests
remain active; source publication and Codex review are different operations.

Read S3 before assigning budgets: source_error and common_pair are different;
common_pair includes the source lead RETURN once, while g_analog measures the
remaining ADC-ground-to-J105.2 offset. Exported DVDD uses the opposite ground
conversion sign. Shared feed losses belong to each sink but are not summed as
separate trunk currents. Local_ADC_DVDD and each buffer rail have separate rows;
monitor reads are diagnostics, not downstream acceptance. C3's3.0–3.6V envelope
is an ANALYSIS window, not a full electrical/ground-offset acceptance criterion.
A filled hypothetical worksheet always retains physical_qualification=false.
Measurements/evidence need their own reviewed provenance; no physical data exists.

S3's99mV remainder assumes10mA through R11 at its initial+1% value and charges no
other loss. A hypothetical110mV common-pair loss yields4.739V. These are not
measured results or accepted cable specifications. They do not replace S1's
94.867mV example, which includes other illustrative feed losses. Do not silently
promote mean S2 current, a catalog no-load limit or a targetsource to a bound.

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

The next dependency is the user's actual regulated bench-source model (or an
explicit statement it is not chosen), then its lead set and applicable source
accuracy/load-regulation conditions. Ask for that identity instead of repeating
a generic current study. The nominal5V/1A target is not an actual supply. Use the
EXISTING S3 worksheet: do not create a new acceptance framework, pick hardware
without a decision, replace unknown currents with capacity ratings, or energize
anything. Even source identity alone cannot bound all current/contact/return
terms; retain the separate missing operating/peak and measurement evidence.
S4 has already checked the TPS7A20, module-current and DevKit schematic rows;
do not repeat that search or turn conditional regulator data into an assembled
rail guarantee. Obtain condition-matched limits or a separately reviewed empirical
envelope for total MCU/exported currents. No supplier messages have been sent.

The measurement plan begins with disconnected PASSIVE harnesses and explicit
four-wire sense/contact boundaries. An ohmmeter injects test current: "unpowered"
does not authorize rail probing on assembled ICs. Current/compliance, fixture,
accuracy, temperature and mating conditions remain to be selected/reviewed.
Future powered measurements require separate approval and simultaneous source,
local/remote supply, ground and branch-current observations; do not bridge C1's
HOST/TARGET boundary with instruments. No powered protocol is released by S3.

Run the same locked tools.check entry point and all-file hooks. The S3 code,
executable document/model/tests are source-snapshotted in the schematic gate;
its calculations are ordinary source/data tests, not new native CAD cases.
Retain the450s CAD deadline,71%branch floor, and historical receipts. Read actual
exact-head CI/review before merge; positive arithmetic does not approve hardware.

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
