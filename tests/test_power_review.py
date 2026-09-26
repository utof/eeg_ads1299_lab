"""Public pilot regressions from review; mocked process results are not native evidence."""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Literal

import numpy as np
import pytest

from lab.data_types import FloatArray
from lab.rev_a_power import main, prepare_library, run_pilot, switch_netlist
from lab.validation import read_object


def _available(_name: str) -> str:
    return "/fake/ngspice"


def _probe_results(root: Path) -> list[dict[str, object]]:
    report = read_object(json.loads((root / "pilot.json").read_text()), "pilot")
    probes = report["switch_probes"]
    assert isinstance(probes, list)
    values: list[object] = probes
    return [read_object(probe, "switch") for probe in values]


@pytest.mark.parametrize("fault", ["early_stop", "process_failure"])
def test_incomplete_switch_is_rejected_not_an_incompatibility(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    def version(args: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args, 0, "ngspice test fixture", "")

    def trace(
        _netlist: Path,
        _out: Path,
        *,
        columns: int,
        expected_stop_s: float | None = None,
        expected_vectors: tuple[str, ...] | None = None,
    ) -> tuple[FloatArray, FloatArray]:
        assert columns == 1
        assert expected_vectors == ("v(out)",)
        if fault == "process_failure":
            raise RuntimeError("injected native execution failure")
        return np.array([0.0, 5e-6]), np.array([[0.003626], [0.003626]])

    monkeypatch.setattr("lab.rev_a_power.shutil.which", _available)
    monkeypatch.setattr("lab.rev_a_power.subprocess.run", version)
    monkeypatch.setattr("lab.rev_a_power.run_ngspice_transient", trace)
    root = run_pilot(tmp_path)
    probes = _probe_results(root)
    assert len(probes) == 6
    for probe in probes:
        assert probe["outcome"] == "rejected"
        assert probe["window_complete"] is False
        assert probe["compatible_endpoint"] is None
        assert isinstance(probe["reason"], str)
    assert not list(root.rglob(".spiceinit"))


@pytest.mark.skipif(os.name != "posix", reason="POSIX special-file input boundary")
def test_nonregular_archive_is_rejected_before_reading() -> None:
    with pytest.raises(ValueError, match="regular file"):
        prepare_library(Path("/dev/null"), normalize_switch=False)


@pytest.mark.skipif(os.name != "posix", reason="POSIX FIFO input boundary")
def test_archive_fifo_does_not_block_before_rejection(tmp_path: Path) -> None:
    fifo = tmp_path / "archive.fifo"
    os.mkfifo(fifo)
    program = (
        "from pathlib import Path\n"
        "from lab.rev_a_power import prepare_library\n"
        f"prepare_library(Path({str(fifo)!r}), normalize_switch=False)\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", program], text=True, capture_output=True, timeout=3, check=False
    )
    assert result.returncode != 0
    assert "regular file" in result.stderr


def test_archive_growth_after_open_stays_bounded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = tmp_path / "growing.zip"
    archive.write_bytes(b"small")
    original = os.fstat
    calls = 0

    def grow(descriptor: int) -> os.stat_result:
        nonlocal calls
        result = original(descriptor)
        calls += 1
        archive.write_bytes(b"x" * 4_000_001)
        return result

    monkeypatch.setattr(os, "fstat", grow)
    with pytest.raises(ValueError, match="archive size"):
        prepare_library(archive, normalize_switch=False)
    assert calls == 1


@pytest.mark.parametrize("failure", ["exit", "timeout", "launch", "empty"])
def test_version_failures_keep_diagnostics_without_a_completion_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    def broken(args: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        if failure == "timeout":
            raise subprocess.TimeoutExpired(
                args, 5, output=b"partial version", stderr=b"timeout detail"
            )
        if failure == "launch":
            raise OSError("version executable disappeared")
        if failure == "empty":
            return subprocess.CompletedProcess(args, 0, "", "empty version detail")
        if _kwargs.get("check"):
            raise subprocess.CalledProcessError(
                9, args, output="partial version", stderr="nonzero version detail"
            )
        return subprocess.CompletedProcess(args, 9, "partial version", "nonzero version detail")

    monkeypatch.setattr("lab.rev_a_power.shutil.which", _available)
    monkeypatch.setattr("lab.rev_a_power.subprocess.run", broken)
    monkeypatch.setattr(sys, "argv", ["power-pilot", "--out", str(tmp_path)])
    assert main() == 1
    roots = list(tmp_path.iterdir())
    assert len(roots) == 1
    text = (roots[0] / "ngspice-version.log").read_text()
    assert "detail" in text or "disappeared" in text
    if failure in ("timeout", "exit"):
        assert "partial version" in text
    assert not (roots[0] / "pilot.json").exists()
    assert not (roots[0] / "manifest.json").exists()


@pytest.mark.native
def test_padded_switch_export_cannot_hide_early_raw_stop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def truncated(variant: Literal["usual", "inverse", "normalized"], control_v: float) -> str:
        assert variant in ("usual", "inverse", "normalized")
        original = switch_netlist(variant, control_v)
        # The returned table still ends at 10 us, but native integration stops at 5 us.
        return original.replace("tran 1u 10u", "tran 1u 5u").replace(
            "wrdata transient.txt",
            "let lin-tstart = 0\nlet lin-tstop = 10u\nlet lin-tstep = 1u\n"
            "linearize v(out)\nwrdata transient.txt",
        )

    monkeypatch.setattr("lab.rev_a_power.switch_netlist", truncated)
    root = run_pilot(tmp_path)
    for probe in _probe_results(root):
        assert probe["outcome"] == "rejected"
        assert probe["window_complete"] is False
        assert probe["compatible_endpoint"] is None
        assert "window" in str(probe["reason"])
