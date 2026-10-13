"""Exercise the real probe's net selection with API doubles, not native CAD evidence."""

import sys
from dataclasses import dataclass
from types import ModuleType

import pytest

from tests.test_auxiliary_clock import MEASURE


@dataclass(frozen=True)
class _Item:
    name: str
    kind: int = 1

    def Type(self) -> int:
        return self.kind

    def GetNetname(self) -> str:
        return self.name


@dataclass(frozen=True)
class _Board:
    items: list[_Item]

    def GetTracks(self) -> list[_Item]:
        return self.items


def _selected(monkeypatch: pytest.MonkeyPatch, items: list[_Item]) -> object:
    """Execute the unchanged selection preamble; deliberately do not emulate geometry."""
    native = ModuleType("pcbnew")

    def version() -> str:
        return "9.0.2"

    def load_board(_path: str) -> _Board:
        return _Board(items)

    monkeypatch.setattr(native, "Version", version, raising=False)
    monkeypatch.setattr(native, "LoadBoard", load_board, raising=False)
    monkeypatch.setattr(native, "PCB_TRACE_T", 1, raising=False)
    monkeypatch.setitem(sys.modules, "pcbnew", native)
    monkeypatch.setattr(sys, "argv", ["clock-selection-unit", "not-a-real-board"])
    parts = MEASURE.split("# Native exact segment distances", 1)
    assert len(parts) == 2, "probe selection boundary changed; review this unit adapter"
    scope: dict[str, object] = {}
    exec(compile(parts[0], "<real-clock-selection>", "exec"), scope)
    return scope["response"]


@pytest.mark.parametrize(
    ("name", "kind", "included"),
    [
        ("MCU_MISO_DRV", 1, True),
        ("MCU_MISO", 1, True),
        ("MCU_MISO_DRV", 2, False),
        ("AFE_MISO_DRV", 1, False),
        ("MCU_MISO_DRV_SPARE", 1, False),
        ("HOST_MISO", 1, False),
    ],
)
def test_clock_probe_covers_both_response_segments_only(
    monkeypatch: pytest.MonkeyPatch, name: str, kind: int, included: bool
) -> None:
    clock, receiver, candidate = _Item("MCU_SCLK"), _Item("MCU_MISO"), _Item(name, kind)
    expected = [receiver, candidate] if included else [receiver]
    assert _selected(monkeypatch, [clock, receiver, candidate]) == expected


@pytest.mark.parametrize("remaining", ["MCU_SCLK", "MCU_MISO"])
def test_clock_probe_rejects_absent_measured_side(
    monkeypatch: pytest.MonkeyPatch, remaining: str
) -> None:
    with pytest.raises(AssertionError, match="missing measured net"):
        _selected(monkeypatch, [_Item(remaining)])
