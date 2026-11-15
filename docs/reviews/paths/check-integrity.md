---
id: check-integrity
code: CHECK
title: Checks that actually fail
status: partial
stage: before-fab
reviewed_at: 652193d
reviewed_on: 2026-11-01
scope:
  - tools/check.py
  - tools/dc_budget.py
  - pyproject.toml
  - hardware/rev_a/check_baseline.py
  - hardware/rev_a/check_schematic.py
  - lab/analog/_spice.py
  - tests
  - .github/workflows
---

# Checks that actually fail

## Covers

Whether `tools.check`, the hardware validators, SPICE freshness handling and
the test suites fail when the thing they guard is broken: assertions that
cannot fail, swallowed exceptions, stale simulator output, skipped tiers.

## Findings

| ID | Status | Summary | Where (at 652193d) |
|---|---|---|---|
| CHECK-01 | open (by design, note) | Native tests are deselected from the default local gate and run only in the CI native job; local `--native` exists but times out on this machine | `tools/check.py:74` |
| CHECK-02 | suspected | A sub-review reported that `main` has no required status checks; not re-verified | GitHub branch protection |

See also SAFE-01/SAFE-02 (guards with no failing test) and DATA-01 (bare
asserts) in their paths.

## Not yet covered

- KiCad schematic/CAD test tier execution (hosted only).
- `tools.check --native` / `--firmware` end-to-end locally.
- Mutation testing beyond the firmware interlock.

## Log

- 2026-11-01, 652193d, Opus critical-bug review, verification sub-review:
  read all of `tools/check.py`, `dc_budget.py` and pytest config; baseline and
  schematic checkers detected mutated nets; SPICE output freshness checked; AST
  scan for assertions that can't fail; firmware mutation runs (produced
  SAFE-01). Nothing critical beyond the cross-referenced findings.
