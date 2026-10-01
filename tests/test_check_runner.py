"""The quality gate must fail closed, not just print a reassuring report."""

import importlib.metadata
import json
import subprocess
import sys
from collections.abc import Sequence
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


def test_native_gate_requires_cad_renderer(monkeypatch: pytest.MonkeyPatch) -> None:
    def lookup(name: str) -> str | None:
        return None if name == "openscad" else f"/usr/bin/{name}"

    monkeypatch.setattr("tools.check.shutil.which", lookup)
    with pytest.raises(RuntimeError, match="openscad"):
        require_native_tools()


@pytest.mark.parametrize(
    "stdout,stderr,returncode,accepted",
    [
        ("", "OpenSCAD version 2021.01\n", 0, True),
        ("OpenSCAD version 2021.01\n", "", 0, True),
        ("", "OpenSCAD version 2019.05\n", 0, False),
        ("", "OpenSCAD version 2021.01.01\n", 0, False),
        ("", "OpenSCAD version 2026.10\n", 0, False),
        ("", "OpenSCAD version 2021.01\n", 1, False),
        ("", "unrecognized version", 0, False),
        ("", "", 0, False),
        ("OpenSCAD version 2021.01\n", "WARNING: broken setup", 0, False),
    ],
)
def test_native_renderer_release_is_checked(
    monkeypatch: pytest.MonkeyPatch,
    stdout: str,
    stderr: str,
    returncode: int,
    accepted: bool,
) -> None:
    calls: list[list[str]] = []

    def lookup(name: str) -> str:
        return f"/native/{name}"

    def run(
        command: Sequence[str], *, capture_output: bool, text: bool, timeout: float, check: bool
    ) -> subprocess.CompletedProcess[str]:
        assert list(command) == ["/native/openscad", "--version"]
        assert capture_output and text and not check and 0 < timeout <= 10
        calls.append(list(command))
        return subprocess.CompletedProcess(list(command), returncode, stdout, stderr)

    monkeypatch.setattr("tools.check.shutil.which", lookup)
    monkeypatch.setattr("tools.check.subprocess.run", run)
    if accepted:
        require_native_tools()
    else:
        with pytest.raises(RuntimeError, match=r"OpenSCAD.*2021\.01"):
            require_native_tools()
    assert len(calls) == 1


@pytest.mark.parametrize("timed_out", [True, False])
def test_native_renderer_version_probe_failure_is_not_a_pass(
    monkeypatch: pytest.MonkeyPatch, timed_out: bool
) -> None:
    def lookup(name: str) -> str:
        return f"/native/{name}"

    def run(
        command: Sequence[str], *, capture_output: bool, text: bool, timeout: float, check: bool
    ) -> subprocess.CompletedProcess[str]:
        assert capture_output and text and not check and 0 < timeout <= 10
        if timed_out:
            raise subprocess.TimeoutExpired(list(command), timeout)
        raise OSError("renderer disappeared")

    monkeypatch.setattr("tools.check.shutil.which", lookup)
    monkeypatch.setattr("tools.check.subprocess.run", run)
    with pytest.raises(RuntimeError, match=r"OpenSCAD.*2021\.01"):
        require_native_tools()
