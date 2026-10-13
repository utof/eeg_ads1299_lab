"""Native L5 pad cuts and copper bypasses. No resistor fit or hardware approval."""

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Literal

import pytest

from tests.test_auxiliary_ground import _fresh
from tests.test_auxiliary_placement import CAD as AUX_CAD
from tests.test_pcb_placement import BOARD as AFE_BOARD
from tests.test_pcb_placement import CAD as AFE_CAD
from tests.test_pcb_placement import _native_report
from tests.test_spi_series_positions import POSITIONS, Board, SeriesPosition

Mode = Literal["cut", "short"]
NETS = {
    "R117": ("AFE_SCLK_DRV", "AFE_SCLK"),
    "R118": ("AFE_MOSI_DRV", "AFE_MOSI"),
    "R119": ("AFE_CS_DRV", "AFE_CS"),
    "R120": ("MCU_MISO_DRV", "MCU_MISO"),
    "R24": ("MISO_DRV", "MISO"),
}

# Changes only a disposable PCB copy. Native parsing, connectivity, refill and
# DRC stay separate from the report-matching unit tests at the end of this file.
MUTATE = r"""
import json, sys
import pcbnew as p
assert p.Version() == '9.0.2', 'unexpected native mutation engine'
path, raw = sys.argv[1:]
spec = json.loads(raw)
b = p.LoadBoard(path)
b.BuildConnectivity()
f = b.FindFootprintByReference(spec['reference'])
assert f is not None, 'L5 native series position missing: ' + spec['reference']
assert f.IsDNP() and not f.IsExcludedFromBOM(), 'series population/BOM flags'
assert f.GetFieldText('Population') == 'dnp', 'series Population field'
assert f.GetValue() == f.GetFieldText('MPN') == 'NOT_SELECTED', 'no fitted value selected'
pads = {a.GetNumber(): a for a in f.Pads()}
assert set(pads) == {'1', '2'}
a, z = pads['1'], pads['2']
assert a.GetNetname() == spec['nets'][0] and z.GetNetname() == spec['nets'][1]
assert a.GetNetCode() != z.GetNetCode(), 'series nets must remain separate'
assert a.GetLayer() == z.GetLayer() == p.F_Cu
assert a.GetPosition() != z.GetPosition(), 'coincident series lands'
for ref, number, net in spec['endpoints']:
    owner = b.FindFootprintByReference(ref)
    assert owner is not None, 'missing physical endpoint ' + ref
    endpoint = next(pad for pad in owner.Pads() if pad.GetNumber() == number)
    assert endpoint.GetNetname() == net, 'wrong native endpoint net'
# Both sides must have actual native copper attachments before any fault is made.
attachments = {}
for number, pad in pads.items():
    attached = list(b.GetConnectivity().GetConnectedTracks(pad))
    assert attached and all(t.Type() == p.PCB_TRACE_T for t in attached), 'no straight pad escape'
    assert all(t.GetNetCode() == pad.GetNetCode() for t in attached), 'preexisting pad bypass'
    attachments[number] = attached
if spec['mode'] == 'cut':
    target = pads[spec['pin']]
    changed = [t.m_Uuid.AsString() for t in attachments[spec['pin']]]
    for track in attachments[spec['pin']]:
        b.Remove(track)
    witness = target.m_Uuid.AsString()
elif spec['mode'] == 'short':
    track = p.PCB_TRACK(b)
    track.SetStart(p.VECTOR2I(a.GetPosition()))
    track.SetEnd(p.VECTOR2I(z.GetPosition()))
    track.SetLayer(p.F_Cu)
    track.SetWidth(p.FromMM(0.2))
    track.SetNet(a.GetNet())
    b.Add(track)
    witness = track.m_Uuid.AsString()
    changed = [witness]
else:
    raise AssertionError('unknown L5 mutation')
p.SaveBoard(path, b)
print(json.dumps({'witness_uuid': witness, 'changed_track_uuids': changed,
                  'mode': spec['mode'], 'reference': spec['reference'], 'pin': spec['pin']}))
"""


def _report(cad: Path, board: Board) -> dict[str, object]:
    # Never let a failed command inherit a copied canonical/fault JSON file.
    for name in ("placement-drc.json", "p2-drc.json"):
        (cad / name).unlink(missing_ok=True)
    report = _native_report(cad) if board == "afe" else _fresh(cad)
    assert report["kicad_version"] == "9.0.2"
    return report


@pytest.fixture(scope="module")
def series_canonical(tmp_path_factory: pytest.TempPathFactory) -> dict[Board, Path]:
    """Two clean native baselines, followed by fifteen independent fault copies."""
    result: dict[Board, Path] = {}
    sources: tuple[tuple[Board, Path], ...] = (("afe", AFE_CAD), ("auxiliary", AUX_CAD))
    for board, source in sources:
        cad = tmp_path_factory.mktemp("series-" + board) / "cad"
        shutil.copytree(source, cad)
        if board == "afe":
            shutil.copyfile(AFE_BOARD, cad / AFE_BOARD.name)
        report = _report(cad, board)
        assert all(report[k] == [] for k in ("schematic_parity", "violations", "unconnected_items"))
        result[board] = cad
    return result


def _mutate(cad: Path, position: SeriesPosition, mode: Mode, pin: str) -> str:
    driver_net, receiver_net = NETS[position.reference]
    # MOD1 is the logical off-board MCU in the AFE schematic, not a PCB footprint.
    endpoints = [(position.driver[0], position.driver[1], driver_net)]
    endpoints.extend(
        (ref, number, receiver_net)
        for ref, number in sorted(position.downstream)
        if (ref, number) != ("MOD1", "GPIO13")
    )
    spec = {
        "reference": position.reference,
        "mode": mode,
        "pin": pin,
        "nets": [driver_net, receiver_net],
        "endpoints": endpoints,
    }
    name = "rev_a.kicad_pcb" if position.board == "afe" else "auxiliary.kicad_pcb"
    result = subprocess.run(
        [
            os.environ.get("KICAD_PYTHON", "/usr/bin/python3"),
            "-c",
            MUTATE,
            str(cad / name),
            json.dumps(spec),
        ],
        capture_output=True,
        text=True,
        timeout=45,
    )
    (cad / "series-mutation.log").write_text(result.stdout + result.stderr)
    assert result.returncode == 0, result.stdout + result.stderr
    raw: object = json.loads(result.stdout)
    assert isinstance(raw, dict)
    assert (raw["mode"], raw["reference"], raw["pin"]) == (mode, position.reference, pin)
    witness: object = raw["witness_uuid"]
    assert isinstance(witness, str) and witness
    (cad / "series-mutation.json").write_text(json.dumps(raw, indent=2) + "\n")
    return witness


def _item_witnesses(items: object) -> tuple[set[str], str]:
    assert isinstance(items, list)
    identifiers: set[str] = set()
    descriptions: list[str] = []
    entries: list[object] = items
    for item in entries:
        assert isinstance(item, dict)
        ident: object = item["uuid"]
        text: object = item["description"]
        assert isinstance(ident, str) and isinstance(text, str)
        identifiers.add(ident)
        descriptions.append(text)
    return identifiers, " ".join(descriptions)


def _has_witness(rows: object, kind: str, witness: str, nets: tuple[str, ...]) -> bool:
    """Match one native finding, not unrelated diagnostics elsewhere on a PCB."""
    assert isinstance(rows, list)
    records: list[object] = rows
    for row in records:
        assert isinstance(row, dict)
        if row["type"] != kind:
            continue
        items: object = row["items"]
        identifiers, descriptions = _item_witnesses(items)
        if witness in identifiers and all(f"[{net}]" in descriptions for net in nets):
            return True
    return False


@pytest.mark.schematic
@pytest.mark.parametrize("position", POSITIONS, ids=[site.reference for site in POSITIONS])
@pytest.mark.parametrize(("mode", "pin"), [("cut", "1"), ("cut", "2"), ("short", "2")])
def test_native_series_pad_fault_has_its_own_drc_witness(
    tmp_path: Path,
    series_canonical: dict[Board, Path],
    position: SeriesPosition,
    mode: Mode,
    pin: str,
) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(series_canonical[position.board], cad)
    witness = _mutate(cad, position, mode, pin)
    report = _report(cad, position.board)
    assert report["schematic_parity"] == [], "a copper fault must not change logical parity"
    if mode == "cut":
        net = NETS[position.reference][int(pin) - 1]
        assert _has_witness(report["unconnected_items"], "unconnected_items", witness, (net,))
    else:
        assert _has_witness(
            report["violations"], "shorting_items", witness, NETS[position.reference]
        )


@pytest.mark.parametrize("fault", ["none", "uuid", "net", "kind", "split-findings"])
def test_drc_witness_matching_cannot_pass_on_an_unrelated_fault(fault: str) -> None:
    """Synthetic report-matching cases, explicitly not native fault executions."""
    items: list[dict[str, str]] = [
        {"uuid": "bridge", "description": "Track [MISO_DRV] on F.Cu"},
        {"uuid": "pad-2", "description": "Pad 2 [MISO] of R24 on F.Cu"},
    ]
    rows: list[dict[str, object]] = [{"type": "shorting_items", "items": items}]
    if fault == "uuid":
        items[0]["uuid"] = "unrelated-track"
    elif fault == "net":
        items[1]["description"] = "Pad 2 [MISO_DRV] of R24 on F.Cu"
    elif fault == "kind":
        rows[0]["type"] = "clearance"
    elif fault == "split-findings":
        rows = [{"type": "shorting_items", "items": [item]} for item in items]
    assert _has_witness(rows, "shorting_items", "bridge", ("MISO_DRV", "MISO")) is (fault == "none")
