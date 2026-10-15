"""The quality gate must fail closed, not just print a reassuring report."""

import importlib.metadata
import io
import json
import os
import select
import signal
import subprocess
import sys
from collections.abc import Sequence
from contextlib import suppress
from pathlib import Path
from typing import TextIO

import pytest

from tests.test_carrier_cad import _render
from tools.check import check_branch_coverage, command_plan, main, require_native_tools, run_step

_FIFO_WRITER = (
    "import os, sys, time\n"
    "with open(sys.argv[1], 'w') as stream:\n"
    "    print('child started', flush=True)\n"
    "    stream.write(str(os.getpid()))\n"
    "    stream.flush()\n"
    "    time.sleep(10)\n"
)


def test_plan_contains_all_checks(tmp_path: Path) -> None:
    names = [name for name, _command in command_plan(tmp_path)]
    assert names == ["format", "lint", "types", "complexity", "architecture", "baseline", "tests"]


def test_missing_native_tools_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PATH", "")
    with pytest.raises(RuntimeError, match="ngspice"):
        require_native_tools()


def test_nonzero_exit_fails_and_retains_log(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="exit code 7"):
        run_step(
            "bad",
            [sys.executable, "-c", "print('failure evidence'); raise SystemExit(7)"],
            tmp_path,
            timeout=20,
        )
    assert "failure evidence" in (tmp_path / "bad.log").read_text()


def test_timeout_fails(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="timed out"):
        run_step(
            "slow", [sys.executable, "-c", "import time; time.sleep(10)"], tmp_path, timeout=0.05
        )
    assert "timed out" in (tmp_path / "slow.log").read_text()


@pytest.mark.skipif(os.name != "posix", reason="POSIX process-group and FIFO regression")
def test_timeout_closes_descendant_processes(tmp_path: Path) -> None:
    # A live grandchild keeps the FIFO open even after its parent is killed.
    # EOF is an independent lifetime witness; no elapsed-time performance claim.
    fifo = tmp_path / "descendant"
    os.mkfifo(fifo)
    reader = os.open(fifo, os.O_RDONLY | os.O_NONBLOCK)
    parent = (
        "import subprocess, sys\n"
        "subprocess.run([sys.executable, '-c', sys.argv[1], sys.argv[2]], check=True)\n"
    )
    pid: int | None = None
    try:
        with pytest.raises(RuntimeError, match="timed out"):
            run_step(
                "descendants", [sys.executable, "-c", parent, _FIFO_WRITER, str(fifo)], tmp_path, 3
            )
        ready = os.read(reader, 64)
        assert ready, "grandchild must start before the timeout to exercise cleanup"
        pid = int(ready)
        assert select.select([reader], [], [], 2)[0], "grandchild survived the timeout"
        assert os.read(reader, 1) == b"", "grandchild still holds the pipe after timeout"
        pid = None
        assert "timed out" in (tmp_path / "descendants.log").read_text()
    finally:
        os.close(reader)
        if pid is not None:
            with suppress(ProcessLookupError):
                os.kill(pid, signal.SIGKILL)


@pytest.mark.skipif(os.name != "posix", reason="POSIX process-group and FIFO regression")
@pytest.mark.parametrize(
    "cancel_signal,expected_exit",
    [(signal.SIGINT, -signal.SIGINT), (signal.SIGTERM, 128 + signal.SIGTERM)],
)
def test_cancellation_closes_the_isolated_child(
    tmp_path: Path, cancel_signal: signal.Signals, expected_exit: int
) -> None:
    fifo = tmp_path / "cancelled-child"
    os.mkfifo(fifo)
    reader = os.open(fifo, os.O_RDONLY | os.O_NONBLOCK)
    driver = (
        "import sys\nfrom pathlib import Path\nfrom tools.check import run_step\n"
        "run_step('cancelled', [sys.executable, '-c', sys.argv[1], sys.argv[2]], "
        "Path(sys.argv[3]), timeout=30)\n"
    )
    pid: int | None = None
    with (tmp_path / "controller.log").open("w") as log:
        controller = subprocess.Popen(
            [sys.executable, "-c", driver, _FIFO_WRITER, str(fifo), str(tmp_path)],
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        try:
            assert select.select([reader], [], [], 10)[0], "child never started"
            ready = os.read(reader, 64)
            assert ready, "cancellation must happen after the child starts"
            pid = int(ready)
            os.killpg(controller.pid, cancel_signal)
            returncode = controller.wait(timeout=5)
            assert select.select([reader], [], [], 2)[0], "child survived controller cancellation"
            assert os.read(reader, 1) == b""
            pid = None
            assert returncode == expected_exit
            assert "child started" in (tmp_path / "cancelled.log").read_text()
        finally:
            os.close(reader)
            if controller.poll() is None:
                with suppress(ProcessLookupError):
                    os.killpg(controller.pid, signal.SIGKILL)
            controller.wait(timeout=5)
            if pid is not None:
                with suppress(ProcessLookupError):
                    os.killpg(pid, signal.SIGKILL)


@pytest.mark.skipif(os.name != "posix", reason="POSIX termination signal policy")
@pytest.mark.parametrize("cancel_signal", [signal.SIGINT, signal.SIGTERM])
def test_cancellation_during_process_creation_cleans_up(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, cancel_signal: signal.Signals
) -> None:
    # Inject the signal after a real fork but before Popen returns to run_step.
    # The runner must register cleanup before propagating that cancellation.
    original_popen = subprocess.Popen
    child: subprocess.Popen[str] | None = None

    def interrupted_start(
        command: Sequence[str],
        *,
        cwd: Path,
        stdout: TextIO,
        stderr: int,
        text: bool,
        start_new_session: bool,
    ) -> subprocess.Popen[str]:
        nonlocal child
        child = original_popen(
            command,
            cwd=cwd,
            stdout=stdout,
            stderr=stderr,
            text=text,
            start_new_session=start_new_session,
        )
        signal.raise_signal(cancel_signal)
        return child

    default = signal.default_int_handler if cancel_signal == signal.SIGINT else signal.SIG_DFL
    previous = signal.signal(cancel_signal, default)
    monkeypatch.setattr("tools.check.subprocess.Popen", interrupted_start)
    try:
        expected = KeyboardInterrupt if cancel_signal == signal.SIGINT else SystemExit
        with pytest.raises(expected):
            run_step(
                "startup-cancel", [sys.executable, "-c", "import time; time.sleep(10)"], tmp_path
            )
        assert child is not None
        assert child.poll() is not None, "child survived cancellation during Popen construction"
        assert signal.getsignal(cancel_signal) == default
    finally:
        signal.signal(cancel_signal, previous)
        if child is not None:
            child.kill()
            child.wait(timeout=5)


@pytest.mark.skipif(os.name != "posix", reason="POSIX termination signal policy")
@pytest.mark.parametrize("previous", [signal.SIG_DFL, signal.SIG_IGN])
def test_step_restores_termination_handler(tmp_path: Path, previous: signal.Handlers) -> None:
    original = signal.signal(signal.SIGTERM, previous)
    try:
        run_step("handler-restore", [sys.executable, "-c", "pass"], tmp_path, timeout=5)
        assert signal.getsignal(signal.SIGTERM) == previous
    finally:
        signal.signal(signal.SIGTERM, original)


@pytest.mark.parametrize("covered,total,passed", [(80, 100, True), (79, 100, False), (0, 0, False)])
def test_branch_floor_is_actual_branch_coverage(
    tmp_path: Path, covered: int, total: int, passed: bool
) -> None:
    report = tmp_path / "coverage.json"
    report.write_text(json.dumps({"totals": {"covered_branches": covered, "num_branches": total}}))
    if passed:
        assert check_branch_coverage(report, 80.0) == 80.0
    else:
        with pytest.raises(ValueError):
            check_branch_coverage(report, 80.0)


def test_missing_distribution_still_records_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def unavailable_plan(_out: Path) -> list[tuple[str, list[str]]]:
        raise RuntimeError("Missing ruff in this Python environment")

    def unavailable_version(_name: str) -> str:
        raise importlib.metadata.PackageNotFoundError("ruff")

    monkeypatch.setattr("tools.check.command_plan", unavailable_plan)
    monkeypatch.setattr(importlib.metadata, "version", unavailable_version)
    assert main(["--out", str(tmp_path)]) == 1
    report = json.loads((tmp_path / "CHECK_REPORT.json").read_text())
    assert report["passed"] is False
    assert "Missing ruff" in report["error"]
    assert report["versions"]["ruff"] == "not installed"


def test_native_gate_requires_cad_renderer(monkeypatch: pytest.MonkeyPatch) -> None:
    def lookup(name: str) -> str | None:
        return None if name == "openscad" else f"/usr/bin/{name}"

    monkeypatch.setattr("tools.check.shutil.which", lookup)
    with pytest.raises(RuntimeError, match="openscad"):
        require_native_tools()


@pytest.mark.parametrize(
    "stdout,stderr,returncode,accepted",
    [
        ("", "OpenSCAD version 2021.01\n", 0, True),
        ("OpenSCAD version 2021.01\n", "", 0, True),
        ("", "OpenSCAD version 2019.05\n", 0, False),
        ("", "OpenSCAD version 2021.01.01\n", 0, False),
        ("", "OpenSCAD version 2026.10\n", 0, False),
        ("", "OpenSCAD version 2021.01\n", 1, False),
        ("", "unrecognized version", 0, False),
        ("", "", 0, False),
        ("OpenSCAD version 2021.01\n", "WARNING: broken setup", 0, False),
    ],
)
def test_native_renderer_release_is_checked(
    monkeypatch: pytest.MonkeyPatch,
    stdout: str,
    stderr: str,
    returncode: int,
    accepted: bool,
) -> None:
    calls: list[list[str]] = []

    def lookup(name: str) -> str:
        return f"/native/{name}"

    def run(
        command: Sequence[str], *, capture_output: bool, text: bool, timeout: float, check: bool
    ) -> subprocess.CompletedProcess[str]:
        assert list(command) == ["/native/openscad", "--version"]
        assert capture_output and text and not check and 0 < timeout <= 10
        calls.append(list(command))
        return subprocess.CompletedProcess(list(command), returncode, stdout, stderr)

    monkeypatch.setattr("tools.check.shutil.which", lookup)
    monkeypatch.setattr("tools.check.subprocess.run", run)
    if accepted:
        require_native_tools()
    else:
        with pytest.raises(RuntimeError, match=r"OpenSCAD.*2021\.01"):
            require_native_tools()
    assert len(calls) == 1


@pytest.mark.parametrize("timed_out", [True, False])
def test_native_renderer_version_probe_failure_is_not_a_pass(
    monkeypatch: pytest.MonkeyPatch, timed_out: bool
) -> None:
    def lookup(name: str) -> str:
        return f"/native/{name}"

    def run(
        command: Sequence[str], *, capture_output: bool, text: bool, timeout: float, check: bool
    ) -> subprocess.CompletedProcess[str]:
        assert capture_output and text and not check and 0 < timeout <= 10
        if timed_out:
            raise subprocess.TimeoutExpired(list(command), timeout)
        raise OSError("renderer disappeared")

    monkeypatch.setattr("tools.check.shutil.which", lookup)
    monkeypatch.setattr("tools.check.subprocess.run", run)
    with pytest.raises(RuntimeError, match=r"OpenSCAD.*2021\.01"):
        require_native_tools()


@pytest.mark.parametrize("timed_out", [True, False])
def test_native_renderer_probe_preserves_failure_diagnostics(
    monkeypatch: pytest.MonkeyPatch, timed_out: bool
) -> None:
    def lookup(name: str) -> str:
        return f"/native/{name}"

    def run(
        command: Sequence[str], *, capture_output: bool, text: bool, timeout: float, check: bool
    ) -> subprocess.CompletedProcess[str]:
        assert capture_output and text and not check
        if timed_out:
            raise subprocess.TimeoutExpired(
                list(command),
                timeout,
                output=b"partial version stdout",
                stderr=b"partial version stderr",
            )
        raise OSError("specific renderer execution error")

    monkeypatch.setattr("tools.check.shutil.which", lookup)
    monkeypatch.setattr("tools.check.subprocess.run", run)
    with pytest.raises(RuntimeError) as failure:
        require_native_tools()
    detail = str(failure.value)
    if timed_out:
        assert "partial version stdout" in detail and "partial version stderr" in detail
        assert "10" in detail and "timed out" in detail
    else:
        assert "specific renderer execution error" in detail


@pytest.mark.parametrize("timed_out", [True, False])
def test_cad_renderer_retains_failure_log_without_accepting_a_mesh(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, timed_out: bool
) -> None:
    def lookup(_name: str) -> str:
        return "/native/openscad"

    def run(command: Sequence[str], **options: object) -> subprocess.CompletedProcess[str]:
        assert options.get("timeout") == 90
        # Exercise either capture-based or streaming execution with a process double.
        stream = options.get("stdout")
        if stream is not None:
            assert isinstance(stream, io.TextIOBase)
            stream.write("partial render stdout\npartial render stderr\n")
        if timed_out:
            raise subprocess.TimeoutExpired(
                list(command), 90, output=b"partial render stdout", stderr=b"partial render stderr"
            )
        raise OSError("specific CAD execution error")

    monkeypatch.setattr("tests.test_carrier_cad.shutil.which", lookup)
    monkeypatch.setattr("tests.test_carrier_cad.subprocess.run", run)
    expected = subprocess.TimeoutExpired if timed_out else OSError
    with pytest.raises(expected):
        _render(tmp_path, "cube(1);")
    log = (tmp_path / "probe-000.log").read_text()
    if timed_out:
        assert "partial render stdout" in log and "partial render stderr" in log
        assert "timed out" in log
    else:
        assert "specific CAD execution error" in log
    assert not list(tmp_path.glob("*.stl")), "A failed renderer must not yield an accepted mesh"
