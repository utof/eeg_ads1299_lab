"""One-shot native PCB import from the checked schematic, not a layout generator.

The output is a parking grid with no outline, tracks or planes. Library pad and
courtyard geometry is preserved. Edit the resulting native PCB for placement;
never regenerate over that work. Native DRC/parity remains an independent check.
"""

import json
import xml.etree.ElementTree as ET
from uuid import UUID, uuid5

from .check_baseline import BillOfMaterials, BoardProfile
from .check_schematic import (
    SchematicNetlist,
    SchematicPart,
    parse_schematic_xml,
    validate_schematic,
)
from .footprint_geometry import validate_footprint
from .schematic_symbols import _children, _Form, _name, _parse

_HEADER = """(kicad_pcb (version 20241229) (generator "eeg-pcb-import")
(general (thickness 1.6)) (paper "A3")
(title_block (title "UNROUTED IMPORT - NOT FOR FABRICATION")
(comment 1 "Parking grid only; stackup, outline and placement are not selected"))
(layers (0 "F.Cu" signal) (31 "B.Cu" signal)
(32 "B.Adhes" user "B.Adhesive") (33 "F.Adhes" user "F.Adhesive")
(34 "B.Paste" user) (35 "F.Paste" user)
(36 "B.SilkS" user "B.Silkscreen") (37 "F.SilkS" user "F.Silkscreen")
(38 "B.Mask" user) (39 "F.Mask" user)
(40 "Dwgs.User" user "User.Drawings") (41 "Cmts.User" user "User.Comments")
(44 "Edge.Cuts" user) (46 "B.CrtYd" user "B.Courtyard")
(47 "F.CrtYd" user "F.Courtyard") (48 "B.Fab" user) (49 "F.Fab" user))
(setup (pad_to_mask_clearance 0))
(net 0 "")
"""
_FIELDS = ("ContractRef", "MPN", "BOM_ID", "Population", "Tolerance")


def _form(*items: str | _Form) -> _Form:
    return _Form(items)


def _render(item: str | _Form) -> str:
    return item if isinstance(item, str) else "(" + " ".join(map(_render, item.items)) + ")"


def _property(name: str, value: str) -> _Form:
    return _form(
        "property",
        json.dumps(name),
        json.dumps(value),
        _form("at", "0", "0", "0"),
        _form("layer", '"F.Fab"'),
        _form("hide", "yes"),
        _form("effects", _form("font", _form("size", "1", "1"), _form("thickness", "0.15"))),
    )


def _symbol_path(component: ET.Element, root_id: str) -> str:
    sheet = component.find("sheetpath")
    stamp = component.findtext("tstamps", "")
    if sheet is None or not stamp:
        raise ValueError("PCB import requires the native symbol and sheet UUID path")
    UUID(stamp)
    path = sheet.get("tstamps", "")
    if not path.startswith("/") or not path.endswith("/"):
        raise ValueError("invalid native sheet UUID path")
    for element in path.strip("/").split("/"):
        if element:
            UUID(element)
    return "/" + root_id + path + stamp


def _pad(
    item: _Form, ref: str, graph: SchematicNetlist, names: dict[str, str], namespace: UUID
) -> _Form:
    pin = (ref, _name(item))
    code = graph.nets[pin]
    return _form(
        *item.items,
        _form("net", code, json.dumps(names[code])),
        _form("pinfunction", json.dumps(graph.pin_functions[pin])),
        _form("pintype", json.dumps(graph.pin_types[pin])),
        _form("uuid", json.dumps(str(uuid5(namespace, f"pad:{ref}:{pin[1]}")))),
    )


def _display_property(child: _Form, required: dict[str, str]) -> _Form:
    name = _name(child)
    if name not in required:
        raise ValueError("duplicate footprint display property")
    return _form(*child.items[:2], json.dumps(required.pop(name)), *child.items[3:])


def _instance_body(
    source: _Form,
    ref: str,
    part: SchematicPart,
    graph: SchematicNetlist,
    names: dict[str, str],
    namespace: UUID,
) -> list[_Form]:
    result: list[_Form] = []
    required = {"Reference": part.native_ref, "Value": part.value}
    for child in source.items[2:]:
        if not isinstance(child, _Form):
            raise ValueError("invalid footprint body")
        head = child.items[0]
        if head in {"version", "generator"}:
            continue  # Library header fields do not belong in a board instance.
        if head == "property" and _name(child) in {"Reference", "Value"}:
            child = _display_property(child, required)
        elif head == "pad":
            child = _pad(child, ref, graph, names, namespace)
        elif head == "attr" and "dnp" in part.properties:
            child = _form(*child.items, "dnp")
        result.append(child)
    if required:
        raise ValueError("missing footprint reference/value properties")
    result.extend(_property(key, part.properties[key]) for key in _FIELDS if key in part.properties)
    return result


def make_pcb_seed(
    netlist_xml: str,
    schematic: str,
    footprint_sources: dict[str, str],
    profile: BoardProfile,
    bom: BillOfMaterials,
) -> str:
    """Return editable native board text; do not overwrite, place, route or approve.

    Only source-derived nets, UUID paths, properties and native DNP/board flags
    are imported. No physical GPIO numbers or alternative BOM are invented.
    The two-layer/1.6-mm file defaults are not a selected production stackup.
    """
    graph = parse_schematic_xml(netlist_xml)
    errors = validate_schematic(graph, profile, bom)
    if errors:
        raise ValueError("PCB import requires a valid schematic: " + "; ".join(errors))
    selected = {part.footprint for part in graph.parts.values()} - {""}
    if set(footprint_sources) != selected:
        raise ValueError("PCB import needs exactly the selected footprint sources")
    sources = {}
    for name, content in footprint_sources.items():
        validate_footprint(name, content)
        sources[name] = _parse(content)
    root = _parse(schematic)
    ids = _children(root, "uuid")
    if root.items[0] != "kicad_sch" or len(ids) != 1:
        raise ValueError("PCB import requires a native root schematic UUID")
    root_id = _name(ids[0])
    namespace = UUID(root_id)
    xml = ET.fromstring(netlist_xml)  # Already bounded and DTD-rejected by the graph parser.
    names = {net.attrib["code"]: net.attrib["name"] for net in xml.findall("nets/net")}
    if any(
        not code.isascii() or not code.isdecimal() or int(code) <= 0 or str(int(code)) != code
        for code in names
    ):
        raise ValueError("PCB net codes must be positive decimal integers")
    components = {comp.attrib["ref"]: comp for comp in xml.findall("components/comp")}
    lines = [_HEADER]
    lines.extend(_render(_form("net", code, json.dumps(name))) for code, name in names.items())
    on_board = [
        (ref, part)
        for ref, part in graph.parts.items()
        if "exclude_from_board" not in part.properties
    ]
    for index, (ref, part) in enumerate(sorted(on_board, key=lambda pair: pair[1].native_ref)):
        path = _symbol_path(components[part.native_ref], root_id)
        instance = _form(
            "footprint",
            json.dumps(part.footprint),
            _form("at", str(20 + index % 10 * 18), str(25 + index // 10 * 32)),
            _form("uuid", json.dumps(str(uuid5(namespace, "footprint:" + ref)))),
            _form("path", json.dumps(path)),
            _form("sheetname", json.dumps(part.properties["Sheetname"])),
            _form("sheetfile", json.dumps(part.properties["Sheetfile"])),
            *_instance_body(sources[part.footprint], ref, part, graph, names, namespace),
        )
        lines.append(_render(instance))
    return "\n".join(lines) + "\n)\n"
