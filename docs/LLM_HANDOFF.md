# Continue PR98: L5 population and preservation source guards repaired; native integration pending

Read root `AGENTS.md`, `REPOSITORY_PUBLICATION.md`, `DEVELOPMENT.md` and
`REV_A_BENCH_FIRST.md`. Check live main, open/recently merged PRs and original
review submissions. Continue `work/l5-spi-series` / draft PR98, not a new study.

## Source state and this bounded change

This slice starts from remote `a23a3726f5553a7eaa72615e0cfa2438ce426f00`, complete
tree `96266a7dc6d0322f3bb2bb74b1af1749fca08b2f`. Main was c2f93ee3 (PR97).
Read the live PR for the published successor head; do not reuse an old green run.
The actual eleven-file hardware candidate is STILL UNAPPLIED to active PR CAD.
Its unchanged durable source is [the recovery packet](recovery/l5_spi_candidate_20261008/README.md).
Base ff953c03/tree928e944 produces exact candidate tree
`2e50d2bdd9f25f6cc74e0294d8015a822dda50f2`. Do not recreate or re-upload it.

Two concrete validator portions of Codex review 5462618515 are now repaired:

1. AFE placement/seed inventory checks verify the closed native-reference set,
   unique contract references, pad totals and BOM membership. They check native
   DNP, Population, MPN and BOM_ID agreement, not just an aggregate DNP count.
   The existing eight clamp DNPs stay required. Exactly R24/R_MISO_SER can add
   one unpopulated, NOT_SELECTED two-pad position; an unexpected selected value,
   duplicate reference or contradictory field fails. The auxiliary native probe
   similarly admits only R117-R120 as DNP, keeps their BOM membership and checks
   contract/field/native-bit agreement. The native inventory remains 48 parts /
   212 electrical pins plus exactly all four additions when present, not a loose
   lower bound. Field-getter unit doubles do NOT establish native execution.
2. P2 and clock preservation retain their ORIGINAL snapshots. A new exact
   `tests/fixtures/auxiliary_l5_delta.json` comparison delta maps only the complete
   original candidate's affected records back to the historical comparison set.
   It accepts the entire old state OR the entire exact proposed state, never a
   partial mixture. It does not edit PCB data or electrically merge split nets.
   Unrelated records remain visible to the original 153-object P2 and 831-object
   non-clock aggregate guards. Native routing/reference/clearance checks remain.

The delta audit found 21 before / 41 after records: 15 modified, six removed,
26 added. Only U102 changes among existing footprints. Replacing exactly its
four changed pad-net fields (5/11/12/13) restores every other original byte.
Affected copper belongs only to the four selected SPI paths; new footprints are
R117-R120. The new exact hashes bind a source candidate, NOT approved geometry.
Tests corrupt each of the 41 candidate records and exercise partial application,
resurrected deleted copper, unrelated changes/additions/removals and duplicate IDs.
Do not turn this into blanket net-name filtering or regenerate broad snapshots.

The existing `tools.check` snapshot list includes the four new helper/test/fixture
inputs. No orchestration, command, dependency, permission, limit or skip changed.
Clock filtering still includes MCU_MISO and MCU_MISO_DRV with the unchanged
0.60 mm/length/via/layer conditions from the previous repair.

## Evidence scope and exact identities

Local installed-pytest authoring evidence, NOT a locked/native gate:
- Fail-first population input blob `a54ed1c8917274d9358a2ac7f85b8783a08c2397`,
  source-equivalent tree `50eccc450aee06b5b3a935c3aa0089b609cca927`: ten failures,
  seven passes using `python -m pytest -q tests/test_pcb_population.py`.
- Before changing preservation checks, the actual saved candidate failed the
  existing P2 U102 hash check and clock non-clock count (851 versus 831).
- The corrected code-only source-equivalent tree, before these doc edits, is
  `637503144890cd0f40305343a92d24eaa393fde6`. The focused command selects
  `tests/test_pcb_population.py`, `tests/test_auxiliary_preservation.py`, the
  source-only inventory/P2/clock tests in their existing modules, and
  `tests/test_auxiliary_clock_selection.py`: 37 passes on the old active boards
  AND 37 passes when the original eleven-file candidate is overlaid locally.
  Candidate geometry is unchanged; these are source/field/hash checks only.
- A broader selection of these modules, PCB seed, auxiliary placement and
  `tests/test_check_runner.py`, excluding schematic/native/integration markers,
  produced 80 passes and one failure because Ruff is absent. It is not a gate
  pass. No skipped native test is represented as executed.

The source-equivalent trees include the five unchanged hidden-root identities
verified against the remote tree; synthetic local reconstruction ancestry is
not remote history. Exact source hashes, logs and later hosted receipts belong
in the PR discussion/evidence. Read actual current-head CI and review before
acceptance; these local counts are not borrowed results for every later head.

Both locked sync and the locked gate were attempted with bounded downloads;
no project gate completed. Available uv remains 0.10.0 versus pinned 0.12.18.
A real `/usr/bin/python3` import still fails because pcbnew is absent. Ordinary
Git/download attempts fail DNS. The previously blocked runtime workflow must
NOT be retried or bypassed through APIs, project tests or another service.
Small source-object publication works; large active-PCB transfer and native-tool
availability are separate unresolved capabilities. No new runtime is authorized.

## Remaining integration work: not a clean hardware review

The source-level DNP and exact-preservation fixes require independent review and
an actual pinned native run. They are NOT a claim that every inventory/export
consumer or the complete original P1 findings are qualified. In particular:
- Add and run ten native resistor-pad-side cut cases and five across-pad copper
  short/bypass cases. Old terminal cuts and API doubles do not replace them.
- Integrate the eleven real candidate files into THIS PR, retaining later commits.
  Obtain native XML/CSV exports and update stale export/count consumers coherently;
  never hand-edit frozen XML to simulate an export. Refill stale copper and run
  ERC, schematic/BOM/PCB parity, DRC and reference/bypass/domain regressions.
- The AFE output-reference and mutation selectors still use only MISO. Their
  driver-side MISO_DRV coverage needs a failure-first repair during integration;
  do not merge electrical nets or relax own-contact/escape/length/via limits.
- Review K2's board binding and access before any hash update. Review driver-side
  detours, especially R24's approximately 10.85 mm/two-via path, and installed
  component/probe access. Accessible lands are not SI or workmanship acceptance.

Require exact applied-head CI and independent review before merge. The original
five fixture-backed missing-position requirements remain red on active PR source.
Do not xfail them, treat preserved data as applied hardware, or equate this source
repair with manufacture readiness. Do not repeat recovery searches in an unchanged
blocked environment. The next bounded implementation is the native cut/short
regressions and coherent native integration, not another general timing study.

## Unchanged engineering and permission boundaries

The [retained detailed handoff](recovery/l5_spi_candidate_20261008/previous_handoff.md)
and canonical L1-L4/B1-B3 documents remain authoritative for their requirements.
Keep selected parts/profile, original boards/BOM/contracts/firmware, all protection
and startup gates, 450 s CAD allowance, 71% branch floor and ordinary workflow
permissions unchanged. No parking-grid importer over authored copper. Original
P2/clock snapshots, native XML, pending-reference records and Q1 hashes are retained.

All five new positions remain proposed DNP/NOT_SELECTED; no resistance, including
zero ohms, is approved for power. R114 stays the receiver-side 42.2k shunt and
logical MOD1.GPIO13 stays downstream with J1.5. An absent series part is open.
The pilot remains INTERNAL-TEST-ONLY with the six upstream analog pairs retained;
E1 external-input acceptance and possible additional PCB revision are unchanged.
The other MCU-driven stages and DRDY/control requirements remain separate.

B1 passive keyed J2 fixture, B2 run card and B3 attachment/earth/uncertainty checks
remain required. Preserve R -> fresh F1 arm -> wake/clock -> 150 ms -> VCAP1 >1.1 V
-> reset. BOARD_PROFILE_REVIEWED remains false; both DevKit USB ports stay excluded;
HOST/TARGET isolation, analog limits and complete-run invalidation remain. STOP is
not a power disconnect. No physical acquisition or fault behavior was measured.

Moscow is a planning assumption; sole Q1 snapshot remains unsent and frozen.
No price campaign, outreach, purchase, fabrication, physical construction/rework/
mating, powering, external-input acquisition or person/animal use is authorized.
