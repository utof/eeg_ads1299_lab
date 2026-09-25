"""CI requires completed executions, not a favorable compatibility hypothesis."""

import json
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pytest

from lab.data_types import FloatArray
from lab.rev_a_power import main as power_main
from lab.validation import read_object
from tools.check import main as check_main


@pytest.mark.parametrize("failed", [False, True])
def test_native_gate_runs_and_requires_the_retained_power_pilot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failed: bool
) -> None:
    commands: dict[str, list[str]] = {}

    def plan(_out: Path) -> list[tuple[str, list[str]]]:
        return []

    def coverage(_path: Path, _minimum: float) -> float:
        return 79.0

    def available() -> None:
        pass

    def step(name: str, command: Sequence[str], out: Path, timeout: float = 300) -> None:
        commands[name] = list(command)
        if name == "rev-a-power" and failed:
            (out / "rev-a-power.log").write_text("injected incomplete power probe")
            raise RuntimeError("incomplete power probe; retained evidence")

    monkeypatch.setattr("tools.check.command_plan", plan)
    monkeypatch.setattr("tools.check.check_branch_coverage", coverage)
    monkeypatch.setattr("tools.check.require_native_tools", available)
    monkeypatch.setattr("tools.check.run_step", step)
    assert check_main(["--native", "--out", str(tmp_path)]) == int(failed)
    assert "rev-a-power" in commands
    command = commands["rev-a-power"]
    assert command[:3] == [sys.executable, "-m", "lab.rev_a_power"]
    assert "--require-complete-switches" in command
    assert command[command.index("--out") + 1] == str(tmp_path / "rev_a_power")
    report = read_object(json.loads((tmp_path / "CHECK_REPORT.json").read_text()), "check")
    assert report["passed"] is (not failed)
    if failed:
        assert "loopback" not in commands
        assert "native" not in str(report["completed"])


@pytest.mark.parametrize("required", [False, True])
@pytest.mark.parametrize("complete", [False, True])
def test_completion_gate_preserves_investigation_and_accepts_completed_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, required: bool, complete: bool
) -> None:
    def available(_name: str) -> str:
        return "/fake/ngspice"

    def version(args: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args, 0, "software fixture, not native evidence", "")

    def trace(
        _netlist: Path, _out: Path, *, columns: int, expected_stop_s: float
    ) -> tuple[FloatArray, FloatArray]:
        assert columns == 1 and expected_stop_s == 10e-6
        if not complete:
            raise RuntimeError("injected incomplete native integration window")
        # Deliberately mismatches every endpoint: completed incompatibility is
        # still an executed investigation, not a missing/failed simulation.
        return np.array([0.0, 10e-6]), np.array([[1.0], [1.0]])

    monkeypatch.setattr("lab.rev_a_power.shutil.which", available)
    monkeypatch.setattr("lab.rev_a_power.subprocess.run", version)
    monkeypatch.setattr("lab.rev_a_power.run_ngspice_transient", trace)
    argv = ["power-pilot", "--out", str(tmp_path)]
    if required:
        argv.append("--require-complete-switches")
    monkeypatch.setattr(sys, "argv", argv)
    assert power_main() == int(required and not complete)
    roots = list(tmp_path.iterdir())
    assert len(roots) == 1
    assert (roots[0] / "manifest.json").is_file()
    report = read_object(json.loads((roots[0] / "pilot.json").read_text()), "pilot")
    assert report["switch_execution_complete"] is complete
    assert report["hardware_validated"] is False
    probes = report["switch_probes"]
    assert isinstance(probes, list)
    values: list[object] = probes
    assert len(values) == 6
    for value in values:
        probe = read_object(value, "probe")
        assert probe["compatible_endpoint"] is (False if complete else None)
