"""Electrical limits for C3 are conditional calculations, not hardware approval."""

import gzip
import json
from dataclasses import replace
from pathlib import Path

import pytest

from hardware.rev_a import (
    AuxiliaryContract,
    SchematicNetlist,
    load_documents,
    parse_auxiliary_contract,
    parse_schematic_xml,
    validate_auxiliary,
    validate_auxiliary_erc,
)

ROOT = Path(__file__).resolve().parents[1]
BUS_PULLS = (
    "R_CS_DN",
    "R_CLKSEL_DN",
    "R_RESET_DN",
    "R_PWDN_DN",
    "R_START_DN",
    "R_SCLK_DN",
    "R_DIN_DN",
)


@pytest.mark.parametrize("reference", BUS_PULLS)
def test_bus_pull_fits_both_loaded_high_and_disabled_low(reference: str) -> None:
    """TI 100-uA VOH row and ADC leakage must both work; bigger R is not free."""
    _, bom, _ = load_documents(ROOT / "hardware/rev_a")
    item = next(row for row in bom["line_items"] if reference in row["references"])
    resistance = item["spec"]["resistance_ohm"]
    # 1% initial + 100 ppm/K * 5 K for the declared 20--30 C bench target.
    r_min, r_max = resistance * 0.9895, resistance * 1.0105
    # ADS input: 10 uA max. Additional board leakage <=1 uA is a REQUIREMENT.
    enabled_current = 3.6 / r_min + 11e-6
    assert enabled_current <= 100e-6, "outside the cited TXU near-rail VOH load row"
    # 2.5 uA is the conservative TXU off-state current; not a ramp guarantee.
    assert (10e-6 + 2.5e-6 + 1e-6) * r_max < 0.2 * 3.0
    assert item["population"] == "fit"


def test_auxiliary_native_source_exists_separately_from_the_afe() -> None:
    assert (ROOT / "hardware/rev_a/auxiliary/auxiliary.kicad_sch").is_file()


def _fixture() -> SchematicNetlist:
    return parse_schematic_xml(
        gzip.decompress((ROOT / "tests/fixtures/auxiliary_c3_netlist.xml.gz").read_bytes()).decode()
    )


def _contract() -> AuxiliaryContract:
    return parse_auxiliary_contract((ROOT / "hardware/rev_a/auxiliary/contract.json").read_text())


def test_native_auxiliary_frozen_graph_accounts_for_every_terminal() -> None:
    graph, contract = _fixture(), _contract()
    assert len(graph.parts) == len(contract.parts) == 48
    assert len(graph.nets) == sum(len(p.pins) for p in contract.parts.values()) == 212
    assert sum(p.in_bom for p in contract.parts.values()) == 43
    assert validate_auxiliary(graph, contract) == []


def test_independent_critical_power_direction_and_fresh_arm_connections() -> None:
    parts = _contract().parts
    for ref in ("BU1", "BU2", "BU3"):
        assert parts[ref].mpn == "TXU0304PWR"
        assert [parts[ref].pins[n].net for n in ("1", "14", "7", "8")] == [
            "MCU_3V3",
            "AFE_DVDD",
            "TARGET_GND",
            "BUS_OE",
        ]
    assert [parts["ISO"].pins[n].net for n in ("1", "4", "8", "5")] == [
        "HOST_3V3",
        "HOST_GND",
        "MCU_3V3",
        "TARGET_GND",
    ]
    assert [parts["ARM_FF"].pins[n].net for n in ("1", "2", "5", "6", "7", "8")] == [
        "ARM_CLK",
        "MCU_3V3",
        "BUS_OE",
        "CLR_N",
        "MCU_3V3",
        "MCU_3V3",
    ]
    # Gating ARM with READY would manufacture a new rising edge on rail recovery.
    assert parts["ARM_BUFFER"].pins["6"].net == "MCU_3V3"
    assert parts["ARM_BUFFER"].pins["3"].net == "ARM_REQ"
    assert parts["CLEAR_AND"].pins["6"].net == "RAILS_OK"
    assert parts["CLEAR_AND"].pins["3"].net == "SESSION"
    assert parts["MON_D"].pins["1"].net == "AFE_DVDD_SENSE"
    assert parts["MON_A"].pins["1"].net == "AFE_AVDD_SENSE"
    for ref in ("MON_M", "MON_D", "MON_A", "MON_V"):
        assert parts[ref].pins["2"].net == "MCU_3V3"
        assert parts[ref].pins["4"].net == "RAILS_OK"
    assert parts["AFE_RAIL_ACCESS"].pins["2"].net == "AFE_DVDD"
    assert parts["AFE_RAIL_ACCESS"].pins["3"].net == "AFE_DVDD_SENSE"
    assert parts["AFE_TAILS"].pins["19"].net == "AFE_CLKSEL"
    assert all(parts["AFE_TAILS"].pins[str(i)].net == "TARGET_GND" for i in range(2, 21, 2))


def test_every_single_terminal_move_is_detected_by_native_graph_contract() -> None:
    graph, contract = _fixture(), _contract()
    codes = sorted(set(graph.nets.values()))
    for pin, code in graph.nets.items():
        changed = dict(graph.nets)
        changed[pin] = next(c for c in codes if c != code)
        assert validate_auxiliary(replace(graph, nets=changed), contract), pin


@pytest.mark.parametrize(
    "fault",
    [
        "missing-part",
        "missing-pin",
        "type",
        "function",
        "value",
        "mpn",
        "population",
        "off-board",
        "bom",
    ],
)
def test_auxiliary_identity_and_terminal_faults(fault: str) -> None:
    graph = _fixture()
    parts, nets = dict(graph.parts), dict(graph.nets)
    types, functions = dict(graph.pin_types), dict(graph.pin_functions)
    part = parts["BU1"]
    properties = dict(part.properties)
    if fault == "missing-part":
        del parts["BU1"]
    elif fault == "missing-pin":
        del nets[("BU1", "1")]
    elif fault == "type":
        types[("BU1", "1")] = "passive"
    elif fault == "function":
        functions[("BU1", "1")] = "VCCB"
    elif fault == "value":
        parts["BU1"] = replace(part, value="incorrect")
    else:
        key = {
            "mpn": "MPN",
            "population": "Population",
            "off-board": "exclude_from_board",
            "bom": "exclude_from_bom",
        }[fault]
        properties[key] = "wrong"
        parts["BU1"] = replace(part, properties=properties)
    assert validate_auxiliary(
        replace(graph, parts=parts, nets=nets, pin_types=types, pin_functions=functions),
        _contract(),
    )


def test_net_renumbering_and_nonpolar_reversal_are_benign() -> None:
    graph = _fixture()
    nets = {pin: "renamed-" + code for pin, code in graph.nets.items()}
    for ref in ("R_MISO", "C_ISO_HOST"):
        nets[(ref, "1")], nets[(ref, "2")] = nets[(ref, "2")], nets[(ref, "1")]
    assert validate_auxiliary(replace(graph, nets=nets), _contract()) == []


@pytest.mark.parametrize(
    "content",
    [
        "[]",
        "{}",
        "null",
        '{"revision":"C3","approval":true,"parts":[]}',
        '{"revision":"C3","approval":false,"parts":{}}',
        " " * 200001,
    ],
)
def test_auxiliary_manifest_rejects_invalid_roots(content: str) -> None:
    with pytest.raises(ValueError):
        parse_auxiliary_contract(content)


@pytest.mark.parametrize(
    "old,new",
    [
        ('"reference": "J102"', '"reference": "J101"'),
        ('"contract_ref": "MCU_TAILS"', '"contract_ref": "AFE_TAILS"'),
        ('"in_bom": false', '"in_bom": "false"'),
        ('"net": "AFE_SCLK"', '"net": 3'),
        ('"function": "SCLK"', '"function": ""'),
        ('"1": {', '"0": {'),
    ],
)
def test_auxiliary_manifest_rejects_invalid_records(old: str, new: str) -> None:
    text = (ROOT / "hardware/rev_a/auxiliary/contract.json").read_text()
    assert old in text
    with pytest.raises(ValueError):
        parse_auxiliary_contract(text.replace(old, new, 1))


@pytest.mark.parametrize("resistance,valid", [(10000, False), (42200, True), (100000, False)])
def test_two_sided_pull_requirement_rejects_smaller_and_larger_shortcuts(
    resistance: float, valid: bool
) -> None:
    driven = 3.6 / (resistance * 0.9895) + 11e-6 <= 100e-6
    stopped = 13.5e-6 * resistance * 1.0105 < 0.6
    assert (driven and stopped) is valid


@pytest.mark.parametrize(
    "fault",
    [
        "none",
        "source",
        "version",
        "missing-sheet",
        "duplicate-sheet",
        "wrong-sheet",
        "warning",
        "absent-violations",
    ],
)
def test_auxiliary_erc_requires_the_exact_four_sheet_report(fault: str) -> None:
    rows: list[dict[str, object]] = [
        {"path": p, "violations": []} for p in ("/", "/BUS/", "/ARMING/", "/SUPERVISION/")
    ]
    source, version = "auxiliary.kicad_sch", "9.0.2"
    if fault == "source":
        source = "rev_a.kicad_sch"
    elif fault == "version":
        version = "9.0.1"
    elif fault == "missing-sheet":
        rows.pop()
    elif fault == "duplicate-sheet":
        rows[1]["path"] = "/"
    elif fault == "wrong-sheet":
        rows[1]["path"] = "/WRONG/"
    elif fault == "warning":
        rows[1]["violations"] = [{"severity": "warning"}]
    elif fault == "absent-violations":
        del rows[1]["violations"]
    content = json.dumps({"source": source, "kicad_version": version, "sheets": rows})
    if fault == "none":
        validate_auxiliary_erc(content)
    else:
        with pytest.raises(ValueError):
            validate_auxiliary_erc(content)
