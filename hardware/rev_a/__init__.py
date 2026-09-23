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

__all__ = [
    "BillOfMaterials",
    "BoardProfile",
    "CostTotals",
    "SourcesDocument",
    "load_documents",
    "totals",
    "validate",
]
