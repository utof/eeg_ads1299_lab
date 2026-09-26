"""Bench interface evidence: software contracts are not inspected physical wiring."""

import shutil
import subprocess
from pathlib import Path

import pytest

import hardware.rev_a as rev_a

ROOT = Path(__file__).resolve().parents[1]
FIRMWARE = ROOT / "firmware/esp32_ads1299_bench"


def test_physical_harness_boundary_exists() -> None:
    assert callable(getattr(rev_a, "bench_harness", None)), "missing physical harness derivation"


@pytest.mark.native
@pytest.mark.parametrize("cdc", [0, 1])
def test_s3_console_cannot_silently_become_usb(tmp_path: Path, cdc: int) -> None:
    compiler = shutil.which("g++") or shutil.which("clang++")
    assert compiler is not None, "native compiler required"
    source = tmp_path / "console.cpp"
    source.write_text('#include "board_config.h"\nint main() { return 0; }\n')
    result = subprocess.run(
        [
            compiler,
            "-std=c++17",
            "-fsyntax-only",
            "-DEEGLAB_REV_A_S3",
            "-DCONFIG_IDF_TARGET_ESP32S3=1",
            f"-DARDUINO_USB_CDC_ON_BOOT={cdc}",
            "-I",
            str(FIRMWARE),
            str(source),
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert (result.returncode == 0) is (cdc == 0), result.stderr
    if cdc:
        assert "console requires UART0" in result.stderr
