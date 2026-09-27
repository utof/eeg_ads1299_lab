"""Offline consistency of a dated manufacturer snapshot, not live lifecycle checks."""

import json
import re
from pathlib import Path

import pytest

from hardware.rev_a import load_documents
from lab.validation import read_object

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "docs/references/murata_20260927/source_record.json"
EXPECTED = [
    ("input_c", "GRM1885C1H472JA01", "B", 4),
    ("bias_c", "GRM1885C1H152JA01", "B", 1),
    ("decap_1u", "GRM188R61E105KA12", "C", 15),
    ("decap_100n", "GRM188R71H104KA93", "C", 7),
    ("bulk_10u", "GRM219R61A106KE44", "D", 4),
]


def _record() -> dict[str, object]:
    return read_object(json.loads(RECORD.read_text()), "capacitor source record")


@pytest.mark.parametrize(("role", "core", "status", "quantity"), EXPECTED)
def test_exact_bom_parts_have_dated_manufacturer_rows(
    role: str, core: str, status: str, quantity: int
) -> None:
    _, bom, _ = load_documents()
    line = next(line for line in bom["line_items"] if line["id"] == role)
    parts = read_object(_record()["selected_parts"], "selected parts")
    row = read_object(parts[line["mpn"]], "manufacturer row")
    assert line["mpn"] == core + "D"
    assert line["quantity"] == len(line["references"]) == quantity
    assert row["part_number"] == core and row["public_part_number"] == core + "#"
    assert [row["production_status_" + lang] for lang in ("ja", "en-us", "zh-cn")] == [status] * 3
    assert row["Condition"] == ("1kHz / 0.5Vrms" if role == "bulk_10u" else "1kHz / 1Vrms")
    pdf = read_object(row["technical_pdf"], "technical PDF")
    assert pdf["typical_only"] is True
    assert "partnumber=" + core + "&" in str(pdf["url"])
    assert re.fullmatch(r"[0-9a-f]{64}", str(pdf["sha256"]))


def test_snapshot_covers_selected_murata_inventory_without_becoming_a_new_bom() -> None:
    _, bom, _ = load_documents()
    selected = {line["mpn"] for line in bom["line_items"] if line["manufacturer"] == "Murata"}
    assert set(read_object(_record()["selected_parts"], "parts")) == selected
    assert len(selected) == 5
    assert sum(quantity for _, _, _, quantity in EXPECTED) == 31


def test_planned_discontinuation_is_not_relabelled_as_stopped_production() -> None:
    legend = read_object(_record()["status_legend"], "legend")
    assert legend["codes"] == {"B": "In Production", "C": "To be discontinued", "D": "Discontinued"}
    assert re.fullmatch(r"[0-9a-f]{64}", str(legend["sha256"]))


def test_typical_catalog_evidence_cannot_claim_qualification_or_a_pcn_date() -> None:
    data = _record()
    assert data["scope"] == "dated_manufacturer_evidence_not_a_bom_or_live_readiness_gate"
    assert data["captured_date_utc"] == "2026-09-27"
    assert data["manufacturer_pcn_obtained"] is False
    assert data["discontinuation_dates_verified"] is False
    assert data["assembly_qualified"] is False
    assert data["minimum_effective_capacitance_qualified"] is False
    assert data["replacement_selected"] is False
    catalog = read_object(data["catalog"], "catalog")
    assert catalog["url"] == "https://ds.murata.com/simsurfing_data/data/mlcc.zip"
    assert re.fullmatch(r"[0-9a-f]{64}", str(catalog["csv_sha256"]))
