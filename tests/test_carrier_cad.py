"""Real CGAL checks of the K2 fit prototype, NOT a mechanical safety proof."""

import hashlib
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
    # Unique names preserve every comparison and prevent same-directory reuse.
    index = len(list(tmp_path.glob("probe-*.scad")))
    source, output = tmp_path / f"probe-{index:03d}.scad", tmp_path / f"probe-{index:03d}.stl"
    output.unlink(missing_ok=True)
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
    source.with_suffix(".log").write_text(result.stdout + result.stderr)
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
    assert abs(_overlap(tmp_path, "frame();", "board_and_component_allocation();")) < 1e-4


@pytest.mark.parametrize(
    "part",
    [
        "carrier()",
        "bridge(0)",
        "bridge(1)",
        "cartridge(0)",
        "cartridge(1)",
        "cap()",
        "edge_clip()",
        "strain_bar()",
    ],
)
def test_carrier_parts_are_real_closed_solids(tmp_path: Path, part: str) -> None:
    assert _render(tmp_path, part + ";") > 1


@pytest.mark.parametrize("lift", [0, 2, 6, 10])
def test_cable_drawing_tolerance_envelope_has_clear_travel(tmp_path: Path, lift: int) -> None:
    # Independent 1.6-mm vertical envelope includes drawing body-height range;
    # do not shrink it to the convenient nominal cable cuboid inside the CAD.
    cable = f"translate([-25,-12.7,{2.54 + 6.2 + lift}]) cube([22.46,25.4,1.6]);"
    # Release the carrier-mounted bar before a withdrawal (no hot plugging).
    bar = "strain_bar();" if lift == 0 else ""
    obstacles = f"union() {{ receiver(0); translate([-16,0,0]) {{ saddle(); {bar} }} }}"
    assert abs(_overlap(tmp_path, obstacles, cable)) < 1e-4
    # Cable moves with socket, not necessarily the floating cartridge shell.
    assert (
        abs(_overlap(tmp_path, "plug(0);", "translate([-25,-12.7,6.2]) cube([22.46,25.4,1.6]);"))
        < 1e-4
    )


def test_socket_capture_and_exit_orientation(tmp_path: Path) -> None:
    assert abs(_overlap(tmp_path, "plug(0);", "translate([0,0,0.001]) socket_envelope();")) < 1e-4
    assert _overlap(tmp_path, "plug(0);", "translate([0,0,-0.05]) socket_envelope();") > 0.01
    assert _overlap(tmp_path, "plug(0);", "translate([0,0,0.3]) socket_envelope();") > 0.01
    assert _overlap(tmp_path, "plug(0);", "rotate([0,0,180]) cable_envelope();") > 0.1


def test_release_strain_bar_before_withdrawal(tmp_path: Path) -> None:
    cable = "translate([-25,-12.7,10.74]) cube([22.46,25.4,1.6]);"
    assert _overlap(tmp_path, "translate([-16,0,0]) strain_bar();", cable) > 0.1


def test_carrier_is_bound_to_reviewed_board() -> None:
    # A changed PCB must have its mechanical relationship reviewed, not inherit K2.
    board = ROOT / "hardware/rev_a/layout/rev_a.kicad_pcb"
    assert hashlib.sha256(board.read_bytes()).hexdigest() == (
        "dfe893f958128ba28eb69188cf6debbbc9fcafa0ef5dd67bd58627d4b8a26842"
    )


def test_board_installation_before_removable_bridges(tmp_path: Path) -> None:
    # Base must accept the populated board from above BEFORE guides are installed.
    assert (
        abs(
            _overlap(tmp_path, "carrier();", "translate([0,0,5]) board_and_component_allocation();")
        )
        < 1e-4
    )


@pytest.mark.parametrize("port", [0, 1])
@pytest.mark.parametrize("lift", [0, 2, 6, 10])
def test_cable_clears_complete_installed_support(tmp_path: Path, port: int, lift: int) -> None:
    # Check actual global assembly, not only a receiver or local saddle.
    obstacles = """
    union() {
        frame();
        for(side=[0,1], y=contact_y(side))
            translate([side==0 ? 0 : 98,y,0])
                scale([side==0 ? 1 : -1,1,1]) edge_clip();
    """
    if lift == 0:
        obstacles += "for(p=ports()) translate([p[0]-16,p[1],0]) strain_bar();"
    obstacles += "}"
    cable = f"p=ports()[{port}]; translate([p[0],p[1],{2.54 + lift}]) cable_envelope();"
    assert abs(_overlap(tmp_path, obstacles, cable)) < 1e-4
