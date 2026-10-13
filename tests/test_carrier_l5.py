"""K2/R24 allocation and upper-access checks, not part or rework qualification."""

import os
import re
import subprocess
from pathlib import Path

import pytest

from tests import test_carrier_cad as carrier
from tests.test_pcb_power import _form_end

BOARD_PATH = "hardware/rev_a/layout/rev_a.kicad_pcb"
B3 = carrier.ROOT / "docs/studies/b3_access_envelope.scad"
# Allocated space, NOT the dimensions of a selected resistor or its solder joints.
R24_SPACE = "translate([55.4,28.6,0]) cube([3.2,1.6,4]);"


def _intersection(tmp_path: Path, first: str, second: str) -> float:
    # Reuse B3's complete K2/header/socket/ribbon/service/retainer obstacles.
    return (
        carrier._render(
            tmp_path,
            f"use <{B3}>\nunion() {{ translate([100,100,100]) cube(1); "
            f"intersection() {{ union() {{ {first} }} union() {{ {second} }} }} }}",
        )
        - 1.0
    )


@pytest.mark.native
def test_r24_space_is_inside_allocation_and_clear_of_installed_support(tmp_path: Path) -> None:
    assert (
        abs(_intersection(tmp_path, R24_SPACE, "board_and_component_allocation();") - 20.48) < 1e-4
    )
    assert abs(_intersection(tmp_path, R24_SPACE, "retained_obstacles(); pair_corridors();")) < 1e-4
    # A misplaced copy collides with the outboard rail; renderer failures stay failures.
    assert _intersection(tmp_path, "translate([-50,0,0]) { " + R24_SPACE + " }", "carrier();") > 1


@pytest.mark.native
@pytest.mark.parametrize("x", [56.175, 57.825])
def test_r24_upper_approach_is_blocked_until_upper_assembly_is_removed(
    tmp_path: Path, x: float
) -> None:
    # B3's 0.5-mm virtual probe ABOVE the 4-mm allocation, not a soldering tool.
    approach = f"translate([{x},29.4,4.1]) cylinder(h=25.9,d=0.5,$fn=32);"
    assert _intersection(tmp_path, approach, "retained_obstacles(); pair_corridors();") > 0.01
    # Conservative inspection state: bridges, cartridges, ribbons and sense tails absent.
    assert abs(_intersection(tmp_path, approach, "carrier(); service_envelope();")) < 1e-4


@pytest.mark.schematic
def test_r24_native_lands_and_courtyard_match_the_allocated_space(tmp_path: Path) -> None:
    script = r"""
import pcbnew as p, sys
assert p.Version() == '9.0.2'
b = p.LoadBoard(sys.argv[1]); f = b.FindFootprintByReference('R24')
assert f is not None and f.IsDNP()
fields = {field.GetName(): field.GetText() for field in f.GetFields()}
assert fields['Population'] == 'dnp'
assert f.GetValue() == 'NOT_SELECTED' and fields['MPN'] == 'NOT_SELECTED'
assert f.GetLayer() == p.F_Cu and f.GetOrientationDegrees() == 0
assert (f.GetPosition().x, f.GetPosition().y) == (57000000, 29400000)
pads = {a.GetNumber(): a for a in f.Pads()}
assert set(pads) == {'1', '2'}
for number, x, net in [('1', 56175000, 'MISO_DRV'), ('2', 57825000, 'MISO')]:
    a = pads[number]
    assert (a.GetPosition().x, a.GetPosition().y) == (x, 29400000)
    assert (a.GetSize().x, a.GetSize().y) == (800000, 950000)
    assert a.GetNetname() == net and a.GetAttribute() == p.PAD_ATTRIB_SMD
edges = [a for a in f.GraphicalItems() if a.GetLayer() == p.F_CrtYd]
assert len(edges) == 4
for edge in edges:
    assert edge.GetWidth() == 50000
    for point in [edge.GetStart(), edge.GetEnd()]:
        # Include half the courtyard line width, without inventing a part maximum.
        assert 55400000 <= point.x - 25000 <= point.x + 25000 <= 58600000
        assert 28600000 <= point.y - 25000 <= point.y + 25000 <= 30200000
print('R24: two native SMD lands and full courtyard inside 3.2 x 1.6 mm allocation; DNP.')
"""
    result = subprocess.run(
        [
            os.environ.get("KICAD_PYTHON", "/usr/bin/python3"),
            "-c",
            script,
            str(carrier.ROOT / BOARD_PATH),
        ],
        capture_output=True,
        text=True,
        timeout=45,
    )
    (tmp_path / "r24-native.log").write_text(result.stdout + result.stderr)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("edit", ["placement", "pad_size"])
def test_carrier_binding_rejects_altered_r24(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, edit: str
) -> None:
    text = (carrier.ROOT / BOARD_PATH).read_text()
    forms = [text[m.start() : _form_end(text, m.start())] for m in re.finditer(r"\(footprint\s", text)]
    footprint = next(f for f in forms if '(property "Reference" "R24"' in f)
    old, new = (
        ("(at 57.0 29.4 0)", "(at 57.5 29.4 0)")
        if edit == "placement"
        else ("(size 0.8 0.95)", "(size 0.9 0.95)")
    )
    assert old in footprint
    changed = footprint.replace(old, new, 1)
    destination = tmp_path / BOARD_PATH
    destination.parent.mkdir(parents=True)
    destination.write_text(text.replace(footprint, changed, 1))
    monkeypatch.setattr(carrier, "ROOT", tmp_path)
    with pytest.raises(AssertionError):
        carrier.test_carrier_is_bound_to_reviewed_board()
