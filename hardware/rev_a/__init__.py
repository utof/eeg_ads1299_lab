"""Public, standard-library-only Rev A contract API. Never enables hardware."""

from .auxiliary import (
    AuxiliaryContract,
    auxiliary_source_snapshot,
    parse_auxiliary_contract,
    validate_auxiliary,
    validate_auxiliary_erc,
)
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
from .footprint_geometry import FootprintPad, validate_footprint
from .harness import HarnessNet, bench_harness
from .pcb_seed import make_pcb_seed
from .schematic_bom import validate_schematic_bom
from .schematic_sources import read_schematic_file, schematic_source_snapshot, validate_erc

__all__ = [
    "AuxiliaryContract",
    "BillOfMaterials",
    "BoardProfile",
    "CostTotals",
    "FootprintPad",
    "HarnessNet",
    "SchematicNetlist",
    "SchematicPart",
    "SourcesDocument",
    "auxiliary_source_snapshot",
    "bench_harness",
    "load_documents",
    "make_pcb_seed",
    "parse_auxiliary_contract",
    "parse_schematic_xml",
    "read_schematic_file",
    "schematic_source_snapshot",
    "totals",
    "validate",
    "validate_auxiliary",
    "validate_auxiliary_erc",
    "validate_erc",
    "validate_footprint",
    "validate_schematic",
    "validate_schematic_bom",
]
