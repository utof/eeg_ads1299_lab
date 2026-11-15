"""Reviewed L5 fits: exactly the selected 33 ohm part, never open or a zero-ohm link."""

import copy
from pathlib import Path

import pytest

from hardware.rev_a import load_documents, parse_auxiliary_contract, validate

ROOT = Path(__file__).resolve().parents[1]


def test_reviewed_afe_series_fit_validates() -> None:
    assert validate(*load_documents()) == []


@pytest.mark.parametrize("fault", ["open", "unselected", "substitute", "extra-site"])
def test_afe_series_position_cannot_be_left_open_or_substituted(fault: str) -> None:
    profile, bom, sources = copy.deepcopy(load_documents())
    row = next(item for item in bom["line_items"] if item["id"] == "spi_series")
    if fault == "open":
        row["population"] = "dnp"
    elif fault == "unselected":
        row["mpn"] = "NOT_SELECTED"
    elif fault == "substitute":
        row["mpn"] = "RC0603FR-07100RL"
    else:
        row["references"] = ["R_MISO_SER", "R_SPARE_SER"]
        row["quantity"] = 2
    assert any("SPI series" in error for error in validate(profile, bom, sources))


@pytest.mark.parametrize("resistance", [0.0, 100.0])
def test_afe_series_position_keeps_the_reviewed_resistance(resistance: float) -> None:
    profile, bom, sources = copy.deepcopy(load_documents())
    row = next(item for item in bom["line_items"] if item["id"] == "spi_series")
    row["spec"]["resistance_ohm"] = resistance
    assert any("SPI series" in error for error in validate(profile, bom, sources))


@pytest.mark.parametrize("reference", ["R117", "R118", "R119", "R120"])
def test_auxiliary_series_population_is_the_reviewed_fit(reference: str) -> None:
    path = ROOT / "hardware/rev_a/auxiliary/contract.json"
    contract = parse_auxiliary_contract(path.read_text())
    part = next(item for item in contract.parts.values() if item.reference == reference)
    assert part.population == "fit" and part.in_bom
    assert (part.value, part.mpn) == ("33", "RC0603FR-0733RL")


def _series_text(reference: str, old: str, new: str) -> str:
    text = (ROOT / "hardware/rev_a/auxiliary/contract.json").read_text()
    before, marker, after = text.partition(f'"reference": "{reference}"')
    assert marker and old in after
    return before + marker + after.replace(old, new, 1)


@pytest.mark.parametrize("reference", ["R117", "R120"])
def test_auxiliary_manifest_rejects_an_open_series_position(reference: str) -> None:
    text = _series_text(reference, '"population": "fit"', '"population": "dnp"')
    with pytest.raises(ValueError, match="population"):
        parse_auxiliary_contract(text)


def test_auxiliary_manifest_rejects_dnp_on_any_other_device() -> None:
    text = (ROOT / "hardware/rev_a/auxiliary/contract.json").read_text()
    with pytest.raises(ValueError, match="population"):
        parse_auxiliary_contract(text.replace('"population": "fit"', '"population": "dnp"', 1))


@pytest.mark.parametrize(
    "old,new",
    [
        ('"value": "33"', '"value": "0"'),
        ('"value": "33"', '"value": "NOT_SELECTED"'),
        ('"mpn": "RC0603FR-0733RL"', '"mpn": "RC0603FR-070RL"'),
        ('"in_bom": true', '"in_bom": false'),
    ],
)
def test_auxiliary_series_fit_cannot_be_substituted_or_dropped(old: str, new: str) -> None:
    with pytest.raises(ValueError, match="reviewed 33 ohm"):
        parse_auxiliary_contract(_series_text("R117", old, new))
