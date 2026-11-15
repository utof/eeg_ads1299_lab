"""Breadboard ESP32-S3 build of the bench sketch: profile, helpers, actual setup.

Host doubles record software calls only. Nothing here measures the hand-wired
circuit, validates SPI timing or authorizes connecting a person. The Rev A
build and its tests are separate and unchanged.
"""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from lab.validation import read_object, text

ROOT = Path(__file__).resolve().parents[1]
FIRMWARE = ROOT / "firmware/esp32_ads1299_bench"
STUBS = ROOT / "tests/firmware_stubs"
CARD = ROOT / "docs/BREADBOARD_S3_BRINGUP.md"
GATE = "BREADBOARD_WIRING_CHECKED = false"
# Independent expectation: the review's corrected ESP32-S3 wiring (GPIO numbers)
# and Espressif's DevKitC-1 v1.1 J1 header table (GPIO -> header pin).
BREADBOARD_GPIO = {
    "SCLK": 12,
    "MISO": 13,
    "MOSI": 11,
    "CS": 10,
    "DRDY": 4,
    "RESET": 5,
    "START": 6,
    "PWDN": 7,
    "CLKSEL": 8,
}
DEVKIT_J1_PIN = {12: 18, 11: 17, 13: 19, 10: 16, 4: 4, 5: 5, 6: 6, 7: 7, 8: 12}
SCENARIOS = (
    "guard",
    "no-input",
    "queued",
    "only-R",
    "test-4",
    "short-8",
    "revision-id",
    "mode-retry",
    "six-channel",
    "bad-id",
    "readback-fault",
    "gpio-failure",
)


def _toolchain() -> dict[str, object]:
    return read_object(json.loads((ROOT / "firmware/toolchain.json").read_text()), "toolchain")


def _compiler() -> str:
    compiler = shutil.which("g++") or shutil.which("clang++")
    if compiler is None:
        pytest.skip("native C++ compiler absent")
    return compiler


def test_breadboard_profile_reuses_the_s3_pins_and_has_its_own_closed_gate() -> None:
    header = FIRMWARE / "board_config_breadboard_s3.h"
    assert header.is_file(), "breadboard compile profile is missing"
    profile = header.read_text()
    assert profile.count(GATE) == 1
    assert '#include "board_config_rev_a_s3.h"' in profile
    assert "CONFIG_IDF_TARGET_ESP32S3" in profile
    assert "c2_interlock" not in profile
    rev_a = (FIRMWARE / "board_config_rev_a_s3.h").read_text()
    pins = {n: int(v) for n, v in re.findall(r"constexpr int PIN_(\w+)\s*=\s*(\d+);", rev_a)}
    assert pins == BREADBOARD_GPIO
    config = (FIRMWARE / "board_config.h").read_text()
    assert "BOARD_PROFILE_REVIEWED = false" in config
    assert '#include "board_config_breadboard_s3.h"' in config


def test_toolchain_declares_a_separate_breadboard_compile_flag() -> None:
    config = _toolchain()
    assert text(config, "cpp_flags") == "-DEEGLAB_REV_A_S3"
    assert text(config, "breadboard_cpp_flags") == "-DEEGLAB_BREADBOARD_S3"


def test_bringup_card_wiring_and_commands_match_the_firmware() -> None:
    card = CARD.read_text()
    rows = re.findall(
        r"^\|[^|\n]*\|[^|\n]*\|\s*GPIO(\d+)\s*\|\s*J1\.(\d+)\s*\|", card, re.MULTILINE
    )
    assert {int(gpio): int(pin) for gpio, pin in rows} == DEVKIT_J1_PIN
    assert len(rows) == len(DEVKIT_J1_PIN)
    config = _toolchain()
    assert text(config, "fqbn") in card
    assert "compiler.cpp.extra_flags=" + text(config, "breadboard_cpp_flags") in card
    assert "BREADBOARD_WIRING_CHECKED" in card
    assert "BREADBOARD_FIRST_STEPS.md" in card
    for command in ("run_lab.py receive", "run_lab.py decode", "run_lab.py inspect"):
        assert command in card, command


@pytest.mark.native
@pytest.mark.parametrize(
    ("target", "flags", "error"),
    [
        ("ESP32S3", ["-DEEGLAB_BREADBOARD_S3"], ""),
        ("ESP32", ["-DEEGLAB_BREADBOARD_S3"], "EEGLAB_BREADBOARD_S3 requires"),
        ("ESP32C3", ["-DEEGLAB_BREADBOARD_S3"], "EEGLAB_BREADBOARD_S3 requires"),
        ("ESP32S3", ["-DEEGLAB_BREADBOARD_S3", "-DEEGLAB_REV_A_S3"], "one board profile"),
    ],
)
def test_breadboard_profile_target_guards(
    tmp_path: Path, target: str, flags: list[str], error: str
) -> None:
    source = tmp_path / "profile.cpp"
    source.write_text(
        '#include "board_config.h"\n'
        "static_assert(PIN_SCLK==12 && PIN_MISO==13 && PIN_MOSI==11 && PIN_CS==10);\n"
        "static_assert(PIN_DRDY==4 && PIN_RESET==5 && PIN_START==6 && PIN_PWDN==7 && PIN_CLKSEL==8);\n"
        "static_assert(!BREADBOARD_WIRING_CHECKED && !BOARD_PROFILE_REVIEWED && !USE_WIFI_UDP);\n"
        "int main() { return 0; }\n"
    )
    args = [_compiler(), "-std=c++17", "-fsyntax-only", f"-DCONFIG_IDF_TARGET_{target}=1", *flags]
    result = subprocess.run(
        [*args, "-I", str(FIRMWARE), str(source)], capture_output=True, text=True, timeout=15
    )
    assert (result.returncode == 0) is (not error), result.stdout + result.stderr
    if error:
        assert error in result.stderr, result.stderr


def _run_helper(directory: Path) -> subprocess.CompletedProcess[str]:
    exe = directory / "breadboard-modes"
    built = subprocess.run(
        [
            _compiler(),
            "-std=c++17",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-pedantic",
            "-I",
            str(directory),
            str(ROOT / "tests/native_breadboard_modes_test.cpp"),
            "-o",
            str(exe),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert built.returncode == 0, built.stderr
    return subprocess.run([str(exe)], capture_output=True, text=True, timeout=5)


@pytest.mark.native
@pytest.mark.parametrize(
    ("before", "after"),
    [
        ("", ""),
        ("== 0x1e ? 8", "== 0x1d ? 6"),
        ("key == 'T' ?", "key == 'N' ?"),
        ("test ? 0xd0 : 0xc0", "test ? 0xd0 : 0xd0"),
        ("out[n++] = {address, 0x00, 0xff};", "out[n++] = {address, 0x01, 0xff};"),
        ("raw - 'a' + 'A' : raw", "raw : raw"),
    ],
    ids=[
        "production",
        "accepts-six-channel",
        "swapped-mode-key",
        "test-signal-in-noise-mode",
        "lead-off-enabled",
        "case-sensitive-keys",
    ],
)
def test_breadboard_helper_tables(tmp_path: Path, before: str, after: str) -> None:
    header = FIRMWARE / "breadboard_modes.h"
    assert header.is_file(), "portable breadboard helper is missing"
    content = header.read_text()
    if before:
        assert content.count(before) == 1, "mutation no longer matches one operation"
        content = content.replace(before, after)
    (tmp_path / header.name).write_text(content)
    result = _run_helper(tmp_path)
    assert (result.returncode == 0) is (not before), result.stdout + result.stderr
    if before:
        assert "BREADBOARD_MODES_ASSERTION:" in result.stderr


def _sketch_copy(directory: Path, scenario: str, mutation: tuple[str, str, str]) -> None:
    for path in FIRMWARE.iterdir():
        if path.suffix in {".h", ".ino"}:
            shutil.copyfile(path, directory / path.name)
    # Only the disposable copy opens the wiring gate. No production escape hatch.
    header = directory / "board_config_breadboard_s3.h"
    original = header.read_text()
    assert original.count(GATE) == 1
    if scenario != "guard":
        header.write_text(original.replace(GATE, "BREADBOARD_WIRING_CHECKED = true"))
    filename, before, after = mutation
    if before:
        target = directory / filename
        source = target.read_text()
        assert source.count(before) == 1, "mutation no longer matches one operation"
        target.write_text(source.replace(before, after))


def _run_sketch(
    directory: Path, scenario: str, mutation: tuple[str, str, str] = ("", "", "")
) -> subprocess.CompletedProcess[str]:
    _sketch_copy(directory, scenario, mutation)
    exe = directory / "breadboard-sketch"
    built = subprocess.run(
        [
            _compiler(),
            "-std=c++17",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-pedantic",
            "-DCONFIG_IDF_TARGET_ESP32S3=1",
            "-DEEGLAB_BREADBOARD_S3",
            "-I",
            str(directory),
            "-I",
            str(STUBS),
            str(ROOT / "tests/native_breadboard_sketch_test.cpp"),
            "-o",
            str(exe),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert built.returncode == 0, built.stderr
    return subprocess.run([str(exe), scenario], capture_output=True, text=True, timeout=5)


@pytest.mark.native
@pytest.mark.parametrize("scenario", SCENARIOS)
def test_actual_breadboard_sketch(tmp_path: Path, scenario: str) -> None:
    gate = (FIRMWARE / "board_config_breadboard_s3.h").read_text()
    result = _run_sketch(tmp_path, scenario)
    assert result.returncode == 0, result.stdout + result.stderr
    assert (FIRMWARE / "board_config_breadboard_s3.h").read_text() == gate


@pytest.mark.native
@pytest.mark.parametrize(
    ("scenario", "filename", "before", "after"),
    [
        ("guard", "esp32_ads1299_bench.ino", "if(!BREADBOARD_WIRING_CHECKED)", "if(false)"),
        ("queued", "esp32_ads1299_bench.ino", "while(Serial.available()>0)Serial.read();", ""),
        (
            "test-4",
            "esp32_ads1299_bench.ino",
            "eeglab::startRevA(breadboard);",
            "(void)breadboard;",
        ),
        ("test-4", "esp32_ads1299_bench.ino", "command(0x11); // SDATAC", "// no SDATAC"),
        ("six-channel", "breadboard_modes.h", "== 0x1e ? 8", "== 0x1d ? 6"),
        ("short-8", "breadboard_modes.h", "key == 'T' ?", "key == 'N' ?"),
        (
            "test-4",
            "breadboard_modes.h",
            "out[n++] = {address, 0x00, 0xff};",
            "out[n++] = {address, 0x01, 0xff};",
        ),
        (
            "gpio-failure",
            "esp32_ads1299_bench.ino",
            'if(status!=ESP_OK)fail("GPIO',
            'if(false)fail("GPIO',
        ),
    ],
    ids=[
        "mutant-open-gate",
        "mutant-stale-replies",
        "mutant-no-startup-sequence",
        "mutant-no-sdatac",
        "mutant-six-channel",
        "mutant-swapped-mode",
        "mutant-lead-off",
        "mutant-ignored-gpio-failure",
    ],
)
def test_breadboard_sketch_mutations_fail(
    tmp_path: Path, scenario: str, filename: str, before: str, after: str
) -> None:
    result = _run_sketch(tmp_path, scenario, (filename, before, after))
    assert result.returncode != 0, result.stdout + result.stderr
    assert "BREADBOARD_ASSERTION:" in result.stderr
