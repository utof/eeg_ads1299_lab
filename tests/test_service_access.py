"""C4 service wiring and geometry controls; no physical or powered qualification."""

import gzip
import json
import os
import subprocess
from pathlib import Path

import pytest

from hardware.rev_a import load_documents, parse_schematic_xml

ROOT = Path(__file__).resolve().parents[1]


def test_service_profile_and_bom_define_a_separate_six_way_port() -> None:
    profile, bom, _ = load_documents()
    assert "J_SERVICE" in profile["interface_headers"]
    service = profile["interface_headers"]["J_SERVICE"]
    assert service["mpn"] == "B6B-XH-A(LF)(SN)"
    assert service["pin_map"] == {
        "1": "DGND",
        "2": "DVDD",
        "3": "DVDD",
        "4": "AVDD",
        "5": "DGND",
        "6": "NC",
    }
    row = next(item for item in bom["line_items"] if item["id"] == "service_header")
    assert row["references"] == ["J_SERVICE"] and row["quantity"] == 1
    assert row["population"] == "fit" and row["mpn"] == service["mpn"]
    assert not any(profile["gates"].values())


def test_service_native_fixture_has_separate_feed_sense_and_explicit_nc() -> None:
    graph = parse_schematic_xml(
        gzip.decompress((ROOT / "tests/fixtures/rev_a_netlist.xml.gz").read_bytes()).decode()
    )
    assert "J_SERVICE" in graph.parts
    assert graph.parts["J_SERVICE"].native_ref == "J3"
    for pin, other in {"1": "33", "2": "48", "3": "50", "4": "19", "5": "49"}.items():
        assert graph.nets[("J_SERVICE", pin)] == graph.nets[("U1", other)]
    nc = graph.nets[("J_SERVICE", "6")]
    assert list(graph.nets.values()).count(nc) == 1
    assert graph.pin_types[("J_SERVICE", "6")] == "passive+no_connect"


@pytest.mark.schematic
def test_service_native_footprint_has_actual_six_pad_placement() -> None:
    script = r"""
import sys, pcbnew as p
assert p.Version() == '9.0.2'
b = p.LoadBoard(sys.argv[1])
parts = {f.GetReference(): f for f in b.GetFootprints()}
assert 'J3' in parts, 'missing physical J3 service connector'
f = parts['J3']
assert (f.GetPosition().x,f.GetPosition().y)==(75000000,15000000)
assert f.GetOrientationDegrees()==180
pads = {a.GetNumber():a for a in f.Pads()}
assert len(pads)==6
for n,net in {'1':'GND','2':'DVDD','3':'DVDD','4':'AVDD','5':'GND','6':'unconnected-(J3-Pad6)'}.items():
    a=pads[n]
    assert a.GetNetname()==net and a.GetDrillSize().x==950000
    assert a.GetAttribute()==p.PAD_ATTRIB_PTH
# The underside backing must not cover pads, tracks or vias. AABB distances
# conservatively bound these outer-layer shapes, excluding inner copper/fill.
import math
rectangles=[(59,11.5,61,18),(76.5,11.5,78.5,18)]
items=[a for fp in b.GetFootprints() for a in fp.Pads() if a.IsOnLayer(p.B_Cu)]
items += [t for t in b.GetTracks() if t.IsOnLayer(p.B_Cu)]
for x0,y0,x1,y1 in rectangles:
    distances=[]
    for item in items:
        bb=item.GetBoundingBox()
        a,c,e,g=[v/1e6 for v in (bb.GetX(),bb.GetY(),bb.GetRight(),bb.GetBottom())]
        distances.append(math.hypot(max(x0-e,a-x1,0),max(y0-g,c-y1,0)))
    assert min(distances)>=0.5, min(distances)
"""
    result = subprocess.run(
        [
            os.environ.get("KICAD_PYTHON", "/usr/bin/python3"),
            "-c",
            script,
            str(ROOT / "hardware/rev_a/layout/rev_a.kicad_pcb"),
        ],
        capture_output=True,
        text=True,
        timeout=45,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.native
def test_service_backing_supports_exist_below_unperforated_board(tmp_path: Path) -> None:
    from tests.test_carrier_cad import _overlap

    for x in (59.5, 77):
        assert (
            abs(_overlap(tmp_path, "carrier();", f"translate([{x},13,-2.7]) cube(1);") - 1) < 1e-4
        )


@pytest.mark.parametrize("pin,net", [("2", "DVDD"), ("3", "DVDD"), ("4", "AVDD")])
@pytest.mark.schematic
def test_each_service_feed_or_sense_cut_is_a_native_disconnection(
    tmp_path: Path, pin: str, net: str
) -> None:
    """Intact supply/sense elsewhere must not conceal a broken service pad escape."""
    import re
    import shutil

    from tests.test_pcb_placement import BOARD, CAD, _native_report

    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    text = BOARD.read_text()
    x = {"2": "72.5", "3": "70", "4": "67.5"}[pin]
    pattern = rf'\(segment \(start {re.escape(x)} 15\).*?\(uuid "[^"]+"\)\)'
    changed, count = re.subn(pattern, "", text, count=1)
    assert count == 1, "service pad escape changed; independently review the cut target"
    (cad / "rev_a.kicad_pcb").write_text(changed)
    report = _native_report(cad)
    assert report["schematic_parity"] == []
    violations = report["violations"]
    assert isinstance(violations, list) and len(violations) == 1
    violation: object = violations[0]
    assert isinstance(violation, dict) and violation["type"] == "track_dangling"
    assert f"PTH pad {pin} [{net}] of J3" in json.dumps(report["unconnected_items"])


@pytest.mark.parametrize("edit", ["reverse", "split"])
@pytest.mark.schematic
def test_service_route_benign_edits_remain_connected(tmp_path: Path, edit: str) -> None:
    import shutil

    from tests.test_pcb_placement import BOARD, CAD, _native_report

    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    text = BOARD.read_text()
    old = "(start 70 15) (end 70 17)"
    assert text.count(old) == 1
    replacement = "(start 70 17) (end 70 15)" if edit == "reverse" else "(start 70 15) (end 70 16)"
    text = text.replace(old, replacement)
    if edit == "split":
        addition = (
            '(segment (start 70 16) (end 70 17) (width 0.2) (layer "F.Cu") (net 17) '
            '(uuid "f77012c1-0402-4e74-83a7-662c389acbab"))\n'
        )
        position = text.rfind(")")
        text = text[:position] + addition + text[position:]
    (cad / "rev_a.kicad_pcb").write_text(text)
    report = _native_report(cad)
    assert all(report[key] == [] for key in ("schematic_parity", "violations", "unconnected_items"))


@pytest.mark.native
@pytest.mark.parametrize("lift", [0, 5, 20])
def test_service_mating_column_clears_the_existing_carrier(tmp_path: Path, lift: int) -> None:
    """Rigid vertical approach samples, not every tilted path or force/fit proof."""
    from tests.test_carrier_cad import _overlap

    obstacles = """
    union() { frame();
        for (p=ports()) translate([p[0],p[1],2.54]) plug(p==ports()[0] ? 0 : 1);
    }
    """
    envelope = f"translate([59.5,11,{lift}]) cube([18.5,8,12]);"
    assert abs(_overlap(tmp_path, obstacles, envelope)) < 1e-4
    assert (
        abs(_overlap(tmp_path, "carrier();", "translate([61.5,14,-3.5]) cube([14.5,2,3.5]);"))
        < 1e-4
    )


@pytest.mark.native
def test_service_clearance_screen_rejects_receiver_intrusion(tmp_path: Path) -> None:
    from tests.test_carrier_cad import _overlap

    assert (
        _overlap(
            tmp_path,
            "translate([81.27,38.43,0]) receiver(0);",
            "translate([74.1,24.1,0.1]) cube([18.5,8,12]);",
        )
        > 0.1
    )


@pytest.mark.native
def test_service_north_exit_does_not_cross_ribbon_or_frame(tmp_path: Path) -> None:
    from tests.test_carrier_cad import _overlap

    obstacles = """
    union() {frame();
        for(p=ports()) translate([p[0],p[1],2.54]) cable_envelope();
    }
    """
    assert abs(_overlap(tmp_path, obstacles, "translate([59.5,4,12]) cube([18.5,15,6]);")) < 1e-4


# Independent planned cable specification, not an automatically qualified assembly.
EXPECTED_CABLE = json.loads(r"""
{
  "revision": "C4",
  "status": "routed_afe_access_not_powered_release",
  "afe_reference": "J3",
  "auxiliary_reference": "J104",
  "header_mpn_each_board": "B6B-XH-A(LF)(SN)",
  "housing": {
    "mpn": "XHP-6",
    "quantity": 2
  },
  "contact": {
    "mpn": "SXH-001T-P0.6",
    "quantity": 10
  },
  "wire_target": {
    "awg": 24,
    "conductor_count": 5,
    "insulation_OD_mm": [
      0.9,
      1.9
    ],
    "length_between_housing_wire_faces_mm": 150,
    "length_tolerance_mm": 5,
    "supplier_wire_grade_and_crimp_process_qualified": false
  },
  "continuity_afe_pin_to_aux_pin": [
    [
      1,
      1
    ],
    [
      2,
      2
    ],
    [
      3,
      3
    ],
    [
      4,
      4
    ],
    [
      5,
      5
    ]
  ],
  "empty_housing_cavities_each": [
    6
  ],
  "rails": {
    "1": "GND",
    "2": "DVDD_FEED_OUT",
    "3": "DVDD_SENSE",
    "4": "AVDD_SENSE",
    "5": "GND"
  },
  "feed_sense_join": "AFE_local_rail_only_not_auxiliary",
  "acceptance": "test_detached_cable_1_to_1_no_shorts_then_unpowered_assembled_continuity",
  "power_removed_before_mating": true,
  "retention": "XH_friction_lock_plus_independent_external_cable_restraint_pending_physical_fit",
  "purchase_or_powered_approval": false
}
""")


def _checked_service_plan(data: object) -> None:
    # Keep types, keys and finite numeric values, not Python's True == 1 shortcut.
    if json.dumps(data, sort_keys=True, allow_nan=False) != json.dumps(
        EXPECTED_CABLE, sort_keys=True
    ):
        raise ValueError("C4 service harness differs from reviewed target")


def test_service_harness_matches_both_board_endpoints() -> None:
    from hardware.rev_a import parse_auxiliary_contract

    data = json.loads((ROOT / "hardware/rev_a/service_c4.json").read_text())
    _checked_service_plan(data)
    contract = parse_auxiliary_contract(
        (ROOT / "hardware/rev_a/auxiliary/contract.json").read_text()
    )
    part = contract.parts["AFE_RAIL_ACCESS"]
    assert part.reference == "J104" and part.mpn == "B6B-XH-A(LF)(SN)"
    assert [part.pins[str(n)].net for n in range(1, 7)] == [
        "TARGET_GND",
        "AFE_DVDD",
        "AFE_DVDD_SENSE",
        "AFE_AVDD_SENSE",
        "TARGET_GND",
        None,
    ]


@pytest.mark.parametrize(
    "fault", ["feed_sense_swap", "populated_nc", "auxiliary_join", "hot_mate", "approval"]
)
def test_service_plan_rejects_wrong_or_unapproved_harness(fault: str) -> None:
    data = json.loads((ROOT / "hardware/rev_a/service_c4.json").read_text())
    if fault == "feed_sense_swap":
        data["continuity_afe_pin_to_aux_pin"][1:3] = [[2, 3], [3, 2]]
    elif fault == "populated_nc":
        data["empty_housing_cavities_each"] = []
    elif fault == "auxiliary_join":
        data["feed_sense_join"] = "short at auxiliary"
    elif fault == "hot_mate":
        data["power_removed_before_mating"] = False
    else:
        data["purchase_or_powered_approval"] = True
    with pytest.raises(ValueError):
        _checked_service_plan(data)


def test_auxiliary_native_note_identifies_installed_service_access() -> None:
    """The editable schematic must not send a fresh agent back to missing-J3 work."""
    text = (ROOT / "hardware/rev_a/auxiliary/auxiliary.kicad_sch").read_text()
    assert "AFE J3 present; use inspected C4 cable." in text
    assert "AFE mating connector/pads NOT YET ADDED." not in text
