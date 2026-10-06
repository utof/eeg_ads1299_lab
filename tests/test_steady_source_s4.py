"""Named serial evidence must not turn conditional component data into a board pass."""

import hashlib
import json
from pathlib import Path

import pytest

from lab.validation import read_object
from tests.test_supply_acceptance_s3 import MODEL, ROOT, _run

RECORD = ROOT / "docs/studies/s4_serial_evidence.json"
DOCUMENT = ROOT / "docs/REV_A_STEADY_SOURCE_S4.md"


def _record() -> dict[str, object]:
    assert RECORD.is_file(), "missing named serial source-evidence record"
    return read_object(json.loads(RECORD.read_text()), "S4 record")


def test_named_case_is_existing_internal_serial_mode_not_permission() -> None:
    m = _record()
    assert m["schema"] == "S4-serial-evidence-v1"
    assert m["setup_id"] == "rev_a_f1_serial_internal_250"
    assert m["physical_qualification"] is False and m["measurement_records"] == []
    setup = read_object(m["setup"], "setup")
    assert setup["channels"] == 4 and setup["sps_nominal"] == 250
    assert setup["gain"] == 24 and setup["spi_hz"] == 1000000
    assert setup["USE_INTERNAL_TEST"] is True and setup["USE_WIFI_UDP"] is False
    assert setup["BOARD_PROFILE_REVIEWED"] is False
    config = (ROOT / "firmware/esp32_ads1299_bench/board_config.h").read_text()
    for text in ("USE_INTERNAL_TEST=true", "USE_WIFI_UDP=false", "BOARD_PROFILE_REVIEWED = false"):
        assert text in config
    toolchain = read_object(json.loads((ROOT / "firmware/toolchain.json").read_text()), "build")
    assert setup["fqbn"] == toolchain["fqbn"]
    assert setup["cpu_clock_measured_hz"] is None  # not a claimed running-clock measurement


def test_evidence_is_bound_to_current_sources_and_existing_worksheet() -> None:
    m = _record()
    hashes = read_object(m["input_sha256"], "hashes")
    assert set(hashes) == {
        "firmware/esp32_ads1299_bench/board_config.h",
        "firmware/esp32_ads1299_bench/esp32_ads1299_bench.ino",
        "firmware/toolchain.json",
        "hardware/rev_a/bom.json",
        "hardware/rev_a/auxiliary/contract.json",
        "docs/studies/s3_acceptance.json",
        "docs/REV_A_SUPPLY_ACCEPTANCE_S3.md",
    }
    for name, digest in hashes.items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    assert DOCUMENT.is_file(), "missing evidence-to-worksheet explanation"
    text = DOCUMENT.read_text()
    for required in ("SGM2212", "CP2102N", "1 mA", "3.6 V", "250.5 mV", "not a maximum"):
        assert required in text
    assert "REV_A_SUPPLY_ACCEPTANCE_S3.md" in text


def test_datasheet_regulator_interval_has_conditions_not_assembled_bounds() -> None:
    regulator = read_object(_record()["adc_regulator"], "regulator")
    assert regulator["mpn"] == "TPS7A2033PDBVR"
    assert regulator["nominal_V"] == 3.3 and regulator["tolerance_fraction"] == 0.015
    # Independent endpoint arithmetic, not inferred from another generated report.
    assert regulator["conditional_pin_window_V"] == pytest.approx([3.2505, 3.3495])
    assert regulator["accuracy_VIN_range_V"] == [3.6, 6.0]
    assert regulator["accuracy_IOUT_range_A"] == [0.001, 0.3]
    assert regulator["TJ_range_C"] == [-40, 125]
    assert regulator["dropout_test_output_fraction"] == 0.95
    assert regulator["dropout_DBV_max_V"] == 0.145
    assert regulator["assembled_pin_window_V"] is None
    assert all(
        v is None for v in read_object(regulator["unverified_conditions"], "conditions").values()
    )
    assert pytest.approx(0.2505) == 3.2505 - 3.0
    assert pytest.approx(0.2505) == 3.6 - 3.3495
    assert 3.3 + 0.145 < 3.6  # dropout headline is NOT the accuracy row's input minimum


def test_module_capacity_and_typical_current_are_not_total_current_limits() -> None:
    m = _record()
    controller = read_object(m["controller"], "controller")
    assert controller["module_supply_capability_min_A"] == 0.5
    assert controller["capacity_is_load_maximum"] is False
    assert controller["table_6_6_columns"] == ["typical", "typical"]
    assert controller["devkit_regulator_schematic"] == "SGM2212-3.3XKC3G/TR"
    unknowns = read_object(m["required_unavailable_bounds"], "unknown bounds")
    assert set(unknowns) == {
        "source_model",
        "source_regulation_V",
        "common_pair_ohm",
        "MCU_branch_operating_A",
        "DVDD_export_operating_A",
        "source_total_operating_A",
        "ground_offsets_V",
        "startup_peak_A",
        "measurement_instrument_identity",
    }
    assert all(v is None for v in unknowns.values())
    assert read_object(m["translator"], "translator")["loaded_dynamic_max_A"] is None


@pytest.mark.parametrize("optimization", ["normal", "flag", "env"])
def test_conditional_regulator_scenario_reuses_s3_and_still_cannot_pass(
    tmp_path: Path, optimization: str
) -> None:
    data = read_object(json.loads(MODEL.read_text()), "S3 template")
    terms = read_object(data["bounds_V"], "terms")
    assert len(terms) == 21 and all(value is None for value in terms.values())
    regulator = read_object(_record()["adc_regulator"], "regulator")
    terms["regulator"] = regulator["conditional_pin_window_V"]
    data["bounds_V"] = terms
    candidate = tmp_path / "conditional-only.json"
    candidate.write_text(json.dumps(data))
    result = _run(candidate, tmp_path / "conditional.log", optimization)
    assert result["physical_qualification"] is False
    rows = read_object(result["windows"], "rows")
    assert len(rows) == 8
    for key, raw in rows.items():
        row = read_object(raw, key)
        assert row["voltage_V"] is None and row["margins_V"] is None
        assert row["missing_terms"] and "regulator" not in row["missing_terms"]
    remote = read_object(rows["DVDD_U104"], "remote")
    assert set(remote["missing_terms"]) == {"dvdd_feed_U104", "g_U104"}
    actual = read_object(json.loads(MODEL.read_text()), "unchanged original")
    assert all(v is None for v in read_object(actual["bounds_V"], "original terms").values())
