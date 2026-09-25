"""Rejected switch runs are not completed incompatibility measurements."""

import json
import subprocess
from pathlib import Path

import numpy as np
import pytest

from lab.data_types import FloatArray
from lab.rev_a_power import run_pilot
from lab.validation import read_object


@pytest.mark.parametrize("complete", [False, True])
def test_switch_result_preserves_completion_separately_from_endpoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, complete: bool
) -> None:
    def fake_run(_path: Path, _text: str, columns: int) -> tuple[FloatArray, FloatArray]:
        assert columns == 1
        stop = 10e-6 if complete else 5e-6
        # First fixture: usual switch at 0 V. An incomplete but numerically
        # correct endpoint must not be interpreted as a completed comparison.
        voltage = 3.3 * 1100 / (1100 + 1e6)
        return np.array([0.0, stop]), np.array([[voltage], [voltage]])

    def executable(_name: str) -> str:
        return "/fake/ngspice"

    def version(args: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args, 0, "software fixture, not native evidence", "")

    monkeypatch.setattr("lab.rev_a_power._run", fake_run)
    monkeypatch.setattr("lab.rev_a_power.shutil.which", executable)
    monkeypatch.setattr("lab.rev_a_power.subprocess.run", version)
    root = run_pilot(tmp_path)
    report = read_object(json.loads((root / "pilot.json").read_text()), "report")
    probes = report["switch_probes"]
    assert isinstance(probes, list)
    probe = read_object(probes[0], "switch probe")
    assert probe["window_complete"] is complete
    assert probe["compatible_endpoint"] is (True if complete else None)
    assert probe["outcome"] == ("probe_completed_not_validated" if complete else "rejected")
