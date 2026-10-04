"""Snapshot binds the S1 centerline hypothesis to real source, not ground impedance."""

import json
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.schematic
def test_supply_inventory_matches_current_native_geometry(tmp_path: Path) -> None:
    from tests.supply_inventory_probe import SCRIPT

    result = subprocess.run(
        [os.environ.get("KICAD_PYTHON", "/usr/bin/python3"), "-c", SCRIPT, str(ROOT)],
        capture_output=True, text=True, timeout=45, check=False,
    )
    (tmp_path / "supply-inventory.log").write_text(result.stdout + result.stderr)
    assert result.returncode == 0, result.stdout + result.stderr
    actual: object = json.loads(result.stdout)
    expected: object = json.loads((ROOT / "docs/studies/s1_supply_paths.json").read_text())
    assert actual == expected, "native paths/assumptions changed; redo S1 review, not just its hashes"
