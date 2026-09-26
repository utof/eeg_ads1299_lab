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


# Frozen native graph is an ordinary-test fixture, never a fresh KiCad run.
def _harness() -> tuple[rev_a.HarnessNet, ...]:
    import gzip

    profile, bom, sources = rev_a.load_documents()
    netlist = rev_a.parse_schematic_xml(
        gzip.decompress((ROOT / "tests/fixtures/rev_a_netlist.xml.gz").read_bytes()).decode()
    )
    return rev_a.bench_harness(
        netlist, profile, bom, sources, (FIRMWARE / "bench_console.h").read_text()
    )


def test_manufacturer_header_numbers_not_gpio_numbers() -> None:
    groups = {group.name: group.endpoints for group in _harness()}
    # Independent V1.1 J1 table / schematic p2 expected pads. Not calculated
    # from the firmware or from the derivation's own manufacturer lookup table.
    expected = {
        "SCLK / GPIO12": ("DEVKIT.J1.18", "AFE.J1.1"),
        "MOSI / GPIO11": ("DEVKIT.J1.17", "AFE.J1.3"),
        "MISO / GPIO13": ("AFE.J1.5", "DEVKIT.J1.19"),
        "CS / GPIO10": ("DEVKIT.J1.16", "AFE.J1.7"),
        "DRDY / GPIO4": ("AFE.J1.9", "DEVKIT.J1.4"),
        "RESET / GPIO5": ("DEVKIT.J1.5", "AFE.J1.11"),
        "START / GPIO6": ("DEVKIT.J1.6", "AFE.J1.13"),
        "PWDN / GPIO7": ("DEVKIT.J1.7", "AFE.J1.15"),
        "CLKSEL / GPIO8": ("DEVKIT.J1.12", "AFE.J1.19"),
        "Console receive / GPIO17": ("INTERFACE.TX_3V3", "DEVKIT.J1.10"),
        "Console transmit / GPIO18": ("DEVKIT.J1.11", "INTERFACE.RX_3V3"),
        "External regulated 5 V": ("SUPPLY.+5V", "AFE.J1.17", "DEVKIT.J1.21"),
        "Common return": (
            "SUPPLY.RETURN",
            "DEVKIT.J1.22",
            "INTERFACE.GND",
            *(f"AFE.J1.{pin}" for pin in range(2, 21, 2)),
        ),
    }
    assert groups == expected


def test_every_digital_connector_contact_accounted_for_once() -> None:
    ends = [point for group in _harness() for point in group.endpoints]
    assert len(ends) == len(set(ends)) == 38
    assert {p for p in ends if p.startswith("AFE.")} == {f"AFE.J1.{p}" for p in range(1, 21)}
    # No adapter power, auto-reset, boot pin or onboard-bridge UART path.
    assert {p for p in ends if p.startswith("INTERFACE.")} == {
        "INTERFACE.TX_3V3",
        "INTERFACE.RX_3V3",
        "INTERFACE.GND",
    }
    assert not {"DEVKIT.J1.1", "DEVKIT.J1.2", "DEVKIT.J1.3", "DEVKIT.J3.2", "DEVKIT.J3.3"} & set(
        ends
    )


@pytest.mark.parametrize("fault", ["v1.0", "mcu", "gpio", "power", "header", "graph"])
def test_harness_will_not_derive_from_unreviewed_or_inconsistent_sources(fault: str) -> None:
    import gzip

    profile, bom, sources = rev_a.load_documents()
    netlist = rev_a.parse_schematic_xml(
        gzip.decompress((ROOT / "tests/fixtures/rev_a_netlist.xml.gz").read_bytes()).decode()
    )
    if fault == "v1.0":
        profile["mcu"]["preferred_pcb_revision"] = "v1.0"
    elif fault == "mcu":
        profile["mcu"]["board_mpn"] = "CLONE"
    elif fault == "gpio":
        profile["spi"]["signals"][0]["gpio"] = 17
    elif fault == "power":
        profile["power"]["devkit_usb_and_5v_header_simultaneous"] = True
    elif fault == "header":
        profile["interface_headers"]["J_DIG"]["pin_map"]["1"] = "PWDN"
    else:
        del netlist.nets["U1", "40"]
    with pytest.raises(ValueError):
        rev_a.bench_harness(
            netlist, profile, bom, sources, (FIRMWARE / "bench_console.h").read_text()
        )


@pytest.mark.parametrize(
    ("before", "after"),
    [
        ("CONSOLE_RX = 17", "CONSOLE_RX = 44"),
        ("CONSOLE_TX = 18", "CONSOLE_TX = 43"),
        ("CONSOLE_RX = 17", "CONSOLE_RX = 18"),
        ("CONSOLE_BAUD = 460800", "CONSOLE_BAUD = 115200"),
        ("constexpr int CONSOLE_TX = 18;", ""),
        ("constexpr int CONSOLE_RX = 17;", "constexpr int CONSOLE_RX = 17;" * 2),
    ],
)
def test_firmware_console_declaration_drift_is_not_silently_published(
    before: str, after: str
) -> None:
    import gzip

    profile, bom, sources = rev_a.load_documents()
    netlist = rev_a.parse_schematic_xml(
        gzip.decompress((ROOT / "tests/fixtures/rev_a_netlist.xml.gz").read_bytes()).decode()
    )
    header = (FIRMWARE / "bench_console.h").read_text()
    assert before in header
    with pytest.raises(ValueError, match="console"):
        rev_a.bench_harness(netlist, profile, bom, sources, header.replace(before, after))


def test_native_reference_name_is_derived_not_another_header_registry() -> None:
    import gzip
    from dataclasses import replace

    profile, bom, sources = rev_a.load_documents()
    netlist = rev_a.parse_schematic_xml(
        gzip.decompress((ROOT / "tests/fixtures/rev_a_netlist.xml.gz").read_bytes()).decode()
    )
    netlist.parts["J_DIG"] = replace(netlist.parts["J_DIG"], native_ref="J9")
    groups = rev_a.bench_harness(
        netlist, profile, bom, sources, (FIRMWARE / "bench_console.h").read_text()
    )
    assert {p for g in groups for p in g.endpoints if p.startswith("AFE.")} == {
        f"AFE.J9.{p}" for p in range(1, 21)
    }


def test_written_worksheet_stays_in_sync_with_source() -> None:
    text = (ROOT / "docs/REV_A_BENCH_HARNESS.md").read_text()
    for group in _harness():
        assert (
            "| " + group.name + " | " + ", ".join(f"`{p}`" for p in group.endpoints) + " |" in text
        )
    import json

    toolchain = json.loads((ROOT / "firmware/toolchain.json").read_text())
    assert "CDCOnBoot=default" in toolchain["fqbn"].split(":")[-1].split(",")
