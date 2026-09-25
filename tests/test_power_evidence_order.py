"""Orchestration failure injection, not native simulation evidence."""

import json
from collections.abc import Sequence
from pathlib import Path

import pytest

from lab.validation import read_object
from tools.check import main


@pytest.mark.parametrize("failure", ["native-tests", "rev-a-power"])
def test_retained_power_probe_cannot_be_preempted_by_native_tests(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    commands: list[str] = []
    retained = tmp_path / "rev_a_power" / "injected-evidence.txt"

    def plan(_out: Path) -> list[tuple[str, list[str]]]:
        return []

    def coverage(_path: Path, _minimum: float) -> float:
        return 79.0

    def available() -> None:
        pass

    def step(name: str, _command: Sequence[str], _out: Path, timeout: float = 300) -> None:
        commands.append(name)
        if name == "rev-a-power":
            retained.parent.mkdir()
            retained.write_text("orchestration fixture, not native evidence")
        if name == failure:
            raise RuntimeError(f"injected {name} failure")

    monkeypatch.setattr("tools.check.command_plan", plan)
    monkeypatch.setattr("tools.check.check_branch_coverage", coverage)
    monkeypatch.setattr("tools.check.require_native_tools", available)
    monkeypatch.setattr("tools.check.run_step", step)
    assert main(["--native", "--out", str(tmp_path)]) == 1
    assert commands[0] == "rev-a-power"
    assert retained.is_file()
    assert "loopback" not in commands
    if failure == "rev-a-power":
        assert "native-tests" not in commands
    report = read_object(json.loads((tmp_path / "CHECK_REPORT.json").read_text()), "check")
    assert report["passed"] is False
    assert f"injected {failure} failure" in str(report["error"])
