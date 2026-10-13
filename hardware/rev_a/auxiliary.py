"""C3's finite native netlist contract; connectivity is not fault qualification."""

import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .check_schematic import SchematicNetlist
from .schematic_sources import _strings, read_schematic_file
from .schematic_symbols import _children, _Form, _name, _parse, validate_symbol_caches


@dataclass(frozen=True)
class AuxiliaryPin:
    net: str | None
    function: str
    kind: str


@dataclass(frozen=True)
class AuxiliaryPart:
    reference: str
    symbol: str
    value: str
    mpn: str
    footprint: str
    in_bom: bool
    population: str
    pins: dict[str, AuxiliaryPin]
    sheet: str


@dataclass(frozen=True)
class AuxiliaryContract:
    parts: dict[str, AuxiliaryPart]


def _object(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("C3 expected object")
    result: dict[str, object] = {}
    items: dict[object, object] = value
    for key, item in items.items():
        if not isinstance(key, str):
            raise ValueError("C3 keys must be strings")
        result[key] = item
    return result


def _string(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("C3 expected nonempty string")
    return value


_ROOT_FIELDS = frozenset({"revision", "status", "parts", "external_assumptions", "approval"})
_PART_FIELDS = frozenset(
    {
        "reference",
        "contract_ref",
        "symbol",
        "value",
        "mpn",
        "footprint",
        "in_bom",
        "population",
        "pins",
        "sheet",
    }
)
_PIN_FIELDS = frozenset({"net", "function", "type"})
_PIN_TYPES = frozenset(
    {
        "input",
        "no_connect",
        "open_collector",
        "output",
        "passive",
        "power_in",
        "power_out",
        "tri_state",
    }
)
_EXTERNAL_ASSUMPTIONS = frozenset(
    {
        "interface pin types describe actual external endpoint roles, not always-powered sources",
        "AFE six-way rail access requires the separate inspected 1:1 service harness; no hot mating",
        "MCU tails remain permanent; bare-board USB programming requires removal",
        "no HOST/TARGET power or ground jumper",
        "F1 implements the C2 handshake; automatic analog source isolation remains absent",
    }
)


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("C3 duplicate JSON field")
        result[key] = value
    return result


def _closed_object(value: object, fields: frozenset[str]) -> dict[str, object]:
    result = _object(value)
    if set(result) != fields:
        raise ValueError("C3 record field inventory differs")
    return result


def _member(value: object, permitted: frozenset[str], field: str) -> str:
    text = _string(value)
    if text not in permitted:
        raise ValueError(f"C3 invalid {field}")
    return text


def _assumptions(value: object) -> None:
    # Fixed draft scope: changing an assumption requires a coordinated design review.
    if not isinstance(value, list) or len(value) != len(_EXTERNAL_ASSUMPTIONS):
        raise ValueError("C3 external assumptions inventory differs")
    items: list[object] = value
    if {_string(item) for item in items} != _EXTERNAL_ASSUMPTIONS:
        raise ValueError("C3 external assumptions differ")


def _pins(value: object) -> dict[str, AuxiliaryPin]:
    result: dict[str, AuxiliaryPin] = {}
    for number, raw in _object(value).items():
        if re.fullmatch(r"[1-9][0-9]*", number) is None:
            raise ValueError("C3 invalid pin number")
        pin = _closed_object(raw, _PIN_FIELDS)
        net = pin["net"]
        result[number] = AuxiliaryPin(
            None if net is None else _string(net),
            _string(pin["function"]),
            _member(pin["type"], _PIN_TYPES, "pin type"),
        )
    if not result:
        raise ValueError("C3 empty pin inventory")
    return result


def _part(row: dict[str, object]) -> AuxiliaryPart:
    if not isinstance(row["in_bom"], bool):
        raise ValueError("C3 invalid BOM flag")
    return AuxiliaryPart(
        _string(row["reference"]),
        _string(row["symbol"]),
        _string(row["value"]),
        _string(row["mpn"]),
        _string(row["footprint"]),
        row["in_bom"] is True,
        _member(row["population"], frozenset({"fit", "dnp"}), "population"),
        _pins(row["pins"]),
        _member(row["sheet"], _AUX_SHEETS, "sheet"),
    )


_SERIES_POSITIONS = {
    "R_AFE_SCLK_SER": "R117",
    "R_AFE_MOSI_SER": "R118",
    "R_AFE_CS_SER": "R119",
    "R_MCU_MISO_SER": "R120",
}


def _population(ref: str, part: AuxiliaryPart) -> None:
    expected = "dnp" if ref in _SERIES_POSITIONS else "fit"
    if part.population != expected:
        raise ValueError("C3 population must retain fitted devices and unpopulated SPI positions")
    if expected == "dnp" and not (
        part.reference == _SERIES_POSITIONS[ref]
        and part.symbol == "R"
        and part.value == part.mpn == "NOT_SELECTED"
        and part.footprint == "Resistor_SMD:R_0603_1608Metric"
        and part.in_bom
        and part.sheet == "bus.kicad_sch"
    ):
        raise ValueError("C3 SPI position must remain an unselected in-BOM 0603 resistor")


def parse_auxiliary_contract(content: str) -> AuxiliaryContract:
    """Validate the complete finite draft manifest, including discarded metadata."""
    if len(content) > 200_000:
        raise ValueError("C3 manifest too large")
    root = _closed_object(json.loads(content, object_pairs_hook=_unique_json_object), _ROOT_FIELDS)
    if root["revision"] != "C3" or root["approval"] is not False:
        raise ValueError("C3 revision/approval drift")
    if root["status"] != "native_schematic_draft_not_layout_or_powered_release":
        raise ValueError("C3 draft status differs")
    _assumptions(root["external_assumptions"])
    rows = root["parts"]
    if not isinstance(rows, list) or not rows:
        raise ValueError("C3 expected nonempty parts list")
    items: list[object] = rows
    parts: dict[str, AuxiliaryPart] = {}
    references: set[str] = set()
    for item in items:
        row = _closed_object(item, _PART_FIELDS)
        ref, part = _string(row["contract_ref"]), _part(row)
        if ref in parts or part.reference in references:
            raise ValueError("C3 duplicate part")
        _population(ref, part)
        references.add(part.reference)
        parts[ref] = part
    return AuxiliaryContract(parts)


def _identity_errors(netlist: SchematicNetlist, contract: AuxiliaryContract) -> list[str]:
    errors: list[str] = []
    if set(netlist.parts) != set(contract.parts):
        errors.append("C3 part inventory differs")
    for ref, expected in contract.parts.items():
        actual = netlist.parts.get(ref)
        if actual is None:
            continue
        if (actual.native_ref, actual.symbol, actual.value, actual.footprint) != (
            expected.reference,
            expected.symbol,
            expected.value,
            expected.footprint,
        ):
            errors.append(f"C3 {ref}: reference/symbol/value/footprint differs")
        if actual.properties.get("MPN") != expected.mpn:
            errors.append(f"C3 {ref}: MPN differs")
        if ("exclude_from_bom" not in actual.properties) != expected.in_bom:
            errors.append(f"C3 {ref}: BOM inclusion differs")
        if actual.properties.get("Population") != expected.population or (
            "dnp" in actual.properties
        ) != (expected.population == "dnp"):
            errors.append(f"C3 {ref}: population differs")
        if "exclude_from_board" in actual.properties:
            errors.append(f"C3 {ref}: missing from board")
    return errors


def _part_pin_errors(
    netlist: SchematicNetlist, ref: str, part: AuxiliaryPart, sizes: Counter[str]
) -> list[str]:
    errors: list[str] = []
    for number, pin in part.pins.items():
        key = (ref, number)
        expected_type = pin.kind
        if pin.net is None and pin.kind != "no_connect":
            expected_type += "+no_connect"
        if (netlist.pin_types.get(key), netlist.pin_functions.get(key)) != (
            expected_type,
            pin.function,
        ):
            errors.append(f"C3 {ref}.{number}: pin function/type differs")
        if pin.net is None and sizes.get(netlist.nets.get(key, ""), 0) != 1:
            errors.append(f"C3 {ref}.{number}: NC is not isolated")
    return errors


def _pin_errors(netlist: SchematicNetlist, contract: AuxiliaryContract) -> list[str]:
    errors: list[str] = []
    expected_pins = {(r, n) for r, p in contract.parts.items() for n in p.pins}
    if set(netlist.nets) != expected_pins:
        errors.append("C3 pin inventory differs")
    sizes = Counter(netlist.nets.values())
    for ref, part in contract.parts.items():
        errors.extend(_part_pin_errors(netlist, ref, part, sizes))
    return errors


def _anchor_nets(
    netlist: SchematicNetlist, contract: AuxiliaryContract
) -> tuple[dict[str, str], list[str]]:
    anchors = {
        (ref, number): pin.net
        for ref, part in contract.parts.items()
        if part.symbol not in {"R", "C"}
        for number, pin in part.pins.items()
        if pin.net is not None
    }
    errors: list[str] = []
    actual_to_expected: dict[str, str] = {}
    expected_to_actual: dict[str, str] = {}
    for terminal, expected_net in anchors.items():
        code = netlist.nets.get(terminal, "")
        if actual_to_expected.setdefault(code, expected_net) != expected_net:
            errors.append(f"C3 {terminal}: forbidden net join")
        if expected_to_actual.setdefault(expected_net, code) != code:
            errors.append(f"C3 {terminal}: missing net connection")
    return actual_to_expected, errors


def _net_errors(netlist: SchematicNetlist, contract: AuxiliaryContract) -> list[str]:
    """Anchor to IC/port terminals; label renames and passive reversals are benign."""
    mapping, errors = _anchor_nets(netlist, contract)
    for ref, part in contract.parts.items():
        if part.symbol not in {"R", "C"}:
            continue
        actual = Counter(mapping.get(netlist.nets.get((ref, n), "")) for n in part.pins)
        expected = Counter(pin.net for pin in part.pins.values())
        if actual != expected:
            errors.append(f"C3 {ref}: passive terminal pair differs")
    return errors


def validate_auxiliary(netlist: SchematicNetlist, contract: AuxiliaryContract) -> list[str]:
    """Check every manifest terminal and its partition; do not authorize hardware."""
    return (
        _identity_errors(netlist, contract)
        + _pin_errors(netlist, contract)
        + _net_errors(netlist, contract)
    )


def validate_auxiliary_erc(content: str) -> None:
    """Require all four C3 sheets and zero native findings, including warnings."""
    report = _object(json.loads(content))
    if report.get("kicad_version") != "9.0.2" or report.get("source") != "auxiliary.kicad_sch":
        raise ValueError("C3 ERC source/version mismatch")
    raw = report.get("sheets")
    if not isinstance(raw, list) or len(raw) != 4:
        raise ValueError("C3 ERC requires four sheets")
    rows: list[object] = raw
    paths: set[str] = set()
    for row in rows:
        sheet = _object(row)
        path = _string(sheet.get("path"))
        if path in paths or sheet.get("violations") != []:
            raise ValueError("C3 duplicate sheet or nonempty/missing violations")
        paths.add(path)
    if paths != {"/", "/BUS/", "/SUPERVISION/", "/ARMING/"}:
        raise ValueError("C3 ERC sheet identity mismatch")


_AUX_SHEETS = frozenset(
    {"auxiliary.kicad_sch", "bus.kicad_sch", "supervision.kicad_sch", "arming.kicad_sch"}
)
_AUX_FILES = _AUX_SHEETS | {
    "auxiliary.kicad_pro",
    "auxiliary.kicad_pcb",
    "auxiliary.kicad_dru",
    "RevA.kicad_sym",
    "sym-lib-table",
    "fp-lib-table",
}
_AUX_LIBRARIES = frozenset(
    {
        "Package_SO",
        "Package_SON",
        "Package_TO_SOT_SMD",
        "Resistor_SMD",
        "Capacitor_SMD",
        "Connector_JST",
        "Aux_Lands",
        "MountingHole",
    }
)


def _table_entry(entry: _Form) -> tuple[str, str]:
    """Read the existing bounded parser's fields; allow only plain KiCad libraries."""
    fields: dict[str, str] = {}
    for field in entry.items[1:]:
        if not isinstance(field, _Form) or len(field.items) != 2:
            raise ValueError("C3 malformed library field")
        key, raw = field.items
        if not isinstance(key, str) or not isinstance(raw, str) or key in fields:
            raise ValueError("C3 duplicate or malformed library field")
        value: object = json.loads(raw)
        if not isinstance(value, str):
            raise ValueError("C3 library field must be quoted text")
        fields[key] = value
    if set(fields) != {"name", "type", "uri", "options", "descr"}:
        raise ValueError("C3 library field inventory differs")
    if fields["type"] != "KiCad" or fields["options"] != "":
        raise ValueError("C3 library type/options override")
    return fields["name"], fields["uri"]


def _library_table(text: str, head: str, expected: dict[str, str]) -> None:
    table = _parse(text)
    versions = _children(table, "version")
    entries = _children(table, "lib")
    if table.items[0] != head or len(table.items) != 2 + len(entries):
        raise ValueError("C3 library table structure differs")
    if len(versions) != 1 or versions[0].items != ("version", "7"):
        raise ValueError("C3 library table version differs")
    pairs = [_table_entry(entry) for entry in entries]
    if len(pairs) != len(expected) or dict(pairs) != expected:
        raise ValueError("C3 library name/URI inventory differs")


_P1_RULES = """(version 1)
(rule "U111 selected 0.5mm-pitch native land"
  (condition "A.Type == 'Pad' && B.Type == 'Pad' && A.memberOfFootprint('U111') && B.memberOfFootprint('U111')")
  (constraint clearance (min 0.15mm)))
(rule "HOST TARGET external copper separation"
  (condition "(A.NetName == 'HOST_*' && B.NetName != 'HOST_*' && B.NetName != '') || (B.NetName == 'HOST_*' && A.NetName != 'HOST_*' && A.NetName != '')")
  (constraint clearance (min 3.0mm)))
"""


def _source_configuration(contents: dict[str, str]) -> None:
    if _parse("(rules " + contents["auxiliary.kicad_dru"] + ")") != _parse(
        "(rules " + _P1_RULES + ")"
    ):
        raise ValueError("P1 rules differ from the reviewed placement constraints")
    project = _object(json.loads(contents["auxiliary.kicad_pro"]))
    if project.get("erc") != {"erc_exclusions": [], "rule_severities": {}}:
        raise ValueError("C3 ERC exclusions/severity overrides are not permitted")
    if (
        set(project) != {"meta", "erc", "text_variables"}
        or project["meta"] != {"filename": "auxiliary.kicad_pro", "version": 1}
        or project["text_variables"] != {}
    ):
        raise ValueError("C3 undeclared project configuration")
    children = _strings(r'\(property\s+"Sheetfile"', contents["auxiliary.kicad_sch"])
    if sorted(children) != ["arming.kicad_sch", "bus.kicad_sch", "supervision.kicad_sch"]:
        raise ValueError("C3 root hierarchy differs from snapshotted sheets")
    for name in sorted(_AUX_SHEETS - {"auxiliary.kicad_sch"}):
        if _strings(r'\(property\s+"Sheetfile"', contents[name]):
            raise ValueError("C3 nested sheet is not snapshotted")
    _library_table(
        contents["sym-lib-table"], "sym_lib_table", {"RevA": "${KIPRJMOD}/RevA.kicad_sym"}
    )
    _library_table(
        contents["fp-lib-table"],
        "fp_lib_table",
        {
            name: "${"
            + ("KIPRJMOD" if name == "Aux_Lands" else "KICAD9_FOOTPRINT_DIR")
            + "}/"
            + name
            + ".pretty"
            for name in _AUX_LIBRARIES
        },
    )
    validate_symbol_caches(
        contents["RevA.kicad_sym"], {n: contents[n] for n in sorted(_AUX_SHEETS)}
    )


def _instance_reference(symbol: _Form) -> str:
    fields = [p for p in _children(symbol, "property") if _name(p) == "Reference"]
    if len(fields) != 1 or len(fields[0].items) < 3:
        raise ValueError("C3 sheet symbol requires one Reference")
    raw = fields[0].items[2]
    if not isinstance(raw, str) or not raw.startswith('"'):
        raise ValueError("C3 sheet symbol Reference must be quoted")
    return _string(json.loads(raw))


def _sheet_assignments(contents: dict[str, str], contract: AuxiliaryContract) -> None:
    """Bind declared sheet metadata to actual top-level instances, not just file names."""
    actual = Counter(
        (_instance_reference(symbol), sheet)
        for sheet in sorted(_AUX_SHEETS)
        for symbol in _children(_parse(contents[sheet]), "symbol")
    )
    expected = Counter((part.reference, part.sheet) for part in contract.parts.values())
    if actual != expected:
        raise ValueError("C3 native sheet assignments differ from manifest")


def _auxiliary_land_snapshot(
    cad: Path, footprints: Path, contract: AuxiliaryContract
) -> dict[str, str]:
    identifiers = {p.footprint for p in contract.parts.values()} | {
        "MountingHole:MountingHole_2.7mm_M2.5"
    }
    local = cad / "Aux_Lands.pretty"
    if local.is_symlink() or footprints.is_symlink():
        raise ValueError("C3 footprint directory link is not permitted")
    expected = {i.split(":")[1] + ".kicad_mod" for i in identifiers if i.startswith("Aux_Lands:")}
    if {p.name for p in local.iterdir()} != expected:
        raise ValueError("C3 local footprint inventory differs")
    result: dict[str, str] = {}
    for identifier in sorted(identifiers):
        if re.fullmatch(r"[A-Za-z0-9_.+-]+:[A-Za-z0-9_.+-]+", identifier) is None:
            raise ValueError("C3 invalid footprint identifier")
        library, name = identifier.split(":")
        if library not in _AUX_LIBRARIES:
            raise ValueError("C3 undeclared footprint library")
        directory = (cad if library == "Aux_Lands" else footprints) / (library + ".pretty")
        if directory.is_symlink():
            raise ValueError("C3 footprint library link is not permitted")
        result["auxiliary-footprint/" + identifier] = hashlib.sha256(
            read_schematic_file(directory / (name + ".kicad_mod")).encode()
        ).hexdigest()
    return result


def auxiliary_source_snapshot(cad: Path, footprints: Path) -> dict[str, str]:
    """Reject suppressed ERC/hidden dependencies before hashing the closed C3 input set."""
    if cad.is_symlink():
        raise ValueError("C3 CAD directory link is not permitted")
    actual = {
        p.name
        for p in cad.iterdir()
        if p.suffix.startswith(".kicad_") or p.name.endswith("-lib-table")
    }
    if actual != _AUX_FILES:
        raise ValueError("C3 native CAD input inventory differs")
    contents = {name: read_schematic_file(cad / name) for name in sorted(_AUX_FILES)}
    _source_configuration(contents)
    contents["contract.json"] = read_schematic_file(cad / "contract.json")
    contract = parse_auxiliary_contract(contents["contract.json"])
    _sheet_assignments(contents, contract)
    result = {"auxiliary/" + n: hashlib.sha256(t.encode()).hexdigest() for n, t in contents.items()}
    result.update(_auxiliary_land_snapshot(cad, footprints, contract))
    return result
