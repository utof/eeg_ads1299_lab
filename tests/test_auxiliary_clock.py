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
        length = data["all_clock_trace_length_mm"]
        assert isinstance(length, (int, float)) and 0 < length <= 75, "long clock detour"
    elif criterion == "transitions":
        assert data["clock_vias"] <= 4, "excess clock layer changes"
    else:
        gap = data["minimum_same_layer_trace_edge_gap_to_MISO_mm"]
        assert isinstance(gap, (int, float)) and gap >= 0.60, "clock hugs MISO"
    assert data["physical_signal_integrity_qualified"] is False
