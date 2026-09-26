"""Closed native source inventory and fail-closed ERC report contracts."""

import json
import os
import shutil
from pathlib import Path

import pytest

import hardware.rev_a as rev_a
from hardware.rev_a import read_schematic_file, schematic_source_snapshot, validate_erc

CAD = Path(__file__).resolve().parents[1] / "hardware/rev_a/kicad"


@pytest.fixture
def cad_copy(tmp_path: Path) -> Path:
    target = tmp_path / "cad"
    shutil.copytree(CAD, target)
    return target


def test_all_seven_native_inputs_are_snapshotted(cad_copy: Path) -> None:
    snapshot = schematic_source_snapshot(cad_copy)
    assert len(snapshot) == 7
    for name in ("power.kicad_sch", "RevA.kicad_sym", "rev_a.kicad_pro"):
        path = cad_copy / name
        old = path.read_text()
        path.write_text(old + "\n")
        assert schematic_source_snapshot(cad_copy)[name] != snapshot[name]
        path.write_text(old)


@pytest.mark.parametrize(
    "name",
    ["power.kicad_sch", "RevA.kicad_sym", "sym-lib-table", "fp-lib-table", "rev_a.kicad_pro"],
)
def test_missing_input_not_hidden_by_embedded_caches(cad_copy: Path, name: str) -> None:
    (cad_copy / name).unlink()
    with pytest.raises(ValueError, match="source files"):
        schematic_source_snapshot(cad_copy)


@pytest.mark.parametrize(
    "fault",
    [
        "extra-sheet",
        "extra-library",
        "external-child",
        "nested-child",
        "foreign-lib-id",
        "symbol-uri",
        "footprint-uri",
        "footprint-uri-swapped",
        "ignore-erc",
        "erc-exclusion",
        "symlink-file",
        "symlink-root",
    ],
)
def test_undeclared_inputs_and_suppression_rejected(
    cad_copy: Path, tmp_path: Path, fault: str
) -> None:
    if fault == "extra-sheet":
        (cad_copy / "hidden.kicad_sch").write_text("extra")
    elif fault == "extra-library":
        (cad_copy / "Other.kicad_sym").write_text("extra")
    elif fault in {
        "external-child",
        "nested-child",
        "foreign-lib-id",
        "symbol-uri",
        "footprint-uri",
        "footprint-uri-swapped",
    }:
        _break_dependency(cad_copy, fault)
    elif fault in {"ignore-erc", "erc-exclusion"}:
        path = cad_copy / "rev_a.kicad_pro"
        project = json.loads(path.read_text())
        if fault == "ignore-erc":
            project["erc"]["rule_severities"]["pin_not_connected"] = "ignore"
        else:
            project["erc"]["erc_exclusions"] = ["hidden finding"]
        path.write_text(json.dumps(project))
    elif fault == "symlink-file":
        path = cad_copy / "RevA.kicad_sym"
        other = tmp_path / "borrowed.kicad_sym"
        path.rename(other)
        path.symlink_to(other)
    elif fault == "symlink-root":
        link = tmp_path / "link"
        link.symlink_to(cad_copy, target_is_directory=True)
        cad_copy = link
    with pytest.raises(ValueError):
        schematic_source_snapshot(cad_copy)


def test_nonregular_and_oversize_inputs_rejected(tmp_path: Path) -> None:
    path = tmp_path / "fifo"
    os.mkfifo(path)
    with pytest.raises(ValueError, match="regular"):
        read_schematic_file(path)
    path.unlink()
    path.write_bytes(b"x" * 2_000_001)
    with pytest.raises(ValueError, match="oversized"):
        read_schematic_file(path)


def clean_erc() -> dict[str, object]:
    return {
        "kicad_version": "9.0.2",
        "source": "rev_a.kicad_sch",
        "sheets": [
            {"path": name, "violations": list[object]()} for name in ("/", "/POWER/", "/DIGITAL/")
        ],
    }


def test_complete_clean_erc_report_passes() -> None:
    validate_erc(json.dumps(clean_erc()))


@pytest.mark.parametrize(
    "fault",
    [
        "wrong-version",
        "wrong-source",
        "missing-sheets",
        "missing-child",
        "duplicate-sheet",
        "violation",
        "excluded",
        "missing-violations",
        "not-object",
        "not-sheet",
    ],
)
def test_erc_cannot_accept_partial_or_suppressed_reports(fault: str) -> None:
    report = clean_erc()
    if fault == "wrong-version":
        report["kicad_version"] = "9.0.1"
    elif fault == "wrong-source":
        report["source"] = "other.kicad_sch"
    elif fault == "missing-sheets":
        report.pop("sheets")
    elif fault == "missing-child":
        report["sheets"] = [{"path": "/", "violations": list[object]()}]
    elif fault == "duplicate-sheet":
        report["sheets"] = [{"path": "/", "violations": list[object]()}] * 3
    elif fault in {"violation", "excluded"}:
        report["sheets"] = [
            {"path": "/", "violations": [{"severity": "warning", "excluded": fault == "excluded"}]}
        ]
    elif fault == "missing-violations":
        report["sheets"] = [{"path": "/"}]
    elif fault == "not-sheet":
        report["sheets"] = [None]
    with pytest.raises(ValueError):
        validate_erc("[]" if fault == "not-object" else json.dumps(report))


def test_source_and_erc_boundaries_exist() -> None:
    assert callable(getattr(rev_a, "schematic_source_snapshot", None)), (
        "missing CAD dependency snapshot"
    )
    assert callable(getattr(rev_a, "validate_erc", None)), "missing strict ERC validation"


def _break_dependency(cad_copy: Path, fault: str) -> None:
    if fault in {"external-child", "nested-child", "foreign-lib-id"}:
        name = "power.kicad_sch" if fault == "nested-child" else "rev_a.kicad_sch"
        path = cad_copy / name
        text = path.read_text()
        if fault == "external-child":
            text = text.replace('"power.kicad_sch"', '"../power.kicad_sch"')
        elif fault == "nested-child":
            text += '\n(property "Sheetfile" "hidden.kicad_sch")\n'
        else:
            text = text.replace('lib_id "RevA:', 'lib_id "Other:')
        path.write_text(text)
    elif fault in {"symbol-uri", "footprint-uri", "footprint-uri-swapped"}:
        name = "sym-lib-table" if fault == "symbol-uri" else "fp-lib-table"
        path = cad_copy / name
        text = path.read_text()
        if fault == "symbol-uri":
            text = text.replace("${KIPRJMOD}/", "../")
        elif fault == "footprint-uri":
            text = text.replace("${KICAD9_FOOTPRINT_DIR}", "/tmp/untracked")
        else:
            text = (
                text.replace("/Resistor_SMD.pretty", "/SWAP.pretty")
                .replace("/Capacitor_SMD.pretty", "/Resistor_SMD.pretty")
                .replace("/SWAP.pretty", "/Capacitor_SMD.pretty")
            )
        path.write_text(text)
