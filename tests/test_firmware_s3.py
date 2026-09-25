"""Profile consistency and compiler guards; none of these authorizes GPIO use."""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from hardware.rev_a import load_documents, validate
from lab.validation import read_object
from tools.check import main

ROOT = Path(__file__).resolve().parents[1]
FIRMWARE = ROOT / "firmware/esp32_ads1299_bench"


def test_explicit_s3_header_matches_selected_pin_map() -> None:
    profile, bom, sources = load_documents()
    assert validate(profile, bom, sources) == []
    header = FIRMWARE / "board_config_rev_a_s3.h"
    assert header.is_file(), "selected S3 compile profile is missing"
    pins = dict(re.findall(r"constexpr int PIN_(\w+)\s*=\s*(\d+);", header.read_text()))
    assert {name: int(value) for name, value in pins.items()} == {
        row["signal"]: row["gpio"] for row in profile["spi"]["signals"]
    }
    assert "EXPECTED_ADS_CHANNELS = 4" in header.read_text()
    config = (FIRMWARE / "board_config.h").read_text()
    assert "BOARD_PROFILE_REVIEWED = false" in config
    assert "USE_WIFI_UDP=false" in config
    sketch = (FIRMWARE / "esp32_ads1299_bench.ino").read_text()
    assert sketch.index("if(!BOARD_PROFILE_REVIEWED)") < sketch.index("pinMode(")


def test_requested_firmware_gate_rejects_missing_tool(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def no_commands(_out: Path) -> list[tuple[str, list[str]]]:
        return []

    def coverage(_path: Path, _minimum: float) -> float:
        return 79.0

    def missing(_name: str) -> None:
        return None

    monkeypatch.setattr("tools.check.command_plan", no_commands)
    monkeypatch.setattr("tools.check.check_branch_coverage", coverage)
    monkeypatch.setattr(shutil, "which", missing)
    assert main(["--firmware", "--out", str(tmp_path)]) == 1
    report = read_object(json.loads((tmp_path / "CHECK_REPORT.json").read_text()), "report")
    assert report["firmware_requested"] is True
    assert report["passed"] is False
    assert "arduino-cli" in str(report["error"])


@pytest.mark.native
@pytest.mark.parametrize(
    ("target", "explicit_s3", "accepted"),
    [
        ("ESP32", False, True),
        ("ESP32S3", True, True),
        ("ESP32S3", False, False),
        ("ESP32", True, False),
        ("ESP32C3", False, False),
        ("ESP32C3", True, False),
    ],
)
def test_compile_profile_target_guards(
    tmp_path: Path, target: str, explicit_s3: bool, accepted: bool
) -> None:
    compiler = shutil.which("g++") or shutil.which("clang++")
    if compiler is None:
        pytest.skip("native C++ compiler absent")
    sclk, miso, mosi, cs = (12, 13, 11, 10) if explicit_s3 else (18, 19, 23, 27)
    source = tmp_path / "profile.cpp"
    source.write_text(
        '#include "board_config.h"\n'
        f"static_assert(PIN_SCLK=={sclk} && PIN_MISO=={miso} && PIN_MOSI=={mosi} && PIN_CS=={cs});\n"
        "static_assert(!BOARD_PROFILE_REVIEWED && !USE_WIFI_UDP && USE_INTERNAL_TEST);\n"
        "int main() { return 0; }\n"
    )
    args = [compiler, "-std=c++17", "-fsyntax-only", f"-DCONFIG_IDF_TARGET_{target}=1"]
    if explicit_s3:
        args.append("-DEEGLAB_REV_A_S3")
    result = subprocess.run(
        [*args, "-I", str(FIRMWARE), str(source)], capture_output=True, text=True, timeout=15
    )
    assert (result.returncode == 0) is accepted, result.stdout + result.stderr
    if not accepted:
        assert "error:" in result.stderr
