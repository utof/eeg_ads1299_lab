"""C3's finite native netlist contract; connectivity is not fault qualification."""

import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .check_schematic import SchematicNetlist
from .schematic_sources import read_schematic_file


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


def auxiliary_source_snapshot(cad: Path, footprints: Path) -> dict[str, str]:
    """Bind the actual authored auxiliary source and selected installed land patterns."""
    result: dict[str, str] = {}
    for name in (
        "auxiliary.kicad_sch",
        "bus.kicad_sch",
        "supervision.kicad_sch",
        "arming.kicad_sch",
        "auxiliary.kicad_pro",
        "RevA.kicad_sym",
        "sym-lib-table",
        "fp-lib-table",
        "contract.json",
    ):
        result["auxiliary/" + name] = hashlib.sha256(
            read_schematic_file(cad / name).encode()
        ).hexdigest()
    contract = parse_auxiliary_contract(read_schematic_file(cad / "contract.json"))
    for identifier in sorted({part.footprint for part in contract.parts.values()}):
        if re.fullmatch(r"[A-Za-z0-9_.+-]+:[A-Za-z0-9_.+-]+", identifier) is None:
            raise ValueError("C3 invalid footprint identifier")
        library, name = identifier.split(":")
        base = cad if library == "Aux_Lands" else footprints
        path = base / (library + ".pretty") / (name + ".kicad_mod")
        result["auxiliary-footprint/" + identifier] = hashlib.sha256(
            read_schematic_file(path).encode()
        ).hexdigest()
    return result
