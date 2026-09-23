"""Commit policy is checked against real Git history, not PR titles."""

import subprocess
from pathlib import Path

import pytest

from tools.commit_messages import check_range, main, valid_subject


@pytest.mark.parametrize(
    "subject",
    [
        "feat: add a circuit",
        "fix(recording): reject gaps",
        "refactor(analog)!: simplify the model",
        "docs: explain uv",
        "build(dx): lock tooling",
        "ci: run native checks",
        "chore: synchronize labels",
        "test(protocol): cover wraparound",
        "perf(acquisition): stream packets",
        "style: format source",
        "revert: undo an experiment",
    ],
)
def test_valid_subjects(subject: str) -> None:
    assert valid_subject(subject)


@pytest.mark.parametrize(
    "subject",
    [
        "",
        "update things",
        "Fix: capitalize",
        "feat:",
        "feat:   ",
        "feat(): empty scope",
        "feat: line\nbreak",
        "fix: trailing space ",
        "Merge pull request #5",
        "unknown: type",
    ],
)
def test_invalid_subjects(subject: str) -> None:
    assert not valid_subject(subject)


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, text=True, capture_output=True, check=True, timeout=15
    ).stdout.strip()


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "-b", "main")
    _git(tmp_path, "config", "user.name", "Policy test")
    _git(tmp_path, "config", "user.email", "policy@example.invalid")
    _git(tmp_path, "commit", "--allow-empty", "-m", "Historical unstructured message")
    return tmp_path


def test_old_history_is_grandfathered_but_new_bad_commit_is_not(repository: Path) -> None:
    base = _git(repository, "rev-parse", "HEAD")
    _git(repository, "commit", "--allow-empty", "-m", "fix: good new change")
    assert check_range(base, "HEAD", repository) == []
    _git(repository, "commit", "--allow-empty", "-m", "not a conventional commit")
    errors = check_range(base, "HEAD", repository)
    assert len(errors) == 1
    assert "not a conventional commit" in errors[0]


def test_only_actual_merge_commits_are_exempt(repository: Path) -> None:
    base = _git(repository, "rev-parse", "HEAD")
    _git(repository, "switch", "-c", "feature")
    _git(repository, "commit", "--allow-empty", "-m", "feat: independent work")
    _git(repository, "switch", "main")
    _git(repository, "commit", "--allow-empty", "-m", "chore: advance main")
    _git(repository, "merge", "--no-ff", "feature", "-m", "Merge branch 'feature'")
    assert check_range(base, "HEAD", repository) == []
    _git(repository, "commit", "--allow-empty", "-m", "Merge forged single-parent commit")
    assert len(check_range(base, "HEAD", repository)) == 1


def test_empty_range_and_cli_range(repository: Path) -> None:
    assert check_range("HEAD", "HEAD", repository) == []
    assert main(["--base", "HEAD", "--repo", str(repository)]) == 0
    _git(repository, "commit", "--allow-empty", "-m", "invalid")
    assert main(["--base", "HEAD~1", "--repo", str(repository)]) == 1


@pytest.mark.parametrize("ref", ["missing-ref", "--all", "HEAD; touch unwanted"])
def test_invalid_revisions_fail_closed(repository: Path, ref: str) -> None:
    with pytest.raises(ValueError, match="Git"):
        check_range(ref, "HEAD", repository)
    assert not (repository / "unwanted").exists()


def test_message_file_and_real_merge_context(repository: Path) -> None:
    message = repository / "message.txt"
    message.write_text("fix(dx): enforce subjects\n\nA longer explanation.\n", encoding="utf-8")
    argv = ["--message-file", str(message), "--repo", str(repository)]
    assert main(argv) == 0
    message.write_text("invalid\n", encoding="utf-8")
    assert main(argv) == 1
    message.write_text("", encoding="utf-8")
    assert main(argv) == 1
    (repository / ".git/MERGE_HEAD").write_text(_git(repository, "rev-parse", "HEAD"))
    message.write_text("Merge branch 'feature'\n", encoding="utf-8")
    assert main(argv) == 0


def test_cli_reports_missing_file(repository: Path) -> None:
    assert main(["--message-file", str(repository / "absent")]) == 1


def _timeout(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
    raise subprocess.TimeoutExpired("git", 30)


def test_git_timeout_fails_closed(repository: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("subprocess.run", _timeout)
    with pytest.raises(ValueError, match="Git"):
        check_range("HEAD", "HEAD", repository)
