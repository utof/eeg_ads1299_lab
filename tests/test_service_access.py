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
    violation = violations[0]
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
