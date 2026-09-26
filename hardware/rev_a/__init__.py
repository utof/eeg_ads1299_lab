"""Public, standard-library-only Rev A contract API. Never enables hardware."""

from .check_baseline import (
    BillOfMaterials,
    BoardProfile,
    CostTotals,
    SourcesDocument,
    load_documents,
    totals,
    validate,
)
from .check_schematic import (
    SchematicNetlist,
    SchematicPart,
    parse_schematic_xml,
    validate_schematic,
)
from .schematic_bom import validate_schematic_bom
from .schematic_sources import read_schematic_file, schematic_source_snapshot, validate_erc

__all__ = [
    "BillOfMaterials",
    "BoardProfile",
    "CostTotals",
    "SchematicNetlist",
    "SchematicPart",
    "SourcesDocument",
    "load_documents",
    "parse_schematic_xml",
    "read_schematic_file",
    "schematic_source_snapshot",
    "totals",
    "validate",
    "validate_erc",
    "validate_schematic",
    "validate_schematic_bom",
]
