"""Check the native review BOM against the already-validated connectivity inventory."""

import csv
import io
from collections.abc import Iterator

from .check_schematic import SchematicNetlist, SchematicPart

_BOM_COLUMNS = (
    "Reference",
    "ContractRef",
    "Value",
    "MPN",
    "Footprint",
    "Population",
    "DNP",
    "OffBoard",
)


def _bom_row(ref: str, part: SchematicPart) -> dict[str, str]:
    return {
        "Reference": part.native_ref,
        "ContractRef": ref,
        "Value": part.value,
        "MPN": part.properties.get("MPN", ""),
        "Footprint": part.footprint,
        "Population": part.properties.get("Population", ""),
        "DNP": "DNP" if "dnp" in part.properties else "",
        "OffBoard": "Excluded from board" if "exclude_from_board" in part.properties else "",
    }


def _bom_csv_rows(content: str) -> Iterator[dict[str, str]]:
    try:
        reader = (row for row in csv.reader(io.StringIO(content, newline=""), strict=True) if row)
        header = next(reader, list[str]())
        if len(header) != len(_BOM_COLUMNS) or set(header) != set(_BOM_COLUMNS):
            raise ValueError("BOM CSV requires each declared column exactly once")
        for cells in reader:
            if len(cells) != len(header):
                raise ValueError("BOM CSV row has missing/extra cells")
            yield dict(zip(header, cells, strict=True))
    except csv.Error as exc:
        raise ValueError("malformed BOM CSV export") from exc


def validate_schematic_bom(content: str, netlist: SchematicNetlist) -> None:
    """Require a complete native CSV matching the already-validated XML inventory.

    Call validate_schematic first: this cross-export check does not independently
    approve the circuit. Locale is pinned to C by the native gate. Header/row
    order and CSV quoting may vary, but each ungrouped component must appear once,
    including DNP and the off-board controller; field substitutions are rejected.
    """
    if len(content) > 2_000_000 or not netlist.parts:
        raise ValueError("BOM CSV oversized or expected component inventory empty")
    seen: set[str] = set()
    for row in _bom_csv_rows(content):
        ref = row["ContractRef"]
        if ref not in netlist.parts or ref in seen:
            raise ValueError(f"BOM CSV has unknown/duplicate component {ref!r}")
        if row != _bom_row(ref, netlist.parts[ref]):
            raise ValueError(f"BOM CSV fields differ from validated XML for {ref}")
        seen.add(ref)
    if seen != set(netlist.parts):
        raise ValueError("BOM CSV component inventory is incomplete")
