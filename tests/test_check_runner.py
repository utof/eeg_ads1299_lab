"""The quality gate must fail closed, not just print a reassuring report."""

import importlib.metadata
import json
import sys
from pathlib import Path

import pytest

from tools.check import check_branch_coverage, command_plan, main, require_native_tools, run_step


def test_plan_contains_all_checks(tmp_path: Path) -> None:
    names = [name for name, _command in command_plan(tmp_path)]
    assert names == ["format", "lint", "types", "complexity", "architecture", "baseline", "tests"]


def test_missing_native_tools_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PATH", "")
    with pytest.raises(RuntimeError, match="ngspice"):
        require_native_tools()


def test_nonzero_exit_fails_and_retains_log(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="exit code 7"):
        run_step(
            "bad",
            [sys.executable, "-c", "print('failure evidence'); raise SystemExit(7)"],
            tmp_path,
            timeout=20,
        )
    assert "failure evidence" in (tmp_path / "bad.log").read_text()


def test_timeout_fails(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="timed out"):
        run_step(
            "slow", [sys.executable, "-c", "import time; time.sleep(10)"], tmp_path, timeout=0.05
        )
    assert "timed out" in (tmp_path / "slow.log").read_text()


@pytest.mark.parametrize("covered,total,passed", [(80, 100, True), (79, 100, False), (0, 0, False)])
def test_branch_floor_is_actual_branch_coverage(
    tmp_path: Path, covered: int, total: int, passed: bool
) -> None:
    report = tmp_path / "coverage.json"
    report.write_text(json.dumps({"totals": {"covered_branches": covered, "num_branches": total}}))
    if passed:
        assert check_branch_coverage(report, 80.0) == 80.0
    else:
        with pytest.raises(ValueError):
            check_branch_coverage(report, 80.0)


def test_missing_distribution_still_records_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def unavailable_plan(_out: Path) -> list[tuple[str, list[str]]]:
        raise RuntimeError("Missing ruff in this Python environment")

    def unavailable_version(_name: str) -> str:
        raise importlib.metadata.PackageNotFoundError("ruff")

    monkeypatch.setattr("tools.check.command_plan", unavailable_plan)
    monkeypatch.setattr(importlib.metadata, "version", unavailable_version)
    assert main(["--out", str(tmp_path)]) == 1
    report = json.loads((tmp_path / "CHECK_REPORT.json").read_text())
    assert report["passed"] is False
    assert "Missing ruff" in report["error"]
    assert report["versions"]["ruff"] == "not installed"
