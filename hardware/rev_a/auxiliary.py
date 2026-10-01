"""C3's finite native netlist contract; connectivity is not fault qualification."""

import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .check_schematic import SchematicNetlist
from .schematic_sources import _strings, read_schematic_file
from .schematic_symbols import _children, _Form, _parse, validate_symbol_caches


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
    pins: dict[str, AuxiliaryPin]


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


def _pins(value: object) -> dict[str, AuxiliaryPin]:
    result: dict[str, AuxiliaryPin] = {}
    for number, raw in _object(value).items():
        if not number.isdecimal() or int(number) < 1:
            raise ValueError("C3 invalid pin number")
        pin = _object(raw)
        if "net" not in pin:
            raise ValueError("C3 pin requires an explicit net or null")
        net = pin["net"]
        result[number] = AuxiliaryPin(
            None if net is None else _string(net),
            _string(pin.get("function")),
            _string(pin.get("type")),
        )
    if not result:
        raise ValueError("C3 empty pin inventory")
    return result


def parse_auxiliary_contract(content: str) -> AuxiliaryContract:
    """Validate the small source manifest, never use a cast as schema validation."""
    if len(content) > 200_000:
        raise ValueError("C3 manifest too large")
    root = _object(json.loads(content))
    if root.get("revision") != "C3" or root.get("approval") is not False:
        raise ValueError("C3 revision/approval drift")
    rows = root.get("parts")
    if not isinstance(rows, list) or not rows:
        raise ValueError("C3 expected nonempty parts list")
    items: list[object] = rows
    parts: dict[str, AuxiliaryPart] = {}
    references: set[str] = set()
    for item in items:
        row = _object(item)
        ref, native = _string(row.get("contract_ref")), _string(row.get("reference"))
        if ref in parts or native in references or not isinstance(row.get("in_bom"), bool):
            raise ValueError("C3 duplicate part or invalid BOM flag")
        references.add(native)
        parts[ref] = AuxiliaryPart(
            native,
            _string(row.get("symbol")),
            _string(row.get("value")),
            _string(row.get("mpn")),
            _string(row.get("footprint")),
            row["in_bom"] is True,
            _pins(row.get("pins")),
        )
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
        if actual.properties.get("Population") != "fit" or "dnp" in actual.properties:
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


def _source_configuration(contents: dict[str, str]) -> None:
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


def _auxiliary_land_snapshot(
    cad: Path, footprints: Path, contract: AuxiliaryContract
) -> dict[str, str]:
    identifiers = {p.footprint for p in contract.parts.values()}
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
    result = {"auxiliary/" + n: hashlib.sha256(t.encode()).hexdigest() for n, t in contents.items()}
    result.update(_auxiliary_land_snapshot(cad, footprints, contract))
    return result
