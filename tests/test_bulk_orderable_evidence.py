"""The newly resolved suffix is a documented target, never a silent BOM substitution."""

import json
from pathlib import Path

import pytest

from hardware.rev_a import load_documents
from lab.validation import read_object

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "docs/references/murata_20260927/bulk_orderable_addendum.json"
CORE = "GRM21BR61C106KE15"


def _record() -> dict[str, object]:
    return read_object(json.loads(RECORD.read_text()), "orderable evidence")


@pytest.mark.parametrize("suffix,reel,quantity", [("L", 180, 3000), ("K", 330, 10000)])
def test_exact_manufacturer_packaging_does_not_inherit_the_old_d_suffix(
    suffix: str, reel: int, quantity: int
) -> None:
    data = _record()
    assert data["core"] == CORE
    packaging = read_object(data["packaging"], "packaging")
    assert set(packaging) == {"L", "K"}
    assert packaging[suffix] == {
        "mpn": CORE + suffix,
        "type": "embossed_tape",
        "reel_diameter_mm": reel,
        "reel_quantity": quantity,
    }


def test_terminal_length_e_is_not_the_gap_g() -> None:
    data = _record()
    assert data["body_mm"] == {"length": [1.9, 2.1], "width": [1.15, 1.35], "height": [1.15, 1.35]}
    assert data["terminal_geometry_mm"] == {"external_terminal_e": [0.2, 0.7], "gap_g_min": 0.7}
    source = read_object(data["source"], "source")
    assert source["document_date"] == "2023-03-19"
    assert source["manufacturer_authored_mirror"] is True
    assert source["sha256"] == "10cc75d69025ba450626bfaee4937d849c40d0e9c3d2ebd9caa2bffa7dc965f0"


def test_identity_evidence_neither_rewrites_the_snapshot_nor_approves_hardware() -> None:
    data = _record()
    assert data["scope"] == "dated_orderable_identity_not_a_bom_change"
    assert data["orderable_for_qualification"] == CORE + "L"
    assert data["qualified_or_authorized"] == {
        "current_approval_sheet": False,
        "termination_metallurgy": False,
        "assembly_lands": False,
        "minimum_effective_capacitance": False,
        "delivered_quote": False,
        "replacement": False,
        "purchase": False,
        "body_connection": False,
    }
    previous = read_object(
        json.loads((RECORD.parent / "bulk_candidate_assessment.json").read_text()), "prior screen"
    )
    assert previous["preferred_for_qualification"] == CORE
    assert previous["replacement_orderable_mpn"] is None  # Historical result remains historical.
    _, bom, _ = load_documents()
    assert next(row for row in bom["line_items"] if row["id"] == "bulk_10u")["mpn"] == (
        "GRM219R61A106KE44D"
    )
