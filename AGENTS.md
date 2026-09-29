# Working on ADS1299 Learning Lab

Read `docs/DEVELOPMENT.md`, `docs/LLM_HANDOFF.md`, and the Rev A hardware baseline before changing code.

## Repository-first continuation

The repository is the handoff, not the previous chat. Start from the live main/open
PR state and the current `docs/LLM_HANDOFF.md`; record the exact branch, SHA/tree and
working-tree state before changing anything. The current routed PCB is authored
source at `hardware/rev_a/layout/rev_a.kicad_pcb`, not an importer output to rebuild.

Before reporting a slice delivered, publish its source and tests to a named PR,
read back the remote head, and update the current handoff with the next task and
blockers. Bind verification/review claims to the actual tested head. Preserve
small durable evidence summaries and necessary reference inputs in Git; transient
logs may be artifacts, but a chat ZIP or expiring artifact must not be the only
copy needed to continue. Clearly report unpublished work or unavailable tools.
Keep unfinished work discoverable in its open PR; never imply it is already main.

## Completion reports

For every meaningful slice, start the user-facing report with a short **TLDR**:
what actually changed, whether it is published/merged, and the important limit
or blocker. Follow it with a glanceable roadmap table containing **category**,
**estimated remaining substantial chat turns**, **done/status**, and **next slice
or blocker**. Keep `docs/REV_A_COMPLETION_ROADMAP.md` current and use it as the
starting point. Estimates are ranges, not promises or percentages of safety;
exclude manufacturing wait time and identify work needing physical measurements
or user decisions. End the substantive report with the specific next bounded
step. Include useful technical/test evidence after the overview, tied to exact
source heads; do not substitute test-count growth for engineering progress.

## Non-negotiable scope

Keep the selected Rev A components, board profile, BOM, firmware target guards, and all safety gates unchanged unless the task explicitly calls for a reviewed change. Software checks, SPICE, and native C++ helper tests do not authorize body connection or establish physical hardware safety. Do not reopen component selection as part of simulation or DX work. Do not claim a target firmware build because the portable helper compiled.

## Development loop

Use the pinned environment: `uv sync --locked --all-extras`. Run `uv run --locked python -m tools.check` before and after changes. Use `--native` only with ngspice, Node, and a C++ compiler installed; missing required tools must fail.

For a bug or new behavior, first write a focused test, run it, and observe the intended failure. Implement the smallest correction; then refactor with the tests green. Characterize existing numerical behavior before reorganizing it. Keep random seeds and numerical tolerances explicit, with an independent expected result where possible. Do not rewrite expected outputs just to make a test pass.

## Interfaces and typing

Import another component through its public interface. In particular, use `lab.analog` and `hardware.rev_a`, never their implementation modules. Within a component, import implementation modules directly rather than looping through its own facade. Keep facade `__all__` and `tach.toml` interfaces aligned. No import-time simulations, configuration reads, directories, sockets, or radio/device access.

Annotate functions and tests. Validate JSON, NPZ arrays, and other untrusted input at entry points. A cast is not validation. Array annotations do not establish array dimensions, physical units, or finiteness. Keep untyped-library adaptations narrow; do not export `Any` throughout the program.

## Checks and evidence

Ruff uses safe fixes only. Pyrefly is strict and fails on warnings as well as errors. Cognitive complexity must be at most 15 (aim for 10). Do not add blanket suppressions, ignored modules, hidden complexity baselines, or lower coverage thresholds to bypass failures. Any narrowly justified exception requires an explicit rationale and review.

Run the same `tools.check` entry point locally and in CI. Keep subprocesses bounded and retain failure output. Never accept stale simulator output as a fresh successful run. CI evidence belongs in ignored `reports/`; do not overwrite committed `results/`, `VALIDATION.json`, or historical validation records during routine quality checks.

Treat `pyproject.toml` and `uv.lock` as the dependency source of truth. Regenerate requirements exports using the commands in the development guide. `requirements-tested.txt` is a historical record, not a second dependency input. Keep feature changes separate from broad formatting or dependency upgrades.

## Commits and ownership

Use Conventional Commit subjects (`feat`, `fix`, `refactor`, `docs`, `test`, `build`, `ci`, `chore`, etc.) with optional lowercase scopes. Install hooks with `uv run --locked pre-commit install`; CI validates the actual new commit range. Preserve history with merge commits, not squash. Use the type/priority/area issue-label taxonomy in `.github/labels.json`.

`lab.recording` owns the synthetic-recording contract and persistence; `lab.pipeline` re-exports its old load/save names for compatibility. `tools.check` is the only verification orchestrator. Read `docs/ADVERSARIAL_REVIEW.md` before introducing new layers. Project commands run through uv; do not introduce a second pip-managed environment.
