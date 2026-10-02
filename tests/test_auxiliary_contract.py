"""Electrical limits for C3 are conditional calculations, not hardware approval."""

import gzip
import json
import shutil
from dataclasses import replace
from pathlib import Path

import pytest

from hardware.rev_a import (
    AuxiliaryContract,
    SchematicNetlist,
    auxiliary_source_snapshot,
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


# TI SLLSEP3G p6 Figure 5-4 / ISO7721 D,DWV column, NOT ISO7720.
# Directions in C1 were correct; the C3 channel letters were swapped.
@pytest.mark.parametrize("source", ["manifest", "native-export"])
def test_iso7721d_pin_functions_and_uart_directions_match_manufacturer(source: str) -> None:
    expected = {
        "1": ("VCC1", "power_in", "HOST_3V3"),
        "2": ("OUTA", "output", "HOST_RX"),
        "3": ("INB", "input", "HOST_TX"),
        "4": ("GND1", "power_in", "HOST_GND"),
        "5": ("GND2", "power_in", "TARGET_GND"),
        "6": ("OUTB", "output", "CONSOLE_RX"),
        "7": ("INA", "input", "CONSOLE_TX"),
        "8": ("VCC2", "power_in", "MCU_3V3"),
    }
    if source == "manifest":
        pins = _contract().parts["ISO"].pins
        assert {n: (p.function, p.kind, p.net) for n, p in pins.items()} == expected
    else:
        graph = _fixture()
        assert {
            n: (graph.pin_functions[("ISO", n)], graph.pin_types[("ISO", n)]) for n in expected
        } == {n: (v[0], v[1]) for n, v in expected.items()}


@pytest.fixture
def auxiliary_sources(tmp_path: Path) -> tuple[Path, Path]:
    cad, libraries = tmp_path / "auxiliary", tmp_path / "installed"
    shutil.copytree(ROOT / "hardware/rev_a/auxiliary", cad)
    # Supply explicit empty policy so negative cases isolate one forbidden edit.
    project = cad / "auxiliary.kicad_pro"
    value = json.loads(project.read_text())
    value["erc"] = {"erc_exclusions": [], "rule_severities": {}}
    project.write_text(json.dumps(value))
    for part in _contract().parts.values():
        library, name = part.footprint.split(":")
        if library != "Aux_Lands":
            path = libraries / (library + ".pretty") / (name + ".kicad_mod")
            path.parent.mkdir(parents=True, exist_ok=True)
            # This tests source closure, not geometry (covered by native tests).
            path.write_text(f'(footprint "{name}")')
    mount = libraries / "MountingHole.pretty/MountingHole_2.7mm_M2.5.kicad_mod"
    mount.parent.mkdir(exist_ok=True)
    mount.write_text("source-only mounting-land stub, not native geometry")
    return cad, libraries


@pytest.mark.parametrize(
    "erc",
    [
        {"erc_exclusions": [], "rule_severities": {"pin_to_pin": "ignore"}},
        {"erc_exclusions": [], "rule_severities": {"pin_to_pin": "warning"}},
        {"erc_exclusions": ["excluded"], "rule_severities": {}},
        {"erc_exclusions": [], "rule_severities": {}, "future_override": True},
        None,
        [],
    ],
)
def test_auxiliary_snapshot_rejects_erc_waivers(
    auxiliary_sources: tuple[Path, Path], erc: object
) -> None:
    cad, libraries = auxiliary_sources
    path = cad / "auxiliary.kicad_pro"
    value = json.loads(path.read_text())
    value["erc"] = erc
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="ERC"):
        auxiliary_source_snapshot(cad, libraries)


@pytest.mark.parametrize(
    "key,value",
    [
        ("text_variables", {"RAIL": "HOST_3V3"}),
        ("net_settings", {}),
        ("meta", {"filename": "another.kicad_pro", "version": 1}),
    ],
)
def test_auxiliary_snapshot_rejects_undeclared_project_settings(
    auxiliary_sources: tuple[Path, Path], key: str, value: object
) -> None:
    cad, libraries = auxiliary_sources
    path = cad / "auxiliary.kicad_pro"
    project = json.loads(path.read_text())
    project[key] = value
    path.write_text(json.dumps(project))
    with pytest.raises(ValueError, match="project"):
        auxiliary_source_snapshot(cad, libraries)


@pytest.mark.parametrize(
    "file,before,after",
    [
        ("sym-lib-table", "${KIPRJMOD}/RevA.kicad_sym", "/tmp/other.kicad_sym"),
        ("sym-lib-table", '(type "KiCad")', '(type "Legacy")'),
        ("fp-lib-table", "${KICAD9_FOOTPRINT_DIR}/Package_SO.pretty", "/tmp/Package_SO.pretty"),
        ("fp-lib-table", '(options "")', '(options "override")'),
        ("auxiliary.kicad_sch", '"bus.kicad_sch"', '"../bus.kicad_sch"'),
        ("bus.kicad_sch", '"RevA:TXU0304PW"', '"Other:TXU0304PW"'),
        ("RevA.kicad_sym", '(name "VCC1"', '(name "BAD_VCC1"'),
    ],
)
def test_auxiliary_snapshot_rejects_hidden_or_stale_dependencies(
    auxiliary_sources: tuple[Path, Path], file: str, before: str, after: str
) -> None:
    cad, libraries = auxiliary_sources
    path = cad / file
    text = path.read_text()
    assert before in text
    path.write_text(text.replace(before, after, 1))
    with pytest.raises(ValueError):
        auxiliary_source_snapshot(cad, libraries)


@pytest.mark.parametrize("extra", ["hidden.kicad_sch", "Aux_Lands.pretty/extra.kicad_mod"])
def test_auxiliary_snapshot_rejects_extra_native_inputs(
    auxiliary_sources: tuple[Path, Path], extra: str
) -> None:
    cad, libraries = auxiliary_sources
    (cad / extra).write_text("undeclared")
    with pytest.raises(ValueError):
        auxiliary_source_snapshot(cad, libraries)


@pytest.mark.parametrize("directory", ["Aux_Lands.pretty", "Package_SO.pretty"])
def test_auxiliary_snapshot_rejects_linked_library_directories(
    auxiliary_sources: tuple[Path, Path], directory: str
) -> None:
    cad, libraries = auxiliary_sources
    path = (cad if directory == "Aux_Lands.pretty" else libraries) / directory
    target = path.with_name("elsewhere")
    path.rename(target)
    path.symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError, match="link"):
        auxiliary_source_snapshot(cad, libraries)


def test_auxiliary_snapshot_accepts_whitespace_and_reordered_empty_project(
    auxiliary_sources: tuple[Path, Path],
) -> None:
    cad, libraries = auxiliary_sources
    before = auxiliary_source_snapshot(cad, libraries)
    path = cad / "auxiliary.kicad_pro"
    value = json.loads(path.read_text())
    path.write_text(json.dumps(value, indent=4, sort_keys=True))
    after = auxiliary_source_snapshot(cad, libraries)
    assert before.keys() == after.keys()
    assert before["auxiliary/auxiliary.kicad_pro"] != after["auxiliary/auxiliary.kicad_pro"]


def _manifest_child(node: object, key: str | int) -> object:
    if isinstance(node, dict) and isinstance(key, str):
        mapping: dict[str, object] = node
        return mapping[key]
    assert isinstance(node, list) and isinstance(key, int)
    sequence: list[object] = node
    return sequence[key]


def _changed_manifest(path: tuple[str | int, ...], value: object, remove: bool) -> str:
    data: object = json.loads((ROOT / "hardware/rev_a/auxiliary/contract.json").read_text())
    node = data
    for key in path[:-1]:
        node = _manifest_child(node, key)
    last = path[-1]
    if isinstance(last, str):
        assert isinstance(node, dict)
        mapping: dict[str, object] = node
        if remove:
            del mapping[last]
        else:
            mapping[last] = value
    else:
        assert isinstance(node, list)
        sequence: list[object] = node
        if remove:
            del sequence[last]
        else:
            sequence[last] = value
    return json.dumps(data)


@pytest.mark.parametrize(
    "path,value,remove",
    [
        (("status",), None, True),
        (("status",), "released", False),
        (("status",), None, False),
        (("external_assumptions",), None, True),
        (("external_assumptions",), "not a list", False),
        (("external_assumptions",), {}, False),
        (("external_assumptions",), [], False),
        (("external_assumptions",), [""], False),
        (("external_assumptions",), [3], False),
        (("external_assumptions", 0), "external ports are always powered", False),
        (("external_assumptions", 0), None, True),
        (("parts", 0, "sheet"), None, True),
        (("parts", 0, "sheet"), None, False),
        (("parts", 0, "sheet"), "../bus.kicad_sch", False),
        (("extra_approval",), True, False),
        (("parts", 0, "extra_population"), "DNP", False),
        (("parts", 0, "pins", "1", "ignored_type"), "passive", False),
        (("parts", 0, "pins", "1", "type"), "unknown", False),
    ],
)
def test_auxiliary_manifest_closes_metadata_and_record_fields(
    path: tuple[str | int, ...], value: object, remove: bool
) -> None:
    """Required draft metadata cannot silently disappear or acquire release semantics."""
    with pytest.raises(ValueError):
        parse_auxiliary_contract(_changed_manifest(path, value, remove))


@pytest.mark.parametrize("field", ["status", "sheet", "net"])
def test_auxiliary_manifest_rejects_duplicate_json_fields(field: str) -> None:
    text = (ROOT / "hardware/rev_a/auxiliary/contract.json").read_text()
    assert f'"{field}":' in text
    text = text.replace(f'"{field}":', f'"{field}": "discarded", "{field}":', 1)
    with pytest.raises(ValueError):
        parse_auxiliary_contract(text)


@pytest.mark.parametrize("number", ["01", "\u0661"])
def test_auxiliary_manifest_requires_canonical_pin_numbers(number: str) -> None:
    text = (ROOT / "hardware/rev_a/auxiliary/contract.json").read_text()
    with pytest.raises(ValueError):
        parse_auxiliary_contract(text.replace('"1": {', f'"{number}": {{', 1))


def test_auxiliary_manifest_rejects_duplicate_assumptions() -> None:
    data = json.loads((ROOT / "hardware/rev_a/auxiliary/contract.json").read_text())
    data["external_assumptions"].append(data["external_assumptions"][0])
    with pytest.raises(ValueError):
        parse_auxiliary_contract(json.dumps(data))


def test_auxiliary_manifest_accepts_reordered_objects_and_assumptions() -> None:
    data = json.loads((ROOT / "hardware/rev_a/auxiliary/contract.json").read_text())
    data["external_assumptions"].reverse()
    assert parse_auxiliary_contract(json.dumps(data, sort_keys=True, indent=4)) == _contract()


def test_auxiliary_snapshot_checks_declared_sheet_against_native_instances(
    auxiliary_sources: tuple[Path, Path],
) -> None:
    cad, libraries = auxiliary_sources
    # This is a valid filename but a false physical sheet location for J101.
    path = cad / "contract.json"
    path.write_text(_changed_manifest(("parts", 0, "sheet"), "bus.kicad_sch", False))
    with pytest.raises(ValueError, match="sheet"):
        auxiliary_source_snapshot(cad, libraries)


def test_auxiliary_snapshot_includes_placement_rules_and_mechanical_land(
    auxiliary_sources: tuple[Path, Path],
) -> None:
    cad, libraries = auxiliary_sources
    p = libraries / "MountingHole.pretty/MountingHole_2.7mm_M2.5.kicad_mod"
    p.parent.mkdir(exist_ok=True)
    p.write_text("mechanical land hash fixture, not native geometry")
    snapshot = auxiliary_source_snapshot(cad, libraries)
    assert {
        "auxiliary/auxiliary.kicad_pcb",
        "auxiliary/auxiliary.kicad_dru",
        "auxiliary-footprint/MountingHole:MountingHole_2.7mm_M2.5",
    } <= snapshot.keys()


@pytest.mark.parametrize("before,after", [("0.15mm", "0.1mm"), ("3.0mm", "0.3mm"), ("U111", "U*")])
def test_auxiliary_snapshot_rejects_weakened_placement_rules(
    auxiliary_sources: tuple[Path, Path],
    before: str,
    after: str,
) -> None:
    cad, libraries = auxiliary_sources
    p = cad / "auxiliary.kicad_dru"
    original = p.read_text()
    assert before in original
    p.write_text(original.replace(before, after))
    with pytest.raises(ValueError, match="P1 rules"):
        auxiliary_source_snapshot(cad, libraries)
