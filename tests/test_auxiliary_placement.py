"""P1 is editable, unrouted auxiliary placement; never a fabrication pass."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CAD = ROOT / "hardware/rev_a/auxiliary"
BOARD = CAD / "auxiliary.kicad_pcb"


def test_auxiliary_placement_is_present_and_explicitly_unrouted() -> None:
    text = BOARD.read_text()
    assert "P1 PLACEMENT ONLY - NOT FOR FABRICATION" in text
    assert "(footprint " in text and "(gr_rect" in text
    assert "(segment " not in text and "(via " not in text


@pytest.mark.schematic
def test_auxiliary_placement_native_schematic_parity(tmp_path: Path) -> None:
    """Native engine must agree with actual schematic; unconnected is not clean DRC."""
    cli = shutil.which("kicad-cli")
    assert cli is not None
    assert BOARD.is_file(), "auxiliary PCB placement has not been authored"
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    report = tmp_path / "placement-drc.json"
    with report.with_suffix(".log").open("w") as log:
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
                str(report),
                str(cad / BOARD.name),
            ],
            stdout=log,
            stderr=subprocess.STDOUT,
            timeout=45,
            env=dict(os.environ, KICAD_CONFIG_HOME=str(tmp_path / "config"), LC_ALL="C", LANG="C"),
        )
    data: object = json.loads(report.read_text())
    assert isinstance(data, dict)
    assert data["schematic_parity"] == []
    assert data["violations"] == []
    assert data["unconnected_items"], "P1 is not routed; do not accept a suppressed empty report"
    assert result.returncode == 5
