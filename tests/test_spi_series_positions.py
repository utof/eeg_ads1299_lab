"""L4 fail-first connectivity requirements, not added PCB lands or damping approval.

Fresh native exports must still match these retained fixtures through the existing
schematic gate. These tests do not turn fixture edits into native CAD evidence.
"""

import gzip
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import pytest

from hardware.rev_a import SchematicNetlist, parse_schematic_xml

ROOT = Path(__file__).resolve().parents[1]
Pin = tuple[str, str]
Board = Literal["afe", "auxiliary"]


@dataclass(frozen=True)
class SeriesPosition:
    board: Board
    reference: str
    driver: Pin
    function: str
    kind: str
    downstream: frozenset[Pin]


# Native references are independent of any new ContractRef spelling. Pad 1 is
# the L4 driver-side drawing convention; the component itself is nonpolar.
POSITIONS = (
    SeriesPosition(
        "auxiliary",
        "R117",
        ("U102", "13"),
        "B1Y",
        "tri_state",
        frozenset({("J101", "1")}),
    ),
    SeriesPosition(
        "auxiliary",
        "R118",
        ("U102", "12"),
        "B2Y",
        "tri_state",
        frozenset({("J101", "3")}),
    ),
    SeriesPosition(
        "auxiliary",
        "R119",
        ("U102", "11"),
        "B3Y",
        "tri_state",
        frozenset({("J101", "7")}),
    ),
    SeriesPosition(
        "auxiliary",
        "R120",
        ("U102", "5"),
        "A4Y",
        "tri_state",
        frozenset({("J102", "19"), ("R114", "1")}),
    ),
    SeriesPosition(
        "afe",
        "R24",
        ("U1", "43"),
        "DOUT",
        "output",
        frozenset({("J1", "5"), ("MOD1", "GPIO13")}),
    ),
)


@pytest.fixture(scope="module")
def spi_graphs() -> dict[Board, SchematicNetlist]:
    fixtures: dict[Board, str] = {
        "afe": "rev_a_netlist.xml.gz",
        "auxiliary": "auxiliary_c3_netlist.xml.gz",
    }
    return {
        board: parse_schematic_xml(
            gzip.decompress((ROOT / "tests/fixtures" / name).read_bytes()).decode()
        )
        for board, name in fixtures.items()
    }


def _native_nodes(graph: SchematicNetlist, anchor: Pin) -> frozenset[Pin]:
    references = {part.native_ref: ref for ref, part in graph.parts.items()}
    key = (references[anchor[0]], anchor[1])
    code = graph.nets[key]
    return frozenset(
        (graph.parts[ref].native_ref, pin) for (ref, pin), net in graph.nets.items() if net == code
    )


@pytest.mark.parametrize("position", POSITIONS, ids=[position.reference for position in POSITIONS])
def test_each_spi_driver_has_its_own_two_terminal_series_boundary(
    spi_graphs: dict[Board, SchematicNetlist], position: SeriesPosition
) -> None:
    graph = spi_graphs[position.board]
    references = {part.native_ref: ref for ref, part in graph.parts.items()}
    assert position.reference in references, f"L4 series position missing: {position.reference}"
    ref = references[position.reference]
    part = graph.parts[ref]
    assert part.symbol == "R"
    assert part.footprint == "Resistor_SMD:R_0603_1608Metric"
    assert "exclude_from_board" not in part.properties
    assert {pin for owner, pin in graph.nets if owner == ref} == {"1", "2"}
    assert all(graph.pin_types[(ref, pin)] == "passive" for pin in ("1", "2"))
    driver = (references[position.driver[0]], position.driver[1])
    assert (graph.pin_functions[driver], graph.pin_types[driver]) == (
        position.function,
        position.kind,
    )
    assert _native_nodes(graph, position.driver) == frozenset(
        {position.driver, (position.reference, "1")}
    ), "driver net must not also reach a receiver, shunt or bypass"
    assert _native_nodes(graph, (position.reference, "2")) == (
        position.downstream | {(position.reference, "2")}
    ), "downstream endpoints must remain together, without a netlist bypass"


def test_miso_pulldown_remains_a_receiver_shunt_not_a_series_spare(
    spi_graphs: dict[Board, SchematicNetlist],
) -> None:
    graph = spi_graphs["auxiliary"]
    references = {part.native_ref: ref for ref, part in graph.parts.items()}
    shunt = graph.parts[references["R114"]]
    assert (shunt.symbol, shunt.value, shunt.properties["MPN"]) == (
        "R",
        "42.2k",
        "RC0603FR-0742K2L",
    )
    assert shunt.properties["Population"] == "fit" and "dnp" not in shunt.properties
    assert ("J102", "19") in _native_nodes(graph, ("R114", "1"))
    assert ("U102", "7") in _native_nodes(graph, ("R114", "2"))
    assert _native_nodes(graph, ("R114", "1")) != _native_nodes(graph, ("R114", "2"))
