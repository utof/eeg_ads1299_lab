"""Fail-closed process behavior, tested without invoking an actual simulator."""

import shutil
import subprocess
from pathlib import Path

import pytest

from lab.analog import run_ngspice


def test_spice_never_accepts_stale_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def find_tool(command: str) -> str:
        return "/fake/ngspice"

    def no_output(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(shutil, "which", find_tool)
    monkeypatch.setattr(subprocess, "run", no_output)
    (tmp_path / "ac.txt").write_text("frequency real imag\n1 1 0\n2 1 0\n")
    netlist = tmp_path / "input.cir"
    netlist.write_text("not used by this process stub\n")
    with pytest.raises(RuntimeError, match="ngspice failed"):
        run_ngspice(netlist, tmp_path)


def test_spice_timeout_preserves_log(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def find_tool(command: str) -> str:
        return "/fake/ngspice"

    def timeout(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(args, 45, output=b"partial simulator output")

    monkeypatch.setattr(shutil, "which", find_tool)
    monkeypatch.setattr(subprocess, "run", timeout)
    with pytest.raises(RuntimeError, match="timed out"):
        run_ngspice(tmp_path / "input.cir", tmp_path)
    assert "partial simulator output" in (tmp_path / "ngspice.log").read_text()
