# Continue from merged PR81: supply/return review S1

**Read `REPOSITORY_PUBLICATION.md` before any GitHub publication or recovery.**
Root `AGENTS.md`, README and DEVELOPMENT point there too. Source publishing,
Codex review, hosted checks and merge are different operations. Do not ask a
Codex editing task to publish and then infer its missing environment blocks
review or the connector. Follow actual schemas and stop explicit denials.

PR81 is MERGED: base main `f6932ead58c1d02af145de405312a7f885dbb010`, tree
`a1bb3a16687c65f736de9c2634bb5ec2e4b990ac`, includes the original R1 correction
and both documentation histories. Its two original review findings were resolved
and the actual corrected tree passed hosted checks. Never reconstruct P3/R1,
J3, F1 or prior source because an old chat reports a publication blocker.

This continuation is `review/supply-return-s1` until its live PR is merged.
Read live main/open PRs and the actual head, not this baseline as a permanent
current-main claim. S1 changes analysis/checks/docs only; both PCBs, circuit,
BOM/profile, firmware, cable, carrier, dependencies and release flags stay intact.
Read `REV_A_SUPPLY_RETURN_S1.md` and `studies/s1_supply_paths.json`.

S1 uses a source-bound read-only native centerline-tree inventory and a small
validated constant-current KCL/KVL calculator. Shared edges carry summed
loads; signed ground offsets affect the sensed source and actual receiver rail
differently from forward feed loss. The existing conductance/transient model
in `lab.rev_a_supply` is untouched. This is not a plane/EM/mesh extraction,
measured current or qualification. The modeled local ADC load is lumped at C33.

The 5mA-per-buffer example gives3.557mV farthest feed drop, not1.344mV from
incorrect per-path loading. Under the stated0.5A-MCU example only94.867mV is
left for all omitted feed/return and errors before E1's4.75V AVDD limit. Treating
that as a shared-loop allowance gives an optimistic0.180ohm ceiling, NOT an
approved specification. Multiple grounds and a separately sensed source must
not be replaced by zero impedance or assumed equal wire currents.

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

Close the S1 mode-specific current envelope and allocate the actual source,
K1/C4, crimp/contact, plane/return and regulator losses. The native inventory is
not a current-distribution solver. Use actual F1 clock/data duty and output loads;
do not use no-load microamp buffer ICC as an active-load maximum. Specify how
four-wire resistance and simultaneous source/sink voltage measurements would
validate those bounds on the future person-disconnected fixture, without power
permission now. No speculative wider traces, generic termination or meanders.

After source publication, inspect exact-head CI/review and merge only after
acceptance. S1's native study is an additional snapshot check, not new global DRC
or a physical fault test; retain the actual tested counts from JUnit. Use locked
uv and `tools.check` locally/CI, keep all native deadlines and the450s CAD batch
budget unchanged, and do not overwrite historical results. Small durable source
inputs belong in Git; ignored reports hold logs. Source hashes, source/tree
identity, local/hosted/native/physical evidence must stay distinct.

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
