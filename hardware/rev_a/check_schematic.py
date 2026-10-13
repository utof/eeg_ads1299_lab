"""Pin-level checks of a KiCad XML export; never an electrical/safety approval.

The native schematic is authoritative. This checker independently specifies the
chosen circuit's connectivity and consumes the existing validated BOM/profile.
Net names and the orientation of nonpolar two-terminal passives are immaterial.
"""

from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass

from .check_baseline import BillOfMaterials, BoardProfile, BomItem

Pin = tuple[str, str]


@dataclass(frozen=True)
class SchematicPart:
    native_ref: str
    value: str
    footprint: str
    properties: dict[str, str]
    symbol: str


@dataclass(frozen=True)
class SchematicNetlist:
    parts: dict[str, SchematicPart]
    nets: dict[Pin, str]
    pin_types: dict[Pin, str]
    pin_functions: dict[Pin, str]


FOOTPRINTS = {
    "afe": "Package_QFP:TQFP-64_10x10mm_P0.5mm",
    "controller": "",
    "dvdd_ldo": "Package_TO_SOT_SMD:SOT-23-5",
    "input_r": "Resistor_SMD:R_0603_1608Metric",
    "bias_r": "Resistor_SMD:R_0603_1608Metric",
    "straps": "Resistor_SMD:R_0603_1608Metric",
    "bus_pulldowns": "Resistor_SMD:R_0603_1608Metric",
    "analog_feed": "Resistor_SMD:R_0603_1608Metric",
    "spi_series": "Resistor_SMD:R_0603_1608Metric",
    "input_c": "Capacitor_SMD:C_0603_1608Metric",
    "bias_c": "Capacitor_SMD:C_0603_1608Metric",
    "decap_1u": "Capacitor_SMD:C_0603_1608Metric",
    "decap_100n": "Capacitor_SMD:C_0603_1608Metric",
    "bulk_10u": "Capacitor_SMD:C_0805_2012Metric",
    "vcap1": "RevA_Passives:T491D_7343_DensityB",
    "vref": "RevA_Passives:T491B_3528_DensityB",
    "service_header": "Connector_JST:JST_XH_B6B-XH-A_1x06_P2.50mm_Vertical",
    "headers": "Connector_PinHeader_2.54mm:PinHeader_2x10_P2.54mm_Vertical",
    "clamps": "Package_TO_SOT_SMD:SOT-23",
}


def _properties(comp: ET.Element) -> dict[str, str]:
    result: dict[str, str] = {}
    for prop in comp.findall("property"):
        name = prop.get("name", "")
        if not name or name in result:
            raise ValueError("missing/duplicate component property")
        result[name] = prop.get("value", "")
    return result


def _parts(root: ET.Element) -> tuple[dict[str, SchematicPart], dict[str, str]]:
    parts: dict[str, SchematicPart] = {}
    refs: dict[str, str] = {}
    for comp in root.findall("components/comp"):
        native = comp.get("ref", "")
        props = _properties(comp)
        contract = props.get("ContractRef", "")
        if not native or not contract or native in refs or contract in parts:
            raise ValueError("missing/duplicate native or contract reference")
        source = comp.find("libsource")
        if source is None or source.get("lib") != "RevA":
            raise ValueError("component must use the reviewed local symbol library")
        parts[contract] = SchematicPart(
            native,
            comp.findtext("value", ""),
            comp.findtext("footprint", ""),
            props,
            source.get("part", ""),
        )
        refs[native] = contract
    if not parts:
        raise ValueError("empty component inventory")
    return parts, refs


def parse_schematic_xml(content: str) -> SchematicNetlist:
    """Read an exported, bounded XML document; do not resolve external entities."""
    if len(content) > 2_000_000 or re.search(r"<!\s*(?:DOCTYPE|ENTITY)", content, re.I):
        raise ValueError("oversize XML or forbidden DTD/entity declaration")
    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        raise ValueError("malformed KiCad XML export") from exc
    if root.tag != "export" or root.get("version") != "E":
        raise ValueError("expected KiCad XML export version E")
    parts, refs = _parts(root)
    nets: dict[Pin, str] = {}
    types: dict[Pin, str] = {}
    functions: dict[Pin, str] = {}
    codes: set[str] = set()
    names: set[str] = set()
    for net in root.findall("nets/net"):
        code, name = net.get("code", ""), net.get("name", "")
        if not code or not name or code in codes or name in names:
            raise ValueError("missing/duplicate net code or name")
        codes.add(code)
        names.add(name)
        _nodes(net, refs, nets, types, functions, code)
    if not nets:
        raise ValueError("empty connectivity inventory")
    return SchematicNetlist(parts, nets, types, functions)


def _nodes(
    net: ET.Element,
    refs: dict[str, str],
    nets: dict[Pin, str],
    types: dict[Pin, str],
    functions: dict[Pin, str],
    code: str,
) -> None:
    nodes = net.findall("node")
    if not nodes:
        raise ValueError("net without nodes")
    for node in nodes:
        native, number = node.get("ref", ""), node.get("pin", "")
        if native not in refs or not number:
            raise ValueError("unknown component or missing pin in net")
        pin = (refs[native], number)
        if pin in nets:
            raise ValueError("pin occurs more than once in connectivity")
        nets[pin] = code
        types[pin] = node.get("pintype", "")
        functions[pin] = node.get("pinfunction", "")


def _number(value: str) -> float:
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?(?:[eE][+-]?\d+)?)([pnumkKM]?)", value)
    if match is None:
        raise ValueError(f"not a supported finite engineering value: {value}")
    scales = {"": 1.0, "p": 1e-12, "n": 1e-9, "u": 1e-6, "m": 1e-3, "k": 1e3, "K": 1e3, "M": 1e6}
    number = float(match[1]) * scales[match[2]]
    if not math.isfinite(number):
        raise ValueError("nonfinite component value")
    return number


def _part_errors(part: SchematicPart, row: BomItem) -> list[str]:
    props = part.properties
    required = {"MPN": row["mpn"], "BOM_ID": row["id"], "Population": row["population"]}
    errors = []
    if any(props.get(key) != value for key, value in required.items()):
        errors.append("BOM identity/population mismatch")
    if ("dnp" in props) != (row["population"] == "dnp"):
        errors.append("native DNP flag differs from BOM")
    if ("exclude_from_board" in props) != (row["id"] == "controller"):
        errors.append("native board inclusion differs from contract")
    if part.footprint != FOOTPRINTS[row["id"]]:
        errors.append("footprint differs from selected package")
    if part.symbol != _symbol(row["id"]):
        errors.append("symbol differs from selected device/polarity")
    _value_errors(part, row, errors)
    return errors


def _symbol(item: str) -> str:
    choices = {
        "afe": "ADS1299_4",
        "controller": "External_S3",
        "dvdd_ldo": "TPS7A2033",
        "headers": "Header_2x10",
        "service_header": "Service_1x06",
        "clamps": "BAV199",
        "vcap1": "CP",
        "vref": "CP",
    }
    if item in choices:
        return choices[item]
    resistors = {"input_r", "bias_r", "straps", "bus_pulldowns", "analog_feed", "spi_series"}
    return "R" if item in resistors else "C"


def _value_errors(part: SchematicPart, row: BomItem, errors: list[str]) -> None:
    spec = row["spec"]
    expected = spec.get("resistance_ohm", spec.get("capacitance_f"))
    try:
        if expected is None:
            if part.value != row["mpn"]:
                errors.append("displayed device value differs from MPN")
        elif not math.isclose(_number(part.value), expected, rel_tol=1e-9, abs_tol=0):
            errors.append("displayed passive value differs from BOM")
        tolerance = spec.get("tolerance_fraction")
        if tolerance is not None and _number(part.properties.get("Tolerance", "")) != tolerance:
            errors.append("tolerance differs from BOM")
    except ValueError as exc:
        errors.append(str(exc))


# These are package pad identities from TI SBAS499C, not library coordinates.
# Each tuple is (functional net, electrical type, pin function). None means NC.
def _channel_pins() -> dict[str, tuple[str | None, str, str]]:
    pins: dict[str, tuple[str | None, str, str]] = {}
    for channel in range(1, 9):
        for offset, leg in [(18, "P"), (17, "N")]:
            function = f"IN{channel}{leg}"
            pins[str(offset - 2 * channel)] = (
                function if channel <= 4 else "AVDD",
                "input",
                function,
            )
    return pins


def _ads_pins() -> dict[str, tuple[str | None, str, str]]:
    pins = _channel_pins()
    for numbers, net, kind, function in [
        ([19, 21, 22, 56, 59], "AVDD", "power_in", "AVDD"),
        ([54], "AVDD", "power_in", "AVDD1"),
        ([20, 23, 32, 57, 58], "GND", "power_in", "AVSS"),
        ([53], "GND", "power_in", "AVSS1"),
        ([33, 49, 51], "GND", "power_in", "DGND"),
        ([48, 50], "DVDD", "power_in", "DVDD"),
        ([25], "GND", "power_in", "VREFN"),
        ([31], "GND", "input", "RESV1"),
        ([41], "GND", "input", "DAISY_IN"),
        ([60], "GND", "input", "BIASREF"),
        ([62], "GND", "input", "BIASIN"),
        ([27, 29], None, "no_connect", "NC"),
        ([64], None, "no_connect", "RESERVED"),
        ([17], None, "bidirectional", "SRB1"),
        ([18], None, "bidirectional", "SRB2"),
    ]:
        for number in numbers:
            pins[str(number)] = (net, kind, function)
    for number, function in [
        (24, "VREFP"),
        (28, "VCAP1"),
        (30, "VCAP2"),
        (55, "VCAP3"),
        (26, "VCAP4"),
        (63, "BIASOUT"),
        (43, "DOUT"),
        (47, "DRDY"),
    ]:
        pins[str(number)] = ("MISO_DRV" if function == "DOUT" else function, "output", function)
    for number, function in [
        (34, "DIN"),
        (35, "PWDN"),
        (36, "RESET"),
        (37, "CLK"),
        (38, "START"),
        (39, "CS"),
        (40, "SCLK"),
        (52, "CLKSEL"),
        (61, "BIASINV"),
    ]:
        pins[str(number)] = ("MOSI" if function == "DIN" else function, "input", function)
    for number, function in [(42, "GPIO1"), (44, "GPIO2"), (45, "GPIO3"), (46, "GPIO4")]:
        pins[str(number)] = (function, "bidirectional", function)
    return pins


def _fixed_pins(profile: BoardProfile) -> dict[Pin, tuple[str | None, str, str]]:
    fixed = {("U1", pin): value for pin, value in _ads_pins().items()}
    for pin, net, kind, function in [
        ("1", "VIN_5V_AFE", "power_in", "IN"),
        ("2", "GND", "power_in", "GND"),
        ("3", "VIN_5V_AFE", "input", "EN"),
        ("4", None, "no_connect", "NC"),
        ("5", "DVDD", "power_out", "OUT"),
    ]:
        fixed["U2", pin] = net, kind, function
    for ref, header in profile["interface_headers"].items():
        for pin, net in header["pin_map"].items():
            fixed[ref, pin] = _alias(net), "passive", pin
    for signal in profile["spi"]["signals"]:
        pin = f"GPIO{signal['gpio']}"
        kind = "output" if signal["direction_from_mcu"] == "out" else "input"
        fixed["MOD1", pin] = signal["signal"], kind, pin
    fixed["MOD1", "5V"] = "VIN_5V_AFE", "power_in", "5V_input"
    fixed["MOD1", "GND"] = "GND", "power_in", "GND"
    for channel in range(1, 5):
        for leg in ("P", "N"):
            ref = f"D_IN{channel}{leg}"
            fixed[ref, "1"] = "GND", "passive", "A"
            fixed[ref, "2"] = "AVDD", "passive", "K"
            fixed[ref, "3"] = f"IN{channel}{leg}", "passive", "K1_A2"
    for ref, net in [("C_VCAP1", "VCAP1"), ("C_REF", "VREFP")]:
        fixed[ref, "1"] = net, "passive", ""
        fixed[ref, "2"] = "GND", "passive", ""
    return fixed


def _alias(net: str) -> str | None:
    return None if net == "NC" else "GND" if net in {"DGND", "AVSS"} else net


def _supply_caps() -> dict[str, str]:
    caps = {
        "C_VCAP1_HF": "VCAP1",
        "C_VCAP2": "VCAP2",
        "C_VCAP3": "VCAP3",
        "C_VCAP3_HF": "VCAP3",
        "C_VCAP4": "VCAP4",
        "C_REF_HF": "VREFP",
    }
    caps.update({f"C_AVDD_{pin}": "AVDD" for pin in [19, 21, 22, 56, 59]})
    caps.update({"C_AVDD1_54": "AVDD", "C_DVDD_48": "DVDD", "C_DVDD_50": "DVDD"})
    for suffix in ("A", "B"):
        caps[f"C_LDO_IN_{suffix}"] = "VIN_5V_AFE"
        caps[f"C_LDO_OUT_{suffix}"] = "DVDD"
    for supply in ("VIN", "AVDD", "AVDD1", "DVDD"):
        net = "VIN_5V_AFE" if supply == "VIN" else "AVDD" if supply == "AVDD1" else supply
        for suffix in ("BULK", "HF"):
            caps[f"C_{supply}_{suffix}"] = net
    return caps


def _passive_pairs() -> dict[str, tuple[str, str]]:
    pairs = {
        "R_AVDD_FEED": ("VIN_5V_AFE", "AVDD"),
        "R_MISO_SER": ("MISO_DRV", "MISO"),
        "R_BIAS_FB": ("BIASOUT", "BIASINV"),
        "C_BIAS_FB": ("BIASOUT", "BIASINV"),
        "R_BIAS_OUT": ("BIASOUT", "BIAS_AFTER_1M_DUMMY"),
    }
    for channel in range(1, 5):
        pairs[f"C_DIFF{channel}"] = f"IN{channel}P", f"IN{channel}N"
        for leg in ("P", "N"):
            pairs[f"R_IN{channel}{leg}"] = f"CH{channel}{leg}_DUMMY", f"IN{channel}{leg}"
    for signal in (
        "CS",
        "CLKSEL",
        "CLK",
        "RESET",
        "PWDN",
        "START",
        "SCLK",
        "DIN",
        "GPIO1",
        "GPIO2",
        "GPIO3",
        "GPIO4",
    ):
        pairs[f"R_{signal}_DN"] = "MOSI" if signal == "DIN" else signal, "GND"
    caps = _supply_caps()
    pairs.update({ref: (net, "GND") for ref, net in caps.items()})
    return pairs


def _anchors(
    netlist: SchematicNetlist, fixed: dict[Pin, tuple[str | None, str, str]], errors: list[str]
) -> dict[str, str]:
    mapped: dict[str, str] = {}
    sizes = Counter(netlist.nets.values())
    for pin, (expected, kind, function) in fixed.items():
        observed = netlist.nets.get(pin)
        if observed is None:
            errors.append(f"{pin}: missing pin")
            continue
        actual_type = netlist.pin_types.get(pin, "")
        if actual_type.split("+")[0] != kind or netlist.pin_functions.get(pin) != function:
            errors.append(f"{pin}: wrong symbol pin type/function")
        if expected is None:
            if "no_connect" not in actual_type or sizes[observed] != 1:
                errors.append(f"{pin}: must be an explicit isolated no-connect")
        elif "no_connect" in actual_type or mapped.setdefault(expected, observed) != observed:
            errors.append(f"{pin}: disconnected/wrong {expected} net")
    if len(set(mapped.values())) != len(mapped):
        errors.append("distinct functional nets shorted together")
    return mapped


def validate_schematic(
    netlist: SchematicNetlist, profile: BoardProfile, bom: BillOfMaterials
) -> list[str]:
    """Check complete package/pin and component contracts, not power-up voltages."""
    errors: list[str] = []
    if {row["id"] for row in bom["line_items"]} != set(FOOTPRINTS):
        return ["unsupported schematic BOM item set"]
    rows = {ref: row for row in bom["line_items"] for ref in row["references"]}
    if set(netlist.parts) != set(rows):
        errors.append("schematic component inventory differs from BOM")
    for ref in rows.keys() & netlist.parts.keys():
        errors.extend(f"{ref}: {error}" for error in _part_errors(netlist.parts[ref], rows[ref]))
    fixed, pairs = _fixed_pins(profile), _passive_pairs()
    expected_pins = set(fixed) | {(ref, pin) for ref in pairs for pin in ("1", "2")}
    if (
        set(netlist.nets) != expected_pins
        or set(netlist.pin_types) != expected_pins
        or set(netlist.pin_functions) != expected_pins
    ):
        errors.append("missing or extra package pin in netlist")
    mapped = _anchors(netlist, fixed, errors)
    _check_pairs(netlist, pairs, mapped, errors)
    return errors


def _check_pairs(
    netlist: SchematicNetlist,
    pairs: dict[str, tuple[str, str]],
    mapped: dict[str, str],
    errors: list[str],
) -> None:
    for ref, ends in pairs.items():
        actual = {netlist.nets.get((ref, pin)) for pin in ("1", "2")}
        expected = {mapped.get(net) for net in ends}
        if None in actual or None in expected or actual != expected:
            errors.append(f"{ref}: wrong passive net pair")
        if any(netlist.pin_types.get((ref, pin)) != "passive" for pin in ("1", "2")):
            errors.append(f"{ref}: nonpassive or no-connect terminal")
