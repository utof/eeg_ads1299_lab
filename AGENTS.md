# Working on ADS1299 Learning Lab

Read `docs/DEVELOPMENT.md`, `docs/LLM_HANDOFF.md`, and the Rev A hardware baseline before changing code.

## Practical engineering first — standing user preference

Read [the bench-first decision](docs/REV_A_BENCH_FIRST.md) before choosing a slice.
The user prioritizes a safe real prototype, not accumulating studies or tests.
Use clearly labelled, reversible planning assumptions when details are missing;
do not invent measured limits or block independent work on an unanswered model.
Each slice must close a build decision, fix a demonstrated defect, or prepare a
specific physical check. Reuse existing calculators, contracts and the one gate.
Refactor when a concrete ownership/duplication problem obstructs that task, not
for speculative elegance. No new framework or parallel worksheet without need.
Separate before-fabrication, before-power and later-characterization questions.
Keep safety gates and necessary regressions; fewer checks is not the objective.
A planning assumption never authorizes purchasing, energization or body use.

Delivery planning is Moscow, Russia (user assumption, not a verified address).
Do not spend slices on detailed price/stock lookups; keep unknown costs open and
prioritize the next independent build or inspection decision. No supplier contact
or order is implied. The canonical Q1 packet is in `docs/quote/`; do not duplicate it.

## GitHub: read this before trying to publish

**Mandatory for every fresh agent:** read `docs/REPOSITORY_PUBLICATION.md` before
GitHub publication, recovery, or telling the user that manual setup is required.
Read live main, open PRs and original review threads; chat memory is not current
repository state. In a connector session, discover the relevant GitHub actions
with `api_tool.list_resources` and obey their actual schemas. A missing action,
a network failure and an explicit permission denial are different conditions.

`@codex review` is review, NOT a commit/push operation. The missing environment
message from a non-review Codex task does not mean GitHub writes or reviews are
unavailable. PR77 and PR81 used source publication separately from Codex review;
the runbook records the successful, hash-verified methods. Never repeat the old
import loop, reroute preserved copper, or upload the same recovery data again.

Prefer ordinary authenticated Git or available blob/tree/commit/non-force-ref
actions; verify the remote full tree and disclose recreated commit metadata.
A scoped publisher is a separate authorized capability, never an automatic
fallback after a denied action. Do not change permissions, expose credentials,
force branches, modify main directly or invent tool names. If genuinely blocked,
record the exact failed capability and preserve source on a discoverable branch
when writes permit; otherwise retain verified recovery evidence and state that
publication is incomplete.
Do not call a staging note or encoded archive the active engineering source.
For a failed/interrupted chat, follow
[the recovery check](docs/REPOSITORY_PUBLICATION.md#resuming-an-interrupted-turn):
inspect recently merged PRs too. A failed reply can follow a successful merge;
never redo the finished task just because its final chat message is missing.

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
