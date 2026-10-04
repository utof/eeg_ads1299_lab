"""P3 full auxiliary routing requires real native connectivity, not net labels."""

import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.auxiliary_routing_probe import MUTATE, SCRIPT
from tests.test_auxiliary_ground import _fresh
from tests.test_auxiliary_placement import BOARD, CAD, ROOT
from tests.test_pcb_power import _form_end


@pytest.mark.schematic
def test_auxiliary_all_required_connections_are_complete(tmp_path: Path) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    report = _fresh(cad)
    assert report["schematic_parity"] == []
    assert report["violations"] == []
    assert report["unconnected_items"] == [], json.dumps(report["unconnected_items"])


def _proof(cad: Path) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [
            os.environ.get("KICAD_PYTHON", "/usr/bin/python3"),
            "-c",
            SCRIPT,
            str(cad / BOARD.name),
            "reference",
            str(ROOT / "tests/fixtures/auxiliary_p3_pending_edges.json"),
        ],
        capture_output=True,
        text=True,
        timeout=45,
    )
    (cad / "p3-reference.log").write_text(result.stdout + result.stderr)
    return result


def _mutate(cad: Path, mode: str, ref: str = "", pin: str = "") -> None:
    result = subprocess.run(
        [
            os.environ.get("KICAD_PYTHON", "/usr/bin/python3"),
            "-c",
            MUTATE,
            str(cad / BOARD.name),
            mode,
            ref,
            pin,
        ],
        capture_output=True,
        text=True,
        timeout=45,
    )
    (cad / "p3-mutation.log").write_text(result.stdout + result.stderr)
    assert result.returncode == 0, result.stdout + result.stderr


def test_p3_preserves_all_p2_footprints_and_original_copper() -> None:
    data: object = json.loads((ROOT / "tests/fixtures/auxiliary_p2_preservation.json").read_text())
    assert isinstance(data, dict)
    expected: object = data["items"]
    assert isinstance(expected, dict) and len(expected) == 153
    actual: dict[str, dict[str, str]] = {}
    text = BOARD.read_text()
    for match in re.finditer(r"\((footprint|segment|via)\s", text):
        raw = text[match.start() : _form_end(text, match.start())]
        ident = re.search(r'\(uuid "([^"]+)"', raw)
        assert ident is not None
        assert ident[1] not in actual, "duplicate source UUID"
        actual[ident[1]] = {"type": match[1], "sha256": hashlib.sha256(raw.encode()).hexdigest()}
    records: dict[object, object] = expected
    for ident, record in records.items():
        assert isinstance(ident, str) and isinstance(record, dict)
        assert actual.get(ident) == record, f"original P2 source changed: {ident}"


@pytest.mark.schematic
def test_global_routes_have_explicit_reference_screen_and_limits(tmp_path: Path) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    result = _fresh(cad)
    assert all(result[k] == [] for k in ("schematic_parity", "violations", "unconnected_items"))
    proof = _proof(cad)
    assert proof.returncode == 0, proof.stdout + proof.stderr
    raw: object = json.loads(proof.stdout)
    assert isinstance(raw, dict)
    assert raw["reference_spine_width_mm"] == 0.10
    assert raw["pending_edge_geometry_status"] == "PENDING_ELECTRICAL_REVIEW_NOT_A_RELEASE"
    assert raw["unreviewed_edge_growth_detected"] is False
    assert raw["full_width_ground_coverage_qualified"] is False
    assert raw["EMC_impedance_timing_or_physical_qualification"] is False


@pytest.mark.schematic
@pytest.mark.parametrize(
    "net,ref,pin",
    [
        ["AFE_AVDD_SENSE", "J104", "4"],
        ["AFE_CLKSEL", "J101", "19"],
        ["AFE_CS", "J101", "7"],
        ["AFE_DRDY", "J101", "9"],
        ["AFE_DVDD", "J104", "2"],
        ["AFE_DVDD_SENSE", "J104", "3"],
        ["AFE_MISO", "J101", "5"],
        ["AFE_MOSI", "J101", "3"],
        ["AFE_PWDN", "J101", "15"],
        ["AFE_RESET", "J101", "11"],
        ["AFE_SCLK", "J101", "1"],
        ["AFE_START", "J101", "13"],
        ["ARM_CLK", "U110", "4"],
        ["ARM_REQ", "J102", "15"],
        ["BUS_OE", "J102", "9"],
        ["CLR_N", "J102", "8"],
        ["CONSOLE_RX", "J102", "10"],
        ["CONSOLE_TX", "J102", "11"],
        ["CT_MON_A", "R105", "2"],
        ["CT_MON_D", "R103", "2"],
        ["CT_MON_M", "R101", "2"],
        ["CT_MON_V", "R107", "2"],
        ["HOST_3V3", "J103", "1"],
        ["HOST_RX", "J103", "4"],
        ["HOST_TX", "J103", "3"],
        ["MCU_3V3", "J102", "2"],
        ["MCU_CLKSEL", "J102", "12"],
        ["MCU_CS", "J102", "16"],
        ["MCU_DRDY", "J102", "4"],
        ["MCU_MISO", "J102", "19"],
        ["MCU_MOSI", "J102", "17"],
        ["MCU_PWDN", "J102", "7"],
        ["MCU_RESET", "J102", "5"],
        ["MCU_SCLK", "J102", "18"],
        ["MCU_START", "J102", "6"],
        ["RAILS_OK", "R112", "1"],
        ["SESSION", "J102", "20"],
        ["STOP_N", "J106", "1"],
        ["TARGET_VIN5", "J101", "17"],
    ],
)
def test_native_missing_terminal_escape_is_detected(
    tmp_path: Path, net: str, ref: str, pin: str
) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    _mutate(cad, "cut", ref, pin)
    report = _fresh(cad)
    assert report["schematic_parity"] == []
    missing = json.dumps(report["unconnected_items"])
    assert f"[{net}]" in missing and ref in missing, missing
    raw = report["violations"]
    assert isinstance(raw, list)
    records: list[object] = raw
    for item in records:
        assert isinstance(item, dict)
        kind: object = item["type"]
        assert isinstance(kind, str) and kind in ("track_dangling", "via_dangling"), item


@pytest.mark.schematic
@pytest.mark.parametrize("edit", ["reverse", "split", "remote-void"])
def test_benign_p3_representations_and_remote_void_pass(tmp_path: Path, edit: str) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    _mutate(cad, edit)
    report = _fresh(cad)
    assert all(report[k] == [] for k in ("schematic_parity", "violations", "unconnected_items"))
    proof = _proof(cad)
    assert proof.returncode == 0, proof.stdout + proof.stderr


@pytest.mark.schematic
def test_actual_routed_signal_over_reference_void_is_rejected(tmp_path: Path) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    _mutate(cad, "reference-void")
    report = _fresh(cad)
    assert all(report[k] == [] for k in ("schematic_parity", "violations", "unconnected_items"))
    proof = _proof(cad)
    assert proof.returncode != 0 and "P3 central reference spine gap" in proof.stderr


@pytest.mark.schematic
def test_new_full_width_edge_gap_cannot_hide_behind_an_intact_spine(tmp_path: Path) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    _mutate(cad, "edge-growth")
    report = _fresh(cad)
    assert all(report[k] == [] for k in ("schematic_parity", "violations", "unconnected_items"))
    proof = _proof(cad)
    assert proof.returncode != 0 and "P3 unreviewed full-width reference growth" in proof.stderr


@pytest.mark.schematic
@pytest.mark.parametrize("edit", ["edge-remote", "reverse-residual", "split-residual"])
def test_pending_edge_geometry_allows_remote_void_and_equivalent_copper(
    tmp_path: Path, edit: str
) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    _mutate(cad, edit)
    report = _fresh(cad)
    assert all(report[k] == [] for k in ("schematic_parity", "violations", "unconnected_items"))
    proof = _proof(cad)
    assert proof.returncode == 0, proof.stdout + proof.stderr
