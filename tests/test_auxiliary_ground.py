"""P2 ground references and bypass access: native checks, not electrical qualification."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.auxiliary_ground_probe import SCRIPT
from tests.test_auxiliary_placement import BOARD, CAD
from tests.test_pcb_placement import _FILL_SCRIPT


def _probe(cad: Path, mode: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [
            os.environ.get("KICAD_PYTHON", "/usr/bin/python3"),
            "-c",
            SCRIPT,
            str(cad / BOARD.name),
            mode,
        ],
        capture_output=True,
        text=True,
        timeout=45,
    )
    (cad / f"p2-{mode}.log").write_text(result.stdout + result.stderr)
    return result


def _fresh(cad: Path) -> dict[str, object]:
    """Refill modified copies before asking the independent native DRC engine."""
    result = subprocess.run(
        [
            os.environ.get("KICAD_PYTHON", "/usr/bin/python3"),
            "-c",
            _FILL_SCRIPT,
            str(cad / BOARD.name),
        ],
        capture_output=True,
        text=True,
        timeout=45,
    )
    (cad / "p2-refill.log").write_text(result.stdout + result.stderr)
    assert result.returncode == 0, result.stderr
    cli = shutil.which("kicad-cli")
    assert cli is not None
    output = cad / "p2-drc.json"
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
            str(cad / BOARD.name),
        ],
        capture_output=True,
        text=True,
        timeout=45,
        env=dict(os.environ, KICAD_CONFIG_HOME=str(cad / "config"), LC_ALL="C", LANG="C"),
    )
    (cad / "p2-drc.log").write_text(result.stdout + result.stderr)
    data: object = json.loads(output.read_text())
    assert isinstance(data, dict)
    findings = any(data[k] for k in ("schematic_parity", "violations", "unconnected_items"))
    assert result.returncode == (5 if findings else 0), "exit/report disagreement"
    return data


@pytest.fixture(scope="module")
def p2_canonical(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict[str, object]]:
    cad = tmp_path_factory.mktemp("p2-ground-canonical") / "cad"
    shutil.copytree(CAD, cad)
    return cad, _fresh(cad)


@pytest.mark.schematic
def test_two_ground_domains_have_actual_complete_native_connections(
    p2_canonical: tuple[Path, dict[str, object]],
) -> None:
    cad, report = p2_canonical
    assert report["schematic_parity"] == [] and report["violations"] == []
    unfinished = json.dumps(report["unconnected_items"])
    assert "HOST_GND" not in unfinished and "TARGET_GND" not in unfinished
    assert report["unconnected_items"], "P2 is not a completed routing release"
    proof = _probe(cad, "grounds")
    assert proof.returncode == 0, proof.stdout + proof.stderr


@pytest.mark.schematic
@pytest.mark.parametrize("cap", [f"C{n}" for n in range(101, 116)])
def test_each_bypass_has_a_short_native_copper_path(
    p2_canonical: tuple[Path, dict[str, object]],
    cap: str,
) -> None:
    proof = _probe(p2_canonical[0], "bypass-" + cap)
    assert proof.returncode == 0, proof.stdout + proof.stderr


@pytest.mark.schematic
def test_a_reference_window_cannot_masquerade_as_a_short_bypass_loop(tmp_path: Path) -> None:
    """Still-connected copper can have an unwanted local return-plane void."""
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    _mutate(cad, "reference-window")
    report = _fresh(cad)
    assert report["schematic_parity"] == [] and report["violations"] == []
    proof = _probe(cad, "bypass-C110")
    assert proof.returncode != 0 and "local reference gap" in proof.stderr


def _mutate(cad: Path, mode: str) -> None:
    script = r"""
import sys,pcbnew as p
path,mode=sys.argv[1:];b=p.LoadBoard(path)
if mode in ('reference-window','benign-window'):
    z=p.ZONE(b);z.SetIsRuleArea(True);z.SetLayer(p.In1_Cu);z.SetZoneName('P2_fault_window')
    z.SetDoNotAllowTracks(False);z.SetDoNotAllowVias(False);z.SetDoNotAllowPads(False)
    z.SetDoNotAllowCopperPour(True);z.SetDoNotAllowFootprints(False)
    y=46 if mode=='reference-window' else 40
    o=z.Outline();o.NewOutline()
    for x,yy in [(51.2,y-.2),(51.4,y-.2),(51.4,y+.2),(51.2,y+.2)]:o.Append(p.FromMM(x),p.FromMM(yy))
    b.Add(z)
else:raise AssertionError(mode)
p.SaveBoard(path,b)
"""
    result = subprocess.run(
        [
            os.environ.get("KICAD_PYTHON", "/usr/bin/python3"),
            "-c",
            script,
            str(cad / BOARD.name),
            mode,
        ],
        capture_output=True,
        text=True,
        timeout=45,
    )
    (cad / "mutation.log").write_text(result.stdout + result.stderr)
    assert result.returncode == 0, result.stderr
