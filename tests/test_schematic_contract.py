"""Native exports are fixtures here; only fresh CLI runs are CAD execution evidence."""

import copy
import gzip
import xml.etree.ElementTree as ET
from dataclasses import replace
from pathlib import Path

import pytest

import hardware.rev_a as rev_a
from hardware.rev_a import (
    BillOfMaterials,
    BoardProfile,
    SchematicNetlist,
    load_documents,
    parse_schematic_xml,
    validate_schematic,
)

FIXTURE = Path(__file__).parent / "fixtures/rev_a_netlist.xml.gz"


@pytest.fixture
def circuit() -> tuple[SchematicNetlist, BoardProfile, BillOfMaterials]:
    profile, bom, _ = load_documents()
    return parse_schematic_xml(gzip.decompress(FIXTURE.read_bytes()).decode()), profile, bom


def test_native_fixture_has_complete_known_inventory(
    circuit: tuple[SchematicNetlist, BoardProfile, BillOfMaterials],
) -> None:
    netlist, profile, bom = circuit
    assert len(netlist.parts) == 71
    assert len(netlist.nets) == 264
    assert validate_schematic(netlist, profile, bom) == []
    assert all(value is False for value in profile["gates"].values())


def test_every_single_pin_move_to_another_existing_net_is_rejected(
    circuit: tuple[SchematicNetlist, BoardProfile, BillOfMaterials],
) -> None:
    netlist, profile, bom = circuit
    destinations = set(netlist.nets.values())
    count = 0
    for pin, original in list(netlist.nets.items()):
        for destination in destinations - {original}:
            netlist.nets[pin] = destination
            assert validate_schematic(netlist, profile, bom), (pin, original, destination)
            count += 1
        netlist.nets[pin] = original
    assert count == 15576
    assert validate_schematic(netlist, profile, bom) == []


def test_every_missing_component_or_pin_is_rejected(
    circuit: tuple[SchematicNetlist, BoardProfile, BillOfMaterials],
) -> None:
    netlist, profile, bom = circuit
    for ref in list(netlist.parts):
        part = netlist.parts.pop(ref)
        assert validate_schematic(netlist, profile, bom), ref
        netlist.parts[ref] = part
    for pin in list(netlist.nets):
        net = netlist.nets.pop(pin)
        assert validate_schematic(netlist, profile, bom), pin
        netlist.nets[pin] = net


@pytest.mark.parametrize(
    "field,value",
    [
        ("MPN", "wrong"),
        ("Population", "dnp"),
        ("BOM_ID", "wrong"),
        ("Tolerance", "NaN"),
        ("dnp", ""),
        ("exclude_from_board", ""),
    ],
)
def test_component_field_faults_rejected(
    circuit: tuple[SchematicNetlist, BoardProfile, BillOfMaterials], field: str, value: str
) -> None:
    netlist, profile, bom = circuit
    netlist.parts["R_IN1P"].properties[field] = value
    assert validate_schematic(netlist, profile, bom)


@pytest.mark.parametrize("value", ["0", "NaN", "1e999", "4.99m", "inf", "4.99k garbage"])
def test_displayed_value_is_not_hidden_by_correct_mpn(
    circuit: tuple[SchematicNetlist, BoardProfile, BillOfMaterials], value: str
) -> None:
    netlist, profile, bom = circuit
    netlist.parts["R_IN1P"] = replace(netlist.parts["R_IN1P"], value=value)
    assert validate_schematic(netlist, profile, bom)


def test_device_display_and_footprint_faults(
    circuit: tuple[SchematicNetlist, BoardProfile, BillOfMaterials],
) -> None:
    netlist, profile, bom = circuit
    netlist.parts["U2"] = replace(netlist.parts["U2"], value="different LDO", footprint="wrong")
    errors = validate_schematic(netlist, profile, bom)
    assert any("device value" in error for error in errors)
    assert any("footprint" in error for error in errors)


def test_native_population_flags_are_independent(
    circuit: tuple[SchematicNetlist, BoardProfile, BillOfMaterials],
) -> None:
    netlist, profile, bom = circuit
    del netlist.parts["D_IN1P"].properties["dnp"]
    del netlist.parts["MOD1"].properties["exclude_from_board"]
    errors = validate_schematic(netlist, profile, bom)
    assert any("DNP" in error for error in errors)
    assert any("board inclusion" in error for error in errors)


def test_daisy_requires_direct_ground_and_analog_reference_is_not_dvdd(
    circuit: tuple[SchematicNetlist, BoardProfile, BillOfMaterials],
) -> None:
    netlist, profile, bom = circuit
    netlist.nets["U1", "41"] = "brand-new-floating-net"
    netlist.nets["U1", "24"] = netlist.nets["U1", "48"]
    assert validate_schematic(netlist, profile, bom)


def test_symbol_types_and_nc_flags_cannot_silence_erc(
    circuit: tuple[SchematicNetlist, BoardProfile, BillOfMaterials],
) -> None:
    netlist, profile, bom = circuit
    netlist.pin_types["U1", "19"] = "passive"
    netlist.pin_functions["U2", "5"] = "IN"
    netlist.pin_types["U1", "17"] = "bidirectional"
    netlist.pin_types["R_IN1P", "1"] = "passive+no_connect"
    assert len(validate_schematic(netlist, profile, bom)) >= 4


def test_benign_net_renames_pass(
    circuit: tuple[SchematicNetlist, BoardProfile, BillOfMaterials],
) -> None:
    netlist, profile, bom = circuit
    renamed = {pin: "renamed_" + net for pin, net in netlist.nets.items()}
    assert validate_schematic(replace(netlist, nets=renamed), profile, bom) == []


def test_every_nonpolar_passive_reversal_passes_but_tantalum_reversal_fails(
    circuit: tuple[SchematicNetlist, BoardProfile, BillOfMaterials],
) -> None:
    netlist, profile, bom = circuit
    accepted = 0
    for ref in netlist.parts:
        if ref.startswith(("R_", "C_")):
            p1, p2 = (ref, "1"), (ref, "2")
            netlist.nets[p1], netlist.nets[p2] = netlist.nets[p2], netlist.nets[p1]
            errors = validate_schematic(netlist, profile, bom)
            assert bool(errors) is (ref in {"C_VCAP1", "C_REF"}), ref
            accepted += not errors
            netlist.nets[p1], netlist.nets[p2] = netlist.nets[p2], netlist.nets[p1]
    assert accepted == 55


@pytest.mark.parametrize(
    "fault",
    [
        "root",
        "version",
        "empty-parts",
        "duplicate-ref",
        "duplicate-contract",
        "missing-contract",
        "duplicate-prop",
        "wrong-library",
        "empty-nets",
        "duplicate-net",
        "missing-net-code",
        "unknown-node",
        "missing-pin",
        "duplicate-node",
        "empty-net",
        "doctype",
        "oversize",
        "bad-xml",
    ],
)
def test_parser_rejects_ambiguous_or_malformed_exports(fault: str) -> None:
    original = gzip.decompress(FIXTURE.read_bytes()).decode()
    root = ET.fromstring(original)
    comps, nets = root.find("components"), root.find("nets")
    assert comps is not None and nets is not None
    net = nets[0]
    node = net[0]
    _break_component_xml(root, comps, fault)
    if fault == "empty-nets":
        nets.clear()
    elif fault == "duplicate-net":
        nets.append(copy.deepcopy(net))
    elif fault == "missing-net-code":
        net.set("code", "")
    elif fault == "unknown-node":
        node.set("ref", "UNKNOWN")
    elif fault == "missing-pin":
        node.set("pin", "")
    elif fault == "duplicate-node":
        net.append(copy.deepcopy(node))
    elif fault == "empty-net":
        net.remove(node)
        net[:] = []
    text = ET.tostring(root, encoding="unicode")
    if fault == "doctype":
        text = '<!DOCTYPE export [<!ENTITY x "boom">]>' + text
    elif fault == "oversize":
        text = " " * 2_000_001
    elif fault == "bad-xml":
        text = "<export"
    with pytest.raises(ValueError):
        parse_schematic_xml(text)


def test_schematic_checker_public_api_exists() -> None:
    assert callable(getattr(rev_a, "parse_schematic_xml", None)), "no native netlist parser"
    assert callable(getattr(rev_a, "validate_schematic", None)), "no pin-level checker"


def _break_component_xml(root: ET.Element, comps: ET.Element, fault: str) -> None:
    comp = comps[0]
    if fault == "root":
        root.tag = "other"
    elif fault == "version":
        root.set("version", "unknown")
    elif fault == "empty-parts":
        comps.clear()
    elif fault == "duplicate-ref":
        comps.append(copy.deepcopy(comp))
    elif fault == "duplicate-contract":
        new = copy.deepcopy(comp)
        new.set("ref", "NEW1")
        comps.append(new)
    elif fault == "missing-contract":
        prop = comp.find("property[@name='ContractRef']")
        assert prop is not None
        comp.remove(prop)
    elif fault == "duplicate-prop":
        prop = comp.find("property")
        assert prop is not None
        comp.append(copy.deepcopy(prop))
    elif fault == "wrong-library":
        source = comp.find("libsource")
        assert source is not None
        source.set("lib", "Other")


def test_nonpolar_symbol_cannot_hide_polarized_footprint(
    circuit: tuple[SchematicNetlist, BoardProfile, BillOfMaterials],
) -> None:
    netlist, profile, bom = circuit
    netlist.parts["C_VCAP1"] = replace(netlist.parts["C_VCAP1"], symbol="C")
    assert validate_schematic(netlist, profile, bom), "polarized part displayed without polarity"
