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
def test_a_reference_window_cannot_masquerade_as_a_short_bypass_loop(
    tmp_path: Path,
    p2_canonical: tuple[Path, dict[str, object]],
) -> None:
    """Still-connected copper can have an unwanted local return-plane void."""
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    _mutate(cad, "reference-window")
    report = _fresh(cad)
    assert report["schematic_parity"] == [] and report["violations"] == []
    assert _missing_count(report) == _missing_count(p2_canonical[1])
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
elif mode.startswith(('cut-','reverse-','split-')):
    action,ref=mode.split('-');f=next(f for f in b.GetFootprints() if f.GetReference()==ref)
    pad=next(a for a in f.Pads() if a.GetNumber()=='1');pt=pad.GetPosition()
    tracks=[t for t in b.GetTracks() if t.Type()==p.PCB_TRACE_T and t.GetNetCode()==pad.GetNetCode()
            and (t.GetStart()==pt or t.GetEnd()==pt)]
    assert len(tracks)==1
    t=tracks[0]
    if action=='cut':b.Remove(t)
    elif action=='reverse':
        a,c=p.VECTOR2I(t.GetStart()),p.VECTOR2I(t.GetEnd());t.SetStart(c);t.SetEnd(a)
    else:
        a,c=p.VECTOR2I(t.GetStart()),p.VECTOR2I(t.GetEnd());mid=p.VECTOR2I((a.x+c.x)//2,(a.y+c.y)//2)
        t.SetEnd(mid);tail=p.PCB_TRACK(b);tail.SetStart(mid);tail.SetEnd(c)
        tail.SetWidth(t.GetWidth());tail.SetLayer(t.GetLayer());tail.SetNet(t.GetNet());b.Add(tail)
elif mode.startswith('remove-plane-'):
    net=mode.removeprefix('remove-plane-')
    z=next(z for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname()==net);b.Remove(z)
elif mode=='remove-return-via':
    v=next(t for t in b.GetTracks() if t.Type()==p.PCB_VIA_T and t.GetPosition()==p.VECTOR2I(p.FromMM(48.125),p.FromMM(46)))
    assert v.GetNetname()=='TARGET_GND';b.Remove(v)
elif mode=='wrong-reference-layer':
    z=next(z for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname()=='HOST_GND');z.SetLayer(p.In2_Cu)
elif mode=='remove-mount-exclusion':
    z=next(z for z in b.Zones() if z.GetZoneName()=='MOUNT_NO_COPPER_H4');b.Remove(z)
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


def _missing_count(report: dict[str, object]) -> int:
    raw = report["unconnected_items"]
    assert isinstance(raw, list)
    rows: list[object] = raw
    return len(rows)


@pytest.mark.schematic
@pytest.mark.parametrize("cap", [f"C{n}" for n in range(101, 116)])
def test_native_cut_of_each_local_bypass_is_detected(
    tmp_path: Path,
    p2_canonical: tuple[Path, dict[str, object]],
    cap: str,
) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    _mutate(cad, "cut-" + cap)
    report = _fresh(cad)
    assert report["schematic_parity"] == [] and report["violations"] == []
    assert _missing_count(report) == _missing_count(p2_canonical[1]) + 1
    proof = _probe(cad, "bypass-" + cap)
    assert proof.returncode != 0 and "local bypass path" in proof.stderr


@pytest.mark.schematic
@pytest.mark.parametrize("domain", ["HOST_GND", "TARGET_GND"])
def test_removing_either_reference_is_a_native_ground_failure(tmp_path: Path, domain: str) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    _mutate(cad, "remove-plane-" + domain)
    report = _fresh(cad)
    assert report["schematic_parity"] == []
    assert domain in json.dumps(report["unconnected_items"])
    proof = _probe(cad, "grounds")
    assert proof.returncode != 0 and "two separate ground reference zones" in proof.stderr


@pytest.mark.schematic
@pytest.mark.parametrize(
    "mode,reason",
    [
        ("remove-return-via", "ground access"),
        ("wrong-reference-layer", "reference layer"),
        ("remove-mount-exclusion", "mounting copper exclusion"),
    ],
)
def test_native_return_and_mount_faults_fail(tmp_path: Path, mode: str, reason: str) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    _mutate(cad, mode)
    report = _fresh(cad)
    assert report["schematic_parity"] == []
    if mode == "remove-return-via":
        assert "TARGET_GND" in json.dumps(report["unconnected_items"])
        assert "track_dangling" in json.dumps(report["violations"])
    proof = _probe(cad, "grounds")
    assert proof.returncode != 0 and reason in proof.stderr


@pytest.mark.schematic
@pytest.mark.parametrize("mode", ["reverse-C110", "split-C110", "benign-window"])
def test_benign_copper_representation_or_remote_void_remains_accepted(
    tmp_path: Path,
    p2_canonical: tuple[Path, dict[str, object]],
    mode: str,
) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    _mutate(cad, mode)
    report = _fresh(cad)
    assert report["schematic_parity"] == [] and report["violations"] == []
    assert _missing_count(report) == _missing_count(p2_canonical[1])
    for label in ("grounds", "bypass-C110"):
        proof = _probe(cad, label)
        assert proof.returncode == 0, proof.stdout + proof.stderr
