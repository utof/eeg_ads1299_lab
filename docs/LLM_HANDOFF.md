# Continue from PR81: published P3 and preserved clock correction

**P3 is published. Do not repeat its publication or rebuild either PCB.**
Read live main, PR81 and this handoff before acting. At the 2026-10-04 checkpoint:

| State | Exact source |
|---|---|
| Main, still P2 | `70e8d41bd60d597ecc284859d7e1f71370dcd190` |
| Published P3 engineering base in PR81 | `9d22a6c21eee1bd8983ba61fb4c459870182e734` |
| Published P3 tree | `751d8c8f1058f6d5663e215ce908e34bb5e6f46a` |
| Preserved R1 correction, not yet active in PR81 | `107d72c419149c7501ab4b3847b50c34e186e5da` |
| Corrected R1 tree | `a278956c4f9e57d108a01a455c2cea7dcb81eb18` |
| Durable recovery branch | `workbench/pr81-clock-source` |
| Immutable recovery commit | `ce2d891713a76bcaed300af8fb310d489e3c3479` |

This documentation update does not apply R1 copper. Read back the live PR head:
a new documentation commit does not mean the board or its tests were updated.
Do not count P3's prior green workflows or a documentation-only run as R1 CI.
The original Codex findings are4174991282 (clock/MISO) and4174991286 (stale handoff).
A later clean review summary does not automatically resolve earlier findings.

## Next bounded task: import the existing R1 source, then verify it

The complete three-commit incremental bundle is stored as data at
`recovery/pr81-clock/` on the immutable recovery commit above. It contains the
actual corrected PCB, tests, docs and history, not just a screenshot or patch
narrative. Its manifest lists14 files with byte counts, Git blob IDs and SHA256s.
After checking every file, strip ASCII whitespace from each chunk, concatenate
in manifest order and strict-base64-decode. Expected bundle:23575 bytes,
SHA256 `bacb2f1b82ff04e4a3526e403ae83b43f3ab8663a576ec2ac24b6cde0601a0f3`.

Verify the Git bundle against prerequisite9d22, import it without executing its
scripts, and require head107d/treea278 and exactly these three commits:
`33a070a88aa680d1b511989948afe435ccf89bd9`,
`184e12c8996353a1b51d25f314c08b2918ca9abe`,
`107d72c419149c7501ab4b3847b50c34e186e5da`.
Use a normal non-force update only when ancestry permits. This publication-status
commit is a sibling of R1; reconcile documentation explicitly and retain both
histories rather than force-pushing it away. The recovery-data branch is not an
engineering branch to merge into main. Do not import its transport files into
the final product tree or add an execution workflow to unpack them.

The normal Codex import task5978860999 did not run: bot5978862704 requires a
Codex repository environment. No environment/permissions/credentials/workflow
was changed. GitHub small-object writes work, but that is distinct from normal
local-bundle import. Do not repeat capability probes, reupload the same bundle,
reroute the clock or use an alternative execution service. Use an available
normal Git publisher, or report the specific remaining setup prerequisite.

After the corrected source is active: run exact-head ordinary/native/schematic
and target checks, obtain renewed review and disposition of both findings, then
merge only if accepted. Next electrical work is the AFE_DVDD feed/return budget
and remaining complete-channel/reference assumptions, not routine routing.

## What is active, and what R1 changes

Active P3 auxiliary source is `hardware/rev_a/auxiliary/auxiliary.kicad_pcb`, next
to its four-sheet project:52 footprints,216 pads,647 segments,158 vias, connected.
Its clock is still85.491637mm/5vias in this documentation-only checkout.
R1 changes only MCU_SCLK and the resulting zone fill:71.875101mm/4vias, minimum
same-layer clock/MISO trace-edge gap0.638848mm instead of0.230172mm. It preserves
all831 other copper/footprint forms and all52 footprints. R1 has643segments/157vias.
These are native geometry observations, not signal-integrity qualification.
Read R1's `docs/REV_A_P3_CLOCK_REVIEW.md` after recovering its checkout.

The prior clean R1 local gate was1236ordinary+14subtests,291KiCad,49console subset,
with the CAD batch342.66s inside the unchanged450s budget. These are retained
prior results, not execution by this documentation/publication continuation.
No R1 hostedCI, complete native suite, S3build, renewed review or physical test
is claimed here. Historical evidence must stay bound to its actual source.

## Invariants and outstanding physical requirements

Read root `AGENTS.md`, `docs/DEVELOPMENT.md`, the hardware baseline and the P1/P2/P3,
C1-C4, F1 and reference-review/performance documents. The full older handoff is
preserved at `archive/20261003_pre_publication_handoff.md` for its detailed
requirements, NOT current publication, next-task or test-count statements.
This file and live source take precedence over that archived status narrative.

Never use the parking-grid importer or old authoring helpers to regenerate the
AFE board at `hardware/rev_a/layout/rev_a.kicad_pcb` or the auxiliary board.
AFE hash stays `60097ff4acf8408d5a172930de74bcd36aa50a379dd30a831e4bc64d3841c8a6`.
AFE/J3, circuit/BOM/profile, firmware, service cable, carrier, dependencies and
all hardware/approval flags are unchanged by R1 and this publication work.

Preserve the15P2bypass corridors,39new-net cuts, HOST/TARGET isolation and
mounting/cable rules. The central0.10mm reference strip has declared same-net
through-contact exclusions; it is not full-width ground or an EM model. The
20 pending outlines for18 records remain electrically unapproved and must not
be enlarged to pass a reroute. Own-via/PTH return transitions, layer construction,
long channels, supply necks and sense coupling still require review.

F1 parks outputs and requires actual READY/freshARM before clock/VCAP/reset;
BOARD_PROFILE_REVIEWED remainsfalse. Faults invalidate sessions, and software
cannot preempt blocked I/O or recall emitted bytes. C4 uses separate feed/sense
conductors joining on the AFE, not the auxiliary. Detached cable testing, no hot
mating, excluded DevKitUSB with accessories, and actual restraint remain required.
The42.2k pull calculations are conditional (only24mV disabled-low budget margin).
Partial-rail leakage, TPS3703 timing conditions, SENSE injection, analog-source
exposure, physical latch behavior and rapid/partial power faults remain open.

Keep #45/#48, vendor stackup, E1 calibrated dummy-fixture limits, capacitor
lifecycle/effective-C/assembly and mechanical fit/retention evidence open.
The94.84USD AFE subtotal is not a complete delivered auxiliary/cable/carrier
quote or proof of the100USD target. No supplier outreach, purchase, fabrication,
powered-connection or body-use authorization has been granted.

Use locked uv and the same `tools.check` orchestrator as CI. Missing native tools
are failures; retain complete failure logs. Do not lower rules, coverage floors
or timeouts. Report TLDR and the category/remaining-turns/status/next-step roadmap;
distinguish source custody, active code, local/hosted tests, review and physical
qualification. Future agents can recover the whole correction from GitHub alone.
