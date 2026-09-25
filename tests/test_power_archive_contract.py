"""Synthetic archives exercise the adapter contract, never vendor-model behavior."""

import hashlib
import io
import json
import subprocess
import zipfile
from pathlib import Path

import numpy as np
import pytest

from lab.data_types import FloatArray
from lab.rev_a_power import prepare_library, run_pilot
from lab.validation import read_object

_ORIGINAL = b"Synthetic fixture only\n.MODEL _S2 VSWITCH Roff=1e-6 Ron=1E6 Voff=0 Von=1m\n"
_ADAPTED = b"Synthetic fixture only\n.MODEL _S2 VSWITCH Roff=1E6 Ron=1e-6 Voff=1m Von=0\n"


def _archive(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, library: bytes) -> Path:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("tps7a20-adj_trans.lib", library)
    raw = buffer.getvalue()
    path = tmp_path / "synthetic.zip"
    path.write_bytes(raw)
    monkeypatch.setattr("lab.rev_a_power.ARCHIVE_SHA256", hashlib.sha256(raw).hexdigest())
    monkeypatch.setattr("lab.rev_a_power.LIBRARY_SHA256", hashlib.sha256(library).hexdigest())
    return path


@pytest.mark.parametrize("normalize", [False, True])
def test_private_edit_is_explicit_exact_and_does_not_modify_archive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, normalize: bool
) -> None:
    path = _archive(tmp_path, monkeypatch, _ORIGINAL)
    raw = path.read_bytes()
    result = prepare_library(path, normalize_switch=normalize)
    assert result == (_ADAPTED if normalize else _ORIGINAL)
    assert path.read_bytes() == raw


@pytest.mark.parametrize("library", [b"no matching declaration", _ORIGINAL * 2])
def test_private_edit_requires_exactly_one_match(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, library: bytes
) -> None:
    path = _archive(tmp_path, monkeypatch, library)
    with pytest.raises(ValueError, match="exactly one"):
        prepare_library(path, normalize_switch=True)


def test_uncompressed_library_hash_is_checked_independently(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _archive(tmp_path, monkeypatch, _ORIGINAL)
    monkeypatch.setattr("lab.rev_a_power.LIBRARY_SHA256", "0" * 64)
    with pytest.raises(ValueError, match="library SHA-256"):
        prepare_library(path, normalize_switch=False)


def test_oversized_regular_archive_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "oversize.zip"
    path.write_bytes(b"x" * 4_000_001)
    with pytest.raises(ValueError, match="archive size"):
        prepare_library(path, normalize_switch=False)


def test_complete_wrong_plateau_is_distinct_from_incomplete_integration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def executable(_name: str) -> str:
        return "/fake/ngspice"

    def version(args: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args, 0, "software fixture, not native evidence", "")

    def trace(
        _netlist: Path, _out: Path, *, columns: int, expected_stop_s: float | None = None
    ) -> tuple[FloatArray, FloatArray]:
        stop = 0.02 if columns == 2 else 10e-6
        return np.linspace(0.0, stop, 201), np.zeros((201, columns))

    archive = _archive(tmp_path, monkeypatch, _ORIGINAL)
    monkeypatch.setattr("lab.rev_a_power.shutil.which", executable)
    monkeypatch.setattr("lab.rev_a_power.subprocess.run", version)
    monkeypatch.setattr("lab.rev_a_power.run_ngspice_transient", trace)
    root = run_pilot(tmp_path / "reports", vendor_archive=archive)
    report = read_object(json.loads((root / "pilot.json").read_text()), "pilot")
    raw = report["vendor_probes"]
    assert isinstance(raw, list)
    values: list[object] = raw
    startup = read_object(values[0], "startup")
    assert startup["window_complete"] is True
    assert startup["outcome"] == "rejected"
    assert "plateau" in str(startup["reason"])
    assert report["hardware_validated"] is False
    assert not list(root.rglob("*.lib"))
