"""The same bounded simulator process owns both AC and transient execution."""

import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from lab.analog import run_ngspice_transient


def _process(
    monkeypatch: pytest.MonkeyPatch, root: Path, text: str | None, returncode: int = 0
) -> None:
    def tool(_name: str) -> str:
        return "/fake/ngspice"

    def run(args: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        if text is not None:
            (root / "transient.txt").write_text(text)
        return subprocess.CompletedProcess(args, returncode, "test fixture, not simulation", "")

    monkeypatch.setattr(shutil, "which", tool)
    monkeypatch.setattr(subprocess, "run", run)


def test_transient_reader_keeps_time_and_real_columns(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _process(monkeypatch, tmp_path, "time v1 v2\n0 1 2\n0.1 3 4\n")
    time, values = run_ngspice_transient(tmp_path / "model.cir", tmp_path, columns=2)
    np.testing.assert_array_equal(time, [0.0, 0.1])
    np.testing.assert_array_equal(values, [[1, 2], [3, 4]])


@pytest.mark.parametrize(
    "text",
    [
        "time v\n0 1\n0.1 2\n",  # wrong column count
        "time v1 v2\n0 1 2\n0 3 4\n",  # repeated time
        "time v1 v2\n0.1 1 2\n0 3 4\n",  # backwards time
        "time v1 v2\n-1 1 2\n0 3 4\n",
        "time v1 v2\n0 nan 2\n1 3 4\n",
        "time v1 v2\n0 1 2\n1 3 inf\n",
        "time v1 v2\n0 1 2\n",  # cannot establish a trajectory
        "time v1 v2\n",  # header only
        "time v1 v2\nnot numeric\n",
    ],
)
def test_transient_rejects_invalid_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, text: str
) -> None:
    _process(monkeypatch, tmp_path, text)
    with pytest.raises(RuntimeError, match="transient"):
        run_ngspice_transient(tmp_path / "model.cir", tmp_path, columns=2)


def test_transient_never_accepts_stale_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    old = "time v\n0 0\n1 1\n"
    (tmp_path / "transient.txt").write_text(old)
    _process(monkeypatch, tmp_path, None)
    with pytest.raises(RuntimeError, match="ngspice failed"):
        run_ngspice_transient(tmp_path / "model.cir", tmp_path, columns=1)
    assert not (tmp_path / "transient.txt").exists()


def test_transient_nonzero_exit_cannot_publish_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _process(monkeypatch, tmp_path, "time v\n0 0\n1 1\n", returncode=1)
    with pytest.raises(RuntimeError, match="ngspice failed"):
        run_ngspice_transient(tmp_path / "model.cir", tmp_path, columns=1)


def test_transient_timeout_preserves_partial_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _process(monkeypatch, tmp_path, None)

    def timeout(args: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(args, 45, output=b"transient partial", stderr=b"deadline")

    monkeypatch.setattr(subprocess, "run", timeout)
    with pytest.raises(RuntimeError, match="timed out"):
        run_ngspice_transient(tmp_path / "model.cir", tmp_path, columns=1)
    assert "transient partial" in (tmp_path / "ngspice.log").read_text()
    assert "deadline" in (tmp_path / "ngspice.log").read_text()


@pytest.mark.parametrize("columns", [True, 0, -1])
def test_transient_rejects_invalid_column_contract(tmp_path: Path, columns: int) -> None:
    with pytest.raises(ValueError, match="columns"):
        run_ngspice_transient(tmp_path / "model.cir", tmp_path, columns=columns)
    assert not list(tmp_path.iterdir())


@pytest.mark.native
def test_native_transient_rc_matches_independent_exponential(tmp_path: Path) -> None:
    path = tmp_path / "rc.cir"
    path.write_text(
        "RC reference, no hardware connection\n"
        "Istep 0 out 1m\nRout out 0 1k\nCout out 0 1u IC=0\n"
        ".options reltol=1e-7 vntol=1e-10 abstol=1e-14 method=gear\n"
        ".control\nset wr_singlescale\nset wr_vecnames\nset numdgt=15\n"
        "tran 1u 5m 0 1u uic\nwrdata transient.txt v(out)\nquit\n.endc\n.end\n"
    )
    time, values = run_ngspice_transient(path, tmp_path, columns=1)
    expected = 1 - np.exp(-time / 0.001)
    np.testing.assert_allclose(values[:, 0], expected, rtol=2e-5, atol=1e-7)
