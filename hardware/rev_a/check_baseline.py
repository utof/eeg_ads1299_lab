#!/usr/bin/env python3
"""Check the Rev A design contract; this is NOT a hardware/safety validation.

Python 3.10+, standard library only. Does not access hardware or the network.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections.abc import Callable
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import TypedDict, cast, get_args, get_origin, get_type_hints, is_typeddict

HERE = Path(__file__).resolve().parent
SIGNALS = {
    "SCLK": (12, 40, "out"),
    "MOSI": (11, 34, "out"),
    "MISO": (13, 43, "in"),
    "CS": (10, 39, "out"),
    "DRDY": (4, 47, "in"),
    "RESET": (5, 36, "out"),
    "START": (6, 38, "out"),
    "PWDN": (7, 35, "out"),
}
# Deliberately conservative exclusions for the selected N8R8 devkit, not a
# universal description of all ESP32-S3 variants.
EXCLUDED_GPIOS = {
    0,
    3,
    19,
    20,
    26,
    27,
    28,
    29,
    30,
    31,
    32,
    33,
    34,
    35,
    36,
    37,
    38,
    43,
    44,
    45,
    46,
    48,
}
GATES = {
    "board_profile_reviewed",
    "firmware_port_validated",
    "schematic_released",
    "purchase_approved",
    "human_connection_allowed",
}


class AfeProfile(TypedDict):
    mpn: str
    channels: int
    sample_rate_sps: int
    gain: int
    reference: str
    reference_v: float
    clock: str
    clock_hz_nominal: int
    clk_sel_level: int
    clock_output_enabled: bool
    daisy_chain: bool
    frame_status_bytes: int
    bytes_per_channel: int
    frame_bytes: int
    input_modes_initial: list[str]
    external_dummy_mode_enabled: bool
    lead_off_enabled: bool
    bias_drive_enabled: bool
    srb1_enabled: bool
    srb2_enabled: bool


class McuProfile(TypedDict):
    board_mpn: str
    preferred_pcb_revision: str
    module_mpn: str
    target: str
    onboard_regulator_supplies_mcu: bool
    capture_buffer_memory: str
    psram_required: bool
    wifi_enabled_initially: bool
    ble_enabled: bool


class PowerProfile(TypedDict):
    topology: str
    external_source_nominal_v: float
    external_source_tolerance_fraction: float
    external_source_capacity_a: float
    avss_v: float
    avdd_design_v: float
    avdd_operating_min_v: float
    avdd_operating_max_v: float
    analog_feed_resistance_ohm: float
    analog_branch_design_current_budget_a: float
    dvdd_v: float
    dvdd_regulator_mpn: str
    dvdd_regulator_supplies_mcu: bool
    common_ground: bool
    devkit_usb_and_5v_header_simultaneous: bool
    battery_selected: bool
    charger_fitted: bool


class InputProfile(TypedDict):
    channels: int
    topology: str
    series_resistance_each_ohm: float
    differential_capacitance_f: float
    common_mode_capacitance_fitted_f: float
    clamp_population: str
    nominal_dummy_common_mode_v: float
    bias_feedback_resistance_ohm: float
    bias_feedback_capacitance_f: float
    bias_output_series_resistance_ohm: float


class IntegrationProfile(TypedDict):
    existing_firmware_modified: bool
    existing_model_defaults_modified: bool
    preserve_simulated_channel_counts: list[int]
    requires_explicit_s3_firmware_profile: bool
    do_not_remove_existing_target_guard: bool
    this_json_is_not_loaded_by_existing_firmware: bool


class SpiSignal(TypedDict):
    signal: str
    gpio: int
    ads_pin: int
    direction_from_mcu: str


class SpiProfile(TypedDict):
    mode: int
    clock_hz: int
    pin_map_status: str
    signals: list[SpiSignal]


class InterfaceHeader(TypedDict):
    mpn: str
    pin_map: dict[str, str]


class BoardProfile(TypedDict):
    schema_version: int
    profile_id: str
    revision: str
    status: str
    gates: dict[str, bool]
    afe: AfeProfile
    mcu: McuProfile
    spi: SpiProfile
    power: PowerProfile
    input_network: InputProfile
    interface_headers: dict[str, InterfaceHeader]
    integration: IntegrationProfile


class PartSpec(TypedDict, total=False):
    channels: int
    module: str
    output_v: float
    rated_output_current_a: float
    supplies_mcu: bool
    resistance_ohm: float
    tolerance_fraction: float
    rated_power_w: float
    capacitance_f: float
    dielectric: str
    rated_voltage_v: float
    diodes_per_package: int


class BomItem(TypedDict):
    id: str
    mpn: str
    manufacturer: str
    description: str
    package: str
    references: list[str]
    quantity: int
    population: str
    planning_unit_usd: str
    source_ids: list[str]
    evidence: str
    spec: PartSpec


class Allowance(TypedDict):
    id: str
    description: str
    planning_usd: str


class BillOfMaterials(TypedDict):
    schema_version: int
    revision: str
    scope: str
    currency: str
    prices_are_quotes: bool
    line_items: list[BomItem]
    allowances: list[Allowance]
    budget_target_usd: str
    excluded: list[str]
    purchase_approved: bool


class RepositorySource(TypedDict):
    url: str
    live_read_succeeded: bool
    upstream_commit: str
    remote_write_succeeded: bool
    delivery: str


class SourceIdentifier(TypedDict):
    id: str


class SourceReport(SourceIdentifier, total=False):
    filename: str
    sha256: str
    authority: str


class PrimarySource(SourceIdentifier, total=False):
    title: str
    url: str
    sections: str
    verification: str


class SourcesDocument(TypedDict):
    schema_version: int
    review_date: str
    repository: RepositorySource
    reports: list[SourceReport]
    primary_sources: list[PrimarySource]
    limitations: list[str]


class CostTotals(TypedDict):
    fitted: Decimal
    dnp_options: Decimal
    allowances: Decimal
    planning_total: Decimal


def _object_items(value: object, path: str) -> dict[object, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected an object")
    return value


def _check_record_shape(value: object, schema: object, path: str) -> None:
    # is_typeddict is checked by the dispatcher before introspecting this class.
    hints: dict[str, object] = get_type_hints(cast(type, schema))
    required: frozenset[str] = getattr(schema, "__required_keys__", frozenset[str]())
    values = _object_items(value, path)
    for name in required:
        if name not in values:
            raise ValueError(f"{path}: missing {name}")
    for name, expected in hints.items():
        if name in values:
            _check_shape(values[name], expected, f"{path}.{name}")


def _check_mapping_shape(value: object, schema: object, path: str) -> None:
    arguments: tuple[object, ...] = get_args(schema)
    key_type, value_type = arguments
    for key, child in _object_items(value, path).items():
        _check_shape(key, key_type, path)
        _check_shape(child, value_type, f"{path}.{key}")


def _check_sequence_shape(value: object, schema: object, path: str) -> None:
    if not isinstance(value, list):
        raise ValueError(f"{path}: expected an array")
    values: list[object] = value
    arguments: tuple[object, ...] = get_args(schema)
    (item_type,) = arguments
    for index, child in enumerate(values):
        _check_shape(child, item_type, f"{path}[{index}]")


def _check_shape(value: object, schema: object, path: str) -> None:
    """Validate the supported JSON shapes; unknown schema kinds fail closed.

    Shape validation does not approve any component value or gate. Those
    engineering-contract checks remain the responsibility of validate().
    """
    origin: object = get_origin(schema)
    if is_typeddict(schema):
        _check_record_shape(value, schema, path)
    elif origin is dict:
        _check_mapping_shape(value, schema, path)
    elif origin is list:
        _check_sequence_shape(value, schema, path)
    elif schema is float:
        if type(value) not in (int, float):
            raise ValueError(f"{path}: expected a number, not {type(value).__name__}")
    elif schema not in (str, int, bool) or type(value) is not schema:
        raise ValueError(f"{path}: incorrect JSON type for {schema}")


def _read_document(directory: Path, name: str, schema: object) -> object:
    value: object = json.loads((directory / name).read_text(encoding="utf-8"))
    _check_shape(value, schema, name)
    return value


def load_documents(directory: Path = HERE) -> tuple[BoardProfile, BillOfMaterials, SourcesDocument]:
    """Load UTF-8 JSON and validate its structure before assigning typed views."""
    # Each cast follows full recursive validation against the exact same schema.
    profile = cast(BoardProfile, _read_document(directory, "board_profile.json", BoardProfile))
    bom = cast(BillOfMaterials, _read_document(directory, "bom.json", BillOfMaterials))
    sources = cast(SourcesDocument, _read_document(directory, "sources.json", SourcesDocument))
    return profile, bom, sources


def money(value: object) -> Decimal:
    number = Decimal(str(value))
    if not number.is_finite() or number < 0:
        raise ValueError("prices must be finite and nonnegative")
    return number


def totals(bom: BillOfMaterials) -> CostTotals:
    fitted, dnp = Decimal(0), Decimal(0)
    for row in bom["line_items"]:
        value = money(row["planning_unit_usd"]) * row["quantity"]
        if row["population"] == "fit":
            fitted += value
        elif row["population"] == "dnp":
            dnp += value
        else:
            raise ValueError("population must be fit or dnp")
    allowances = sum((money(row["planning_usd"]) for row in bom["allowances"]), Decimal(0))
    return {
        "fitted": fitted,
        "dnp_options": dnp,
        "allowances": allowances,
        "planning_total": fitted + allowances,
    }


def validate(profile: BoardProfile, bom: BillOfMaterials, sources: SourcesDocument) -> list[str]:
    """Return contract inconsistencies. Never enable acquisition or approve a PCB."""
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    try:
        for document in (profile, bom, sources):
            require(document["schema_version"] == 1, "unsupported schema version")
        require(set(profile["gates"]) == GATES, "gate set changed")
        for name in GATES:
            require(
                profile["gates"][name] is False,
                f"{name} must remain false in this unvalidated baseline",
            )
        require(bom["purchase_approved"] is False, "BOM must not approve purchase")
        require(bom["prices_are_quotes"] is False, "planning prices are not supplier quotes")
        repo = sources["repository"]
        require(repo["live_read_succeeded"] is True, "live repository inspection must be recorded")
        upstream = repo["upstream_commit"]
        require(
            isinstance(upstream, str)
            and len(upstream) == 40
            and all(c in "0123456789abcdef" for c in upstream.lower()),
            "record a full 40-character upstream commit SHA",
        )

        rows = bom["line_items"]
        parts = {row["id"]: row for row in rows}
        require(len(rows) == len(parts), "duplicate BOM item IDs")
        known_sources = {s["id"] for s in sources["primary_sources"] + sources["reports"]}
        references: list[str] = []
        for row in rows:
            require(
                type(row["quantity"]) is int and row["quantity"] > 0,
                f"{row['id']}: invalid quantity",
            )
            require(
                row["quantity"] == len(row["references"]),
                f"{row['id']}: quantity/reference mismatch",
            )
            require(
                bool(row["mpn"].strip()) and bool(row["package"].strip()),
                f"{row['id']}: missing part identity",
            )
            require(row["population"] in {"fit", "dnp"}, f"{row['id']}: invalid population")
            require(
                bool(row["source_ids"]) and set(row["source_ids"]) <= known_sources,
                f"{row['id']}: missing or unknown source",
            )
            money(row["planning_unit_usd"])
            references.extend(row["references"])
        require(
            len(references) == len(set(references)), "duplicate component reference designators"
        )
        require(parts["afe"]["mpn"] == profile["afe"]["mpn"] == "ADS1299-4PAGR", "AFE choice drift")
        require(
            parts["controller"]["mpn"] == profile["mcu"]["board_mpn"] == "ESP32-S3-DevKitC-1-N8R8",
            "controller choice drift",
        )
        require(
            parts["dvdd_ldo"]["mpn"] == profile["power"]["dvdd_regulator_mpn"] == "TPS7A2033PDBVR",
            "DVDD regulator choice drift",
        )
        require(
            parts["afe"]["quantity"]
            == parts["controller"]["quantity"]
            == parts["dvdd_ldo"]["quantity"]
            == 1,
            "one AFE, devkit and DVDD LDO required",
        )
        require(
            not any(r["mpn"] == profile["mcu"]["module_mpn"] for r in rows),
            "do not buy/count the devkit module twice",
        )

        _validate_afe(profile, parts, bom, require)
        _validate_network(profile, parts, bom, require)
        _validate_power(profile, parts, bom, require)
    except (KeyError, TypeError, ValueError, InvalidOperation, AttributeError) as exc:
        errors.append(f"malformed or incomplete design document: {exc}")
    return errors


def _validate_afe(
    profile: BoardProfile,
    parts: dict[str, BomItem],
    bom: BillOfMaterials,
    require: Callable[[bool, str], None],
) -> None:
    afe = profile["afe"]
    require(
        afe["channels"] == parts["afe"]["spec"]["channels"] == 4,
        "Rev A must have four physical channels",
    )
    require(
        afe["frame_bytes"]
        == afe["frame_status_bytes"] + afe["channels"] * afe["bytes_per_channel"]
        == 15,
        "ADS1299-4 raw frame must include 3 status + 12 sample bytes",
    )
    require(
        afe["sample_rate_sps"] == 250 and afe["gain"] == 24, "initial sample rate or gain drift"
    )
    require(
        afe["reference"] == afe["clock"] == "internal",
        "external reference/clock is outside baseline",
    )
    require(
        afe["input_modes_initial"] == ["internal_test", "input_short"],
        "initial input modes must be bench-only",
    )
    for key in (
        "external_dummy_mode_enabled",
        "bias_drive_enabled",
        "lead_off_enabled",
        "srb1_enabled",
        "srb2_enabled",
    ):
        require(afe[key] is False, f"{key} must start disabled")
    require(
        profile["mcu"]["wifi_enabled_initially"] is False
        and profile["mcu"]["ble_enabled"] is False,
        "radios must start disabled",
    )
    require(
        profile["spi"]["mode"] == 1 and profile["spi"]["clock_hz"] == 1000000,
        "SPI contract drift",
    )
    signal_rows = profile["spi"]["signals"]
    actual = {s["signal"]: (s["gpio"], s["ads_pin"], s["direction_from_mcu"]) for s in signal_rows}
    require(
        actual == SIGNALS and len(signal_rows) == len(SIGNALS),
        "proposed pin map changed or duplicated",
    )
    gpios = [s["gpio"] for s in signal_rows]
    require(len(set(gpios)) == len(gpios), "GPIO conflict")
    require(not (set(gpios) & EXCLUDED_GPIOS), "reserved or devkit-conflicting GPIO selected")


def _validate_network(
    profile: BoardProfile,
    parts: dict[str, BomItem],
    bom: BillOfMaterials,
    require: Callable[[bool, str], None],
) -> None:
    network = profile["input_network"]
    require(network["channels"] == 4, "input channel count drift")
    require(
        parts["input_r"]["quantity"] == 8 and parts["input_c"]["quantity"] == 4,
        "input R/C quantity drift",
    )
    require(
        network["topology"] == "two_series_resistors_and_one_differential_cap_per_channel",
        "differential topology required",
    )
    require(
        parts["input_r"]["spec"]["resistance_ohm"] == network["series_resistance_each_ohm"] == 4990,
        "input resistance mismatch",
    )
    require(
        parts["input_c"]["spec"]["capacitance_f"]
        == network["differential_capacitance_f"]
        == 4.7e-9,
        "input capacitance mismatch",
    )
    require(parts["input_c"]["spec"]["dielectric"] == "C0G", "input capacitor must be C0G")
    require(
        network["common_mode_capacitance_fitted_f"] == 0,
        "ground-shunt input capacitors are not fitted",
    )
    require(
        parts["clamps"]["population"] == network["clamp_population"] == "dnp",
        "clamp experiment must start DNP",
    )
    require(parts["clamps"]["quantity"] == 8, "one optional dual-diode footprint per analog leg")
    require(
        parts["bias_r"]["quantity"] == 2 and parts["bias_c"]["quantity"] == 1,
        "BIAS network count mismatch",
    )
    require(
        network["bias_feedback_resistance_ohm"]
        == network["bias_output_series_resistance_ohm"]
        == parts["bias_r"]["spec"]["resistance_ohm"]
        == 1000000,
        "BIAS resistor mismatch",
    )
    require(
        network["bias_feedback_capacitance_f"]
        == parts["bias_c"]["spec"]["capacitance_f"]
        == 1.5e-9,
        "BIAS capacitor mismatch",
    )
    require(
        parts["vcap1"]["spec"]["capacitance_f"] == 100e-6
        and parts["vcap1"]["spec"]["dielectric"] == "solid tantalum",
        "VCAP1 baseline drift",
    )
    ref = parts["vref"]["spec"]
    require(
        ref["capacitance_f"] * (1 - ref["tolerance_fraction"]) >= 10e-6,
        "reference capacitor initial tolerance below 10 uF",
    )
    require(
        parts["decap_1u"]["quantity"] == 15
        and parts["decap_100n"]["quantity"] == 7
        and parts["bulk_10u"]["quantity"] == 4,
        "decoupling population drift",
    )
    require(
        parts["decap_1u"]["spec"]["rated_voltage_v"] >= 16,
        "VCAP3 bypass needs suitable voltage rating",
    )
    require(parts["straps"]["quantity"] == 12, "digital strap count drift")
    require(parts["headers"]["quantity"] == 2, "header count drift")
    for header in profile["interface_headers"].values():
        require(header["mpn"] == parts["headers"]["mpn"], "header MPN drift")
        require(
            set(header["pin_map"]) == {str(n) for n in range(1, 21)},
            "header needs exactly pins 1 through 20",
        )


def _validate_power(
    profile: BoardProfile,
    parts: dict[str, BomItem],
    bom: BillOfMaterials,
    require: Callable[[bool, str], None],
) -> None:
    power = profile["power"]
    require(power["topology"] == "unipolar_bench" and power["avss_v"] == 0, "power topology drift")
    require(
        power["dvdd_v"] == parts["dvdd_ldo"]["spec"]["output_v"] == 3.3,
        "digital voltage mismatch",
    )
    require(
        power["dvdd_regulator_supplies_mcu"] is False
        and parts["dvdd_ldo"]["spec"]["supplies_mcu"] is False,
        "AFE LDO must not supply the ESP32",
    )
    require(
        power["devkit_usb_and_5v_header_simultaneous"] is False,
        "do not combine devkit power sources",
    )
    require(
        power["analog_feed_resistance_ohm"] == parts["analog_feed"]["spec"]["resistance_ohm"],
        "analog feed mismatch",
    )
    low = (
        power["external_source_nominal_v"] * (1 - power["external_source_tolerance_fraction"])
        - power["analog_feed_resistance_ohm"] * power["analog_branch_design_current_budget_a"]
    )
    high = power["external_source_nominal_v"] * (1 + power["external_source_tolerance_fraction"])
    require(
        low >= power["avdd_operating_min_v"] and high <= power["avdd_operating_max_v"],
        "analog rail design envelope outside ADS operating range",
    )
    require(
        profile["integration"]["this_json_is_not_loaded_by_existing_firmware"] is True,
        "this commit does not implement firmware integration",
    )
    require(
        profile["integration"]["preserve_simulated_channel_counts"] == [4, 6, 8],
        "retain multi-variant simulation support",
    )
    costs = totals(bom)
    require(
        costs["planning_total"] <= money(bom["budget_target_usd"]),
        "planning budget exceeded; re-evaluate before buying",
    )
    require(
        "PCB assembly/stencil/setup fees" in bom["excluded"] and "shipping" in bom["excluded"],
        "budget exclusions missing",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--directory", type=Path, default=HERE, help="directory containing the three JSON files"
    )
    args = parser.parse_args()
    try:
        profile, bom, sources = load_documents(args.directory)
        errors = validate(profile, bom, sources)
        if errors:
            for error in errors:
                print(f"FAIL: {error}", file=sys.stderr)
            return 1
        costs = totals(bom)
        network = profile["input_network"]
        pole = 1 / (
            2
            * math.pi
            * 2
            * network["series_resistance_each_ohm"]
            * network["differential_capacitance_f"]
        )
        afe = profile["afe"]
        bits_per_second = 8 * afe["frame_bytes"] * afe["sample_rate_sps"]
        print("PASS: static component/profile consistency; NOT hardware or safety validation")
        print(f"Fitted components: ${costs['fitted']:.2f}; reserves: ${costs['allowances']:.2f}")
        print(
            f"Planning subtotal: ${costs['planning_total']:.2f}; optional DNP parts: ${costs['dnp_options']:.2f}"
        )
        print("Shipping, taxes, assembly and lab equipment are excluded; purchase remains blocked.")
        print(f"Analytic ideal-source differential RC pole: {pole:.2f} Hz (not a SPICE result)")
        print(f"ADS frame: {afe['frame_bytes']} bytes; raw stream: {bits_per_second} bit/s")
        print(
            f"SPI payload occupancy: {100 * bits_per_second / profile['spi']['clock_hz']:.2f}% (excludes transaction overhead)"
        )
        return 0
    except (OSError, ValueError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
