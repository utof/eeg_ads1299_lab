"""Ground and supply copper checks, not a release or powered-board qualification."""

import json
import re
import shutil
from pathlib import Path

import pytest

from tests.test_pcb_placement import BOARD, CAD, _native_report
from tests.test_pcb_placement import native_placement as native_placement


def test_ground_plane_is_present_as_filled_copper_not_only_an_outline() -> None:
    text = BOARD.read_text()
    assert re.search(r"\(zone\s", text)
    assert "(filled_polygon" in text
    assert '(net_name "GND")' in text
    assert '(layer "In1.Cu")' in text


@pytest.mark.schematic
@pytest.mark.parametrize("net", ["GND", "VIN_5V_AFE", "AVDD", "DVDD"])
def test_ground_and_supply_nets_have_no_native_airwires(
    native_placement: tuple[Path, dict[str, object]], net: str
) -> None:
    cad, report = native_placement
    assert report["violations"] == []
    assert report["schematic_parity"] == []
    assert f"[{net}]" not in json.dumps(report["unconnected_items"])
    assert report["unconnected_items"] == []  # Native connectivity, not physical approval.
    fill = json.loads((cad / "zone-fill.json").read_text())
    assert fill["zones"] == [{"net": "GND", "layers": ["In1.Cu"], "regions": [1]}]


def _form_end(text: str, start: int) -> int:
    """Locate one balanced native form without treating quoted parentheses as syntax."""
    depth = 0
    for token in re.finditer(r'"(?:\\.|[^"\\])*"|[()]', text[start:]):
        if token[0] == "(":
            depth += 1
        elif token[0] == ")":
            depth -= 1
            if depth == 0:
                return start + token.end()
    raise ValueError("incomplete test source form")


def _service_after_zone(text: str) -> str:
    """Benign native object order from the interrupted failure; never duplicate J3."""
    for match in re.finditer(r"\(footprint\s", text):
        start, end = match.start(), _form_end(text, match.start())
        if re.search(r'"Reference"\s+"J3"', text[start:end]):
            part = text[start:end]
            remaining = text[:start] + text[end:]
            final = remaining.rfind(")")
            return remaining[:final] + part + "\n" + remaining[final:]
    raise ValueError("test requires the actual service footprint")


@pytest.mark.schematic
@pytest.mark.parametrize("service_last", [False, True])
def test_fresh_native_fill_does_not_depend_on_a_previously_cached_polygon(
    tmp_path: Path, service_last: bool
) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    text = BOARD.read_text()
    if service_last:
        text = _service_after_zone(text)
    # This board has one zone, last in the file. Keep its source outline and
    # settings, deliberately remove all cached copper, and require real refill.
    assert len(re.findall(r"\(zone\s", text)) == 1
    assert "(filled_polygon" in text
    stripped = text[: text.index("(filled_polygon")] + ")\n)\n"
    (cad / "rev_a.kicad_pcb").write_text(stripped)
    report = _native_report(cad)
    assert report["violations"] == [] and report["schematic_parity"] == []
    assert "[GND]" not in json.dumps(report["unconnected_items"])
    assert "(filled_polygon" in (cad / "rev_a.kicad_pcb").read_text()


@pytest.mark.schematic
@pytest.mark.parametrize("fault", ["missing-zone", "clipped-outline-stale-fill"])
@pytest.mark.parametrize("service_last", [False, True])
def test_removed_or_clipped_plane_cannot_reuse_the_old_connected_copper(
    tmp_path: Path, fault: str, service_last: bool
) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    text = BOARD.read_text()
    if service_last:
        text = _service_after_zone(text)
    position = re.search(r"\(zone\s", text)
    assert position is not None
    if fault == "missing-zone":
        text = text[: position.start()] + ")\n"
    else:
        # Only the source outline changes; old full-board copper deliberately
        # remains in the cache. The helper must recompute it before DRC.
        header, cached = text.split("(filled_polygon", 1)
        assert "(xy 87.5 10.5)" in header and "(xy 87.5 67.5)" in header
        header = header.replace("(xy 87.5 10.5)", "(xy 60 10.5)")
        header = header.replace("(xy 87.5 67.5)", "(xy 60 67.5)")
        text = header + "(filled_polygon" + cached
    (cad / "rev_a.kicad_pcb").write_text(text)
    report = _native_report(cad)
    assert report["schematic_parity"] == []
    assert "[GND]" in json.dumps(report["unconnected_items"])


# Exact draft-track UUIDs identify destructive test locations, not an
# independently maintained electrical netlist. Native DRC decides connectivity.
POWER_CUTS = {
    "VIN_5V_AFE": "cbe11a7d-6cba-5df4-9035-6b083f60480b",
    "AVDD": "9175220e-5398-514e-af89-e387e8137756",
    "DVDD": "f4c0a95a-ec70-5293-9724-6d039eb9a369",
}


@pytest.mark.schematic
@pytest.mark.parametrize("net", list(POWER_CUTS))
def test_cut_supply_copper_is_detected_after_refill_even_when_parity_matches(
    tmp_path: Path, net: str
) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    text = BOARD.read_text()
    track = next(line for line in text.splitlines() if POWER_CUTS[net] in line)
    assert track.startswith("(segment ")
    (cad / "rev_a.kicad_pcb").write_text(text.replace(track, "", 1))
    report = _native_report(cad)
    assert report["schematic_parity"] == []
    assert f"[{net}]" in json.dumps(report["unconnected_items"])
    assert "[GND]" not in json.dumps(report["unconnected_items"])
