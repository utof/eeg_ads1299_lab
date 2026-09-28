"""Native placement checks; unconnected non-input nets remain a release blocker."""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CAD = ROOT / "hardware/rev_a/kicad"
BOARD = ROOT / "hardware/rev_a/layout/rev_a.kicad_pcb"


def test_editable_placement_is_a_tracked_design_not_a_parking_grid() -> None:
    text = BOARD.read_text()
    assert text.count('(footprint "') == 68
    assert text.count('(pad "') == 245
    assert text.count(" dnp)") == 8
    assert "(gr_rect " in text and '(layer "Edge.Cuts")' in text
    assert '(1 "In1.Cu" power)' in text and '(2 "In2.Cu" signal)' in text
    assert "(segment " in text
    assert "PLACEMENT DRAFT - NOT FOR FABRICATION" in text
    assert "(zone " not in text  # Planes and their returns have NOT been implemented.


def _native_report(cad: Path) -> dict[str, object]:
    cli = shutil.which("kicad-cli")
    assert cli is not None, "actual placement validation requires KiCad"
    output = cad / "placement-drc.json"
    result = subprocess.run(
        [
            cli,
            "pcb",
            "drc",
            "--format",
            "json",
            "--schematic-parity",
            "--severity-all",
            "--exit-code-violations",
            "-o",
            str(output),
            str(cad / "rev_a.kicad_pcb"),
        ],
        capture_output=True,
        text=True,
        timeout=45,
        env=dict(os.environ, KICAD_CONFIG_HOME=str(cad / "config"), LC_ALL="C", LANG="C"),
    )
    (cad / "placement-drc.log").write_text(result.stdout + result.stderr)
    assert result.returncode == 5, result.stdout + result.stderr
    report: object = json.loads(output.read_text())
    assert isinstance(report, dict)
    return report


def _input_airwire(report: dict[str, object]) -> bool:
    # KiCad's independent connectivity engine, not the authoring script's routes.
    return re.search(r"\bIN[1-4][PN]\b", json.dumps(report["unconnected_items"])) is not None


def _footprint_block(board: str, reference: str) -> str:
    # Split only for localized faults; KiCad remains the actual file parser.
    # Do not require the one-line formatting emitted by the original import.
    marker = r'\(property\s+"Reference"\s+"' + re.escape(reference) + '"'
    return next(
        block
        for block in re.split(r'(?=\(footprint\s+")', board)
        if block.startswith("(footprint ") and re.search(marker, block)
    )


def _fault_board(board: str, fault: str) -> str:
    if fault == "overlap":
        one = _footprint_block(board, "R1")
        two = _footprint_block(board, "R2")
        second_at = re.search(r"\(at [^)]+\)", two)
        assert second_at is not None
        changed = re.sub(r"\(at [^)]+\)", second_at.group(), one, count=1)
        assert changed != one
        board = board.replace(one, changed, 1)
    elif fault == "wrong-net":
        one = _footprint_block(board, "C1")
        ground = re.search(r'\(net \d+ "GND"\)', board)
        assert ground is not None
        changed = re.sub(r'\(net \d+ "IN1P"\)', ground.group(), one, count=1)
        assert changed != one
        board = board.replace(one, changed, 1)
    elif fault == "missing-input-track":
        code = re.search(r'\(net (\d+) "IN1P"\)', board)
        assert code is not None
        tracks = re.findall(r'\(segment\s+(?:(?!\(segment).)*?\(uuid\s+"[^"]+"\)\)', board, re.S)
        track = next(t for t in tracks if f"(net {code.group(1)})" in t)
        board = board.replace(track, "", 1)
    return board


@pytest.mark.schematic
@pytest.mark.parametrize("fault", ["none", "overlap", "wrong-net", "missing-input-track"])
def test_native_placement_and_completed_input_routes(tmp_path: Path, fault: str) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    board = _fault_board(BOARD.read_text(), fault)
    (cad / "rev_a.kicad_pcb").write_text(board)
    report = _native_report(cad)
    assert bool(report["schematic_parity"]) is (fault == "wrong-net")
    assert bool(report["violations"]) is (fault != "none")
    if fault == "none":
        assert not _input_airwire(report)
    elif fault == "missing-input-track":
        assert _input_airwire(report)
    assert report["unconnected_items"]  # Do not call this a routed or fabrication-ready board.
