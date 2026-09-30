"""Real CGAL checks of the K2 fit prototype, NOT a mechanical safety proof."""

import math
import re
import shutil
import subprocess
from collections import Counter
from pathlib import Path

import pytest

pytestmark = pytest.mark.native
ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "hardware/rev_a/mechanical/carrier_k2.scad"
Point = tuple[float, float, float]


def _triple(a: Point, b: Point, c: Point) -> float:
    return (
        a[0] * (b[1] * c[2] - b[2] * c[1])
        + a[1] * (b[2] * c[0] - b[0] * c[2])
        + a[2] * (b[0] * c[1] - b[1] * c[0])
    )


def _volume(path: Path) -> float:
    """Validate a closed, finite ASCII STL then sum oriented tetrahedra."""
    points: list[Point] = []
    for line in path.read_text().splitlines():
        if line.strip().startswith("vertex "):
            _, x, y, z = line.split()
            point = (float(x), float(y), float(z))
            assert all(math.isfinite(v) for v in point)
            points.append(point)
    assert points and len(points) % 3 == 0
    edges: Counter[tuple[Point, Point]] = Counter()
    volume = 0.0
    for i in range(0, len(points), 3):
        a, b, c = points[i : i + 3]
        volume += _triple(a, b, c) / 6
        for start, end in ((a, b), (b, c), (c, a)):
            assert start != end
            edges[(min(start, end), max(start, end))] += 1
    assert all(count == 2 for count in edges.values()), "STL must be closed and manifold"
    return abs(volume)


def _render(tmp_path: Path, expression: str) -> float:
    executable = shutil.which("openscad")
    assert executable is not None, "native CAD tests require OpenSCAD 2021.01"
    assert MODEL.is_file(), "authored carrier CAD is missing"
    source, output = tmp_path / "probe.scad", tmp_path / "probe.stl"
    source.write_text(f"use <{MODEL}>\n{expression}\n")
    result = subprocess.run(
        [
            executable,
            "--hardwarnings",
            "--export-format",
            "asciistl",
            "-o",
            str(output),
            str(source),
        ],
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    (tmp_path / "openscad.log").write_text(result.stdout + result.stderr)
    assert result.returncode == 0, result.stderr
    assert not re.search(r"(?:WARNING|ERROR):", result.stdout + result.stderr), result.stderr
    assert output.is_file(), "render produced no fresh mesh"
    return _volume(output)


def _overlap(tmp_path: Path, first: str, second: str) -> float:
    # The disjoint 1-mm3 witness makes an EMPTY intersection a valid native STL.
    # Nonempty intersection adds volume; no special casing of exporter failure.
    return (
        _render(
            tmp_path,
            f"union() {{ translate([100,100,100]) cube(1); intersection() {{ {first} {second} }} }}",
        )
        - 1.0
    )


@pytest.mark.parametrize("port", [0, 1])
def test_carrier_seated_pair_has_no_interference(tmp_path: Path, port: int) -> None:
    assert (
        abs(_overlap(tmp_path, f"receiver({port});", f"translate([0,0,2.54]) plug({port});")) < 1e-4
    )


@pytest.mark.parametrize("pose", ["wrong", "reverse", "row", "column", "quarter", "ungrooved"])
def test_carrier_blocks_wrong_parallel_approach(tmp_path: Path, pose: str) -> None:
    expressions = {
        "wrong": "cartridge(1);",
        "reverse": "rotate([0,0,180]) cartridge(0);",
        "row": "translate([2.54,0,0]) cartridge(0);",
        "column": "translate([0,2.54,0]) cartridge(0);",
        "quarter": "rotate([0,0,90]) cartridge(0);",
        "ungrooved": "cartridge(0, false);",
    }
    assert (
        _overlap(tmp_path, "receiver(0);", f"translate([0,0,9]) {{ {expressions[pose]} }}") > 0.01
    )


@pytest.mark.parametrize(
    "angles", [(5, 0), (-5, 0), (15, 0), (-15, 0), (0, 5), (0, -5), (0, 15), (0, -15)]
)
@pytest.mark.parametrize("wrong", [False, True])
def test_carrier_blocks_sampled_tilt_at_first_contact(
    tmp_path: Path,
    angles: tuple[int, int],
    wrong: bool,
) -> None:
    ax, ay = angles
    # Independently calculate earliest possible mouth approach: bounding corners
    # of the 20 contact entrances (0.71-mm accepted square-post size included).
    height = 9 + abs(11.785 * math.sin(math.radians(ax))) + abs(1.625 * math.sin(math.radians(ay)))
    moving = f"translate([0,0,{height:.9f}]) rotate([{ax},{ay},0]) cartridge({int(wrong)});"
    assert _overlap(tmp_path, "receiver(0);", moving) > 0.01


@pytest.mark.parametrize("port", [0, 1])
def test_carrier_cable_path_and_closed_wall_control(tmp_path: Path, port: int) -> None:
    cable = "translate([0,0,2.54]) cable_envelope();"
    assert abs(_overlap(tmp_path, f"receiver({port});", cable)) < 1e-4
    assert _overlap(tmp_path, f"receiver({port}, true);", cable) > 0.1


def test_carrier_missing_key_control(tmp_path: Path) -> None:
    assert (
        abs(_overlap(tmp_path, "receiver(0, false, false);", "translate([0,0,9]) cartridge(1);"))
        < 1e-4
    )


@pytest.mark.parametrize("motion", [0, -0.56])
def test_cartridge_adds_no_seating_standoff(tmp_path: Path, motion: float) -> None:
    assert (
        abs(_overlap(tmp_path, "header_envelope();", f"translate([0,0,{2.54 + motion}]) plug(0);"))
        < 1e-4
    )
    assert (
        abs(_overlap(tmp_path, "receiver(0);", f"translate([0,0,{2.54 + motion}]) plug(0);")) < 1e-4
    )


def test_carrier_frame_clears_board_and_component_allocation(tmp_path: Path) -> None:
    assert abs(_overlap(tmp_path, "carrier();", "board_and_component_allocation();")) < 1e-4


@pytest.mark.parametrize(
    "part", ["carrier()", "cartridge(0)", "cartridge(1)", "cap()", "edge_clip()", "strain_bar()"]
)
def test_carrier_parts_are_real_closed_solids(tmp_path: Path, part: str) -> None:
    assert _render(tmp_path, part + ";") > 1
