"""Software-only gate doubles. They do not establish native CAD execution."""

import csv
import gzip
import io
import json
import shutil
from collections.abc import Sequence
from pathlib import Path

import pytest

from hardware.rev_a import parse_auxiliary_contract
from lab.validation import read_object
from tests.footprint_fixtures import write_footprint_library
from tools.check import main

ROOT = Path(__file__).resolve().parents[1]
BOM_CSV = (ROOT / "tests/fixtures/rev_a_bom.csv").read_text()
FIXTURE = gzip.decompress((ROOT / "tests/fixtures/rev_a_netlist.xml.gz").read_bytes()).decode()


def _fake_project(root: Path) -> Path:
    shutil.copytree(ROOT / "hardware/rev_a", root / "hardware/rev_a")
    shutil.copytree(ROOT / "firmware/esp32_ads1299_bench", root / "firmware/esp32_ads1299_bench")
    shutil.copyfile(ROOT / "firmware/toolchain.json", root / "firmware/toolchain.json")
    shutil.copytree(ROOT / "tests", root / "tests", ignore=shutil.ignore_patterns("__pycache__"))
    (root / "tools").mkdir()
    shutil.copyfile(ROOT / "tools/check.py", root / "tools/check.py")
    shutil.copyfile(ROOT / "pyproject.toml", root / "pyproject.toml")
    (root / "docs/studies").mkdir(parents=True)
    shutil.copyfile(
        ROOT / "docs/studies/s1_supply_paths.json", root / "docs/studies/s1_supply_paths.json"
    )
    for name in (
        "tools/dc_budget.py",
        "docs/REV_A_CURRENT_RETURN_S2.md",
        "docs/studies/s2_current_return.json",
    ):
        shutil.copyfile(ROOT / name, root / name)
    footprints = write_footprint_library(root / "footprints")
    contract = parse_auxiliary_contract(
        (root / "hardware/rev_a/auxiliary/contract.json").read_text()
    )
    for part in contract.parts.values():
        library, name = part.footprint.split(":")
        if library == "Aux_Lands":
            continue
        path = footprints / (library + ".pretty") / (name + ".kicad_mod")
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("SOFTWARE-ONLY footprint snapshot double; not native geometry")
    mount = footprints / "MountingHole.pretty/MountingHole_2.7mm_M2.5.kicad_mod"
    mount.parent.mkdir(exist_ok=True)
    mount.write_text("source-only mounting-land stub, not native geometry")
    return footprints


def _clean_erc() -> str:
    return json.dumps(
        {
            "kicad_version": "9.0.2",
            "source": "rev_a.kicad_sch",
            "sheets": [
                {"path": name, "violations": list[object]()}
                for name in ("/", "/POWER/", "/DIGITAL/")
            ],
        }
    )


def _fake_native_step(name: str, command: Sequence[str], out: Path, root: Path, fault: str) -> None:
    text = "software-only process double, not native execution"
    if name == "kicad-version":
        text = "9.0.1" if fault == "wrong-version" else "9.0.2"
    elif name == "schematic-source":
        text = "bad" if fault == "bad-source" else "a" * 40
    elif name == "schematic-dirty":
        text = " M candidate-source"
    (out / (name + ".log")).write_text(text)
    if name in {"schematic-erc", "schematic-netlist", "schematic-pdf", "schematic-bom"}:
        path = Path(command[command.index("-o") + 1])
        assert not path.exists(), "gate reused an earlier native artifact"
        _fake_output(name, path, fault)
    if name == "schematic-netlist":
        _change_dependency(root, fault)
    if name == "harness-console-tests":
        assert "tests/test_firmware_sketch_startup.py" in command
        assert "tests/test_bench_harness.py" in command
        assert "tests/test_firmware_interlock.py" in command
        assert command[command.index("-m", 3) + 1] == "native"
        assert not list(out.glob("schematic-*/harness.json")), (
            "harness published before console proof"
        )
        if fault == "console-route-fails":
            raise RuntimeError("injected actual-sketch route failure")
    failure = {
        "native-tests-timeout": "injected CAD batch timeout",
        "native-tests-fail": "injected native regression failure",
    }.get(fault)
    if name == "schematic-tests" and failure is not None:
        raise RuntimeError(failure)


def _fake_output(name: str, path: Path, fault: str) -> None:
    missing = {
        "no-erc": "schematic-erc",
        "no-netlist": "schematic-netlist",
        "no-pdf": "schematic-pdf",
    }
    if missing.get(fault) == name:
        return
    if name == "schematic-erc":
        if fault == "erc-nonzero":
            raise RuntimeError("injected ERC exit 5")
        path.write_text("{}" if fault == "bad-erc" else _clean_erc())
    elif name == "schematic-netlist":
        text = "<export" if fault == "bad-xml" else FIXTURE
        if fault == "wrong-wiring":
            text = text.replace("<value>4.7n</value>", "<value>4.7u</value>", 1)
        path.write_text(text)
    elif name == "schematic-pdf":
        path.write_bytes(b"SOFTWARE PDF DOUBLE")
    elif name == "schematic-bom":
        path.write_text(_bom_output(fault))


def _bom_output(fault: str) -> str:
    if fault == "empty-bom":
        return ""
    rows = list(csv.reader(io.StringIO(BOM_CSV)))
    if fault == "partial-bom":
        rows.pop()
    elif fault == "wrong-bom-flag":
        next(row for row in rows if row[0] == "D1")[6] = ""
    result = io.StringIO(newline="")
    csv.writer(result).writerows(rows)
    return result.getvalue()


def _change_dependency(root: Path, fault: str) -> None:
    files = {
        "change-auxiliary": root / "hardware/rev_a/auxiliary/bus.kicad_sch",
        "change-aux-contract": root / "hardware/rev_a/auxiliary/contract.json",
        "change-aux-library": root
        / "footprints/Package_SO.pretty/TSSOP-14_4.4x5mm_P0.65mm.kicad_mod",
        "change-aux-fixture": root / "tests/fixtures/auxiliary_c3_netlist.xml.gz",
        "change-child": root / "hardware/rev_a/kicad/power.kicad_sch",
        "change-board": root / "hardware/rev_a/layout/rev_a.kicad_pcb",
        "change-board-test": root / "tests/test_pcb_placement.py",
        "change-power-test": root / "tests/test_pcb_power.py",
        "change-ground-test": root / "tests/test_auxiliary_ground.py",
        "change-ground-oracle": root / "tests/auxiliary_ground_probe.py",
        "change-p3-envelope": root / "tests/fixtures/auxiliary_p3_pending_edges.json",
        "change-reference-performance": root / "tests/test_reference_performance.py",
        "change-clock-review": root / "tests/test_auxiliary_clock.py",
        "change-supply-data": root / "docs/studies/s1_supply_paths.json",
        "change-supply-probe": root / "tests/supply_inventory_probe.py",
        "change-supply-test": root / "tests/test_supply_inventory.py",
        "change-current-calculator": root / "tools/dc_budget.py",
        "change-current-document": root / "docs/REV_A_CURRENT_RETURN_S2.md",
        "change-current-data": root / "docs/studies/s2_current_return.json",
        "change-current-test": root / "tests/test_current_return_s2.py",
        "change-clock-reference": root / "tests/fixtures/auxiliary_clock_before_review.json",
        "change-library": root / "hardware/rev_a/kicad/RevA.kicad_sym",
        "change-console": root / "firmware/esp32_ads1299_bench/bench_console.h",
        "change-interlock": root / "firmware/esp32_ads1299_bench/c2_interlock.h",
        "change-interlock-test": root / "tests/test_firmware_interlock.py",
        "change-interlock-oracle": root / "tests/native_c2_session_test.cpp",
        "change-sketch": root / "firmware/esp32_ads1299_bench/esp32_ads1299_bench.ino",
        "change-profile": root / "firmware/esp32_ads1299_bench/board_config_rev_a_s3.h",
        "change-local-footprint": root
        / "hardware/rev_a/kicad/RevA_Passives.pretty/T491B_3528_DensityB.kicad_mod",
    }
    if fault == "change-footprint":
        # Pick an actually consumed installed definition, never a shadow copy of
        # a project-local library. Filesystem iteration order is not a contract.
        files[fault] = root / "footprints/Package_QFP.pretty/TQFP-64_10x10mm_P0.5mm.kicad_mod"
    path = files.get(fault)
    if path is not None:
        path.write_bytes(path.read_bytes() + b"\n")


@pytest.mark.parametrize(
    "fault",
    [
        "none",
        "wrong-version",
        "bad-source",
        "no-erc",
        "bad-erc",
        "erc-nonzero",
        "no-netlist",
        "bad-xml",
        "wrong-wiring",
        "no-pdf",
        "empty-bom",
        "partial-bom",
        "wrong-bom-flag",
        "change-child",
        "change-aux-fixture",
        "change-auxiliary",
        "change-aux-contract",
        "change-aux-library",
        "change-board",
        "change-board-test",
        "change-power-test",
        "change-ground-test",
        "change-ground-oracle",
        "change-p3-envelope",
        "change-reference-performance",
        "change-clock-review",
        "change-supply-data",
        "change-supply-probe",
        "change-supply-test",
        "change-current-calculator",
        "change-current-document",
        "change-current-data",
        "change-current-test",
        "change-clock-reference",
        "change-library",
        "change-console",
        "change-sketch",
        "change-profile",
        "change-interlock",
        "change-interlock-test",
        "change-interlock-oracle",
        "console-route-fails",
        "missing-console-compiler",
        "wrong-footprint-pad",
        "change-footprint",
        "change-local-footprint",
        "missing-dependency",
        "native-tests-fail",
        "native-tests-timeout",
    ],
)
def test_schematic_gate_rejects_stale_partial_or_mismatched_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    footprints = _fake_project(root)
    out = tmp_path / "reports"
    out.mkdir()
    marker = out / "SCHEMATIC_CHECK.json"
    marker.write_text('{"passed": true, "old": true}')
    if fault == "wrong-footprint-pad":
        path = footprints / "Package_QFP.pretty/TQFP-64_10x10mm_P0.5mm.kicad_mod"
        path.write_text(path.read_text().replace('(pad "1"', '(pad "65"', 1))
    if fault == "missing-dependency":
        (root / "hardware/rev_a/kicad/RevA.kicad_sym").unlink()

    def plan(_out: Path) -> list[tuple[str, list[str]]]:
        return []

    def coverage(_path: Path, _minimum: float) -> float:
        return 80.0

    def tool(name: str) -> str | None:
        if fault == "missing-console-compiler" and name in {"g++", "clang++"}:
            return None
        return "/software-double/kicad-cli"

    def step(name: str, command: Sequence[str], out: Path, timeout: float = 300) -> None:
        assert timeout == (450 if name == "schematic-tests" else 300)
        _fake_native_step(name, command, out, root, fault)

    monkeypatch.setattr("tools.check.ROOT", root)
    monkeypatch.setattr("tools.check.command_plan", plan)
    monkeypatch.setattr("tools.check.check_branch_coverage", coverage)
    monkeypatch.setattr("tools.check.run_step", step)
    monkeypatch.setattr(shutil, "which", tool)
    monkeypatch.setenv("KICAD9_FOOTPRINT_DIR", str(footprints))
    assert main(["--schematic", "--out", str(out)]) == (0 if fault == "none" else 1)
    if fault == "none":
        report = read_object(json.loads(marker.read_text()), "schematic")
        assert report["source_commit"] == "a" * 40
        assert report["source_dirty"] is True
        assert report["component_count"] == 70 and report["terminal_count"] == 262
        assert report["physical_hardware_tested"] is False
        assert report["body_connection_authorized"] is False
        assert report["schematic_released"] is False
        assert len(read_object(report["source_sha256"], "hashes")) == 101
        directory = out / str(report["artifact_directory"])
        harness = read_object(json.loads((directory / "harness.json").read_text()), "harness")
        assert harness["physical_wiring_approved"] is False
        assert harness["console_interface_qualified"] is False
        assert "harness.json" in read_object(report["artifact_sha256"], "artifacts")
    else:
        assert not marker.exists()


def test_ordinary_failure_invalidates_previous_schematic_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def failed(_out: Path) -> list[tuple[str, list[str]]]:
        raise RuntimeError("ordinary check failed before CAD work")

    marker = tmp_path / "SCHEMATIC_CHECK.json"
    marker.write_text('{"stale": true}')
    monkeypatch.setattr("tools.check.command_plan", failed)
    assert main(["--schematic", "--out", str(tmp_path)]) == 1
    assert not marker.exists()


def test_requested_schematic_gate_fails_without_native_tool(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def plan(_out: Path) -> list[tuple[str, list[str]]]:
        return []

    def coverage(_path: Path, _minimum: float) -> float:
        return 80.0

    def missing(_name: str) -> None:
        return None

    monkeypatch.setattr("tools.check.command_plan", plan)
    monkeypatch.setattr("tools.check.check_branch_coverage", coverage)
    monkeypatch.setattr(shutil, "which", missing)
    assert main(["--schematic", "--out", str(tmp_path)]) == 1
