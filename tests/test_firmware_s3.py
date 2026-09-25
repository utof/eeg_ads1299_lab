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


@pytest.mark.parametrize("fault", ["none", "cli_version", "core_version", "no_binary"])
def test_firmware_gate_checks_versions_and_fresh_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    def no_commands(_out: Path) -> list[tuple[str, list[str]]]:
        return []

    def coverage(_path: Path, _minimum: float) -> float:
        return 79.0

    def tool(_name: str) -> str:
        return "/fake/arduino-cli"

    def fake_step(name: str, command: list[str], out: Path, timeout: float = 300) -> None:
        # Explicit software-only contract fixture. This is NOT target-build evidence.
        text = "fixture"
        if name == "arduino-version":
            text = "arduino-cli Version: " + ("0.1.0" if fault == "cli_version" else "1.3.1")
        elif name == "arduino-core":
            text = "esp32:esp32 " + ("2.0.0" if fault == "core_version" else "3.3.12") + " esp32\n"
        elif name == "s3-compile":
            assert timeout == 600
            assert "compiler.cpp.extra_flags=-DEEGLAB_REV_A_S3" in command
            folder = Path(command[command.index("--output-dir") + 1])
            assert folder.is_dir() and not list(folder.iterdir())
            if fault != "no_binary":
                (folder / "fixture.bin").write_bytes(b"not an actual firmware image")
        (out / f"{name}.log").write_text(text)

    monkeypatch.setattr("tools.check.command_plan", no_commands)
    monkeypatch.setattr("tools.check.check_branch_coverage", coverage)
    monkeypatch.setattr("tools.check.run_step", fake_step)
    monkeypatch.setattr(shutil, "which", tool)
    (tmp_path / "FIRMWARE_BUILD.json").write_text('{"stale": true}')
    assert main(["--firmware", "--out", str(tmp_path)]) == (0 if fault == "none" else 1)
    marker = tmp_path / "FIRMWARE_BUILD.json"
    if fault == "none":
        report = read_object(json.loads(marker.read_text()), "firmware")
        assert report["physical_hardware_tested"] is False
        assert report["body_connection_authorized"] is False
    else:
        assert not marker.exists()
