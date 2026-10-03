"""P3 full auxiliary routing requires real native connectivity, not net labels."""

import json
import shutil
from pathlib import Path

import pytest

from tests.test_auxiliary_ground import _fresh
from tests.test_auxiliary_placement import CAD


@pytest.mark.schematic
def test_auxiliary_all_required_connections_are_complete(tmp_path: Path) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    report = _fresh(cad)
    assert report["schematic_parity"] == []
    assert report["violations"] == []
    assert report["unconnected_items"] == [], json.dumps(report["unconnected_items"])
