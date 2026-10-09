# Continue PR98: native fault cases authored; hardware integration remains

Read `REPOSITORY_PUBLICATION.md`, root `AGENTS.md`, `DEVELOPMENT.md` and
`REV_A_BENCH_FIRST.md`. Check live main, open AND recently merged PRs and original
reviews before editing. A failed chat reply does not mean publication failed.

## Published work and actual remaining boundary

Main was checked at `c2f93ee30eb47f80a7702603f20ed22e6cce86af` (PR97).
Continue draft PR98, `work/l5-spi-series`; do not open a duplicate recovery PR.
The interrupted population/preservation slice was already published at
`cc9cc797ccafddb5f5d3de5e643df37c905abdb2`, tree
`a2073200ac9a0d6feba756d517d3c97451887613`. Its CI stopped at formatting, before
project tests. This continuation fixes that formatting and adds the source below.
No board, schematic, BOM, contract, native XML or firmware is changed here.

The eleven-file hardware candidate remains UNAPPLIED to active engineering files.
Use [the existing recovery packet](recovery/l5_spi_candidate_20261008/README.md),
not a new archive or recreated geometry. Exact base is
`ff953c03c452f1572602b52aa62f42e80bfa9588`, tree
`928e94437784b2249042555e1fa17316406dfc41`; exact candidate tree is
`2e50d2bdd9f25f6cc74e0294d8015a822dda50f2`. Preserve later PR98 commits when
integrating its eleven verified files. Frozen XML has not been hand-edited and
candidate copper fills are stale. The original five missing-position tests
therefore remain red. No full gate, merge, fabrication or physical release follows.

## Concrete source changes now present

`tests/test_spi_series_native.py` contains the requested TEN pad-side cuts and
FIVE across-pad copper bridges for R117-R120/R24. Two clean native canonical
copies precede fifteen independent fault copies. Each copy uses existing native
refill/DRC helpers; copied reports are removed first. A cut must produce an
unconnected finding containing the exact target pad UUID and net. A bridge must
produce a short finding containing the added track UUID and both distinct nets
in the SAME finding. Unrelated board errors cannot satisfy those witnesses.
Native DNP/Population/NOT_SELECTED, separate pad nets and physical endpoints are
checked before mutation. Only logical off-board MOD1.GPIO13 is omitted from PCB
endpoint lookup. R114 remains a required physical downstream endpoint.

These are authored NATIVE TESTS, NOT fifteen executed native passes. The local
native attempt stopped during baseline setup because KiCad was absent, before
any mutation. Five ordinary synthetic-report tests exercise only finding matching.
Do not replace native execution with those report tests or count them as CAD.

The AFE output-reference probe now measures MISO_DRV as well as MISO and DRDY.
Presence of the driver segment must agree with R24. Electrical-net-specific own
contact/antipad exclusions remain separate. Only the resulting metrics combine:
MISO plus MISO_DRV share the ORIGINAL two-via, 10 mm inner-route and reference-area
budgets, not an allowance per segment. Existing layer, rectangle and straightness
requirements remain. Native mutation controls select both MISO segments while
preserving each track's net code. DRDY and unrelated guards remain unchanged.
Fifteen API-getter/AST tests check actual selection/aggregation statements without
emulating native polygons or physical connectivity.

The earlier cc9 DNP/inventory and exact-delta preservation repairs remain. Only
R24 and R117-R120 may have the new unpopulated state. Native bits, custom fields
and BOM/contract intent must agree. Original P2 and clock snapshots are unchanged;
the exact 21-before/41-after mapping rejects partial, mixed and unrelated edits.
Formatting-only changes to the population/preservation test files preserve their
ASTs. `tools/check.py` only adds three source-snapshot paths; orchestration,
selection, permissions, 450 s CAD budget and 71% branch floor are unchanged.

## Evidence identity and limits

Fail-first commit `d0934c1a35b86a73b3fa961b2432a6d91652ebfb`, tree
`56a8510f163d5b07ddba7b75b6a117128e902586`, precedes the correction. Local command
`python -m pytest -q tests/test_output_reference_selection.py` produced 13 intended
failures and two passes using test blob `d3952f702941a5f7fd067b19ae4be489de37f31b`
and old probe blob `dc3274f60faf6a62a371d32d94dc7a3b35395f6b`.

Corrected code tree before this handoff update:
`48da78a50c5f96a180cfe6423e405e1d90ea10ac`; corrected probe blob
`a5b157e2e43fd29c4a13348ff458314feaff370d`. The installed-pytest focused command
below passed 57 cases, deselecting the fifteen unexecuted native cases:

```sh
python -m pytest -q -m 'not schematic' \
  tests/test_output_reference_selection.py tests/test_spi_series_native.py \
  tests/test_pcb_population.py tests/test_auxiliary_preservation.py \
  tests/test_auxiliary_clock_selection.py \
  tests/test_pcb_placement.py::test_editable_placement_is_a_tracked_design_not_a_parking_grid \
  tests/test_auxiliary_routing.py::test_p3_preserves_all_p2_footprints_and_original_copper \
  tests/test_auxiliary_clock.py::test_only_clock_copper_changes_in_the_review_repair
```

These results cover the listed source/API-double scope, not native geometry,
full locked verification or the unapplied candidate. Read actual exact-head CI
and new review before extending any claim. Old cc9 CI and ff953/6f879 reviews
cannot approve this change. The reconstructed full base and published blob/tree
hashes were checked independently; synthetic local recovery ancestry is not
remote history. A mismatching loose transport blob was rejected, never attached.

Local uv remains 0.10.0, not pinned 0.12.18. Locked sync timed out in downloads;
the locked gate attempt did not reach project checks. KiCad/pcbnew and ordinary
Git network access remain unavailable. The earlier blocked runtime-packaging
workflow must not be retried or bypassed through tests, Git objects or services.
An old existing runtime run was inspected read-only and had no downloadable
artifacts; no workflow was created, changed or rerun. Do not repeat this search.
Small literal-content object writes work; large-file integration is not achieved
by publishing patch data or by supplying a local filename as content.

## Next bounded work: applied native integration, not another test plan

With working pinned KiCad 9.0.2 and authorized complete-file Git publication,
apply the saved candidate in THIS PR, retaining the new tests and source repairs.
Generate fresh native XML/CSV and update the fixtures from those exports only.
Reconcile remaining export/inventory consumers, including K2's whole-board hash
binding AFTER reviewing actual placement/access. Refill both boards; run parity,
ERC/DRC, all fifteen new fault cases and the existing output/reference/bypass/
domain/mounting regressions. Review driver-side detours and access. No arbitrary
snapshot reset, relaxed limit, xfail or skipped safety regression is acceptable.

Candidate review 5462618515 raised three P1s. DNP and preservation have source
repairs; cut/short regression SOURCE now exists. Native execution and independent
acceptance remain required for all three. Do not mark them physically qualified
or infer closure merely because unit tests pass. Require exact applied-head CI
and independent review before merge. Do not merge the current incomplete draft.

## Retained engineering and permissions

The [detailed earlier handoff](recovery/l5_spi_candidate_20261008/previous_handoff.md)
and canonical L1-L4/B1-B3 documents retain all requirements, including #45/#48.
Keep the authored copper, selected profile, firmware gates, all 15 bypass corridors,
39 existing terminal-cut checks and pending return-reference records. Never run
the parking-grid importer over either authored board. No dependency upgrade or
new framework is part of this slice.

The five candidate positions are DNP/NOT_SELECTED 0603 lands, not fitted damping
parts. R114 stays receiver-side; MOD1.GPIO13 stays downstream with J1.5. No existing
footprint moves, including R20. Driver legs of about 5.3-10.9 mm/two vias, especially
R24's 10.85 mm route, remain a disclosed access-versus-source-distance tradeoff,
not qualified termination. An absent series part is open; zero ohms is not an
approved first-power configuration.

The proposed pilot is INTERNAL-TEST-ONLY, retaining six upstream analog pairs.
Accept its restricted purpose and possible further PCB revision at release; E1
external-input requirements remain. Internal mux modes are not an isolation
barrier. MCU-driven launches and DRDY/control requirements are separate.

B1 requires the passive keyed J2 fixture, not J1. B2's existing run card and B3
joint/insulation/restraint/earth/uncertainty checks remain. Preserve R -> fresh F1
arm -> wake/clock -> 150 ms -> VCAP1 > 1.1 V -> reset, not raised VCAP1 while parked
in PWDN. BOARD_PROFILE_REVIEWED stays false. Both DevKit USB ports remain excluded;
HOST/TARGET isolation, analog fault limits and complete-run invalidation remain.
STOP is not a power disconnect. No assembly or instrument qualification exists.

Moscow is only the planning assumption. Q1 in `docs/quote/` remains the sole frozen
unsent packet; capacitor/stack/process proposals and all source hashes remain.
No price/outreach campaign, purchase, fabrication, physical work/rework/mating,
powering, external-input acquisition or person/animal use is authorized.
