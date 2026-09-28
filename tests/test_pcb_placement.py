"""Native placement-stage checks: no fabrication or routed-copper approval."""

import json
import math
import os
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from hardware.rev_a import load_documents, parse_schematic_xml, validate_schematic
from tests.test_schematic_native import CAD, _export

BOARD = CAD / "rev_a.kicad_pcb"
NS = {"i": "http://webstds.ipc.org/2581"}
# Pad-to-pad distances are draft placement budgets, NOT datasheet guarantees.
LOCAL_CAPS = {
    "C8": ("30", 4.5),
    "C9": ("55", 3.5),
    "C10": ("26", 4.5),
    "C11": ("19", 4.5),
    "C12": ("21", 4.5),
    "C13": ("22", 4.5),
    "C14": ("56", 3.5),
    "C15": ("59", 3.5),
    "C16": ("54", 4.5),
    "C17": ("48", 3.5),
    "C18": ("50", 3.5),
    "C23": ("28", 4.5),
    "C24": ("55", 7.0),
    "C25": ("24", 4.5),
    "C27": ("54", 7.0),
}


def test_editable_board_is_present_but_not_presented_as_routed() -> None:
    text = BOARD.read_text()
    assert "PLACEMENT DRAFT - NOT FOR FABRICATION" in text
    assert text.count('(footprint "') == 68
    assert text.count('(pad "') == 245
    assert text.count(" dnp)") == 8
    assert "(gr_rect " in text
    assert '(1 "In1.Cu"' in text and '(2 "In2.Cu"' in text
    assert not any(token in text for token in ("(segment ", "(via ", "(zone "))


def _native(cad: Path, args: list[str], expected: int) -> None:
    cli = shutil.which("kicad-cli")
    assert cli is not None, "actual placement checks require KiCad"
    result = subprocess.run(
        [cli, *args],
        capture_output=True,
        text=True,
        timeout=45,
        env=dict(os.environ, KICAD_CONFIG_HOME=str(cad / "config"), LC_ALL="C", LANG="C"),
    )
    (cad / (args[1] + ".log")).write_text(result.stdout + result.stderr)
    assert result.returncode == expected, result.stdout + result.stderr


def _drc(cad: Path) -> dict[str, object]:
    output = cad / "placement-drc.json"
    _native(
        cad,
        [
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
        5,  # Routing is deliberately unfinished; do not accept a clean-DRC claim.
    )
    report = json.loads(output.read_text())
    assert isinstance(report, dict)
    assert report["unconnected_items"]
    return report


def _point(root: ET.Element, ref: str, pin: str | None = None) -> tuple[float, float]:
    component = root.find(f'.//i:Component[@refDes="CMP:{ref}"]', NS)
    assert component is not None, ref
    location = component.find("i:Location", NS)
    assert location is not None
    x, y = float(location.attrib["x"]), float(location.attrib["y"])
    if pin is None:
        return x, y
    package = root.find(f'.//i:Package[@name="{component.attrib["packageRef"]}"]', NS)
    assert package is not None
    terminal = package.find(f'i:Pin[@number="PIN:{pin}"]/i:Location', NS)
    assert terminal is not None, (ref, pin)
    transform = component.find("i:Xform", NS)
    angle = 0.0 if transform is None else float(transform.get("rotation", "0"))
    if transform is not None:
        assert transform.get("mirror", "false") == "false"
    dx, dy = float(terminal.attrib["x"]), float(terminal.attrib["y"])
    a = math.radians(angle)
    return x + dx * math.cos(a) - dy * math.sin(a), y + dx * math.sin(a) + dy * math.cos(a)


def _local_decoupling(root: ET.Element) -> None:
    for cap, (pin, maximum) in LOCAL_CAPS.items():
        separation = math.dist(_point(root, cap, "1"), _point(root, "U1", pin))
        assert separation <= maximum, f"{cap}: {separation:.3f} mm exceeds {maximum} mm"


def _ipc(cad: Path) -> ET.Element:
    output = cad / "placement.xml"
    _native(cad, ["pcb", "export", "ipc2581", "-o", str(output), str(cad / BOARD.name)], 0)
    root = ET.parse(output).getroot()
    header = root.find(".//i:CadHeader", NS)
    assert header is not None and header.get("units") == "MILLIMETER"
    return root


def _inventory(root: ET.Element, xml: str) -> None:
    profile, bom, _ = load_documents()
    graph = parse_schematic_xml(xml)
    assert validate_schematic(graph, profile, bom) == []
    on_board = {
        p.native_ref: p for p in graph.parts.values() if "exclude_from_board" not in p.properties
    }
    components = root.findall(".//i:Component", NS)
    assert len(components) == len(on_board) == 68
    assert {c.attrib["refDes"] for c in components} == {"CMP:" + ref for ref in on_board}
    refs = root.findall(".//i:BomItem/i:RefDes", NS)
    assert len(refs) == 68
    for item in refs:
        part = on_board[item.attrib["name"].removeprefix("CMP:")]
        assert item.attrib["populate"] == ("false" if "dnp" in part.properties else "true")
        assert item.attrib["layerRef"] == "LAYER:F.Cu"
    for c in components:
        assert c.attrib["layerRef"] == "LAYER:F.Cu"
    assert _point(root, "J2")[0] < _point(root, "U1")[0] < _point(root, "J1")[0]
    copper = [
        layer
        for layer in root.findall(".//i:Layer", NS)
        if layer.get("layerFunction") == "CONDUCTOR"
    ]
    assert len(copper) == 4


@pytest.mark.schematic
@pytest.mark.parametrize("fault", ["none", "overlap", "wrong-net", "distant-cap"])
def test_actual_placement_and_independent_native_faults(tmp_path: Path, fault: str) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    board = cad / BOARD.name
    text = board.read_text()
    if fault == "wrong-net":
        target = next(line for line in text.splitlines() if '(property "Reference" "C7"' in line)
        ground = next(re.finditer(r'\(net (\d+) "GND"\)', text)).group(0)
        changed = re.sub(r'\(net \d+ "VREFP"\)', ground, target, count=1)
        assert changed != target
        text = text.replace(target, changed, 1)
    elif fault in {"overlap", "distant-cap"}:
        ref, position = ("C7", "41.8 45 270") if fault == "overlap" else ("C9", "60 6 90")
        target = next(
            line for line in text.splitlines() if f'(property "Reference" "{ref}"' in line
        )
        changed = re.sub(r"\(at [^)]+\)", f"(at {position})", target, count=1)
        assert changed != target
        text = text.replace(target, changed, 1)
    board.write_text(text)
    report = _drc(cad)
    if fault == "overlap":
        assert report["violations"]
    elif fault == "wrong-net":
        assert report["schematic_parity"]
    else:
        assert report["violations"] == []
        assert report["schematic_parity"] == []
        root = _ipc(cad)
        if fault == "distant-cap":
            with pytest.raises(AssertionError, match="C9"):
                _local_decoupling(root)
        else:
            _local_decoupling(root)
            _inventory(root, _export(cad, tmp_path))
