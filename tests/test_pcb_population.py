"""Population/inventory regressions; synthetic records are not native CAD evidence."""

import ast
import copy
import re
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace

import pytest

from hardware.rev_a import BillOfMaterials, load_documents
from tests import test_pcb_placement as placement
from tests.auxiliary_placement_probe import SCRIPT
from tests.test_pcb_power import _form_end

# Inventory-only input: deliberately no placement/routing qualification is implied.
_SERIES = """(footprint "Resistor_SMD:R_0603_1608Metric"
(property "Reference" "R24") (property "ContractRef" "R_MISO_SER")
(property "Value" "NOT_SELECTED") (property "MPN" "NOT_SELECTED")
(property "BOM_ID" "spi_series") (property "Population" "dnp")
(attr smd dnp) (pad "1" smd roundrect) (pad "2" smd roundrect))"""


def _part(text: str, reference: str) -> str:
    block = placement._footprint_block(text, reference)
    return block[: _form_end(block, 0)]


def _field(text: str, reference: str, name: str, value: str) -> str:
    before = _part(text, reference)
    after, count = re.subn(rf'(\(property\s+"{name}"\s+)"[^"]*"', rf'\g<1>"{value}"', before)
    assert count == 1
    return text.replace(before, after, 1)


def _series_bom(bom: BillOfMaterials) -> BillOfMaterials:
    result = copy.deepcopy(bom)
    row = copy.deepcopy(next(item for item in result["line_items"] if item["id"] == "input_r"))
    row.update(
        id="spi_series",
        references=["R_MISO_SER"],
        quantity=1,
        population="dnp",
        mpn="NOT_SELECTED",
        spec={},
    )
    result["line_items"] = [item for item in result["line_items"] if item["id"] != "spi_series"]
    result["line_items"].append(row)
    return result


def _inventory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, text: str, bom: BillOfMaterials
) -> None:
    board = tmp_path / "inventory-only.kicad_pcb"
    board.write_text(text)
    profile, _, sources = load_documents()
    monkeypatch.setattr(placement, "BOARD", board)
    monkeypatch.setattr(placement, "load_documents", lambda: (profile, bom, sources), raising=False)
    placement.test_editable_placement_is_a_tracked_design_not_a_parking_grid()


def test_afe_inventory_accepts_the_explicit_unpopulated_series_addition(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    text = placement.BOARD.read_text()
    if not re.search(r'"Reference"\s+"R24"', text):
        text = text[: text.rfind(")")] + _SERIES + "\n)\n"
    _inventory(tmp_path, monkeypatch, text, _series_bom(load_documents()[1]))


@pytest.mark.parametrize("fault", ["population-field", "native-swap", "duplicate", "bom-fit"])
def test_afe_inventory_does_not_accept_equal_counts_with_wrong_population(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    text, bom = placement.BOARD.read_text(), copy.deepcopy(load_documents()[1])
    if fault == "population-field":
        text = _field(text, "D1", "Population", "fit")
    elif fault == "native-swap":
        before = _part(text, "D1")
        text = text.replace(before, before.replace(" dnp)", ")", 1), 1)
        before = _part(text, "R1")
        text = text.replace(before, before.replace("(attr smd)", "(attr smd dnp)", 1), 1)
    elif fault == "duplicate":
        text = _field(text, "R1", "Reference", "R2")
    else:
        next(row for row in bom["line_items"] if row["id"] == "clamps")["population"] = "fit"
    with pytest.raises(AssertionError):
        _inventory(tmp_path, monkeypatch, text, bom)


@dataclass(frozen=True)
class _LibraryId:
    def GetLibItemName(self) -> str:
        return "R_0603_1608Metric"


@dataclass(frozen=True)
class _Footprint:
    """Only field/flag getters; no emulation of native parsing or geometry."""

    value: str = "NOT_SELECTED"
    dnp: bool = True
    excluded: bool = False
    properties: dict[str, str] = field(
        default_factory=lambda: {"Population": "dnp", "MPN": "NOT_SELECTED"}
    )

    def GetValue(self) -> str:
        return self.value

    def GetFPID(self) -> _LibraryId:
        return _LibraryId()

    def IsDNP(self) -> bool:
        return self.dnp

    def IsExcludedFromBOM(self) -> bool:
        return self.excluded

    def GetLayer(self) -> int:
        return 0

    def GetFieldText(self, name: str) -> str:
        return self.properties[name]


def _native_population_block(reference: str, row: dict[str, object], part: _Footprint) -> None:
    """Execute the actual probe statements up to pad geometry with field API doubles."""
    loops = [
        node
        for node in ast.parse(SCRIPT).body
        if isinstance(node, ast.For)
        and isinstance(node.target, ast.Name)
        and node.target.id == "row"
    ]
    assert len(loops) == 2, "review the population adapter if native loop structure changes"
    statements: list[ast.stmt] = []
    for statement in loops[0].body:
        if isinstance(statement, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "pads" for target in statement.targets
        ):
            break
        statements.append(statement)
    else:
        raise AssertionError("native pad boundary missing")
    scope: dict[str, object] = {"row": row, "fs": {reference: part}, "p": SimpleNamespace(F_Cu=0)}
    exec(
        compile(ast.Module(body=statements, type_ignores=[]), "<native-population>", "exec"), scope
    )


def _row(reference: str) -> dict[str, object]:
    return {
        "reference": reference,
        "population": "dnp",
        "in_bom": True,
        "value": "NOT_SELECTED",
        "mpn": "NOT_SELECTED",
        "footprint": "Resistor_SMD:R_0603_1608Metric",
    }


@pytest.mark.parametrize("reference", ["R117", "R118", "R119", "R120"])
def test_native_population_block_accepts_only_the_reviewed_unpopulated_sites(
    reference: str,
) -> None:
    _native_population_block(reference, _row(reference), _Footprint())


@pytest.mark.parametrize("fault", ["native-fit", "field-fit", "declared-fit", "selected", "no-bom"])
def test_native_population_block_rejects_contradictory_series_state(fault: str) -> None:
    row, properties = _row("R117"), {"Population": "dnp", "MPN": "NOT_SELECTED"}
    dnp, excluded, value = True, False, "NOT_SELECTED"
    if fault == "native-fit":
        dnp = False
    elif fault == "field-fit":
        properties["Population"] = "fit"
    elif fault == "declared-fit":
        row["population"] = "fit"
    elif fault == "selected":
        row["value"] = value = "0"
    else:
        row["in_bom"] = False
        excluded = True
    with pytest.raises(AssertionError):
        _native_population_block("R117", row, _Footprint(value, dnp, excluded, properties))


@pytest.mark.parametrize("declared", [False, True])
def test_native_population_block_keeps_legacy_fit_parts(declared: bool) -> None:
    row = _row("R114")
    row.update(value="42.2k", mpn="RC0603FR-0742K2L")
    if declared:
        row["population"] = "fit"
    else:
        del row["population"]
    _native_population_block(
        "R114",
        row,
        _Footprint("42.2k", False, False, {"Population": "fit", "MPN": "RC0603FR-0742K2L"}),
    )


def test_native_population_block_rejects_an_unreviewed_dnp_reference() -> None:
    with pytest.raises(AssertionError):
        _native_population_block("R999", _row("R999"), _Footprint())
