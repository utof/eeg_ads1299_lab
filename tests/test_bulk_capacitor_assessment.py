"""Dated candidate-screen facts and node accounting, never a replacement approval."""

import gzip
import json
import re
from pathlib import Path

import pytest

from hardware.rev_a import load_documents, parse_schematic_xml, validate_schematic
from lab.validation import read_object

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "docs/references/murata_20260927/bulk_candidate_assessment.json"
EXPECTED = [
    ("GRM21BR61A106KE19", "C", "X5R", "10", "1.35", "1kHz / 0.5Vrms"),
    ("GRM21BR61C106KE15", "B", "X5R", "16", "1.35", "1kHz / 0.5Vrms"),
    ("GRM21BR61E106KA73", "B", "X5R", "25", "1.4", "1kHz / 1Vrms"),
    ("GRM21BZ71C106KE15", "B", "X7R", "16", "1.45", "1kHz / 1Vrms"),
]


def _record() -> dict[str, object]:
    return read_object(json.loads(RECORD.read_text()), "bulk assessment")


@pytest.mark.parametrize(
    ("core", "status", "dielectric", "voltage", "height", "condition"), EXPECTED
)
def test_candidate_screen_retains_exact_core_status_and_test_conditions(
    core: str, status: str, dielectric: str, voltage: str, height: str, condition: str
) -> None:
    candidates = read_object(_record()["candidates"], "candidates")
    row = read_object(candidates[core], "candidate")
    assert row["part_number"] == core and row["public_part_number"] == core + "#"
    assert row["channel_code"] == "jp"
    assert [row["production_status_" + lang] for lang in ("ja", "en-us", "zh-cn")] == [status] * 3
    assert row["tempchar"] == dielectric and row["rvol"] == voltage
    assert row["size_thickness_max"] == height
    assert row["LWSize_mm_inch"] == "2012M/0805"
    assert row["capacitance_pu"] == "10μF" and row["tolerance"] == "±10%"
    assert row["Condition"] == condition
    pdf = read_object(row["technical_pdf"], "PDF")
    assert "partnumber=" + core + "&" in str(pdf["url"])
    assert re.fullmatch(r"[0-9a-f]{64}", str(pdf["sha256"]))
    assert pdf["typical_only"] is True


def test_screen_does_not_approve_a_substitution_or_guess_a_packaging_suffix() -> None:
    data = _record()
    assert data["scope"] == "bulk_candidate_screen_not_bom_or_assembly_approval"
    assert data["preferred_for_qualification"] == "GRM21BR61C106KE15"
    assert data["replacement_orderable_mpn"] is None
    assert data["replacement_selected"] is False and data["purchase_approved"] is False
    assert data["assembly_qualified"] is False and data["body_connection_authorized"] is False
    assert data["effective_capacitance_minimum_qualified"] is False
    assert data["simulator_recalibrated"] is False
    candidates = read_object(data["candidates"], "candidates")
    assert set(candidates) == {row[0] for row in EXPECTED}
    assert read_object(candidates[str(data["preferred_for_qualification"])], "preferred")[
        "production_status_en-us"
    ] == "B"


def test_all_four_bulk_instances_are_on_their_actual_distinct_nodes() -> None:
    profile, bom, _ = load_documents()
    row = next(row for row in bom["line_items"] if row["id"] == "bulk_10u")
    baseline = read_object(_record()["baseline"], "baseline")
    assert baseline["mpn"] == row["mpn"] == "GRM219R61A106KE44D"
    assert baseline["quantity"] == row["quantity"] == 4
    assert baseline["nominal_capacitance_f"] == row["spec"]["capacitance_f"] == 10e-6
    fixture = gzip.decompress((ROOT / "tests/fixtures/rev_a_netlist.xml.gz").read_bytes()).decode()
    netlist = parse_schematic_xml(fixture)
    assert validate_schematic(netlist, profile, bom) == []
    nodes = read_object(_record()["bulk_nodes"], "bulk nodes")
    assert nodes == {
        "C_VIN_BULK": "VIN_5V_AFE",
        "C_AVDD_BULK": "AVDD",
        "C_AVDD1_BULK": "AVDD",
        "C_DVDD_BULK": "DVDD",
    }
    assert set(nodes) == set(row["references"])
    # Package-pad anchors, not a guess from cap names or net-label spelling.
    anchors = {"VIN_5V_AFE": ("U2", "1"), "AVDD": ("U1", "19"), "DVDD": ("U2", "5")}
    ground = netlist.nets["U2", "2"]
    for ref, label in nodes.items():
        assert isinstance(label, str)
        assert {netlist.nets[ref, pin] for pin in ("1", "2")} == {
            ground,
            netlist.nets[anchors[label]],
        }


def test_typical_curve_comparisons_remain_conditioned_and_incomplete() -> None:
    data = _record()
    curves = read_object(data["visual_curve_estimates"], "curve estimates")
    assert curves["kind"] == "coarse_visual_typical_not_a_guaranteed_minimum"
    assert curves["dc_bias_v"] == 5.0 and curves["measurement_conditions_identical"] is False
    assert curves["temperature_curve_missing_for"] == ["GRM21BZ71C106KE15"]
    assert data["open_qualification"] == [
        "exact_orderable_mpn_and_packaging",
        "approval_termination_and_assembly_lands",
        "height_clearance_and_process",
        "effective_capacitance_at_each_node_over_operating_envelope",
        "esr_esl_and_regulator_output_network",
        "sourcing_and_delivered_quote",
    ]


def test_current_capture_is_bound_to_prior_catalog_without_rewriting_it() -> None:
    data = _record()
    previous = read_object(
        json.loads((RECORD.parent / "source_record.json").read_text()), "prior snapshot"
    )
    catalog = read_object(data["catalog"], "catalog")
    old_catalog = read_object(previous["catalog"], "old catalog")
    assert data["captured_date_utc"] == "2026-09-27"
    assert catalog["sha256"] == old_catalog["sha256"]
    assert catalog["csv_sha256"] == old_catalog["csv_sha256"]
    assert catalog["url"] == "https://ds.murata.com/simsurfing_data/data/mlcc.zip"
