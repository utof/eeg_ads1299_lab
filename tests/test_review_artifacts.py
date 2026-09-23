"""Publication failures must not corrupt raw input or masquerade as old evidence."""

import hashlib
import json
from pathlib import Path

import pytest

from lab.acquisition import decode_capture
from lab.inspect_capture import inspect_capture
from lab.protocol import Packet


def _raw(path: Path) -> Path:
    path.write_bytes(b"".join(Packet(i, i * 4000, (i, i, i, i)).encode() for i in range(8)))
    return path


def test_new_capture_pair_is_bound_by_digest(tmp_path: Path) -> None:
    csv_path = tmp_path / "capture.csv"
    result = decode_capture(_raw(tmp_path / "input.bin"), csv_path)
    assert result["csv_sha256"] == hashlib.sha256(csv_path.read_bytes()).hexdigest()
    metadata: object = json.loads(csv_path.with_suffix(".json").read_text())
    assert metadata == result


def test_inspection_rejects_mixed_generations(tmp_path: Path) -> None:
    csv_path = tmp_path / "capture.csv"
    decode_capture(_raw(tmp_path / "input.bin"), csv_path)
    with csv_path.open("a", encoding="utf-8") as stream:
        stream.write("\n")
    with pytest.raises(ValueError, match="digest mismatch"):
        inspect_capture(csv_path, tmp_path / "quality")
    assert not (tmp_path / "quality/quality_report.json").exists()


def test_failed_decode_preserves_previous_pair(tmp_path: Path) -> None:
    raw = _raw(tmp_path / "input.bin")
    csv_path = tmp_path / "capture.csv"
    decode_capture(raw, csv_path)
    csv_before = csv_path.read_bytes()
    metadata_before = csv_path.with_suffix(".json").read_bytes()
    raw.write_bytes(
        Packet(0, 0, (0, 0, 0, 0)).encode() + Packet(1, 4000, (0, 0, 0, 0), gain=12).encode()
    )
    with pytest.raises(ValueError, match="Configuration changed"):
        decode_capture(raw, csv_path)
    assert csv_path.read_bytes() == csv_before
    assert csv_path.with_suffix(".json").read_bytes() == metadata_before
    assert not list(tmp_path.glob(".decode-*"))


@pytest.mark.parametrize("output_name", ["input.bin", "input.json"])
def test_decode_never_overwrites_input(tmp_path: Path, output_name: str) -> None:
    raw = _raw(tmp_path / output_name)
    before = raw.read_bytes()
    with pytest.raises(ValueError, match="distinct paths"):
        decode_capture(raw, raw)
    assert raw.read_bytes() == before


def test_empty_decode_does_not_publish(tmp_path: Path) -> None:
    raw, output = tmp_path / "empty.bin", tmp_path / "empty.csv"
    raw.write_bytes(b"broken")
    with pytest.raises(ValueError, match="No valid"):
        decode_capture(raw, output)
    assert not output.exists()
    assert not output.with_suffix(".json").exists()
