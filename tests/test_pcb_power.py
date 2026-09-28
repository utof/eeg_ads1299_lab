"""Ground and supply copper checks, not a release or powered-board qualification."""

import json
import shutil
from pathlib import Path

import pytest

from tests.test_pcb_placement import BOARD, CAD, _native_report


def test_ground_plane_is_present_as_filled_copper_not_only_an_outline() -> None:
    text = BOARD.read_text()
    assert '(zone ' in text
    assert '(filled_polygon' in text
    assert '(net_name "GND")' in text
    assert '(layer "In1.Cu")' in text


@pytest.mark.schematic
@pytest.mark.parametrize("net", ["GND", "VIN_5V_AFE", "AVDD", "DVDD"])
def test_ground_and_supply_nets_have_no_native_airwires(tmp_path: Path, net: str) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    shutil.copyfile(BOARD, cad / "rev_a.kicad_pcb")
    report = _native_report(cad)
    assert report["violations"] == []
    assert report["schematic_parity"] == []
    assert f"[{net}]" not in json.dumps(report["unconnected_items"])
    assert report["unconnected_items"]  # Digital/connector/BIAS remain unfinished.
