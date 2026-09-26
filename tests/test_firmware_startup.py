"""Executable startup ordering; host doubles are not target or electrical evidence."""

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIRMWARE = ROOT / "firmware/esp32_ads1299_bench"


def test_s3_setup_uses_review_guard_and_sequence_before_spi() -> None:
    sketch = (FIRMWARE / "esp32_ads1299_bench.ino").read_text()
    setup = sketch.split("void setup() {", 1)[1].split("\nvoid loop()", 1)[0]
    assert "eeglab::startRevA(startup)" in setup, "S3 does not execute the startup contract"
    assert setup.index("if(!BOARD_PROFILE_REVIEWED)") < setup.index("eeglab::startRevA(startup)")
    assert setup.index("eeglab::startRevA(startup)") < setup.index("SPI.begin(")
    assert "awaitBenchKey('R'" in sketch
    assert "awaitBenchKey('V'" in sketch
    assert "gpio_set_level" in sketch, "low latch must not rely on pre-pinMode digitalWrite"


@pytest.mark.native
@pytest.mark.parametrize(
    ("before", "after", "accepted"),
    [
        ("", "", True),
        ("io.level(PIN_CLKSEL, 1);", "", False),
        ("io.confirmVcap1();", "", False),
        ("io.waitMs(150);", "io.waitMs(1);", False),
        ("io.level(PIN_RESET, 0);", "", False),
        ("io.waitUs(4);", "io.waitUs(0);", False),
        ("io.waitUs(20);", "io.waitUs(0);", False),
        (
            "io.confirmRailsAndInputs();",
            "io.level(PIN_CLKSEL, 1); io.confirmRailsAndInputs();",
            False,
        ),
        (
            "io.level(PIN_PWDN, 1);",
            "io.waitMs(150); io.level(PIN_PWDN, 1);",
            True,
        ),
        ("io.level(PIN_PWDN, 1);", "", False),
        ("io.confirmRailsAndInputs();", "", False),
        ("io.waitMs(150);", "io.level(PIN_PWDN, 0); io.waitMs(150); io.level(PIN_PWDN, 1);", False),
        ("for (int pin : controls) io.level(pin, 0);", "", False),
    ],
    ids=[
        "production",
        "no-clock",
        "no-vcap",
        "short-por",
        "no-reset",
        "short-reset",
        "no-recovery",
        "early-clock",
        "extra-pre-wake-delay",
        "no-wake",
        "no-rails",
        "por-while-powered-down",
        "no-low-latches",
    ],
)
def test_startup_trace_and_faults(tmp_path: Path, before: str, after: str, accepted: bool) -> None:
    compiler = shutil.which("g++") or shutil.which("clang++")
    if compiler is None:
        pytest.skip("native C++ compiler absent")
    header = FIRMWARE / "rev_a_startup.h"
    assert header.is_file(), "executable Rev A startup sequence is missing"
    content = header.read_text()
    if before:
        assert content.count(before) == 1, "fault injection no longer matches one operation"
        content = content.replace(before, after)
    (tmp_path / header.name).write_text(content)
    exe = tmp_path / "startup-test"
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
            str(tmp_path),
            "-I",
            str(FIRMWARE),
            str(ROOT / "tests/native_startup_test.cpp"),
            "-o",
            str(exe),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert built.returncode == 0, built.stderr
    result = subprocess.run([str(exe)], capture_output=True, text=True, timeout=5)
    # An extra wait before wake is benign: it must not count toward the later tPOR.
    assert (result.returncode == 0) is accepted, result.stdout + result.stderr
    if not accepted:
        assert "STARTUP_ASSERTION:" in result.stderr
