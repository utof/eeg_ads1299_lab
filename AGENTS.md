# Working on ADS1299 Learning Lab

Read `docs/DEVELOPMENT.md`, `docs/LLM_HANDOFF.md`, and the Rev A hardware baseline before changing code.

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
