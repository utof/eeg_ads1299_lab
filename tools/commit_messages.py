"""Conventional Commit subjects for hooks and actual newly introduced commits.

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
        ).stdout.rstrip("\n")
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
