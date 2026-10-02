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
    "ready-glitch",
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
    tails = contract.parts["MCU_TAILS"].pins
    assert {k: tails[k].net for k in ("20", "15", "8", "9")} == {
        "20": "SESSION",
        "15": "ARM_REQ",
        "8": "CLR_N",
        "9": "BUS_OE",
    }
    assert contract.parts["ARM_FF"].pins["5"].net == "BUS_OE"
    assert contract.parts["CLEAR_AND"].pins["4"].net == "CLR_N"
    assert "BOARD_PROFILE_REVIEWED = false" in (FIRMWARE / "board_config.h").read_text()


def _compile(
    directory: Path, before: str = "", after: str = "", filename: str = "esp32_ads1299_bench.ino"
) -> Path:
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
        source = directory / filename
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


@pytest.mark.native
@pytest.mark.parametrize(
    "scenario,filename,before,after",
    [
        ("good", "c2_interlock.h", "io.level(C2_SESSION,1);", "io.level(C2_SESSION,0);"),
        ("good", "c2_interlock.h", "io.level(C2_ARM_REQ,1);", "io.level(C2_ARM_REQ,0);"),
        ("ready-glitch", "c2_interlock.h", "} else high=false;", "}"),
        ("good", "c2_interlock.h", "observed-highSince)>=10", "observed-highSince)>=1"),
        ("good", "c2_interlock.h", "io.nowUs()-pulse)<10", "io.nowUs()-pulse)<1"),
        ("recover-fault", "c2_interlock.h", "&& io.read(C2_ARMED)", ""),
        (
            "wait-fault",
            "esp32_ads1299_bench.ino",
            "void waitMs(unsigned value) { waitBenchMs(value); }",
            "void waitMs(unsigned value) { delay(value); }",
        ),
        (
            "frame-fault",
            "esp32_ads1299_bench.ino",
            "frame[i]=busTransfer(0)",
            "frame[i]=SPI.transfer(0)",
        ),
        (
            "write-fault",
            "esp32_ads1299_bench.ino",
            "    }\n    requireBus();lastGoodMs=millis();\n}",
            "    }\n    lastGoodMs=millis();\n}",
        ),
        (
            "idle-fault",
            "esp32_ads1299_bench.ino",
            "if(spiOpened){SPI.end();spiOpened=false;}",
            "spiOpened=false;",
        ),
        (
            "frame-fault",
            "esp32_ads1299_bench.ino",
            "channels=0;consumed=0;overruns=0;lastGoodMs=0;",
            "",
        ),
    ],
)
def test_guard_fault_mutations_are_executable_failures(
    tmp_path: Path, scenario: str, filename: str, before: str, after: str
) -> None:
    exe = _compile(tmp_path, before, after, filename)
    result = subprocess.run([str(exe), scenario], capture_output=True, text=True, timeout=5)
    (tmp_path / "fault.log").write_text(result.stdout + result.stderr)
    assert result.returncode != 0 and "C2_ASSERTION:" in result.stderr, (
        result.stdout + result.stderr
    )
