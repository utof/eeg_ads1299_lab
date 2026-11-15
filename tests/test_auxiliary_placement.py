"""Placement invariants survive P3 connected routing; never a fabrication pass."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from hardware.rev_a import parse_auxiliary_contract

ROOT = Path(__file__).resolve().parents[1]
CAD = ROOT / "hardware/rev_a/auxiliary"
BOARD = CAD / "auxiliary.kicad_pcb"


def test_auxiliary_placement_is_present_and_explicitly_unreleased() -> None:
    text = BOARD.read_text()
    assert "P3 CONNECTED DRAFT - NOT FOR FABRICATION" in text
    assert "(footprint " in text and "(gr_rect" in text
    assert "(segment " in text and "(via " in text


def _pad_center(text: str, reference: str, number: str) -> tuple[float, float]:
    """Board position from the footprint origin/rotation and the local pad offset."""
    import math
    import re

    from tests.test_pcb_power import _form_end

    marker = text.index(f'(property "Reference" "{reference}"')
    start = text.rindex("(footprint ", 0, marker)
    form = text[start : _form_end(text, start)]
    origin = re.search(
        r"\(footprint \"[^\"]+\"[\s\S]*?\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)", form
    )
    pad = re.search(rf'\(pad "{number}" [^\n]*\n?\s*\(at ([-\d.]+) ([-\d.]+)', form)
    assert origin is not None and pad is not None, (reference, number)
    x0, y0 = float(origin[1]), float(origin[2])
    angle = math.radians(float(origin[3] or 0))
    x, y = float(pad[1]), float(pad[2])
    # KiCad: y grows downward and a positive orientation rotates counterclockwise.
    return (
        x0 + x * math.cos(angle) + y * math.sin(angle),
        y0 - x * math.sin(angle) + y * math.cos(angle),
    )


def _front_silk(text: str) -> list[tuple[str, float, float]]:
    import re

    pattern = r'\(gr_text "([^"]*)"\s*\(at ([-\d.]+) ([-\d.]+)[^)]*\)\s*\(layer "F\.SilkS"\)'
    return [(m[1], float(m[2]), float(m[3])) for m in re.finditer(pattern, text)]


@pytest.mark.parametrize(
    "label,reference,number,other",
    [
        ("+5V", "J105", "1", "2"),  # WIRE-03: no reverse-polarity part behind J105
        ("GND", "J105", "2", "1"),
        ("1", "J102", "1", "22"),
        ("22", "J102", "22", "1"),
        ("1", "J101", "1", "20"),
        ("1", "J103", "1", "4"),
        ("4", "J103", "4", "1"),
        ("1", "J106", "1", "2"),
    ],
)
def test_solder_tail_lands_carry_pin_and_polarity_silk(
    label: str, reference: str, number: str, other: str
) -> None:
    import math

    text = BOARD.read_text()
    pad, far = _pad_center(text, reference, number), _pad_center(text, reference, other)
    near = [
        (math.dist(pad, (x, y)), math.dist(far, (x, y)))
        for text_label, x, y in _front_silk(text)
        if text_label == label
    ]
    # One label within 3.5 mm of its own pad and clearly closer to it than to
    # the opposite end of the same tail group, so the marking is unambiguous.
    assert any(own <= 3.5 and own < opposite for own, opposite in near), (label, reference)


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
    assert data["unconnected_items"] == []
    assert result.returncode == 0


def _probe(cad: Path, mode: str, out: Path) -> subprocess.CompletedProcess[str]:
    from tests.auxiliary_placement_probe import SCRIPT

    result = subprocess.run(
        [os.environ.get("KICAD_PYTHON", "/usr/bin/python3"), "-c", SCRIPT, str(cad), mode],
        capture_output=True,
        text=True,
        timeout=45,
    )
    (out / f"geometry-{mode}.log").write_text(result.stdout + result.stderr)
    return result


@pytest.mark.schematic
@pytest.mark.parametrize("mode", ["canonical", "benign", "mount-benign"])
def test_auxiliary_native_placement_geometry(tmp_path: Path, mode: str) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    result = _probe(cad, mode, tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    contract = parse_auxiliary_contract((cad / "contract.json").read_text())
    series = {"R117", "R118", "R119", "R120"}
    present = {part.reference for part in contract.parts.values()} & series
    assert present in (set(), series), "partial series inventory"
    assert len(contract.parts) == 48 + len(present)
    assert sum(len(part.pins) for part in contract.parts.values()) == 212 + 2 * len(present)
    assert json.loads(result.stdout)["all_pads"] == 216 + 2 * len(present)


@pytest.mark.schematic
@pytest.mark.parametrize(
    "mode,reason",
    [
        ("far-bypass", "bypass distance"),
        ("host-in-target", "host side"),
        ("blocked-mating", "mating/termination"),
        ("mount-over-pad", "mount copper"),
        ("mount-into-access", "mount/termination clearance"),
        ("mount-touch-access", "mount/termination clearance"),
        ("mount-near-access", "mount/termination clearance"),
        ("wrong-sense", "net mismatch"),
        ("weaken-keepout", "keepout policy"),
        ("outer-only-barrier", "barrier layers"),
        ("mirrored-buffer", "bypass distance"),
    ],
)
def test_independent_auxiliary_geometry_faults_fail(tmp_path: Path, mode: str, reason: str) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    result = _probe(cad, mode, tmp_path)
    assert result.returncode != 0 and reason in result.stderr, result.stdout + result.stderr


@pytest.mark.schematic
@pytest.mark.parametrize(
    "fault,expected",
    [
        ("barrier", "items_not_allowed"),
        ("inner-barrier", "items_not_allowed"),
        ("domain-gap", "HOST TARGET external copper separation"),
        ("fine-pitch", "U111 selected 0.5mm-pitch native land"),
    ],
)
def test_auxiliary_native_rules_reject_real_copper_faults(
    tmp_path: Path,
    fault: str,
    expected: str,
) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    script = r"""
import sys,pcbnew as p
assert p.Version()=='9.0.2'
path,fault=sys.argv[1:];b=p.LoadBoard(path)
if fault=='fine-pitch':
    f=next(f for f in b.GetFootprints() if f.GetReference()=='U111')
    next(z for z in f.Pads() if z.GetNumber()=='2').Move(p.VECTOR2I(0,-20000))
else:
    tr=p.PCB_TRACK(b);tr.SetLayer(p.In1_Cu if fault=='inner-barrier' else p.B_Cu);tr.SetWidth(p.FromMM(.2))
    x=22 if fault in ('barrier','inner-barrier') else 29
    tr.SetStart(p.VECTOR2I(p.FromMM(x),p.FromMM(39)))
    tr.SetEnd(p.VECTOR2I(p.FromMM(x),p.FromMM(41)))
    tr.SetNet(b.FindNet('TARGET_GND'));b.Add(tr)
    if fault=='domain-gap':
        via=p.PCB_VIA(b);via.SetPosition(p.VECTOR2I(p.FromMM(27),p.FromMM(40)))
        via.SetWidth(p.FromMM(.6));via.SetDrill(p.FromMM(.3))
        via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(b.FindNet('HOST_3V3'));b.Add(via)
p.SaveBoard(path,b)
"""
    result = subprocess.run(
        [
            os.environ.get("KICAD_PYTHON", "/usr/bin/python3"),
            "-c",
            script,
            str(cad / BOARD.name),
            fault,
        ],
        capture_output=True,
        text=True,
        timeout=45,
    )
    (tmp_path / "mutation.log").write_text(result.stdout + result.stderr)
    assert result.returncode == 0, result.stderr
    cli = shutil.which("kicad-cli")
    assert cli is not None
    report = tmp_path / "drc.json"
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
        capture_output=True,
        text=True,
        timeout=45,
    )
    (tmp_path / "drc.log").write_text(result.stdout + result.stderr)
    data: object = json.loads(report.read_text())
    assert isinstance(data, dict)
    assert result.returncode == 5 and data["schematic_parity"] == []
    violations: object = data["violations"]
    assert expected in json.dumps(violations)
