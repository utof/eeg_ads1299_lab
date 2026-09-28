"""Launch-failure injection, not simulator or vendor-model execution evidence."""

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Literal

import pytest

from lab.analog import export_spice, run_ngspice, run_ngspice_transient
from lab.rev_a_power import run_pilot
from lab.validation import read_object


@pytest.mark.parametrize("kind", ["ac", "transient"])
@pytest.mark.parametrize("error_type", [PermissionError, FileNotFoundError, OSError])
def test_launch_error_invalidates_stale_output_and_retains_cause(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    kind: Literal["ac", "transient"],
    error_type: type[OSError],
) -> None:
    netlist = export_spice(tmp_path / "network.cir")
    filename = "ac.txt" if kind == "ac" else "transient.txt"
    output = tmp_path / filename
    output.write_text("old successful output")
    log = tmp_path / "ngspice.log"
    log.write_text("old successful log")
    window = tmp_path / "transient-window.txt"
    window.write_text("old integration window")
    fault = error_type("injected simulator launch failure")

    def available(_name: str) -> str:
        return "/fake/ngspice"

    def launch(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        assert args == ["/fake/ngspice", "-b", str(netlist)]
        assert kwargs["timeout"] == 45
        raise fault

    monkeypatch.setattr("shutil.which", available)
    monkeypatch.setattr(subprocess, "run", launch)
    with pytest.raises(RuntimeError, match="could not start") as rejected:
        if kind == "ac":
            run_ngspice(netlist, tmp_path)
        else:
            run_ngspice_transient(netlist, tmp_path, columns=1, expected_stop_s=10e-6)
    assert rejected.value.__cause__ is fault
    assert not output.exists()
    assert "injected simulator launch failure" in log.read_text()
    assert "old successful" not in log.read_text()
    if kind == "transient":
        assert not window.exists()


@pytest.mark.parametrize("include_vendor", [False, True])
def test_power_investigation_retains_all_launch_rejections(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, include_vendor: bool
) -> None:
    def available(_name: str) -> str:
        return "/fake/ngspice"

    def launch(args: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        if args[-1] == "--version":
            return subprocess.CompletedProcess(args, 0, "software fixture, not native evidence", "")
        raise PermissionError("injected post-version launch denial")

    def synthetic_library(_archive: Path, *, normalize_switch: bool) -> bytes:
        assert not normalize_switch
        return b"* synthetic fixture, never a TI library\n"

    monkeypatch.setattr("shutil.which", available)
    monkeypatch.setattr(subprocess, "run", launch)
    monkeypatch.setattr("lab.rev_a_power.prepare_library", synthetic_library)
    root = run_pilot(tmp_path, vendor_archive=Path("synthetic.zip") if include_vendor else None)
    report = read_object(json.loads((root / "pilot.json").read_text()), "pilot")
    count = 0
    for category in ("switch_probes", "vendor_probes"):
        raw = report[category]
        assert isinstance(raw, list)
        probes: list[object] = raw
        for value in probes:
            probe = read_object(value, "probe")
            assert probe["outcome"] == "rejected"
            assert probe["window_complete"] is False
            assert "could not start" in str(probe["reason"])
            if category == "switch_probes":
                assert probe["compatible_endpoint"] is None
            count += 1
    assert count == (10 if include_vendor else 6)
    logs = list(root.rglob("ngspice.log"))
    assert len(logs) == count
    assert all("injected post-version launch denial" in log.read_text() for log in logs)
    manifest = read_object(json.loads((root / "manifest.json").read_text()), "manifest")
    files = read_object(manifest["files"], "files")
    for relative, digest in files.items():
        assert hashlib.sha256((root / relative).read_bytes()).hexdigest() == digest
    assert not list(root.rglob("*.lib"))


def test_unexpected_process_programming_error_is_not_relabeled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def available(_name: str) -> str:
        return "/fake/ngspice"

    def launch(_args: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        raise TypeError("injected programming error")

    monkeypatch.setattr("shutil.which", available)
    monkeypatch.setattr(subprocess, "run", launch)
    with pytest.raises(TypeError, match="programming error"):
        run_ngspice(export_spice(tmp_path / "network.cir"), tmp_path)
