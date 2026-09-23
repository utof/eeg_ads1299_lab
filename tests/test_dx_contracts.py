"""Executable checks for the development workflow itself."""

import subprocess
import sys
from pathlib import Path

import pytest

from run_lab import main

ROOT = Path(__file__).resolve().parents[1]


def test_default_discovery_includes_hardware_contract() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    names = [
        line
        for line in result.stdout.splitlines()
        if line.startswith("hardware/rev_a/test_baseline.py::BaselineTests::test_")
    ]
    assert len(names) >= 23, result.stdout


def test_installed_package_imports_outside_checkout(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from lab.analog import InputNetwork, transfer; "
            "assert transfer([0.0], InputNetwork()).shape == (1,)",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_cli_circuits_uses_explicit_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PATH", "")
    assert main(["circuits", "--out", str(tmp_path)]) == 0
    assert (tmp_path / "circuit_report.json").exists()


def test_cli_errors_cleanly(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["decode", str(tmp_path / "missing.bin"), "--out", str(tmp_path / "out.csv")]) == 2
    assert "ERROR:" in capsys.readouterr().err


@pytest.mark.parametrize(
    "name,extra", [("requirements.txt", []), ("requirements-serial.txt", ["--extra", "serial"])]
)
def test_requirements_are_generated_from_lock(name: str, extra: list[str]) -> None:
    result = subprocess.run(
        [
            "uv",
            "export",
            "--locked",
            "--offline",
            "--no-dev",
            "--no-emit-project",
            "--no-hashes",
            "--no-header",
            "--no-annotate",
            *extra,
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    actual = "\n".join(
        line for line in (ROOT / name).read_text().splitlines() if not line.startswith("#")
    )
    assert actual.strip() == result.stdout.strip()
