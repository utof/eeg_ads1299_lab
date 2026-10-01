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
    row = next(item for item in bom["items"] if item["id"] == "service_header")
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
