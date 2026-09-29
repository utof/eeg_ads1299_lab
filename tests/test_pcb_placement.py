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
    "MISO": "eb47d5fb-3385-5bc7-901b-bb3b45b51abd",
    "DRDY": "882fbba2-92c6-5003-bc76-a49f900880dd",
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
