"""One-shot reviewed edits; removed before committing the final source."""
from pathlib import Path
import json
import re


def edit(name: str, before: str, after: str, count: int = 1) -> None:
    path = Path(name)
    text = path.read_text(encoding="utf-8")
    if text.count(before) != count:
        raise RuntimeError(f"Expected {count} reviewed fragments in {name}: {before[:80]!r}")
    path.write_text(text.replace(before, after), encoding="utf-8")


Path("tools/commit_messages.py").write_text(r'''"""Conventional Commit subjects for hooks and actual newly introduced commits.

Old history is not rewritten. Only actual multi-parent commits are exempt in CI;
a single-parent commit cannot bypass the rule by calling itself 'Merge ...'.
"""

import argparse
import re
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

_SUBJECT = re.compile(
    r"(?:feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)"
    r"(?:\([a-z0-9][a-z0-9._/-]*\))?!?: ([^\r\n]+)"
)


def valid_subject(subject: str) -> bool:
    match = _SUBJECT.fullmatch(subject)
    return match is not None and bool(match[1].strip()) and subject == subject.strip()


def _git(repo: Path, *args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args], cwd=repo, text=True, capture_output=True, check=True, timeout=30
        ).stdout.strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise ValueError(f"Git revision/history check failed: {exc}") from exc


def _commit(repo: Path, ref: str) -> str:
    # Resolve before constructing a range: user refs cannot become git options.
    sha = _git(repo, "rev-parse", "--verify", "--end-of-options", ref + "^{commit}")
    if re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", sha) is None:
        raise ValueError("Git returned an invalid commit identifier")
    return sha


def check_range(base: str, head: str = "HEAD", repo: Path = Path(".")) -> list[str]:
    start, end = _commit(repo, base), _commit(repo, head)
    records = _git(repo, "log", "--format=%H%x00%P%x00%s", f"{start}..{end}")
    errors: list[str] = []
    for record in records.splitlines():
        sha, parents, subject = record.split("\x00", 2)
        if len(parents.split()) < 2 and not valid_subject(subject):
            errors.append(f"{sha[:12]}: {subject!r} is not a Conventional Commit subject")
    return errors


def _message_error(path: Path, repo: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    subject = lines[0] if lines else ""
    if valid_subject(subject):
        return []
    merge_head = repo / _git(repo, "rev-parse", "--git-path", "MERGE_HEAD")
    if merge_head.is_file():
        return []  # CI still checks actual commit parents, not this hook context.
    return ["Use type(scope): description, for example fix(recording): reject gaps"]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--message-file", type=Path)
    mode.add_argument("--base")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--repo", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    try:
        errors = (
            _message_error(args.message_file, args.repo)
            if args.message_file is not None
            else check_range(args.base, args.head, args.repo)
        )
    except (ValueError, OSError) as exc:
        errors = [str(exc)]
    for error in errors:
        print(error, file=sys.stderr)
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
''', encoding="utf-8")

edit("tests/test_scientific_contracts.py", 'match="duration/port"', 'match="duration"')
edit("tach.toml", '"tools.check", "run_lab"]', '"tools.check", "tools.commit_messages", "run_lab"]')
with Path("tach.toml").open("a", encoding="utf-8") as stream:
    stream.write('\n[[modules]]\npath = "tools.commit_messages"\ndepends_on = []\n\n[[interfaces]]\nfrom = ["tools.commit_messages"]\nexpose = ["valid_subject", "check_range", "main"]\n')

edit(".pre-commit-config.yaml", 'minimum_pre_commit_version: \'4.6.2\'\n', 'minimum_pre_commit_version: \'4.6.2\'\ndefault_install_hook_types: [pre-commit, commit-msg]\ndefault_stages: [pre-commit]\n')
with Path(".pre-commit-config.yaml").open("a", encoding="utf-8") as stream:
    stream.write('''      - id: conventional-commit
        name: Conventional Commit subject
        entry: uv run --locked python -m tools.commit_messages --message-file
        language: system
        stages: [commit-msg]
''')
edit(".github/workflows/quality.yml", "branches: [main, 'dx/quality-foundation']", "branches: [main]")
edit(".github/workflows/quality.yml", "          persist-credentials: false\n", "          persist-credentials: false\n          fetch-depth: 0\n", count=2)
edit(".github/workflows/quality.yml", '      - name: Run the shared quality gate\n', '''      - name: Validate actual new commit subjects
        env:
          BASE_SHA: ${{ github.event.pull_request.base.sha || github.event.before }}
          HEAD_SHA: ${{ github.event.pull_request.head.sha || github.sha }}
        run: uv run --locked python -m tools.commit_messages --base "$BASE_SHA" --head "$HEAD_SHA"
      - name: Run the shared quality gate
''')
edit(".github/workflows/quality.yml", '        run: uv run --locked pre-commit run --all-files --show-diff-on-failure\n', '''        run: |
          uv run --locked pre-commit run --all-files --show-diff-on-failure
          printf 'fix(dx): exercise the actual commit hook\\n' > reports/check/commit-message.txt
          uv run --locked pre-commit run --hook-stage commit-msg --commit-msg-filename reports/check/commit-message.txt
          printf 'invalid subject\\n' > reports/check/commit-message.txt
          if uv run --locked pre-commit run --hook-stage commit-msg --commit-msg-filename reports/check/commit-message.txt; then
            echo 'Invalid commit was unexpectedly accepted'; exit 1
          fi
''')

# Replace a Python -c import trick with a normal module command, preserving the
# callable main(Path) API. Native integration exercises the actual CLI.
edit("tools/run_loopback.py", 'import json\n', 'import argparse\nimport json\n')
edit("tools/run_loopback.py", 'ROOT / "results/loopback"', 'ROOT / "reports/loopback"')
edit("tools/run_loopback.py", '    out.mkdir(parents=True, exist_ok=True)\n', '    out.mkdir(parents=True, exist_ok=True)\n    (out / "LOOPBACK_REPORT.json").unlink(missing_ok=True)\n')
edit("tools/run_loopback.py", '    sys.exit(main())\n', '    parser = argparse.ArgumentParser(description=__doc__)\n    parser.add_argument("--out", type=Path, default=ROOT / "reports/loopback")\n    sys.exit(main(parser.parse_args().out))\n')
edit("tools/check.py", '''            "-c",
            "from pathlib import Path; from tools.run_loopback import main; "
            "raise SystemExit(main(Path(__import__('sys').argv[1])))",
''', '''            "-m",
            "tools.run_loopback",
            "--out",
''')

# Current documentation is uv-first; dated historical results are immutable.
for name in ("README.md", "docs/DEVELOPMENT.md"):
    edit(name, "python -m pip install uv==0.12.18\n", "")
edit("README.md", 'Use `python3` for the first command on systems where `python` is unavailable, or `py -3` in Windows PowerShell. The remaining `uv` commands do not require virtual-environment activation. The editable installation makes package imports work outside the checkout too.', 'Install **uv 0.12.18** first using the [official installation instructions](https://docs.astral.sh/uv/getting-started/installation/). The standalone installer supports an explicit version in its URL. All project commands use `uv`; do not use a separately activated environment or bare Python/pip to run or modify this project. The editable installation makes imports work outside the checkout too.')
edit("README.md", 'The demo makes `results/demo/synthetic_recording.npz`, event/quality CSVs, an analysis JSON, and four PNG figures. The included example results were already generated. Use `--out reports/my_demo` to avoid replacing those examples. Regenerating uses the same seed, but numerical outputs can vary slightly across dependency versions.', 'The demo makes `reports/demo/synthetic_recording.npz`, event/quality CSVs, an analysis JSON, and four PNG figures. Live commands default to ignored `reports/`; committed `results/` examples are historical evidence. Use `--out reports/my_demo` for a separate run. The seed is fixed, but numerical outputs can vary slightly across dependency versions.')
edit("README.md", '**A successful software check is not a native-simulator, firmware-target, or hardware pass.** Run the explicit native command below for native integration. The legacy `uv run --locked python run_lab.py verify` command remains available, but deliberately writes historical-style results under `results/validation/` and replaces `VALIDATION.json`; it is not the routine DX gate.', '**A successful software check is not a native-simulator, firmware-target, or hardware pass.** Run the explicit native command below for native integration. `uv run --locked python run_lab.py verify` is now a compatibility entry point to the **same** `tools.check` gate. Add `--native` for native integration; `--require-ngspice` remains an alias. There is no competing historical-report verifier.')
edit("README.md", 'Before making changes, read [AGENTS.md](AGENTS.md) and install the optional commit hooks:', 'Before making changes, read [AGENTS.md](AGENTS.md) and install both the pre-commit and commit-message hooks:')
edit("README.md", 'To run only the legacy loopback with its default `results/loopback/` output, use `uv run --locked python -m tools.run_loopback`.', 'To run only the loopback, use `uv run --locked python -m tools.run_loopback --out reports/loopback`.')
edit("README.md", 'Keep the `.json` metadata beside the decoded CSV.', 'Keep the `.json` metadata beside the decoded CSV. New captures include a SHA-256 binding the pair; inspection rejects a mismatched generation. Legacy captures without a digest remain readable with an explicit caution.')
edit("README.md", 'lab/pipeline.py         Demo outputs and figures\n', 'lab/recording.py        Synthetic recording validation and atomic NPZ persistence\nlab/pipeline.py         Demo outputs and figures; compatibility persistence re-exports\n')
edit("README.md", 'tools/check.py         Shared local/CI quality command\n', 'tools/check.py         Shared local/CI quality command\ntools/commit_messages.py Conventional Commit hook and actual-history validation\n')
edit("README.md", '## Troubleshooting\n', '''## Contributing: uv and Conventional Commits

Use `uv sync --locked --all-extras` and `uv run --locked ...` for project work. Child processes launched with `sys.executable` inherit that locked interpreter; they do not create a second environment. CI bootstraps uv itself separately, then uses the same locked commands.

Commit subjects follow [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/):

```text
feat(simulation): add a Rev A input-network sweep
fix(recording): reject discontinuous sample times
refactor(acquisition): stream decoded packets
chore(dx): synchronize issue labels
```

Use lowercase `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, or `revert`; an optional lowercase scope describes the affected component. A breaking change uses `!` after the type/scope and should explain the incompatibility in a `BREAKING CHANGE:` footer. Subjects must have a nonempty description and no trailing whitespace.

The installed `commit-msg` hook checks the subject. CI checks **actual commits introduced by the PR**, not just its title. Old history is grandfathered. Actual merge commits are exempt, but writing “Merge” on a single-parent commit is not a bypass. **Merge PRs with merge commits: no squash and no history rewriting.** Validate a range locally with:

```bash
uv run --locked python -m tools.commit_messages --base origin/main --head HEAD
uv run --locked python -m tools.check --native
```

Issues use one `type/*`, one `priority/*`, and applicable `area/*` labels. Examples: `type/bug` + `priority/high` + `area/acquisition`, or `type/refactor` + `priority/medium` + `area/dx`. [The label manifest](.github/labels.json) owns names, colors, and descriptions; trusted-main housekeeping synchronizes it without deleting unrelated labels. Merged same-repository PR branches are removed only after ancestry and exact-head checks. Active or changed branches are retained.

Read [the adversarial review](docs/ADVERSARIAL_REVIEW.md) for the architecture verdict, reproduced failures, corrections, and remaining limits.

## Troubleshooting
''')
edit("docs/DEVELOPMENT.md", 'Work from the repository root. Python 3.11 is the minimum supported version; the normal development interpreter is 3.13. CI checks both. Install the pinned environment manager and synchronize the locked project, development tools, and optional serial dependency:', 'Work from the repository root. Python 3.11 is the minimum supported version; the normal development interpreter is 3.13. CI checks both. Install uv 0.12.18 using its [official standalone installation instructions](https://docs.astral.sh/uv/getting-started/installation/), then synchronize the locked project, development tools, and optional serial dependency:')
edit("docs/DEVELOPMENT.md", 'The old `python run_lab.py verify` command remains an explicit historical-style report generator and is not the DX gate.', '`uv run --locked python run_lab.py verify` delegates to this same gate; `--native` (or the old `--require-ngspice` alias) adds native checks. The redundant `tools.validate` implementation was deleted.')
edit("docs/DEVELOPMENT.md", 'Keep the DX review separate from hardware PR #1 and from new simulation behavior. Review changes against the hardware-baseline branch until #1 is merged, then retarget the DX PR to `main`. Do not merge either PR or change the selected hardware/gates as part of tooling work.', 'Hardware PR #1 and DX PR #2 were merged, in that order, using merge commits. Review subsequent changes against `main`; keep architecture fixes separate from new simulation behavior. Use Conventional Commit subjects as specified in the README. `pre-commit install` installs both hook stages, and CI checks the actual new commit range. Merge with merge commits, never squash or rewrite published history. Merging software does not approve any hardware gate.')
with Path("AGENTS.md").open("a", encoding="utf-8") as stream:
    stream.write('''
## Commits and ownership

Use Conventional Commit subjects (`feat`, `fix`, `refactor`, `docs`, `test`, `build`, `ci`, `chore`, etc.) with optional lowercase scopes. Install hooks with `uv run --locked pre-commit install`; CI validates the actual new commit range. Preserve history with merge commits, not squash. Use the type/priority/area issue-label taxonomy in `.github/labels.json`.

`lab.recording` owns the synthetic-recording contract and persistence; `lab.pipeline` re-exports its old load/save names for compatibility. `tools.check` is the only verification orchestrator. Read `docs/ADVERSARIAL_REVIEW.md` before introducing new layers. Project commands run through uv; do not introduce a second pip-managed environment.
''')
edit("docs/LLM_HANDOFF.md", 'Hardware PR #1 and the DX review are separate. Until #1 is merged, review the DX branch against `hardware/rev-a-component-baseline`; retarget it to `main` afterward. Do not merge or change hardware gates without explicit authorization. The existence of CI workflows is not proof that required-status branch-protection settings are enabled.', 'Hardware PR #1 and DX PR #2 were merged in order with merge commits. Audit #3 and child findings #4–#8 are implemented in PR #9; consult its final checks and `docs/ADVERSARIAL_REVIEW.md` rather than assuming a branch snapshot passed. Use Conventional Commits, uv-first commands, and merge commits without squash. `lab.recording` owns synthetic persistence/continuity, capture decoding streams into digest-bound artifacts, and `tools.check` owns verification. The existence of CI workflows is not proof that required-status branch protection is enabled. All hardware gates remain unchanged.')
for name in ("docs/HARDWARE_BASELINE_REV_A.md", "docs/HARDWARE_GUIDE.md", "docs/LEARNING_GUIDE.md", "docs/EXPERIMENTS.md"):
    path = Path(name)
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"(?m)^python(?:3)? (?=(?:run_lab\.py|hardware/|-m ))", "uv run --locked python ", text)
    path.write_text(text, encoding="utf-8")

labels = []
for prefix, items, color in (
    ("type", {"bug": "Incorrect behavior or invalid scientific evidence", "feature": "New user-facing capability", "refactor": "Simplify structure while preserving intended behavior", "chore": "Repository upkeep and development ergonomics", "docs": "Documentation and learning material", "test": "Regression, property, or integration coverage", "ci": "Continuous integration and repository automation"}, "7057ff"),
    ("priority", {"high": "Correctness, safety-boundary, or evidence-integrity blocker", "medium": "Important work without an immediate correctness blocker", "low": "Useful improvement that can follow higher-priority work"}, "fbca04"),
    ("area", {"dx": "Tooling, contributor workflow, and architecture enforcement", "hardware": "Static Rev A contracts, BOM, and schematic planning", "simulation": "Analog models and independent simulator comparisons", "acquisition": "Capture, packet transport, and decoding", "analysis": "Recording semantics, DSP, and experimental analysis", "firmware": "Guarded MCU code and target-specific builds"}, "0075ca"),
):
    for name, description in items.items():
        labels.append({"name": f"{prefix}/{name}", "description": description, "color": color})
for label in labels:
    if label["name"] in ("type/bug", "priority/high"):
        label["color"] = "d73a4a"
    if label["name"] == "priority/low":
        label["color"] = "c2e0c6"
Path(".github/labels.json").write_text(json.dumps(labels, indent=2) + "\n", encoding="utf-8")
