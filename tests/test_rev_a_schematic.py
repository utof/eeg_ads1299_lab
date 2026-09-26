"""Schematic contracts; no fabricated board or human-use approval is implied."""

from pathlib import Path

from hardware.rev_a import load_documents

ROOT = Path(__file__).resolve().parents[1]
CAD = ROOT / "hardware/rev_a/kicad"


def test_native_schematic_review_sources_exist() -> None:
    for name in ("rev_a.kicad_sch", "power.kicad_sch", "digital.kicad_sch", "RevA.kicad_sym"):
        assert (CAD / name).is_file(), f"native schematic review source missing: {name}"


def test_unused_daisy_input_does_not_consume_a_series_strap() -> None:
    profile, bom, _sources = load_documents()
    assert profile["afe"]["daisy_chain"] is False
    refs = {ref for row in bom["line_items"] for ref in row["references"]}
    assert "R_DAISY_DN" not in refs, "TI Rev. C 10.1.1 requires unused DAISY_IN directly at DGND"
