"""2026-11-15 fitted pilot revision: exact identities and counts, not a build release."""

from pathlib import Path

import pytest

from hardware.rev_a import load_documents, parse_auxiliary_contract

ROOT = Path(__file__).resolve().parents[1]
# docs/REV_A_FITTED_PILOT_BUILD.md section 1: five identical 33 ohm starting fits.
SERIES_MPN = "RC0603FR-0733RL"
# Section 2: (MPN, manufacturer, sites, capacitance F, dielectric, rated V, package).
CAPACITORS = {
    "decap_1u": ("GRM188R61C105KA12D", "Murata", 15, 1e-6, "X5R", 16, "0603"),
    "decap_100n": ("C0603C104K5RACTU", "KEMET", 7, 1e-7, "X7R", 50, "0603"),
    "bulk_10u": ("GRM21BR61C106KE15L", "Murata", 4, 1e-5, "X5R", 16, "0805"),
}
LEGACY = ("GRM188R61E105KA12D", "GRM188R71H104KA93D", "GRM219R61A106KE44D")


def _row(item: str) -> dict[str, object]:
    _, bom, _ = load_documents()
    row = next(row for row in bom["line_items"] if row["id"] == item)
    return dict(row)


def _contract_parts() -> dict[str, tuple[str, str, str, bool]]:
    contract = parse_auxiliary_contract(
        (ROOT / "hardware/rev_a/auxiliary/contract.json").read_text()
    )
    return {
        part.reference: (part.population, part.value, part.mpn, part.in_bom)
        for part in contract.parts.values()
    }


def test_afe_bom_fits_the_selected_series_resistor() -> None:
    row = _row("spi_series")
    assert (row["mpn"], row["manufacturer"], row["population"]) == (SERIES_MPN, "Yageo", "fit")
    assert row["references"] == ["R_MISO_SER"] and row["package"] == "0603"
    # 33 ohm, 1 %, 0.1 W: the manufacturer's exact-part identity, not a tuned value.
    assert row["spec"] == {"resistance_ohm": 33, "tolerance_fraction": 0.01, "rated_power_w": 0.1}


@pytest.mark.parametrize("reference", ["R117", "R118", "R119", "R120"])
def test_aux_series_positions_fit_the_same_part(reference: str) -> None:
    assert _contract_parts()[reference] == ("fit", "33", SERIES_MPN, True)


@pytest.mark.parametrize("item", sorted(CAPACITORS))
def test_afe_capacitor_identities_are_migrated(item: str) -> None:
    mpn, manufacturer, count, farads, dielectric, volts, package = CAPACITORS[item]
    row = _row(item)
    assert (row["mpn"], row["manufacturer"], row["quantity"], row["package"]) == (
        mpn,
        manufacturer,
        count,
        package,
    )
    assert row["population"] == "fit"
    spec = row["spec"]
    assert isinstance(spec, dict)
    assert spec == {
        "capacitance_f": farads,
        "dielectric": dielectric,
        "rated_voltage_v": volts,
        "tolerance_fraction": 0.1,
    }


@pytest.mark.parametrize(
    "path",
    [
        "hardware/rev_a/kicad/power.kicad_sch",
        "hardware/rev_a/layout/rev_a.kicad_pcb",
        "tests/fixtures/rev_a_bom.csv",
    ],
)
def test_active_afe_sources_carry_only_the_migrated_capacitors(path: str) -> None:
    _, bom, _ = load_documents()
    assert not {row["mpn"] for row in bom["line_items"]} & set(LEGACY)
    text = (ROOT / path).read_text()
    assert not [mpn for mpn in LEGACY if mpn in text], "legacy capacitor identity remains"
    if path.endswith((".kicad_sch", ".kicad_pcb")):
        counts = {mpn: text.count(f'(property "MPN" "{mpn}"') for mpn, *_ in CAPACITORS.values()}
        assert counts == {mpn: count for mpn, _, count, *_ in CAPACITORS.values()}


def _afe_rows(population: str) -> list[dict[str, object]]:
    _, bom, _ = load_documents()
    return [
        dict(row)
        for row in bom["line_items"]
        if row["id"] != "controller" and row["population"] == population
    ]


def _quantity(rows: list[dict[str, object]]) -> int:
    total = 0
    for row in rows:
        quantity = row["quantity"]
        assert isinstance(quantity, int)
        total += quantity
    return total


def _capacitor_row(row: dict[str, object]) -> bool:
    references = row["references"]
    assert isinstance(references, list)
    return all(isinstance(ref, str) and ref.startswith("C_") for ref in references)


def test_fitted_inventory_matches_the_reviewed_section_4_delta() -> None:
    afe = _quantity(_afe_rows("fit"))
    parts = _contract_parts()
    aux = sum(1 for population, _, _, in_bom in parts.values() if in_bom and population == "fit")
    assert (afe, aux, afe + aux) == (62, 47, 109)


def test_only_the_clamps_stay_dnp_and_48_capacitors_are_fitted() -> None:
    assert [(row["id"], row["quantity"]) for row in _afe_rows("dnp")] == [("clamps", 8)]
    parts = _contract_parts()
    assert all(population == "fit" for population, *_ in parts.values())
    afe_caps = _quantity([row for row in _afe_rows("fit") if _capacitor_row(row)])
    aux_caps = sum(1 for ref, (pop, *_) in parts.items() if ref.startswith("C") and pop == "fit")
    assert (afe_caps, aux_caps) == (33, 15)
