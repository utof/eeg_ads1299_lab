"""Snapshot binds the S1 centerline hypothesis to real source, not ground impedance."""

import json
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
# The S1 geometry baseline. The reviewed 2026-11-15 fitted revision later edited
# both boards (pad nets, population fields, fills, silkscreen), so the exact record
# is reproduced from this commit and current copper is compared separately.
SOURCE_COMMIT = "3519b21e335584244771c73c5c87b70d66037a7e"
IDENTITY = ("source_commit", "source_tree", "boards")


def _source_checkout(tmp_path: Path) -> Path:
    clone = tmp_path / "repo"
    for command in (
        ["git", "clone", "--shared", "--no-checkout", str(ROOT), str(clone)],
        ["git", "-C", str(clone), "checkout", "--detach", SOURCE_COMMIT],
    ):
        subprocess.run(command, capture_output=True, text=True, timeout=30, check=True)
    return clone


def _inventory(root: Path, log: Path, *mode: str) -> dict[str, object]:
    from tests.supply_inventory_probe import SCRIPT

    result = subprocess.run(
        [os.environ.get("KICAD_PYTHON", "/usr/bin/python3"), "-c", SCRIPT, str(root), *mode],
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
    )
    log.write_text(result.stdout + result.stderr)
    assert result.returncode == 0, result.stdout + result.stderr
    actual: object = json.loads(result.stdout)
    assert isinstance(actual, dict) and all(isinstance(key, str) for key in actual)
    validated: dict[str, object] = actual
    return validated


def _record() -> dict[str, object]:
    expected: object = json.loads((ROOT / "docs/studies/s1_supply_paths.json").read_text())
    assert isinstance(expected, dict) and all(isinstance(key, str) for key in expected)
    validated: dict[str, object] = expected
    return validated


@pytest.mark.schematic
def test_supply_inventory_reproduces_its_exact_source_geometry(tmp_path: Path) -> None:
    actual = _inventory(_source_checkout(tmp_path), tmp_path / "supply-inventory.log")
    assert actual == _record(), (
        "native paths/assumptions changed; redo S1 review, not just its hashes"
    )


@pytest.mark.schematic
def test_current_boards_keep_the_s1_supply_geometry(tmp_path: Path) -> None:
    """Current copper keeps every S1 path; the record's identity stays historical."""
    import hashlib

    actual = _inventory(ROOT, tmp_path / "current-geometry.log", "current-geometry")
    expected = _record()
    paths = (
        "hardware/rev_a/layout/rev_a.kicad_pcb",
        "hardware/rev_a/auxiliary/auxiliary.kicad_pcb",
    )
    boards: object = expected["boards"]
    assert isinstance(boards, dict) and set(boards) == set(paths)
    assert actual["source_commit"] is None and actual["source_tree"] is None
    assert actual["boards"] == {
        path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in paths
    }
    assert {k: v for k, v in actual.items() if k not in IDENTITY} == {
        k: v for k, v in expected.items() if k not in IDENTITY
    }, "current supply copper differs from S1; redo S1 review"


def _run_documented_accounting(cwd: Path, log_dir: Path) -> dict[str, object]:
    """Execute the published instructions, not a separately maintained helper copy."""
    import re
    import sys

    document = (ROOT / "docs/REV_A_SUPPLY_RETURN_S1.md").read_text()
    blocks: list[str] = re.findall(r"```python\n(.*?)\n```", document, re.DOTALL)
    assert len(blocks) == 1
    script = blocks[0] + '\nprint("S1_RESULT=" + json.dumps(res, sort_keys=True))\n'
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    (log_dir / "documented-accounting.log").write_text(result.stdout + result.stderr)
    assert result.returncode == 0, result.stdout + result.stderr
    records = [
        line.removeprefix("S1_RESULT=")
        for line in result.stdout.splitlines()
        if line.startswith("S1_RESULT=")
    ]
    assert len(records) == 1
    data: object = json.loads(records[0])
    assert isinstance(data, dict) and data["no_qualification_result"] is True
    assert all(isinstance(key, str) for key in data)
    validated: dict[str, object] = data
    return validated


def test_documented_accounting_block_runs_and_reproduces_examples(tmp_path: Path) -> None:
    data = _run_documented_accounting(ROOT, tmp_path)
    dvdd: object = data["hypothetical_DVDD_load_cases"]
    vin: object = data["hypothetical_5V_load_cases"]
    assert isinstance(dvdd, list) and isinstance(vin, list)
    assert len(dvdd) == len(vin) == 2
    high_dvdd: object = dvdd[1]
    high_vin: object = vin[1]
    assert isinstance(high_dvdd, dict) and isinstance(high_vin, dict)
    loss: object = high_dvdd["feed_losses_V"]
    assert isinstance(loss, dict)
    # Independently retained, rounded reported values; not re-generated expectations.
    assert loss["U104.14"] == pytest.approx(0.003557471138, abs=1e-10, rel=0)
    assert high_vin["headroom_V_for_ALL_other_feed_return_and_errors"] == pytest.approx(
        0.0948666531, abs=1e-10, rel=0
    )


@pytest.mark.schematic
@pytest.mark.parametrize("board", ["layout", "auxiliary"])
def test_changed_board_cannot_regenerate_old_source_identity(tmp_path: Path, board: str) -> None:
    """Real Git/native copies: even a geometry-neutral edit invalidates exact provenance."""
    from tests.supply_inventory_probe import SCRIPT

    # Start from the exact source so the appended byte is the only difference.
    clone = _source_checkout(tmp_path)
    name = "rev_a.kicad_pcb" if board == "layout" else "auxiliary.kicad_pcb"
    target = clone / "hardware/rev_a" / board / name
    target.write_bytes(target.read_bytes() + b"\n")
    result = subprocess.run(
        [os.environ.get("KICAD_PYTHON", "/usr/bin/python3"), "-c", SCRIPT, str(clone)],
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
    )
    (tmp_path / "changed-board-provenance.log").write_text(result.stdout + result.stderr)
    assert result.returncode != 0, "modified board was falsely attributed to the old source"
    assert "source identity" in result.stderr, result.stderr
    assert not result.stdout.strip(), "failed provenance must not produce a replacement inventory"


def test_accounting_keeps_the_afe_pth_term_when_trace_resistance_is_zero(tmp_path: Path) -> None:
    """Independent term-isolation control, not a zero-resistivity hardware scenario."""
    from lab.validation import read_object

    model = read_object(
        json.loads((ROOT / "docs/studies/s1_supply_paths.json").read_text()), "S1 study"
    )
    assumed = model["assumed"]
    assert isinstance(assumed, dict)
    assumed["rho20_ohm_mm2_per_m"] = 0.0
    assumed["PTH_extra_ohm"] = 0.005
    destination = tmp_path / "docs/studies/s1_supply_paths.json"
    destination.parent.mkdir(parents=True)
    destination.write_text(json.dumps(model))
    result = _run_documented_accounting(tmp_path, tmp_path)
    cases = result["hypothetical_5V_load_cases"]
    assert isinstance(cases, list) and len(cases) == 2
    for raw in cases:
        case: object = raw
        assert isinstance(case, dict)
        # One selected AFE PTH at 5 milliohm, carrying the declared 27.086mA.
        # Trace/via terms are zero by construction; they cannot hide this term.
        assert case["AFE_input_trace_lumped_loss_V"] == pytest.approx(
            0.027086 * 0.005, rel=0, abs=1e-15
        )
