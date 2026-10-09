"""Exercise actual AFE selector/aggregation code, not native polygon geometry."""

import ast
import copy
from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from tests.test_pcb_placement import (
    _OUTPUT_MUTATION_SCRIPT,
    _OUTPUT_REFERENCE_SCRIPT,
    _output_reference_ok,
)


@dataclass(frozen=True)
class _Track:
    ident: str
    net: str
    layer: int = 0
    kind: int = 1

    def GetNetname(self) -> str:
        return self.net

    def GetLayer(self) -> int:
        return self.layer

    def Type(self) -> int:
        return self.kind


@dataclass(frozen=True)
class _Board:
    tracks: tuple[_Track, ...]
    split: bool

    def GetTracks(self) -> tuple[_Track, ...]:
        return self.tracks

    def GetLayerName(self, layer: int) -> str:
        return {0: "F.Cu", 2: "In2.Cu", 31: "B.Cu"}[layer]

    def FindFootprintByReference(self, reference: str) -> object | None:
        return self if reference == "R24" and self.split else None


def _assigns(node: ast.stmt, name: str) -> bool:
    return isinstance(node, ast.Assign) and any(
        isinstance(target, ast.Name) and target.id == name for target in node.targets
    )


def _reference_selection(board: _Board) -> object:
    """Run the real per-net selection prefix; stop before any shape operation."""
    loops = [
        node
        for node in ast.parse(_OUTPUT_REFERENCE_SCRIPT).body
        if isinstance(node, ast.For)
        and isinstance(node.target, ast.Name)
        and node.target.id == "name"
    ]
    assert len(loops) == 1, "review the selector adapter after probe restructuring"
    loop = copy.deepcopy(loops[0])
    boundary = next(i for i, statement in enumerate(loop.body) if _assigns(statement, "allowed"))
    loop.body = loop.body[:boundary] + ast.parse(
        "selected[name] = tuple(item.ident for item in items)"
    ).body
    scope: dict[str, object] = {
        "b": board,
        "p": SimpleNamespace(PCB_VIA_T=2, In2_Cu=2),
        "selected": {},
    }
    exec(compile(ast.Module(body=[loop], type_ignores=[]), "<AFE-selection>", "exec"), scope)
    return scope["selected"]


@pytest.mark.parametrize("split", [False, True])
def test_reference_screen_visits_every_physical_response_segment(split: bool) -> None:
    tracks = (_Track("out", "MISO"), _Track("ready", "DRDY"), _Track("foreign", "MISO_DRV_SPARE"))
    expected = {"MISO": ("out",), "DRDY": ("ready",)}
    if split:
        tracks += (_Track("driver", "MISO_DRV", 2),)
        expected["MISO_DRV"] = ("driver",)
    assert _reference_selection(_Board(tracks, split)) == expected


@pytest.mark.parametrize("fault", ["missing-driver", "stray-driver", "missing-receiver"])
def test_reference_selection_rejects_incomplete_or_unexpected_splits(fault: str) -> None:
    tracks = [_Track("out", "MISO"), _Track("ready", "DRDY"), _Track("driver", "MISO_DRV", 2)]
    if fault == "missing-driver":
        tracks.pop()
    elif fault == "missing-receiver":
        tracks.pop(0)
    with pytest.raises(AssertionError):
        _reference_selection(_Board(tuple(tracks), fault != "stray-driver"))


def test_native_mutations_include_driver_copper_without_changing_net_identity() -> None:
    statements = [
        node
        for node in ast.parse(_OUTPUT_MUTATION_SCRIPT).body
        if _assigns(node, "names") or _assigns(node, "tracks")
    ]
    tracks = (
        _Track("receiver", "MISO"),
        _Track("driver", "MISO_DRV", 2),
        _Track("via", "MISO_DRV", 0, 2),
        _Track("other", "DRDY"),
        _Track("spare", "MISO_DRV_SPARE"),
    )
    scope: dict[str, object] = {
        "b": _Board(tracks, True),
        "p": SimpleNamespace(PCB_VIA_T=2),
        "net": "MISO",
    }
    exec(
        compile(ast.Module(body=statements, type_ignores=[]), "<AFE-mutation-selection>", "exec"),
        scope,
    )
    assert scope["tracks"] == [tracks[0], tracks[1]]
    assert tuple(track.net for track in tracks) == (
        "MISO",
        "MISO_DRV",
        "MISO_DRV",
        "DRDY",
        "MISO_DRV_SPARE",
    )


def _row() -> dict[str, object]:
    return {
        "layers": ["F.Cu", "In2.Cu"],
        "segments": 2,
        "vias": 1,
        "inner_trace_mm": 4.0,
        "inner_in_escape_rectangle": True,
        "inner_tracks_straight": True,
        "unreferenced_projection_mm2": 0.0,
    }


def _combine(rows: dict[str, dict[str, object]]) -> dict[str, object]:
    functions = [
        node
        for node in ast.parse(_OUTPUT_REFERENCE_SCRIPT).body
        if isinstance(node, ast.FunctionDef) and node.name == "combine_output_rows"
    ]
    assert len(functions) == 1, "missing whole-channel output aggregation"
    scope: dict[str, object] = {"rows": rows}
    statements: list[ast.stmt] = [
        *functions,
        *ast.parse("combined = combine_output_rows(rows)").body,
    ]
    exec(
        compile(ast.Module(body=statements, type_ignores=[]), "<AFE-row-aggregation>", "exec"),
        scope,
    )
    result = scope["combined"]
    assert isinstance(result, dict)
    return result


def test_legacy_output_metrics_are_unchanged() -> None:
    rows = {"MISO": _row(), "DRDY": _row()}
    assert _combine(copy.deepcopy(rows)) == rows


@pytest.mark.parametrize(
    "fault", ["none", "via-total", "length-total", "layer", "rectangle", "arc", "void"]
)
def test_split_does_not_reset_the_existing_whole_channel_limits(fault: str) -> None:
    rows = {"MISO": _row(), "MISO_DRV": _row(), "DRDY": _row()}
    if fault == "via-total":
        rows["MISO_DRV"]["vias"] = 2
    elif fault == "length-total":
        rows["MISO_DRV"]["inner_trace_mm"] = 6.1
    elif fault == "layer":
        rows["MISO_DRV"]["layers"] = ["B.Cu"]
    elif fault == "rectangle":
        rows["MISO_DRV"]["inner_in_escape_rectangle"] = False
    elif fault == "arc":
        rows["MISO_DRV"]["inner_tracks_straight"] = False
    elif fault == "void":
        rows["MISO_DRV"]["unreferenced_projection_mm2"] = 0.00002
    saved = copy.deepcopy(rows)
    result = _combine(rows)
    assert rows == saved, "aggregation must not rewrite electrical-net measurements"
    assert _output_reference_ok(result["MISO"]) is (fault == "none")
    assert result["DRDY"] == saved["DRDY"]
    if fault in ("via-total", "length-total"):
        assert _output_reference_ok(rows["MISO"]) and _output_reference_ok(rows["MISO_DRV"])


def test_own_contact_exclusion_does_not_borrow_contacts_across_the_split() -> None:
    """Execute the real terminal selector using only net/layer getter doubles."""
    selectors = [
        node
        for node in ast.walk(ast.parse(_OUTPUT_REFERENCE_SCRIPT))
        if isinstance(node, ast.Assign) and _assigns(node, "terminals")
    ]
    assert len(selectors) == 1, "review terminal-exclusion adapter"

    @dataclass(frozen=True)
    class Pad:
        net: str
        inner: bool = True

        def GetNetname(self) -> str:
            return self.net

        def IsOnLayer(self, layer: int) -> bool:
            assert layer == 1
            return self.inner

    pads = [Pad("MISO"), Pad("MISO_DRV"), Pad("MISO_DRV", False), Pad("DRDY")]
    board = SimpleNamespace(GetFootprints=lambda: [SimpleNamespace(Pads=lambda: pads)])
    for net, expected in (("MISO", [pads[0]]), ("MISO_DRV", [pads[1]])):
        scope: dict[str, object] = {"b": board, "name": net, "p": SimpleNamespace(In1_Cu=1)}
        exec(
            compile(ast.Module(body=selectors, type_ignores=[]), "<own-contact-selection>", "exec"),
            scope,
        )
        assert scope["terminals"] == expected
