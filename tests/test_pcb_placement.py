"""Native routed-draft checks; clean CAD does not establish fabrication approval."""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CAD = ROOT / "hardware/rev_a/kicad"
BOARD = ROOT / "hardware/rev_a/layout/rev_a.kicad_pcb"


def test_editable_placement_is_a_tracked_design_not_a_parking_grid() -> None:
    text = BOARD.read_text()
    assert text.count('(footprint "') == 68
    assert text.count('(pad "') == 245
    assert text.count(" dnp)") == 8
    assert "(gr_rect " in text and '(layer "Edge.Cuts")' in text
    assert '(1 "In1.Cu" power)' in text and '(2 "In2.Cu" signal)' in text
    assert "(segment " in text
    assert "PLACEMENT DRAFT - NOT FOR FABRICATION" in text
    assert len(re.findall(r"\(zone\s", text)) == 1  # One native-filled ground region.


# KiCad's system Python binding is native authoring/check tooling, not a new
# project Python dependency. The subprocess is required even if cached copper
# exists: modified test boards must never borrow the original filled polygon.
_FILL_SCRIPT = """
import json, sys
from pathlib import Path
import pcbnew as p
assert p.Version() == "9.0.2", "unexpected native zone engine"
path = Path(sys.argv[1])
b = p.LoadBoard(str(path))
b.BuildConnectivity()
assert p.ZONE_FILLER(b).Fill(b.Zones()), "native zone fill failed"
p.SaveBoard(str(path), b)
rows = [
    {"net": z.GetNetname(), "layers": [b.GetLayerName(l) for l in z.GetLayerSet().Seq()],
     "regions": [z.GetFilledPolysList(l).OutlineCount() for l in z.GetLayerSet().Seq()]}
    for z in b.Zones()
]
(path.parent / "zone-fill.json").write_text(json.dumps(
    {"kicad_version": p.Version(), "python": sys.version, "zones": rows}, indent=2) + "\\n")
"""


def _refill_zones(cad: Path) -> None:
    board = cad / "rev_a.kicad_pcb"
    if re.search(r"\(zone\s", board.read_text()) is None:
        return  # The plane-removal fault must reach DRC without invented copper.
    result = subprocess.run(
        [os.environ.get("KICAD_PYTHON", "/usr/bin/python3"), "-c", _FILL_SCRIPT, str(board)],
        capture_output=True,
        text=True,
        timeout=45,
        env=dict(os.environ, KICAD_CONFIG_HOME=str(cad / "config"), LC_ALL="C", LANG="C"),
    )
    (cad / "zone-fill.log").write_text(result.stdout + result.stderr)
    assert result.returncode == 0, "native refill failed: " + result.stdout + result.stderr


def _native_report(cad: Path) -> dict[str, object]:
    cli = shutil.which("kicad-cli")
    assert cli is not None, "actual placement validation requires KiCad"
    _refill_zones(cad)
    output = cad / "placement-drc.json"
    result = subprocess.run(
        [
            cli,
            "pcb",
            "drc",
            "--format",
            "json",
            "--schematic-parity",
            "--severity-all",
            "--exit-code-violations",
            "-o",
            str(output),
            str(cad / "rev_a.kicad_pcb"),
        ],
        capture_output=True,
        text=True,
        timeout=45,
        env=dict(os.environ, KICAD_CONFIG_HOME=str(cad / "config"), LC_ALL="C", LANG="C"),
    )
    (cad / "placement-drc.log").write_text(result.stdout + result.stderr)
    assert result.returncode in (0, 5), result.stdout + result.stderr
    report: object = json.loads(output.read_text())
    assert isinstance(report, dict)
    findings = any(report[name] for name in ("violations", "schematic_parity", "unconnected_items"))
    assert result.returncode == (5 if findings else 0), "DRC exit disagrees with its findings"
    return report


@pytest.fixture(scope="module")
def native_placement(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict[str, object]]:
    """One immutable canonical native report per test module, never a fault result.

    Mutated boards are separate copies and are independently refilled/checked.
    Repeating the unchanged canonical fill for every pad adds no fault evidence.
    """
    cad = tmp_path_factory.mktemp("canonical-placement") / "cad"
    shutil.copytree(CAD, cad)
    shutil.copyfile(BOARD, cad / "rev_a.kicad_pcb")
    return cad, _native_report(cad)


def _input_airwire(report: dict[str, object]) -> bool:
    # KiCad's independent connectivity engine, not the authoring script's routes.
    return re.search(r"\bIN[1-4][PN]\b", json.dumps(report["unconnected_items"])) is not None


def _footprint_block(board: str, reference: str) -> str:
    # Split only for localized faults; KiCad remains the actual file parser.
    # Do not require the one-line formatting emitted by the original import.
    marker = r'\(property\s+"Reference"\s+"' + re.escape(reference) + '"'
    return next(
        block
        for block in re.split(r'(?=\(footprint\s+")', board)
        if block.startswith("(footprint ") and re.search(marker, block)
    )


def _fault_board(board: str, fault: str) -> str:
    if fault == "overlap":
        one = _footprint_block(board, "R1")
        two = _footprint_block(board, "R2")
        second_at = re.search(r"\(at [^)]+\)", two)
        assert second_at is not None
        changed = re.sub(r"\(at [^)]+\)", second_at.group(), one, count=1)
        assert changed != one
        board = board.replace(one, changed, 1)
    elif fault == "wrong-net":
        one = _footprint_block(board, "C1")
        ground = re.search(r'\(net \d+ "GND"\)', board)
        assert ground is not None
        changed = re.sub(r'\(net \d+ "IN1P"\)', ground.group(), one, count=1)
        assert changed != one
        board = board.replace(one, changed, 1)
    elif fault == "missing-input-track":
        code = re.search(r'\(net (\d+) "IN1P"\)', board)
        assert code is not None
        tracks = re.findall(r'\(segment\s+(?:(?!\(segment).)*?\(uuid\s+"[^"]+"\)\)', board, re.S)
        track = next(t for t in tracks if f"(net {code.group(1)})" in t)
        board = board.replace(track, "", 1)
    return board


@pytest.mark.schematic
@pytest.mark.parametrize("fault", ["none", "overlap", "wrong-net", "missing-input-track"])
def test_native_placement_and_completed_input_routes(tmp_path: Path, fault: str) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    board = _fault_board(BOARD.read_text(), fault)
    (cad / "rev_a.kicad_pcb").write_text(board)
    report = _native_report(cad)
    assert bool(report["schematic_parity"]) is (fault == "wrong-net")
    assert bool(report["violations"]) is (fault != "none")
    if fault == "none":
        assert not _input_airwire(report)
    elif fault == "missing-input-track":
        assert _input_airwire(report)
    if fault == "none":
        assert report["unconnected_items"] == []  # CAD connectivity, not fabrication approval.


@pytest.mark.schematic
@pytest.mark.parametrize("net", ["VREFP", "VCAP1", "VCAP2", "VCAP3", "VCAP4"])
def test_reference_and_pump_capacitor_nets_have_no_airwires(
    native_placement: tuple[Path, dict[str, object]], net: str
) -> None:
    _, report = native_placement
    assert report["schematic_parity"] == []
    assert report["violations"] == []
    assert f"[{net}]" not in json.dumps(report["unconnected_items"])


# Test fault locations in this authored board, not an alternate connectivity spec.
# Removing just these spokes must isolate a negative terminal without changing
# the completed positive net. A plane cannot repair a missing front-pad spoke.
RETURN_SPOKES = {
    "C7": "7238da55-d8e3-5c43-93f2-54970a1f37d7",
    "C6": "794dffa4-2e2d-5940-8365-10e563a6755c",
    "C25": "0e1a4992-f7d4-5cc6-8526-eec9034846bb",
    "C10": "318fe669-2bdf-5909-9b64-240c431360f7",
    "C23": "2e5d3978-51af-538c-8adb-917643a77c7b",
    "C8": "223dd54d-bd9b-5e49-954e-f7f1f14b4492",
    "C9": "9ef13bc9-c831-5927-a31f-0863f423ce26",
    "C24": "716f2854-f089-5388-b821-d1e4e5e88928",
}


@pytest.mark.schematic
@pytest.mark.parametrize("reference", list(RETURN_SPOKES))
def test_a_broken_capacitor_return_is_not_hidden_by_a_completed_positive_net(
    tmp_path: Path, reference: str, native_placement: tuple[Path, dict[str, object]]
) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    board = BOARD.read_text()
    target = cad / "rev_a.kicad_pcb"
    _, before = native_placement
    assert before["violations"] == [] and before["schematic_parity"] == []
    # These per-item UUIDs identify exactly which copper is removed in the fault.
    # KiCad, not this test, decides whether removing it electrically opens the path.
    spoke = next(line for line in board.splitlines() if RETURN_SPOKES[reference] in line)
    assert spoke.startswith("(segment ") and '(layer "F.Cu")' in spoke
    target.write_text(board.replace(spoke, "", 1))
    after = _native_report(cad)
    assert after["schematic_parity"] == []
    old = before["unconnected_items"]
    new = after["unconnected_items"]
    assert isinstance(old, list) and isinstance(new, list)
    assert len(new) == len(old) + 1
    assert f"Pad 2 [GND] of {reference} on F.Cu" in json.dumps(new)
    for net in ("VREFP", "VCAP1", "VCAP2", "VCAP3", "VCAP4"):
        assert f"[{net}]" not in json.dumps(new)


@pytest.mark.schematic
@pytest.mark.parametrize("net", ["VREFP", "VCAP1", "VCAP2", "VCAP3", "VCAP4"])
def test_native_connectivity_detects_a_cut_sensitive_capacitor_trace(
    tmp_path: Path, net: str
) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    board = BOARD.read_text()
    code = re.search(r'\(net (\d+) "' + net + r'"\)', board)
    assert code is not None
    track = next(
        line
        for line in board.splitlines()
        if line.startswith("(segment ") and f"(net {code.group(1)})" in line
    )
    (cad / "rev_a.kicad_pcb").write_text(board.replace(track, "", 1))
    report = _native_report(cad)
    assert report["schematic_parity"] == []
    assert f"[{net}]" in json.dumps(report["unconnected_items"])


REMAINING_SIGNAL_NETS = (
    "BIASINV",
    "BIASOUT",
    "BIAS_AFTER_1M_DUMMY",
    "CH1N_DUMMY",
    "CH1P_DUMMY",
    "CH2N_DUMMY",
    "CH2P_DUMMY",
    "CH3N_DUMMY",
    "CH3P_DUMMY",
    "CH4N_DUMMY",
    "CH4P_DUMMY",
    "CLK",
    "CLKSEL",
    "CS",
    "DRDY",
    "GPIO1",
    "GPIO2",
    "GPIO3",
    "GPIO4",
    "MISO",
    "MOSI",
    "PWDN",
    "RESET",
    "SCLK",
    "START",
)


@pytest.mark.schematic
@pytest.mark.parametrize("net", REMAINING_SIGNAL_NETS)
def test_remaining_signal_net_is_physically_routed(
    native_placement: tuple[Path, dict[str, object]], net: str
) -> None:
    _, report = native_placement
    assert report["violations"] == [] and report["schematic_parity"] == []
    assert f"[{net}]" not in json.dumps(report["unconnected_items"])


@pytest.mark.schematic
def test_complete_draft_has_no_native_unconnected_items(
    native_placement: tuple[Path, dict[str, object]],
) -> None:
    _, report = native_placement
    assert report["schematic_parity"] == []
    assert report["violations"] == []
    assert report["unconnected_items"] == []


# Individual authored track identities are destructive probe locations, not a
# second netlist. Each copy is independently refilled; KiCad decides connectivity.
SIGNAL_CUTS = {
    "CLKSEL": "9da37015-2385-5d0d-a0a8-f2eee7d27e72",
    "RESET": "40e5dd5f-bd52-58c3-b69b-7a80cb40a92f",
    "GPIO1": "31d63b38-6d8a-5677-94fe-df0cf3083830",
    "GPIO2": "2cd6645a-3169-55d4-b8f1-11a0a91ef3ac",
    "GPIO3": "926571ce-e2dd-5b75-8417-cab5f127f7f3",
    "GPIO4": "c4358fe3-513c-570c-8f50-efb8c9967368",
    "CLK": "14930e7c-bc68-58aa-b4c0-14b20818133e",
    "BIASINV": "58954bb8-e9cf-5611-836c-bf08cc74fa00",
    "BIASOUT": "bc855c18-b185-555a-a5f7-5aed97f89b74",
    "BIAS_AFTER_1M_DUMMY": "77129e41-c112-51f0-ad69-1c606e0e114c",
    "MOSI": "8fbb0c88-0432-5622-80cf-a65af1a9cc06",
    "PWDN": "4b8101e8-5f1a-5738-83ff-e9e15789b0f2",
    "START": "efcf6b23-e65d-5ed7-8a0c-b36c29f1458e",
    "CS": "cb1c727d-3f6c-552a-9067-5dbeffa7281a",
    "SCLK": "ae033c95-a8e2-55ac-81cf-9eaac0ca2a6b",
    "MISO": "426ebbc2-4e29-5247-a683-95487e99e745",
    "DRDY": "57f3e4b0-ea4f-5f98-b335-0d4f1c94a265",
    "CH4N_DUMMY": "cb3c7b24-eceb-5439-b2b4-eea29d883c7c",
    "CH4P_DUMMY": "5b8e6b2c-140b-5165-b77a-c72cde9e1072",
    "CH3N_DUMMY": "de60ff7c-9282-53a9-b116-e4c035d1c669",
    "CH3P_DUMMY": "423e3117-7b50-5213-9337-83c4b21f4214",
    "CH2N_DUMMY": "dfff8551-3136-5437-8922-c94708f32915",
    "CH2P_DUMMY": "452d3ac7-1b75-5924-8b66-1123f4e983a6",
    "CH1N_DUMMY": "5fc9d738-626b-58ea-9dad-ee99dec1ccca",
    "CH1P_DUMMY": "2f3b2335-09b2-515c-8a53-2300b2e2e909",
}


@pytest.mark.schematic
@pytest.mark.parametrize("net", sorted(SIGNAL_CUTS))
def test_each_new_signal_route_exposes_a_cut_without_changing_the_schematic(
    tmp_path: Path, net: str
) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    text = BOARD.read_text()
    track = next(line for line in text.splitlines() if SIGNAL_CUTS[net] in line)
    assert track.startswith("(segment ")
    (cad / "rev_a.kicad_pcb").write_text(text.replace(track, "", 1))
    report = _native_report(cad)
    assert report["schematic_parity"] == []
    assert f"[{net}]" in json.dumps(report["unconnected_items"])
    assert "[GND]" not in json.dumps(report["unconnected_items"])


@pytest.mark.parametrize(
    ("exit_code", "findings", "accepted"),
    [(0, False, True), (5, True, True), (0, True, False), (5, False, False), (1, False, False)],
)
def test_native_exit_and_report_cannot_disagree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, exit_code: int, findings: bool, accepted: bool
) -> None:
    """Software-only process doubles; not native CAD execution."""

    def no_refill(_cad: Path) -> None:
        pass

    def tool(_name: str) -> str:
        return "/software-double/kicad-cli"

    def run(
        command: list[str], *, capture_output: bool, text: bool, timeout: float, env: dict[str, str]
    ) -> subprocess.CompletedProcess[str]:
        Path(command[command.index("-o") + 1]).write_text(
            json.dumps(
                {
                    "violations": [],
                    "schematic_parity": [],
                    "unconnected_items": [{"type": "software_double"}] if findings else [],
                }
            )
        )
        return subprocess.CompletedProcess(command, exit_code, "software double", "")

    monkeypatch.setattr("tests.test_pcb_placement._refill_zones", no_refill)
    monkeypatch.setattr(shutil, "which", tool)
    monkeypatch.setattr(subprocess, "run", run)
    if accepted:
        report = _native_report(tmp_path)
        assert bool(report["unconnected_items"]) is findings
    else:
        with pytest.raises(AssertionError):
            _native_report(tmp_path)


# Local repair design targets, not manufacturer impedance/noise guarantees.
# Distances count whole native track centrelines along a front-only itinerary;
# pad spreading and via barrels are deliberately not represented as extracted L/C.
_BYPASS_LIMITS = {
    ("54", "C16", "1"): 4.0,
    ("54", "C27", "1"): 6.0,
    ("53", "C16", "2"): 4.5,
    ("53", "C27", "2"): 6.5,
    ("55", "C9", "1"): 3.5,
    ("55", "C24", "1"): 6.5,
}

_FRONT_PATH_SCRIPT = r"""
import heapq, json, sys
import pcbnew as p
assert p.Version() == "9.0.2"
b = p.LoadBoard(sys.argv[1])
b.BuildConnectivity()
c = b.GetConnectivity()
pads = {(f.GetReference(), t.GetNumber()): t for f in b.GetFootprints() for t in f.Pads()}

def identity(item):
    return str(item.m_Uuid.AsString())

def neighbours(item):
    # KiCad supplies physical adjacency, including pad contact and T-junctions.
    # Connectivity exposes PCB_TRACK proxies for vias: use native Type(), not isinstance.
    # A via/plane/other layer must not substitute for the local front-side loop.
    for t in c.GetConnectedTracks(item):
        if t.Type() != p.PCB_VIA_T and t.GetLayer() == p.F_Cu:
            yield t
    for pad in c.GetConnectedPads(item):
        if pad.IsOnLayer(p.F_Cu):
            yield pad

def route(start, target):
    sid, tid = identity(start), identity(target)
    queue = [(0.0, sid)]
    known = {sid: start}
    best = {sid: 0.0}
    previous = {}
    while queue:
        distance, key = heapq.heappop(queue)
        if distance != best[key]:
            continue
        if key == tid:
            keys = [key]
            while key != sid:
                key = previous[key]
                keys.append(key)
            return {"trace_mm": distance, "items": list(reversed(keys)),
                    "pads": [v.GetParentFootprint().GetReference() + "." + v.GetNumber()
                             for k in reversed(keys) if isinstance((v := known[k]), p.PAD)]}
        for item in neighbours(known[key]):
            ident = identity(item)
            cost = 0.0 if isinstance(item, p.PAD) else p.ToMM(item.GetLength())
            candidate = distance + cost
            if candidate < best.get(ident, float("inf")):
                best[ident], known[ident], previous[ident] = candidate, item, key
                heapq.heappush(queue, (candidate, ident))
    return {"trace_mm": None, "items": [], "pads": []}

def pre_bypass_exits(start, capacitors, target):
    # Conservative native item-adjacency boundary, not a field solver: traverse
    # the device branch to THIS capacitor, not merely the first in its bank.
    # Other bank pads are allowed contacts, not stopping points. Inspect vias
    # and foreign pads on the target-contacting boundary track too.
    # A future arbitrary overlapping/long boundary track still needs review.
    targets = {identity(pad) for pad in capacitors}
    boundary = identity(target)
    sid = identity(start)
    queue, seen, exits = [start], set(), set()
    while queue:
        item = queue.pop()
        key = identity(item)
        if key in seen:
            continue
        seen.add(key)
        tracks = list(c.GetConnectedTracks(item))
        contacts = list(c.GetConnectedPads(item))
        for track in tracks:
            if track.Type() == p.PCB_VIA_T:
                exits.add("via:" + identity(track))
        for pad in contacts:
            if identity(pad) not in targets | {sid}:
                exits.add("pad:" + pad.GetParentFootprint().GetReference() + "." + pad.GetNumber())
        if any(identity(pad) == boundary for pad in contacts):
            # Stop edges that also touch the target pad, not side branches
            # leaving this boundary item before the capacitor contact.
            tracks = [track for track in tracks if not any(
                identity(pad) == boundary for pad in c.GetConnectedPads(track))]
        # Disjoint track ends can be joined by the intermediate capacitor pad.
        # Traverse that pad's native contacts, never jump through the capacitor
        # dielectric to its other terminal. The requested boundary still stops.
        queue.extend(pad for pad in contacts if identity(pad) in targets - {boundary})
        queue.extend(t for t in tracks if t.Type() != p.PCB_VIA_T and t.GetLayer() == p.F_Cu)
    return sorted(exits)

rows = {}
for pin, cap, terminal in json.loads(sys.argv[2]):
    group = ("C9", "C24") if pin == "55" else ("C16", "C27")
    row = route(pads["U1", pin], pads[cap, terminal])
    row["pre_bypass_exits"] = pre_bypass_exits(
        pads["U1", pin], [pads[r, terminal] for r in group], pads[cap, terminal])
    rows[pin + ":" + cap + ":" + terminal] = row
print(json.dumps(rows))
"""


def _front_paths(board: Path) -> dict[str, object]:
    result = subprocess.run(
        [
            os.environ.get("KICAD_PYTHON", "/usr/bin/python3"),
            "-c",
            _FRONT_PATH_SCRIPT,
            str(board),
            json.dumps(list(_BYPASS_LIMITS)),
        ],
        capture_output=True,
        text=True,
        timeout=45,
        env=dict(
            os.environ, KICAD_CONFIG_HOME=str(board.parent / "path-config"), LC_ALL="C", LANG="C"
        ),
    )
    (board.parent / "front-paths.log").write_text(result.stdout + result.stderr)
    assert result.returncode == 0, result.stdout + result.stderr
    rows: object = json.loads(result.stdout)
    assert isinstance(rows, dict)
    (board.parent / "front-paths.json").write_text(json.dumps(rows, indent=2) + "\n")
    return rows


@pytest.fixture(scope="module")
def front_bypass_paths(tmp_path_factory: pytest.TempPathFactory) -> dict[str, object]:
    cad = tmp_path_factory.mktemp("front-bypass-paths")
    board = cad / "rev_a.kicad_pcb"
    shutil.copyfile(BOARD, board)
    return _front_paths(board)


@pytest.mark.schematic
@pytest.mark.parametrize("connection,limit", list(_BYPASS_LIMITS.items()))
def test_local_bypass_uses_a_bounded_front_path_without_vias(
    front_bypass_paths: dict[str, object], connection: tuple[str, str, str], limit: float
) -> None:
    pin, cap, terminal = connection
    row = front_bypass_paths[":".join(connection)]
    assert isinstance(row, dict)
    assert row["pre_bypass_exits"] == [], "supply/return joins shared copper before the bypass"
    distance: object = row["trace_mm"]
    assert isinstance(distance, (float, int)), f"no direct front path: U1.{pin} to {cap}.{terminal}"
    assert distance <= limit, f"local design target exceeded: {distance} > {limit} mm"
    # A shorter detour through another ADC supply terminal is not the desired path.
    raw_pads: object = row["pads"]
    assert isinstance(raw_pads, list)
    path_pads: list[object] = raw_pads
    assert all(
        isinstance(item, str) and (not item.startswith("U1.") or item == "U1." + pin)
        for item in path_pads
    )


# Deliberately restore the old plane-dependent entry while removing the new
# direct spoke. General DRC/net connectivity should still pass; the local-loop
# checker must not accept that as a substitute for the new front-side connection.
# These are fault fixtures only, never an alternate canonical board generator.
_BYPASS_BACKDOORS = {
    "54": (
        "29bbfcef-5358-5eb4-855e-8ab590506c7c",
        """
(segment (start 49.25 31.3375) (end 49.25 32.2) (width 0.2) (layer "F.Cu") (net 1) (uuid "a7168135-9b35-5086-8791-871818476c49"))
(segment (start 49.25 32.2) (end 48.85 32.6) (width 0.2) (layer "F.Cu") (net 1) (uuid "79e7ef53-2cd2-56f0-a7ab-cb2fe94da14f"))
(segment (start 48.85 32.6) (end 48.85 33.1) (width 0.2) (layer "F.Cu") (net 1) (uuid "65154475-b69d-5add-b414-5eff88547eb9"))
(via (at 48.85 33.1) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net 1) (uuid "84baee1b-6160-5959-a408-2f6fed4d6025"))
(segment (start 48.85 33.1) (end 49.05 32.9) (width 0.3) (layer "In2.Cu") (net 1) (uuid "cc139cdd-ced4-5416-82e5-64c55cb26b68"))
(segment (start 49.05 32.9) (end 49.05 26.075) (width 0.3) (layer "In2.Cu") (net 1) (uuid "f56df49a-4c85-5301-bc8c-86436bebd3ca"))
""",
    ),
    "53": (
        "d3a24851-14f6-55c3-b3cf-89b69174c6d5",
        """
(segment (start 49.750000 31.337500) (end 49.750000 32.900000) (width 0.15) (layer "F.Cu") (net 18) (uuid "111afbb5-8290-5cce-ac43-629b173e4930"))
(via (at 49.750000 32.900000) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net 18) (uuid "c6c269a6-8197-5080-8568-e60116ee585e"))
""",
    ),
}


_BYPASS_LOCAL_CUTS = {
    "54": (
        "29bbfcef-5358-5eb4-855e-8ab590506c7c",
        "38b7240a-a8ff-540c-8b54-36e827e99446",
        "11d40849-b7a3-544d-86e9-72248511563f",
    ),
    "53": (
        "d3a24851-14f6-55c3-b3cf-89b69174c6d5",
        "c5026e54-4396-5f74-a644-9786c0745f83",
        "79bf195e-f095-582a-9a83-6abb3b961a35",
        "be1b3293-799a-5ff4-91fb-0214730f2e2b",
    ),
}


@pytest.mark.schematic
@pytest.mark.parametrize("pin", ["54", "53"])
def test_globally_connected_backdoor_does_not_replace_the_local_bypass(
    tmp_path: Path, pin: str
) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    text = BOARD.read_text()
    _, backdoor = _BYPASS_BACKDOORS[pin]
    # Remove the entire device branch to avoid a dangling stub independently
    # failing DRC. The intended fault is the bypass route, not an open supply.
    for cut in _BYPASS_LOCAL_CUTS[pin]:
        spoke = next(line for line in text.splitlines() if cut in line)
        assert spoke.startswith("(segment ") and '(layer "F.Cu")' in spoke
        text = text.replace(spoke, "", 1)
    board = cad / "rev_a.kicad_pcb"
    board.write_text(text.rstrip()[:-1] + backdoor + ")\n")
    report = _native_report(cad)
    assert all(report[k] == [] for k in ("violations", "schematic_parity", "unconnected_items"))
    rows = _front_paths(board)
    terminal = "1" if pin == "54" else "2"
    for cap in ("C16", "C27"):
        row = rows[f"{pin}:{cap}:{terminal}"]
        assert isinstance(row, dict)
        assert row["trace_mm"] is None, "global plane access concealed the broken local path"


@pytest.mark.schematic
@pytest.mark.parametrize(
    "track_id",
    [
        _BYPASS_BACKDOORS["54"][0],
        "b1e992da-b6ea-529d-be35-8c9c2e062ead",
        "71a8e185-29b0-58ec-b001-1fbad324e95f",
    ],
    ids=["device-entry", "positive-between-capacitors", "return-between-capacitors"],
)
def test_benign_track_subdivision_and_reversal_preserve_local_paths(
    tmp_path: Path, track_id: str
) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    text = BOARD.read_text()
    board = cad / "rev_a.kicad_pcb"
    board.write_text(text)
    before = _front_paths(board)
    # Divide and reverse an entry or inter-capacitor track using native adjacency,
    # not a fixed item count, source hash or route UUID allowlist.
    key = track_id
    track = next(line for line in text.splitlines() if key in line)
    a = re.search(r"\(start ([^)]+)\)", track)
    z = re.search(r"\(end ([^)]+)\)", track)
    assert a is not None and z is not None
    start = [float(v) for v in a.group(1).split()]
    end = [float(v) for v in z.group(1).split()]
    midpoint = " ".join(f"{(x + y) / 2:.7f}" for x, y in zip(start, end, strict=True))
    left = track.replace(a.group(), "(start " + midpoint + ")")
    left = left.replace(z.group(), "(end " + a.group(1) + ")")
    right = track.replace(a.group(), "(start " + midpoint + ")")
    right = right.replace(key, "0b7c73a7-6c89-4dca-97f2-b7d7f529bb5a")
    board.write_text(text.replace(track, left + "\n" + right, 1))
    report = _native_report(cad)
    assert all(report[k] == [] for k in ("violations", "schematic_parity", "unconnected_items"))
    after = _front_paths(board)
    for key, row in before.items():
        other = after[key]
        assert isinstance(row, dict) and isinstance(other, dict)
        assert isinstance(row["trace_mm"], (float, int))
        assert isinstance(other["trace_mm"], (float, int))
        # Whole-track itinerary costs may shrink when a divided track ends in
        # a pad: KiCad can reach that pad before traversing the inner fragment.
        # The physical local path and its target must remain acceptable, not an
        # artificial segmentation-dependent exact floating-point result.
        parts = key.split(":")
        assert len(parts) == 3
        assert other["trace_mm"] <= _BYPASS_LIMITS[parts[0], parts[1], parts[2]]
        assert other["pads"] == row["pads"]
        assert other["pre_bypass_exits"] == row["pre_bypass_exits"] == []


@pytest.mark.schematic
@pytest.mark.parametrize("pin", ["54", "53"])
def test_an_extra_pre_bypass_plane_join_is_rejected_even_with_the_local_path_intact(
    tmp_path: Path, pin: str
) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    text = BOARD.read_text()
    _, backdoor = _BYPASS_BACKDOORS[pin]
    board = cad / "rev_a.kicad_pcb"
    board.write_text(text.rstrip()[:-1] + backdoor + ")\n")
    report = _native_report(cad)
    assert all(report[k] == [] for k in ("violations", "schematic_parity", "unconnected_items"))
    rows = _front_paths(board)
    terminal = "1" if pin == "54" else "2"
    for cap in ("C16", "C27"):
        row = rows[f"{pin}:{cap}:{terminal}"]
        assert isinstance(row, dict)
        assert isinstance(row["trace_mm"], (float, int))
        assert row["trace_mm"] <= _BYPASS_LIMITS[pin, cap, terminal]
        assert row.get("pre_bypass_exits"), (
            "upstream plane join was accepted with a local path intact"
        )


# Review #4137830251: a shared entry between the two parallel capacitors is
# downstream of C16 but upstream of C27. Both direct paths still exist and
# ordinary DRC is clean. The boundary must be evaluated for each capacitor.
_MID_BANK_EXITS = {
    "54": """
(via (at 49.925 28.2) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net 1) (uuid "e5e49115-2baf-5eaf-bd74-030cf6d811db"))
(segment (start 49.925 28.2) (end 49.925 26.375) (width 0.3) (layer "In2.Cu") (net 1) (uuid "6f4a96df-a2c3-51ca-a3c3-9b4b16e6ea3f"))
""",
    "53": """
(via (at 51.475 28.2) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net 18) (uuid "75ae5ce8-44c5-55c5-a039-5d82f428bfdf"))
""",
}


@pytest.mark.schematic
@pytest.mark.parametrize("pin", ["54", "53"])
def test_plane_join_between_capacitors_is_rejected_for_distal_capacitor(
    tmp_path: Path, pin: str
) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    text = BOARD.read_text()
    board = cad / "rev_a.kicad_pcb"
    board.write_text(text.rstrip()[:-1] + _MID_BANK_EXITS[pin] + ")\n")
    report = _native_report(cad)
    assert all(report[k] == [] for k in ("violations", "schematic_parity", "unconnected_items"))
    rows = _front_paths(board)
    terminal = "1" if pin == "54" else "2"
    for cap in ("C16", "C27"):
        row = rows[f"{pin}:{cap}:{terminal}"]
        assert isinstance(row, dict)
        assert isinstance(row["trace_mm"], (float, int))
        assert row["trace_mm"] <= _BYPASS_LIMITS[pin, cap, terminal]
    near, distal = rows[f"{pin}:C16:{terminal}"], rows[f"{pin}:C27:{terminal}"]
    assert isinstance(near, dict) and isinstance(distal, dict)
    assert near["pre_bypass_exits"] == [], "the inserted join is after the near capacitor"
    assert distal["pre_bypass_exits"], "the walk stopped at C16 and never guarded C27"


@pytest.mark.schematic
@pytest.mark.parametrize(
    "pin,x,track_id",
    [
        ("54", "49.925", "b1e992da-b6ea-529d-be35-8c9c2e062ead"),
        ("53", "51.475", "71a8e185-29b0-58ec-b001-1fbad324e95f"),
    ],
)
@pytest.mark.parametrize("with_exit", [False, True])
def test_capacitor_pad_contact_is_traversed_before_the_distal_boundary(
    tmp_path: Path, pin: str, x: str, track_id: str, with_exit: bool
) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    text = BOARD.read_text()
    track = next(line for line in text.splitlines() if track_id in line)
    # Both ends still touch C16, but the tracks no longer touch one another.
    # Native pad contact, not a coincident centreline endpoint, joins the bank.
    shortened = track.replace(f"(start {x} 29)", f"(start {x} 28.65)")
    assert shortened != track
    text = text.replace(track, shortened, 1)
    if with_exit:
        text = text.rstrip()[:-1] + _MID_BANK_EXITS[pin] + ")\n"
    board = cad / "rev_a.kicad_pcb"
    board.write_text(text)
    report = _native_report(cad)
    assert all(report[k] == [] for k in ("violations", "schematic_parity", "unconnected_items"))
    rows = _front_paths(board)
    terminal = "1" if pin == "54" else "2"
    for cap in ("C16", "C27"):
        row = rows[f"{pin}:{cap}:{terminal}"]
        assert isinstance(row, dict)
        assert isinstance(row["trace_mm"], (float, int))
        assert row["trace_mm"] <= _BYPASS_LIMITS[pin, cap, terminal]
        exits: object = row["pre_bypass_exits"]
        assert isinstance(exits, list)
        assert bool(exits) is (with_exit and cap == "C27")


@pytest.mark.schematic
@pytest.mark.parametrize(
    "pin,x,end,y,before",
    [
        ("54", "49.925", "50.7", "28.2", True),
        ("54", "49.925", "50.6", "26.375", False),
        ("53", "51.475", "50.7", "28.2", True),
        ("53", "51.475", "52.3", "26.375", False),
    ],
)
def test_boundary_track_side_branch_is_distinguished_from_post_capacitor_feed(
    tmp_path: Path, pin: str, x: str, end: str, y: str, before: bool
) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    net = "1" if pin == "54" else "18"
    # A real F.Cu spur separates its via from the capacitor-contacting item.
    # Same-net endpoints after the bank are benign controls, not failures.
    patch = f"""
(segment (start {x} {y}) (end {end} {y}) (width 0.2) (layer "F.Cu") (net {net}) (uuid "58bd2f2a-4491-4454-924c-7d7c1f7c3e6d"))
(via (at {end} {y}) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net {net}) (uuid "1b2a439c-eb5c-42d5-ac41-7b08e51eb939"))
"""
    if pin == "54":
        patch += f"""
(segment (start {end} 26.375) (end 49.925 26.375) (width 0.25) (layer "In2.Cu") (net 1) (uuid "f8f4c1a1-f947-4f51-93a5-7cae70460b8e"))
"""
        if before:
            patch += f"""
(segment (start {end} {y}) (end {end} 26.375) (width 0.25) (layer "In2.Cu") (net 1) (uuid "f5ebd00f-cff0-4f01-97d1-41a67e2edac9"))
"""
    board = cad / "rev_a.kicad_pcb"
    board.write_text(BOARD.read_text().rstrip()[:-1] + patch + ")\n")
    report = _native_report(cad)
    assert all(report[k] == [] for k in ("violations", "schematic_parity", "unconnected_items"))
    rows = _front_paths(board)
    terminal = "1" if pin == "54" else "2"
    for cap in ("C16", "C27"):
        row = rows[f"{pin}:{cap}:{terminal}"]
        assert isinstance(row, dict)
        assert isinstance(row["trace_mm"], (float, int))
        assert row["trace_mm"] <= _BYPASS_LIMITS[pin, cap, terminal]
        exits: object = row["pre_bypass_exits"]
        assert isinstance(exits, list)
        assert bool(exits) is (before and cap == "C27")


# Local layout decision after PR63, not a manufacturer trace-length/noise limit:
# outputs may escape on In2 only in the ADC-side rectangle; their long runs must
# be on F. Both face the single In1 GND plane. No B routing or extra layer pair.
_OUTPUT_REFERENCE_SCRIPT = r"""
import json, sys
import pcbnew as p
assert p.Version() == "9.0.2"
b = p.LoadBoard(sys.argv[1])
b.BuildConnectivity()
planes = [z for z in b.Zones() if z.GetNetname() == "GND" and z.IsOnLayer(p.In1_Cu)]
assert len(planes) == 1
reference = planes[0].GetFilledPolysList(p.In1_Cu)
assert reference.OutlineCount() == 1
error = p.FromMM(0.005)

def shape(item, clearance=0):
    poly = p.SHAPE_POLY_SET()
    item.TransformShapeToPolygon(poly, item.GetLayer(), clearance, error, p.ERROR_OUTSIDE)
    return poly

rows = {}
for name in ("MISO", "DRDY"):
    items = [t for t in b.GetTracks() if t.GetNetname() == name]
    vias = [t for t in items if t.Type() == p.PCB_VIA_T]
    traces = [t for t in items if t.Type() != p.PCB_VIA_T]
    layers = sorted({b.GetLayerName(t.GetLayer()) for t in traces})
    inner = [t for t in traces if t.GetLayer() == p.In2_Cu]
    # Exempt only the unavoidable voids at THIS signal's own through contacts.
    # 25um over the declared zone clearance covers polygon approximation;
    # it is not a general tolerance for gaps beneath the route.
    allowed = p.SHAPE_POLY_SET(reference)
    terminals = [pad for f in b.GetFootprints() for pad in f.Pads()
                 if pad.GetNetname() == name and pad.IsOnLayer(p.In1_Cu)]
    for contact in vias + terminals:
        allowed.BooleanAdd(shape(contact, planes[0].GetLocalClearance() + p.FromMM(0.025)))
    uncovered = p.SHAPE_POLY_SET()
    for track in traces:
        projected = shape(track)
        projected.BooleanSubtract(allowed)
        uncovered.BooleanAdd(projected)
    bounds_ok = all(50 <= p.ToMM(v.x) <= 56 and 29.5 <= p.ToMM(v.y) <= 36.5
                    for t in inner for v in (t.GetStart(), t.GetEnd()))
    rows[name] = {
        "layers": layers, "segments": len(traces), "vias": len(vias),
        "inner_trace_mm": sum(p.ToMM(t.GetLength()) for t in inner),
        "inner_in_escape_rectangle": bounds_ok,
        "unreferenced_projection_mm2": uncovered.Area() / 1e12,
    }
print(json.dumps(rows))
"""


def _output_reference(board: Path) -> dict[str, object]:
    result = subprocess.run(
        [
            os.environ.get("KICAD_PYTHON", "/usr/bin/python3"),
            "-c",
            _OUTPUT_REFERENCE_SCRIPT,
            str(board),
        ],
        capture_output=True,
        text=True,
        timeout=45,
        env=dict(os.environ, KICAD_CONFIG_HOME=str(board.parent / "output-config")),
    )
    (board.parent / "output-reference.log").write_text(result.stdout + result.stderr)
    assert result.returncode == 0, result.stdout + result.stderr
    rows: object = json.loads(result.stdout)
    assert isinstance(rows, dict)
    (board.parent / "output-reference.json").write_text(json.dumps(rows, indent=2) + "\n")
    return rows


def _output_reference_ok(row: object) -> bool:
    assert isinstance(row, dict)
    assert isinstance(row["segments"], int) and isinstance(row["vias"], int)
    assert isinstance(row["inner_trace_mm"], (int, float))
    assert isinstance(row["unreferenced_projection_mm2"], (int, float))
    return (
        (row["layers"] == ["F.Cu"] or row["layers"] == ["F.Cu", "In2.Cu"])
        and row["segments"] > 0
        and row["vias"] <= 2
        and row["inner_trace_mm"] <= 10.0
        and row["inner_in_escape_rectangle"] is True
        # Boolean clipping in native integer coordinates, not point sampling.
        and row["unreferenced_projection_mm2"] <= 0.00001
    )


@pytest.fixture(scope="module")
def output_reference(native_placement: tuple[Path, dict[str, object]]) -> dict[str, object]:
    cad, report = native_placement
    assert all(report[k] == [] for k in ("violations", "schematic_parity", "unconnected_items"))
    return _output_reference(cad / "rev_a.kicad_pcb")


@pytest.mark.schematic
@pytest.mark.parametrize("net", ["MISO", "DRDY"])
def test_output_corridor_uses_front_runs_and_local_ground_referenced_escapes(
    output_reference: dict[str, object], net: str
) -> None:
    assert _output_reference_ok(output_reference[net]), output_reference[net]


_OUTPUT_MUTATION_SCRIPT = r"""
import sys
import pcbnew as p
assert p.Version() == "9.0.2"
b = p.LoadBoard(sys.argv[1])
net, change = sys.argv[2:]
tracks = [t for t in b.GetTracks() if t.GetNetname() == net and t.Type() != p.PCB_VIA_T]
assert tracks
if change == "back-escape":
    inner = [t for t in tracks if t.GetLayer() == p.In2_Cu]
    assert inner
    for t in inner:
        t.SetLayer(p.B_Cu)
elif change == "reverse":
    for t in tracks:
        start, end = p.VECTOR2I(t.GetStart()), p.VECTOR2I(t.GetEnd())
        t.SetStart(end)
        t.SetEnd(start)
elif change == "subdivide":
    t = max((t for t in tracks if t.GetLayer() == p.F_Cu), key=lambda t: t.GetLength())
    start, end = p.VECTOR2I(t.GetStart()), p.VECTOR2I(t.GetEnd())
    middle = p.VECTOR2I((start.x + end.x) // 2, (start.y + end.y) // 2)
    tail = p.PCB_TRACK(b)
    tail.SetStart(middle)
    tail.SetEnd(end)
    tail.SetLayer(t.GetLayer())
    tail.SetWidth(t.GetWidth())
    tail.SetNetCode(t.GetNetCode())
    t.SetEnd(middle)
    b.Add(tail)
elif change == "plane-window":
    # A small native copper-pour keepout cuts the reference beneath both long
    # front runs, but leaves the surrounding GND region and all signals connected.
    z = p.ZONE(b)
    z.SetLayer(p.In1_Cu)
    z.SetIsRuleArea(True)
    z.SetDoNotAllowCopperPour(True)
    z.SetDoNotAllowTracks(False)
    z.SetDoNotAllowVias(False)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    z.Outline().NewOutline()
    for x, y in ((69.5, 30.0), (70.5, 30.0), (70.5, 31.4), (69.5, 31.4)):
        z.Outline().Append(p.FromMM(x), p.FromMM(y))
    b.Add(z)
else:
    raise ValueError(change)
p.SaveBoard(sys.argv[1], b)
"""


def _output_mutation(cad: Path, net: str, change: str) -> None:
    shutil.copytree(CAD, cad)
    board = cad / "rev_a.kicad_pcb"
    shutil.copyfile(BOARD, board)
    result = subprocess.run(
        [
            os.environ.get("KICAD_PYTHON", "/usr/bin/python3"),
            "-c",
            _OUTPUT_MUTATION_SCRIPT,
            str(board),
            net,
            change,
        ],
        capture_output=True,
        text=True,
        timeout=45,
        env=dict(os.environ, KICAD_CONFIG_HOME=str(cad / "mutation-config")),
    )
    (cad / "mutation.log").write_text(result.stdout + result.stderr)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.schematic
@pytest.mark.parametrize("net", ["MISO", "DRDY"])
@pytest.mark.parametrize("change", ["back-escape", "reverse", "subdivide"])
def test_output_guard_rejects_wrong_layer_but_accepts_benign_copper_edits(
    tmp_path: Path, net: str, change: str
) -> None:
    cad = tmp_path / "cad"
    _output_mutation(cad, net, change)
    report = _native_report(cad)
    assert all(report[k] == [] for k in ("violations", "schematic_parity", "unconnected_items"))
    rows = _output_reference(cad / "rev_a.kicad_pcb")
    assert _output_reference_ok(rows[net]) is (change != "back-escape"), rows[net]
    other = "DRDY" if net == "MISO" else "MISO"
    assert _output_reference_ok(rows[other]), rows[other]


@pytest.mark.schematic
def test_connected_plane_window_fails_output_reference_even_with_clean_drc(tmp_path: Path) -> None:
    cad = tmp_path / "cad"
    _output_mutation(cad, "MISO", "plane-window")
    report = _native_report(cad)
    assert all(report[k] == [] for k in ("violations", "schematic_parity", "unconnected_items"))
    rows = _output_reference(cad / "rev_a.kicad_pcb")
    for net in ("MISO", "DRDY"):
        assert not _output_reference_ok(rows[net]), rows[net]
        row = rows[net]
        assert isinstance(row, dict)
        assert row["layers"] == ["F.Cu", "In2.Cu"]  # Fails reference, not layer policy.
