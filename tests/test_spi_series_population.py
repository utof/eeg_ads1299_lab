"""Unselected L5 positions stay open; no nominal resistance or fit permission."""

import copy
from pathlib import Path

import pytest

from hardware.rev_a import load_documents, parse_auxiliary_contract, validate

ROOT = Path(__file__).resolve().parents[1]


def test_afe_unselected_series_position_cannot_be_populated() -> None:
    profile, bom, sources = copy.deepcopy(load_documents())
    row = next(item for item in bom["line_items"] if item["id"] == "spi_series")
    row["population"] = "fit"
    assert any("SPI series" in error for error in validate(profile, bom, sources))


def test_afe_series_position_does_not_select_zero_ohms() -> None:
    profile, bom, sources = copy.deepcopy(load_documents())
    row = next(item for item in bom["line_items"] if item["id"] == "spi_series")
    row["spec"]["resistance_ohm"] = 0.0
    assert any("SPI series" in error for error in validate(profile, bom, sources))


@pytest.mark.parametrize("reference", ["R117", "R118", "R119", "R120"])
def test_auxiliary_series_population_is_explicit_and_unselected(reference: str) -> None:
    path = ROOT / "hardware/rev_a/auxiliary/contract.json"
    contract = parse_auxiliary_contract(path.read_text())
    part = next(item for item in contract.parts.values() if item.reference == reference)
    assert part.population == "dnp"
    assert part.mpn == part.value == "NOT_SELECTED"


@pytest.mark.parametrize("old", ['"population": "dnp"', '"population": "fit"'])
def test_auxiliary_manifest_rejects_unreviewed_population_changes(old: str) -> None:
    path = ROOT / "hardware/rev_a/auxiliary/contract.json"
    replacement = '"population": "fit"' if '"dnp"' in old else '"population": "dnp"'
    with pytest.raises(ValueError, match="population"):
        parse_auxiliary_contract(path.read_text().replace(old, replacement, 1))


def test_auxiliary_dnp_does_not_allow_a_selected_resistance() -> None:
    path = ROOT / "hardware/rev_a/auxiliary/contract.json"
    text = path.read_text().replace('"value": "NOT_SELECTED"', '"value": "0"', 1)
    with pytest.raises(ValueError, match="unselected"):
        parse_auxiliary_contract(text)


def test_auxiliary_dnp_part_cannot_be_removed_from_bom() -> None:
    path = ROOT / "hardware/rev_a/auxiliary/contract.json"
    before, marker, after = path.read_text().partition('"reference": "R117"')
    assert marker
    text = before + marker + after.replace('"in_bom": true', '"in_bom": false', 1)
    with pytest.raises(ValueError, match="unselected"):
        parse_auxiliary_contract(text)
