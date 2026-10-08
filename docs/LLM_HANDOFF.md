# Continue PR98: native integration blocked; clock split coverage repaired

Read `REPOSITORY_PUBLICATION.md`, root `AGENTS.md`, `DEVELOPMENT.md` and
`REV_A_BENCH_FIRST.md`. Read live main, open AND recently merged PRs, and original
review threads before changing anything. No missing reply proves work failed.

## Current state: recovery data is NOT the active engineering tree

Main was checked at `c2f93ee30eb47f80a7702603f20ed22e6cce86af` (PR97).
Draft PR98 is `work/l5-spi-series`; the preserved hardware candidate is based on
`ff953c03c452f1572602b52aa62f42e80bfa9588`, tree
`928e94437784b2249042555e1fa17316406dfc41`.

A real eleven-file LOCAL schematic/BOM/PCB/contracts/test candidate was authored.
It is preserved in [the L5 recovery packet](recovery/l5_spi_candidate_20261008/README.md),
with an exact base, per-file hashes, compact Git patch, and expected complete tree.
Preservation did NOT apply that patch, and this repair does not apply it either.
The active board files,
contracts and native XML fixtures still have the old topology. The original five
missing-position tests therefore remain intentionally red. PR98 stays draft;
no implementation completion, green gate, source merge or fabrication is claimed.

The candidate adds DNP 0603 positions AUX R117-R120 and AFE R24, separate driver
nets, and explicit unpopulated/NOT_SELECTED guards. R114 remains a 42.2k
receiver-side shunt; AFE's logical MOD1.GPIO13 stays with J1.5 downstream of R24.
No existing footprint moves, including R20. Other-net copper, analog paths and
zone source were retained. Stored fills are STALE pending native refill.

Do not silently fit zero-ohm links. An absent series part leaves a path open.
The longer retained driver escapes (about 5.3-10.9 mm of track center-line, two
vias each) need review, particularly R24's 10.85 mm route. Accessible lands are
not proof of ideal source termination, timing margin or physical rework access.

## Integration attempt and one active-source repair

An integration attempt recovered the exact eleven-file candidate locally and
verified every manifest hash. A scoped installed-pytest run found 15 failures,
395 passes and 7 passing subtests. This is an incomplete integration diagnostic,
not the ordinary locked gate or native CAD; stale XML explains many, not all,
failures. Do not conclude that exporting the two netlists alone finishes L5.

The actual clock-geometry probe had a separate blind spot: filtering only
MCU_MISO dropped MCU_MISO_DRV after the R120 split. Its active-source selector
now covers precisely both net names; clock limits, layers and native distance
calculation are unchanged. Eight unit cases execute the real selection preamble
with explicitly fake API objects, NOT a native geometry emulator. One intended
failure and seven passes were observed before the correction; all eight passed
after it. No footprint, route, XML, BOM or contract changed in this repair.

Read Codex review 5462618515 on preservation head 8ff5143, requested specifically
against the recovered candidate. It reports three P1 blockers, not approval:
1. Update placement inventory/native-DNP checks for the five exact new sites,
   preserving agreement between native DNP, Population and BOM/contract intent.
   The auxiliary probe currently forbids every DNP; AFE counts still assume
   69 footprints/251 pads/eight DNPs. Native validation is still required.
2. Reconcile P2 U102 preservation narrowly: only pads 5/11/12/13 change nets.
   Keep placement, pad geometry and unrelated copper protected. The older
   non-clock aggregate guard also rejects the intentional L5 changes; do not
   regenerate broad snapshots just to erase those failures.
3. Add native cuts at both pads of every new resistor (ten sides), plus five
   across-pad short/bypass mutations. Existing terminal cuts do not replace them.

Also audit the hardcoded XML/BOM/inventory counts and K2 whole-board hash binding;
review the new footprints' access before accepting any updated board binding.
The per-net return screen still needs a fresh native run, not an inferred pass.
No review finding has been closed, no preservation rule weakened, and no frozen
XML modified. The prior no-major-issues ff953 review is not candidate approval.

Local native execution was actually attempted and failed because pcbnew is
missing. The locked gate attempt stalled in dependency downloads and was bounded
at 20 s; it did not run the project gate. Available uv is 0.10.0, not 0.12.18.
Normal Git access still failed DNS. Connector object writes work for the small
source correction, but do not accept local file paths or apply the saved patch.
A probe for the candidate's auxiliary PCB blob returned 404: its hash is not an
already-published engineering blob. Do not treat the packet as integrated.
The remaining integration needs working pinned native CAD and an ordinary Git
publisher or equivalent authorized full-file transfer. Repeating recovery or
package searches without changed capabilities will not close it. The earlier
blocked runtime workflow remains blocked and must not be retried or bypassed.

## Next bounded source task

Recover the exact candidate in an isolated checkout of ff953c03, following the
packet hashes; verify complete tree `2e50d2bdd9f25f6cc74e0294d8015a822dda50f2`.
Then integrate only the eleven verified source files into this same PR98 without
losing its later handoff/recovery commits or unrelated work. Do not re-create the
L4 decision, five red tests, or another candidate from scratch when bytes exist.

Use pinned KiCad 9.0.2 and the existing locked gate to obtain FRESH native exports,
ERC, schematic/BOM/PCB parity, copper refill and DRC. Refresh frozen XML only from
actual native exports, never hand-edit it to make fixture-backed tests pass.
Implement/run both-side native cut/short cases and existing reference/bypass
regressions; review placement, driver-side detours and populated access. Repair
any demonstrated issue locally. Run exact applied-head CI and independent review
before considering a merge. A green preservation/doc head is not candidate proof.

The full locked local gate was unavailable (dependency DNS; installed uv differs
from the pinned version); KiCad was absent. An attempted runtime-packaging workflow
write was blocked and no such workflow was created. Do not retry it through Git
objects, another service, or project tests. Ordinary GitHub source-data writes
worked; source transfer and native-tool availability are distinct capabilities.
Initial mismatching loose transport blobs were rejected and are not packet parts.
`workbench/l5-native-tools` is an unused branch at the old ff953 base, not an
engineering source or an authorized runnable publisher.

## Evidence limits

Installed-pytest authoring diagnostics: 104 passes and 7 passing subtests; ten new
population checks failed before implementation. The static source interpreter
first matched old native XML partitions for 262 AFE and 212 AUX pins. Candidate
checks found five split paths, no copper bypasses, and ten detected pad-side cuts.
Nominal new/modified copper and pad/via geometry had no modeled conflict below
0.20 mm. Filled zones, fabrication tolerances and mounted hardware were NOT in
that clearance result. This is NOT native DRC, a locked gate or physical evidence.
The later candidate review is recorded above and remains blocking; no actual
target compile was obtained for the candidate. Prior ff953 CI/Codex results
cover only the older red-test/docs stage.

## Retained requirements and permissions

The [previous detailed handoff](recovery/l5_spi_candidate_20261008/previous_handoff.md)
is preserved unchanged as reference, not as a second current task list. Its
L1-L4/B1-B3 requirements and all #45/#48 conditions remain in force. Read their
canonical decision documents before altering those areas.

Keep selected parts/profile/firmware guards, the 450 s CAD budget, 71% branch floor,
all 15 bypass corridors and 39 terminal-cut checks, domain/mounting guards and
pending reference records. Do not run the parking-grid importer over authored
boards. Do not change dependencies, permissions or the single check orchestrator.

The pilot proposal remains INTERNAL-TEST-ONLY, retaining six upstream analog
pairs. Another PCB revision may be needed before E1 external-input acceptance.
Internal test/short mux modes do not isolate analog pins or qualify external paths.
Three MCU-driven stages and DRDY/other controls remain separate from five sites.

B1 passive keyed J2 fixture remains required, not J1. B2's existing run card and
B3 contacts/insulation/restraint/earth/uncertainty checks remain required. Preserve
R -> fresh F1 arm -> wake/clock -> 150 ms -> VCAP1 > 1.1 V -> reset; do not demand
raised VCAP1 while parked in PWDN. BOARD_PROFILE_REVIEWED stays false. Both DevKit
USB ports remain excluded; HOST/TARGET isolation and analog-input limits remain.
STOP is not a power disconnect. No supply, protection or workmanship qualification
is inferred from source topology or test counts.

Moscow remains a planning assumption. Q1 in `docs/quote/` is the sole frozen unsent
snapshot; its source hashes and proposed capacitor/stack/process dispositions are
unchanged. No price campaign, duplicate RFQ or supplier contact. No purchase,
fabrication, physical construction/rework/mating, power, external-input acquisition
or person/animal connection is authorized. Update `REV_A_COMPLETION_ROADMAP.md` and
report actual publication state plus the next bounded step, not a percentage safe.
