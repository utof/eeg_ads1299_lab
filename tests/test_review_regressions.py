"""Adversarial regressions for review issues #4 through #7."""

import copy
import json
import subprocess
import tracemalloc
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pytest

from hardware.rev_a import load_documents, validate
from lab.acquisition import capture_serial, capture_udp, decode_capture, replay_packets
from lab.adc import MAX_CODE
from lab.analog import circuit_report
from lab.data_types import Recording
from lab.inspect_capture import inspect_capture
from lab.pipeline import load_data
from lab.protocol import Packet
from lab.signals import SyntheticConfig, generate
from run_lab import main


@pytest.fixture(scope="module")
def clean_recording() -> Recording:
    return generate(SyntheticConfig(sessions=3, blocks_per_session=4))


@pytest.fixture
def recording(clean_recording: Recording) -> Recording:
    return copy.deepcopy(clean_recording)


def _archive(path: Path, data: Recording) -> Path:
    np.savez_compressed(
        path,
        codes=data["codes"],
        session=data["session"],
        block=data["block"],
        condition=data["condition"],
        time_s=data["time_s"],
        invalid=data["invalid"],
        artifact_truth=data["artifact_truth"],
        metadata_json=np.array(json.dumps(data["metadata"])),
    )
    return path


def test_recording_rejects_non_adc_counts(tmp_path: Path, recording: Recording) -> None:
    recording["codes"][0, 0] = MAX_CODE + 1
    with pytest.raises(ValueError, match="counts|24-bit"):
        load_data(_archive(tmp_path / "bad.npz", recording))


@pytest.mark.parametrize("delta", [0.0, 0.02])
def test_recording_rejects_time_discontinuity(
    tmp_path: Path, recording: Recording, delta: float
) -> None:
    recording["time_s"][100] = recording["time_s"][99] + delta
    with pytest.raises(ValueError, match="time|continu"):
        load_data(_archive(tmp_path / "bad.npz", recording))


def test_recording_rejects_mixed_block_condition(tmp_path: Path, recording: Recording) -> None:
    recording["condition"][100] ^= 1
    with pytest.raises(ValueError, match="condition|block"):
        load_data(_archive(tmp_path / "bad.npz", recording))


def test_recording_rejects_mixed_block_session(tmp_path: Path, recording: Recording) -> None:
    recording["session"][100] = 1
    with pytest.raises(ValueError, match="session|block"):
        load_data(_archive(tmp_path / "bad.npz", recording))


def test_recording_rejects_reused_block(tmp_path: Path, recording: Recording) -> None:
    recording["block"][recording["block"] == 4] = 0
    with pytest.raises(ValueError, match="block"):
        load_data(_archive(tmp_path / "bad.npz", recording))


def test_recording_rejects_inconsistent_scale(tmp_path: Path, recording: Recording) -> None:
    recording["metadata"]["adc_lsb_v"] *= 2
    with pytest.raises(ValueError, match="scale|lsb"):
        load_data(_archive(tmp_path / "bad.npz", recording))


def test_hardware_rejects_self_redefined_voltage_envelope() -> None:
    profile, bom, sources = load_documents()
    profile["power"]["external_source_nominal_v"] = 12.0
    profile["power"]["avdd_operating_max_v"] = 20.0
    assert validate(profile, bom, sources), "editable limits must not authorize a new rail"


def test_hardware_rejects_disabled_target_guard_promise() -> None:
    profile, bom, sources = load_documents()
    profile["integration"]["do_not_remove_existing_target_guard"] = False
    assert validate(profile, bom, sources)


def test_hardware_rejects_disabled_s3_port_requirement() -> None:
    profile, bom, sources = load_documents()
    profile["integration"]["requires_explicit_s3_firmware_profile"] = False
    assert validate(profile, bom, sources)


def test_hardware_loader_rejects_nonfinite_fields(tmp_path: Path) -> None:
    profile, bom, sources = load_documents()
    profile["input_network"]["nominal_dummy_common_mode_v"] = float("nan")
    for name, document in zip(
        ("board_profile.json", "bom.json", "sources.json"), (profile, bom, sources), strict=True
    ):
        (tmp_path / name).write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError, match="finite"):
        load_documents(tmp_path)


def _no_io(*_args: object, **_kwargs: object) -> None:
    raise AssertionError("Invalid input reached an I/O boundary")


@pytest.mark.parametrize("duration", [float("nan"), float("inf"), 0.0, -1.0])
def test_udp_rejects_invalid_duration_before_io(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, duration: float
) -> None:
    monkeypatch.setattr("socket.socket", _no_io)
    with pytest.raises(ValueError):
        capture_udp(tmp_path / "capture.bin", seconds=duration)
    assert not (tmp_path / "capture.bin").exists()


@pytest.mark.parametrize("duration", [float("nan"), float("inf")])
def test_serial_rejects_invalid_duration_before_io(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, duration: float
) -> None:
    monkeypatch.setattr("serial.Serial", _no_io)
    with pytest.raises(ValueError):
        capture_serial(tmp_path / "capture.bin", "unopened", seconds=duration)


@pytest.mark.parametrize("rate", [0, -250, 123])
def test_replay_rejects_invalid_rate_before_io(
    monkeypatch: pytest.MonkeyPatch, rate: int
) -> None:
    monkeypatch.setattr("socket.socket", _no_io)
    with pytest.raises(ValueError):
        replay_packets(fs_hz=rate)


def test_verify_uses_canonical_quality_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    called: list[Sequence[str] | None] = []

    def gate(argv: Sequence[str] | None = None) -> int:
        called.append(argv)
        return 27

    monkeypatch.setattr("tools.check.main", gate)
    monkeypatch.setattr("subprocess.run", _no_io)
    assert main(["verify"]) == 27
    assert len(called) == 1


def _available(name: str) -> str:
    return f"/unavailable-test-path/{name}"


def _failed_process(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(["ngspice"], 1, "", "intentional test failure")


def test_failed_circuit_run_invalidates_old_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    report = tmp_path / "circuit_report.json"
    report.write_text('{"ngspice": {"status": "executed_and_compared"}}', encoding="utf-8")
    monkeypatch.setattr("shutil.which", _available)
    monkeypatch.setattr("subprocess.run", _failed_process)
    with pytest.raises(RuntimeError, match="ngspice failed"):
        circuit_report(tmp_path, require_ngspice=True)
    assert not report.exists(), "a failed attempt must not leave an earlier success report"


def test_short_capture_removes_old_spectrum(tmp_path: Path) -> None:
    raw, csv_path, out = tmp_path / "raw.bin", tmp_path / "capture.csv", tmp_path / "quality"
    raw.write_bytes(b"".join(Packet(i, i * 4000, (i, i, i, i)).encode() for i in range(8)))
    decode_capture(raw, csv_path)
    out.mkdir()
    (out / "spectrum.csv").write_text("stale prior spectrum", encoding="utf-8")
    report = inspect_capture(csv_path, out)
    assert report["four_second_spectral_windows"] == 0
    assert not (out / "spectrum.csv").exists()


def test_decode_memory_is_bounded(tmp_path: Path) -> None:
    raw = tmp_path / "long.bin"
    with raw.open("wb") as stream:
        for i in range(20_000):
            stream.write(Packet(i, i * 4000, (i, i, i, i)).encode())
    tracemalloc.start()
    try:
        summary = decode_capture(raw, tmp_path / "long.csv")
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert summary["accepted"] == 20_000
    assert peak < 8_000_000, f"decode retained {peak:,} bytes for a 740 KB input"
