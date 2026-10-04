"""Native work budget and whole-plane oracle for the P3 reference fast path."""

import json
import os
import subprocess
from pathlib import Path

import pytest

from tests.auxiliary_routing_probe import SCRIPT
from tests.test_auxiliary_placement import BOARD, ROOT

_AUDIT = r"""
import contextlib,io,json,sys
import pcbnew as p
assert p.Version()=='9.0.2'
work=[]
original=p.SHAPE_POLY_SET.BooleanSubtract
def counted(self,other):
    work.append(other.FullPointCount())
    return original(self,other)
p.SHAPE_POLY_SET.BooleanSubtract=counted
scope={'__name__':'__main__'}
output=io.StringIO()
with contextlib.redirect_stdout(output):
    exec(compile(SOURCE,'<committed-P3-probe>','exec'),scope)
p.SHAPE_POLY_SET.BooleanSubtract=original
board=scope['b'];planes=scope['planes']
traces=[t for t in board.GetTracks() if t.Type()==p.PCB_TRACE_T and t.GetNetname() not in planes]
naive=sum(2*planes['HOST_GND' if t.GetNetname().startswith('HOST_') else 'TARGET_GND']
          .GetFilledPolysList(p.In1_Cu).FullPointCount() for t in traces)
# Same observable gap inventory, derived without using the group's fast-path result.
# The per-trace kernel still subtracts native whole-plane geometry, not samples.
expected=[]
for t in traces:
    assert scope['uncovered'](t,p.FromMM(.10)).Area()/1e12<=1e-6
    full=scope['uncovered'](t,t.GetWidth()).Area()/1e12
    if full>1e-6:
        expected.append({'track':t.m_Uuid.AsString(),'net':t.GetNetname(),
            'layer':board.GetLayerName(t.GetLayer()),'uncovered_full_width_area_mm2':full})
report=json.loads(output.getvalue())
assert report['full_width_edge_gaps_pending_review']==expected,'per-trace oracle mismatch'
# Native primitive characterization: overlapping full-width/spine outlines and
# duplicated rectangles must not cancel a small central hole (even-odd trap).
def rectangle(x0,y0,x1,y1):
    s=p.SHAPE_POLY_SET();s.NewOutline()
    for x,y in [(x0,y0),(x0,y1),(x1,y1),(x1,y0)]:s.Append(p.FromMM(x),p.FromMM(y))
    return s
reference=rectangle(0,0,4,4);hole=rectangle(1.98,1.98,2.02,2.02)
reference.BooleanSubtract(hole)
for copies in (1,2,3):
    full=rectangle(1,1.9,3,2.1);spine=rectangle(1,1.95,3,2.05)
    group=p.SHAPE_POLY_SET()
    for _ in range(copies):
        group.AddOutline(full.Outline(0));group.AddOutline(spine.Outline(0))
    group.BooleanSubtract(reference)
    assert group.OutlineCount()==1 and group.Area()==hole.Area(),'overlap erased a real void'

print(json.dumps({'boolean_subtraction_operand_vertices':sum(work),
 'whole_plane_naive_operand_vertices':naive,'same_per_trace_gap_inventory':True,
 'checked_trace_projections':2*len(traces),'nested_outline_controls':3,'board_saved':False}))
"""


@pytest.mark.schematic
def test_reference_screen_reduces_polygon_work_without_changing_gap_inventory(
    tmp_path: Path,
) -> None:
    """Deterministic native work, not a flaky elapsed-time test or relaxed geometry limit."""
    script = "SOURCE = " + repr(SCRIPT) + "\n" + _AUDIT
    result = subprocess.run(
        [
            os.environ.get("KICAD_PYTHON", "/usr/bin/python3"),
            "-c",
            script,
            str(BOARD),
            "reference",
            str(ROOT / "tests/fixtures/auxiliary_p3_pending_edges.json"),
        ],
        capture_output=True,
        text=True,
        timeout=45,
    )
    (tmp_path / "reference-work.log").write_text(result.stdout + result.stderr)
    assert result.returncode == 0, result.stdout + result.stderr
    data: object = json.loads(result.stdout)
    assert isinstance(data, dict)
    actual, naive = (
        data["boolean_subtraction_operand_vertices"],
        data["whole_plane_naive_operand_vertices"],
    )
    assert isinstance(actual, int) and isinstance(naive, int) and naive > 0
    assert actual <= naive // 2, "P3 probe repeats whole-plane work for already-covered routes"
    assert data["same_per_trace_gap_inventory"] is True
