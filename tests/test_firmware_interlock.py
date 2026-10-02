"""Execute actual firmware against independent, settled digital I/O doubles."""

import re
import shutil
import subprocess
from pathlib import Path

import pytest

from hardware.rev_a import parse_auxiliary_contract

ROOT = Path(__file__).resolve().parents[1]
FIRMWARE = ROOT / "firmware/esp32_ads1299_bench"
STUBS = ROOT / "tests/firmware_stubs"
SCENARIOS = (
    "good",
    "wrap",
    "no-ready",
    "stuck-ready",
    "stuck-armed",
    "no-armed",
    "arm-fault",
    "wait-fault",
    "vcap-fault",
    "reference-fault",
    "transaction-fault",
    "idle-fault",
    "recover-fault",
    "frame-fault",
    "write-fault",
)


def test_c2_pins_match_independently_reviewed_roles_and_native_contract() -> None:
    header = FIRMWARE / "c2_interlock.h"
    assert header.is_file(), "C2 firmware absent"
    pins = dict(re.findall(r"constexpr int C2_(\w+)\s*=\s*(\d+);", header.read_text()))
    assert {k: int(v) for k, v in pins.items()} == {
        "SESSION": 14,
        "ARM_REQ": 9,
        "READY": 15,
        "ARMED": 16,
    }
    contract = parse_auxiliary_contract(
        (ROOT / "hardware/rev_a/auxiliary/contract.json").read_text()
    )
    assert len(contract.parts) == 48  # C2 code must use, not silently redesign, the circuit.
    assert "BOARD_PROFILE_REVIEWED = false" in (FIRMWARE / "board_config.h").read_text()


def _compile(directory: Path, before: str = "", after: str = "") -> Path:
    compiler = shutil.which("g++") or shutil.which("clang++")
    if compiler is None:
        pytest.skip("native C++ compiler absent")
    directory.mkdir(parents=True, exist_ok=True)
    for source in FIRMWARE.iterdir():
        if source.suffix in {".h", ".ino"}:
            shutil.copyfile(source, directory / source.name)
    config = directory / "board_config.h"
    config.write_text(
        config.read_text().replace(
            "BOARD_PROFILE_REVIEWED = false", "BOARD_PROFILE_REVIEWED = true"
        )
    )
    if before:
        source = directory / "esp32_ads1299_bench.ino"
        text = source.read_text()
        assert text.count(before) == 1
        source.write_text(text.replace(before, after))
    exe = directory / "c2-session"
    built = subprocess.run(
        [
            compiler,
            "-std=c++17",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-pedantic",
            "-DCONFIG_IDF_TARGET_ESP32S3=1",
            "-DEEGLAB_REV_A_S3",
            "-I",
            str(directory),
            "-I",
            str(STUBS),
            str(ROOT / "tests/native_c2_session_test.cpp"),
            "-o",
            str(exe),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    (directory / "compile.log").write_text(built.stdout + built.stderr)
    assert built.returncode == 0, built.stderr
    return exe


@pytest.fixture(scope="module")
def session_executable(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return _compile(tmp_path_factory.mktemp("c2-actual-sketch"))


@pytest.mark.native
@pytest.mark.parametrize("scenario", SCENARIOS)
def test_actual_sketch_c2_fault_boundaries(session_executable: Path, scenario: str) -> None:
    result = subprocess.run(
        [str(session_executable), scenario], capture_output=True, text=True, timeout=5
    )
    (session_executable.parent / f"{scenario}.log").write_text(result.stdout + result.stderr)
    assert result.returncode == 0, result.stdout + result.stderr
