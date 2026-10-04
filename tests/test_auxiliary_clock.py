"""Clock repair geometry targets, not an impedance or physical timing qualification."""

import json
import os
import subprocess
from pathlib import Path

import pytest

from tests.test_auxiliary_placement import BOARD

MEASURE = r"""
import pcbnew as p,json,sys
assert p.Version()=='9.0.2'
b=p.LoadBoard(sys.argv[1]);items=list(b.GetTracks())
clock=[t for t in items if t.Type()==p.PCB_TRACE_T and t.GetNetname()=='MCU_SCLK']
response=[t for t in items if t.Type()==p.PCB_TRACE_T and t.GetNetname()=='MCU_MISO']
assert clock and response,'missing measured net'
# Native exact segment distances, including nonparallel spans; widths removed
# from the centerline distance. Pads/vias and electrical coupling are separate.
gaps=[]
for a in clock:
 for z in response:
  if a.GetLayer()!=z.GetLayer():continue
  aa=p.SEG(p.VECTOR2I(a.GetStart()),p.VECTOR2I(a.GetEnd()))
  zz=p.SEG(p.VECTOR2I(z.GetStart()),p.VECTOR2I(z.GetEnd()))
  gaps.append((aa.Distance(zz)-(a.GetWidth()+z.GetWidth())/2)/1e6)
print(json.dumps({'all_clock_trace_length_mm':sum(t.GetLength() for t in clock)/1e6,
 'clock_vias':sum(t.Type()==p.PCB_VIA_T and t.GetNetname()=='MCU_SCLK' for t in items),
 'minimum_same_layer_trace_edge_gap_to_MISO_mm':min(gaps),
 'physical_signal_integrity_qualified':False}))
"""


@pytest.mark.schematic
@pytest.mark.parametrize("criterion", ["length", "transitions", "separation"])
def test_reviewed_clock_geometry_does_not_return_to_the_long_close_route(
    tmp_path: Path, criterion: str
) -> None:
    result = subprocess.run(
        [os.environ.get("KICAD_PYTHON", "/usr/bin/python3"), "-c", MEASURE, str(BOARD)],
        capture_output=True,
        text=True,
        timeout=45,
    )
    (tmp_path / "clock-geometry.log").write_text(result.stdout + result.stderr)
    assert result.returncode == 0, result.stdout + result.stderr
    data: object = json.loads(result.stdout)
    assert isinstance(data, dict)
    if criterion == "length":
        length: object = data["all_clock_trace_length_mm"]
        assert isinstance(length, (int, float)) and 0 < length <= 75, "long clock detour"
    elif criterion == "transitions":
        vias: object = data["clock_vias"]
        assert isinstance(vias, int) and vias <= 4, "excess clock layer changes"
    else:
        gap: object = data["minimum_same_layer_trace_edge_gap_to_MISO_mm"]
        assert isinstance(gap, (int, float)) and gap >= 0.60, "clock hugs MISO"
    assert data["physical_signal_integrity_qualified"] is False


def test_only_clock_copper_changes_in_the_review_repair() -> None:
    import hashlib
    import re

    from tests.test_auxiliary_placement import ROOT
    from tests.test_pcb_power import _form_end

    raw: object = json.loads(
        (ROOT / "tests/fixtures/auxiliary_clock_before_review.json").read_text()
    )
    assert isinstance(raw, dict)
    text = BOARD.read_text()
    net = re.search(r'\(net (\d+) "MCU_SCLK"\)', text)
    assert net is not None
    records = []
    for match in re.finditer(r"\((footprint|segment|via)\s", text):
        form = text[match.start() : _form_end(text, match.start())]
        if match[1] != "footprint" and re.search(rf"\(net {net[1]}\)", form):
            continue
        ident = re.search(r'\(uuid "([^"]+)"', form)
        assert ident is not None
        records.append((ident[1], hashlib.sha256(form.encode()).hexdigest()))
    assert len(records) == raw["nonclock_copper_and_all_footprints_count"] == 831
    digest = hashlib.sha256(json.dumps(sorted(records), separators=(",", ":")).encode()).hexdigest()
    assert digest == raw["nonclock_copper_and_all_footprints_sha256"]


def _measure_board(path: Path) -> dict[str, object]:
    result = subprocess.run(
        [os.environ.get("KICAD_PYTHON", "/usr/bin/python3"), "-c", MEASURE, str(path)],
        capture_output=True,
        text=True,
        timeout=45,
    )
    (path.parent / "clock-metrics.log").write_text(result.stdout + result.stderr)
    assert result.returncode == 0, result.stdout + result.stderr
    raw: object = json.loads(result.stdout)
    assert isinstance(raw, dict)
    return raw


@pytest.mark.schematic
def test_original_clock_is_connected_but_fails_review_geometry(tmp_path: Path) -> None:
    import re
    import shutil

    from tests.test_auxiliary_ground import _fresh
    from tests.test_auxiliary_placement import CAD, ROOT
    from tests.test_pcb_power import _form_end

    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    text = (cad / BOARD.name).read_text()
    net = re.search(r'\(net (\d+) "MCU_SCLK"\)', text)
    assert net is not None
    cuts = []
    for match in re.finditer(r"\((segment|via)\s", text):
        end = _form_end(text, match.start())
        if re.search(rf"\(net {net[1]}\)", text[match.start() : end]):
            cuts.append((match.start(), end))
    for start, end in reversed(cuts):
        text = text[:start] + text[end:]
    raw: object = json.loads(
        (ROOT / "tests/fixtures/auxiliary_clock_before_review.json").read_text()
    )
    assert isinstance(raw, dict)
    forms: object = raw["original_clock_forms"]
    assert isinstance(forms, list) and len(forms) == 26
    pieces: list[str] = []
    for item in forms:
        assert isinstance(item, str)
        pieces.append(item)
    end = text.rfind(")")
    (cad / BOARD.name).write_text(text[:end] + "\n".join(pieces) + "\n" + text[end:])
    report = _fresh(cad)
    assert all(report[k] == [] for k in ("schematic_parity", "violations", "unconnected_items"))
    data = _measure_board(cad / BOARD.name)
    length, gap = (
        data["all_clock_trace_length_mm"],
        data["minimum_same_layer_trace_edge_gap_to_MISO_mm"],
    )
    assert isinstance(length, (int, float)) and length > 85
    assert isinstance(gap, (int, float)) and gap < 0.24
    assert data["clock_vias"] == 5


@pytest.mark.schematic
@pytest.mark.parametrize("edit", ["reverse", "split"])
def test_clock_metrics_accept_equivalent_copper(tmp_path: Path, edit: str) -> None:
    import shutil

    from tests.test_auxiliary_ground import _fresh
    from tests.test_auxiliary_placement import CAD

    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    script = r"""
import pcbnew as p,sys
b=p.LoadBoard(sys.argv[1]);items=list(b.GetTracks())
t=max((t for t in items if t.Type()==p.PCB_TRACE_T and t.GetNetname()=='MCU_SCLK'),key=lambda t:t.GetLength())
a,z=p.VECTOR2I(t.GetStart()),p.VECTOR2I(t.GetEnd())
if sys.argv[2]=='reverse':t.SetStart(z);t.SetEnd(a)
else:
 mid=p.VECTOR2I((a.x+z.x)//2,(a.y+z.y)//2);t.SetEnd(mid)
 n=p.PCB_TRACK(b);n.SetStart(mid);n.SetEnd(z);n.SetLayer(t.GetLayer());n.SetWidth(t.GetWidth());n.SetNet(t.GetNet());b.Add(n)
p.SaveBoard(sys.argv[1],b)
"""
    before = _measure_board(cad / BOARD.name)
    result = subprocess.run(
        [
            os.environ.get("KICAD_PYTHON", "/usr/bin/python3"),
            "-c",
            script,
            str(cad / BOARD.name),
            edit,
        ],
        capture_output=True,
        text=True,
        timeout=45,
    )
    (cad / "clock-edit.log").write_text(result.stdout + result.stderr)
    assert result.returncode == 0, result.stdout + result.stderr
    report = _fresh(cad)
    assert all(report[k] == [] for k in ("schematic_parity", "violations", "unconnected_items"))
    after = _measure_board(cad / BOARD.name)
    assert before == after
