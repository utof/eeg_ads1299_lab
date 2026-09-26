"""Execute the real sketch with bounded host I/O doubles, not an emulated MCU."""

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIRMWARE = ROOT / "firmware/esp32_ads1299_bench"
STUBS = ROOT / "tests/firmware_stubs"


@pytest.mark.native
@pytest.mark.parametrize(
    ("scenario", "before", "after"),
    [
        *(
            (scenario, "", "")
            for scenario in (
                "guard",
                "no-input",
                "queued",
                "only-R",
                "early-V",
                "fresh",
                "gpio-failure",
            )
        ),
        ("guard", "if(!BOARD_PROFILE_REVIEWED)", "if(false)"),
        ("queued", "while(Serial.available()>0)Serial.read();", ""),
        ("fresh", "eeglab::startRevA(startup);", "(void)startup;"),
        ("fresh", "awaitBenchKey('V'", "awaitBenchKey('R'"),
        ("gpio-failure", ")!=ESP_OK)", ")==9999)"),
        (
            "fresh",
            "SPI.begin(PIN_SCLK,PIN_MISO,PIN_MOSI,PIN_CS);",
            "SPI.begin(PIN_SCLK,PIN_MOSI,PIN_MISO,PIN_CS);",
        ),
        (
            "fresh",
            "SPI.begin(PIN_SCLK,PIN_MISO,PIN_MOSI,PIN_CS);",
            "SPI.begin(PIN_START,PIN_MISO,PIN_MOSI,PIN_CS);",
        ),
        (
            "fresh",
            "SPI.begin(PIN_SCLK,PIN_MISO,PIN_MOSI,PIN_CS);",
            "SPI.begin(PIN_SCLK,PIN_MISO,PIN_MOSI,PIN_CLKSEL);",
        ),
    ],
    ids=[
        "guard",
        "no-input",
        "queued",
        "only-R",
        "early-V",
        "fresh",
        "gpio-failure",
        "mutant-no-review-stop",
        "mutant-stale-replies",
        "mutant-no-sequence",
        "mutant-wrong-vcap-key",
        "mutant-ignored-gpio-failure",
        "mutant-swapped-spi-data",
        "mutant-wrong-spi-clock",
        "mutant-wrong-spi-cs",
    ],
)
def test_actual_sketch_startup(tmp_path: Path, scenario: str, before: str, after: str) -> None:
    compiler = shutil.which("g++") or shutil.which("clang++")
    if compiler is None:
        pytest.skip("native C++ compiler absent")
    for path in FIRMWARE.iterdir():
        if path.suffix in {".h", ".ino"}:
            shutil.copyfile(path, tmp_path / path.name)
    # Only the disposable test copy enables the branch. No production escape hatch.
    config = tmp_path / "board_config.h"
    original = config.read_text()
    assert original.count("BOARD_PROFILE_REVIEWED = false") == 1
    if scenario != "guard":
        config.write_text(
            original.replace("BOARD_PROFILE_REVIEWED = false", "BOARD_PROFILE_REVIEWED = true")
        )
    if before:
        sketch = tmp_path / "esp32_ads1299_bench.ino"
        text = sketch.read_text()
        assert text.count(before) == 1
        sketch.write_text(text.replace(before, after))
    executable = tmp_path / "sketch-test"
    compiled = subprocess.run(
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
            str(STUBS),
            str(ROOT / "tests/native_sketch_startup_test.cpp"),
            "-o",
            str(executable),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert compiled.returncode == 0, compiled.stderr
    run = subprocess.run([str(executable), scenario], capture_output=True, text=True, timeout=5)
    assert (run.returncode == 0) is (not before), run.stdout + run.stderr
    if before:
        assert "SKETCH_ASSERTION:" in run.stderr
    assert (FIRMWARE / "board_config.h").read_text() == original
