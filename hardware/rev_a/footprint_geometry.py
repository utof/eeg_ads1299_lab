"""Closed pad-layout regression check for the nine inspected library footprints.

Numbers/pitch/orientation are compared with package drawings; exact land sizes
below are seven inspected KiCad choices plus two local T491 nominal reflow
patterns, NOT assembly approval. Several
land patterns differ from manufacturer examples: see REV_A_FOOTPRINT_REVIEW.md.
This reads no PCB, validates no assembly process, and only checks courtyard graphics for the two local T491 patterns.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass

from .check_schematic import FOOTPRINTS
from .schematic_symbols import _children, _Form, _parse


@dataclass(frozen=True)
class FootprintPad:
    number: str
    x_mm: float
    y_mm: float
    width_mm: float
    height_mm: float
    technology: str = "smd"
    shape: str = "roundrect"
    drill_mm: float | None = None
    radius_ratio: float | None = 0.25


_NONPOLAR = {FOOTPRINTS[key] for key in ("input_r", "input_c", "bulk_10u")}


def _two_pads(
    x: float, width: float, height: float, radius: float | None = 0.25
) -> list[FootprintPad]:
    return [
        FootprintPad(
            str(n),
            sign * x,
            0,
            width,
            height,
            shape="rect" if radius is None else "roundrect",
            radius_ratio=radius,
        )
        for n, sign in ((1, -1), (2, 1))
    ]


def _expected(footprint: str) -> list[FootprintPad]:
    # Reuse the existing package identity registry; do not add a second BOM.
    pairs = {
        FOOTPRINTS["input_r"]: (0.825, 0.8, 0.95, 0.25),
        FOOTPRINTS["input_c"]: (0.775, 0.9, 0.95, 0.25),
        FOOTPRINTS["bulk_10u"]: (0.95, 1.0, 1.45, 0.25),
        FOOTPRINTS["vref"]: (1.46, 1.80, 2.23, None),
        FOOTPRINTS["vcap1"]: (3.12, 2.37, 2.43, None),
    }
    if footprint in pairs:
        return _two_pads(*pairs[footprint])
    if footprint == FOOTPRINTS["afe"]:
        return _qfp()
    if footprint == FOOTPRINTS["headers"]:
        return [
            FootprintPad(
                str(n),
                ((n - 1) % 2) * 2.54,
                ((n - 1) // 2) * 2.54,
                1.7,
                1.7,
                "thru_hole",
                "rect" if n == 1 else "circle",
                1.0,
                None,
            )
            for n in range(1, 21)
        ]
    if footprint == FOOTPRINTS["clamps"]:
        coords = [(-0.9375, -0.95), (-0.9375, 0.95), (0.9375, 0)]
        width = 1.475
    elif footprint == FOOTPRINTS["dvdd_ldo"]:
        coords = [(-1.1375, -0.95), (-1.1375, 0), (-1.1375, 0.95), (1.1375, 0.95), (1.1375, -0.95)]
        width = 1.325
    else:
        raise ValueError("footprint is outside the inspected nine-package set")
    return [FootprintPad(str(n), x, y, width, 0.6) for n, (x, y) in enumerate(coords, 1)]


def _qfp() -> list[FootprintPad]:
    pads = []
    for offset in range(16):
        along = -3.75 + 0.5 * offset
        for start, x, y, w, h in (
            (1, -5.6625, along, 1.475, 0.3),
            (17, along, 5.6625, 0.3, 1.475),
            (33, 5.6625, -along, 1.475, 0.3),
            (49, -along, -5.6625, 0.3, 1.475),
        ):
            pads.append(FootprintPad(str(start + offset), x, y, w, h))
    return pads


def _atoms(form: _Form) -> list[str]:
    values = []
    for token in form.items[1:]:
        if not isinstance(token, str):
            raise ValueError("footprint field contains an unexpected nested expression")
        decoded: object = json.loads(token) if token.startswith('"') else token
        if not isinstance(decoded, str):
            raise ValueError("footprint field must contain strings")
        values.append(decoded)
    return values


def _one(root: _Form, name: str) -> list[str]:
    fields = _children(root, name)
    if len(fields) != 1:
        raise ValueError(f"footprint requires exactly one {name} field")
    return _atoms(fields[0])


def _numbers(values: list[str], count: int) -> tuple[float, ...]:
    if len(values) != count:
        raise ValueError("footprint numeric field has wrong length")
    try:
        numbers = tuple(float(value) for value in values)
    except ValueError as exc:
        raise ValueError("footprint numeric field is malformed") from exc
    if not all(math.isfinite(value) for value in numbers):
        raise ValueError("footprint numeric field is nonfinite")
    return numbers


def _pad_fields(form: _Form, technology: str, shape: str) -> None:
    expected_fields = {"at", "size", "layers"}
    if technology == "thru_hole":
        expected_fields |= {"drill", "remove_unused_layers"}
    elif technology == "smd" and shape == "roundrect":
        expected_fields.add("roundrect_rratio")
    elif technology != "smd" or shape != "rect":
        raise ValueError("footprint pad technology/shape is unsupported")
    fields = form.items[4:]
    if (
        len(fields) != len(expected_fields)
        or {item.items[0] for item in fields if isinstance(item, _Form)} != expected_fields
    ):
        raise ValueError("footprint pad has missing, duplicate or unsupported fields")


def _pad(form: _Form) -> FootprintPad:
    if len(form.items) < 4 or any(not isinstance(item, str) for item in form.items[:4]):
        raise ValueError("footprint pad declaration is malformed")
    number, technology, shape = _atoms(_Form(form.items[:4]))
    _pad_fields(form, technology, shape)
    position = _one(form, "at")
    if len(position) == 2:
        position.append("0")
    x, y, angle = _numbers(position, 3)
    width, height = _numbers(_one(form, "size"), 2)
    if width <= 0 or height <= 0 or angle % 90 != 0:
        raise ValueError("footprint requires positive lands and quarter-turn pad angles")
    if int(angle / 90) % 2:
        width, height = height, width
    layers = _one(form, "layers")
    wanted_layers = (
        {"*.Cu", "*.Mask"} if technology == "thru_hole" else {"F.Cu", "F.Mask", "F.Paste"}
    )
    if set(layers) != wanted_layers or len(layers) != len(wanted_layers):
        raise ValueError("footprint pad copper/mask/paste layers differ")
    drill, radius = None, None
    if technology == "thru_hole":
        (drill,) = _numbers(_one(form, "drill"), 1)
        if _one(form, "remove_unused_layers") != ["no"]:
            raise ValueError("footprint through-hole copper removal is unsupported")
    elif shape == "roundrect":
        (radius,) = _numbers(_one(form, "roundrect_rratio"), 1)
    return FootprintPad(number, x, y, width, height, technology, shape, drill, radius)


def _same(actual: FootprintPad, expected: FootprintPad, nonpolar: bool) -> bool:
    if (
        (not nonpolar and actual.number != expected.number)
        or actual.technology != expected.technology
        or actual.shape != expected.shape
    ):
        return False
    pairs = (
        (actual.x_mm, expected.x_mm),
        (actual.y_mm, expected.y_mm),
        (actual.width_mm, expected.width_mm),
        (actual.height_mm, expected.height_mm),
        (actual.drill_mm, expected.drill_mm),
        (actual.radius_ratio, expected.radius_ratio),
    )
    # Representation tolerance (one nanometre), NOT a fabrication allowance.
    return all(
        a is b if a is None or b is None else math.isclose(a, b, rel_tol=0, abs_tol=1e-6)
        for a, b in pairs
    )


def _root(footprint: str, content: str) -> _Form:
    try:
        root = _parse(content)  # Reuse the existing bounded, read-only token reader.
    except ValueError as exc:
        raise ValueError(f"footprint structure: {exc}") from exc
    if root.items[0] != "footprint" or _atoms(_Form(root.items[:2])) != [footprint.split(":")[1]]:
        raise ValueError("footprint root/name differs from its selected library identity")
    if _one(root, "layer") != ["F.Cu"] or _one(root, "attr") != [
        "through_hole" if footprint == FOOTPRINTS["headers"] else "smd"
    ]:
        raise ValueError("footprint side or mounting technology differs")
    _root_fields(root)
    _t491_courtyard(footprint, root)
    return root


def _root_fields(root: _Form) -> None:
    for child in root.items[2:]:
        if not isinstance(child, _Form):
            raise ValueError("footprint root contains unsupported tokens")
        if child.items[0] not in {
            "version",
            "generator",
            "layer",
            "descr",
            "tags",
            "property",
            "attr",
            "fp_line",
            "fp_rect",
            "fp_poly",
            "fp_text",
            "pad",
            "model",
            "embedded_fonts",
        }:
            raise ValueError("footprint has an unsupported root geometry/override")
        if child.items[0] in {"fp_line", "fp_rect", "fp_poly", "fp_text", "property"} and any(
            "Cu" in layer for layer in _one(child, "layer")
        ):
            raise ValueError("footprint contains non-pad copper graphics")


def _t491_courtyard(footprint: str, root: _Form) -> None:
    """Closed local rectangular courtyard, independent of land dimensions.

    V1/V2 are full envelope dimensions from KEMET Table 2, density B.
    Other library graphics remain outside this geometry contract.
    """
    dimensions = {FOOTPRINTS["vref"]: (5.22, 3.50), FOOTPRINTS["vcap1"]: (9.12, 5.10)}
    if footprint not in dimensions:
        return
    outlines = [
        child
        for child in root.items[2:]
        if isinstance(child, _Form)
        and _children(child, "layer")
        and _one(child, "layer") == ["F.CrtYd"]
    ]
    if len(outlines) != 1 or outlines[0].items[0] != "fp_rect":
        raise ValueError("footprint requires one closed rectangular T491 courtyard")
    rectangle = outlines[0]
    width, height = dimensions[footprint]
    start = _numbers(_one(rectangle, "start"), 2)
    end = _numbers(_one(rectangle, "end"), 2)
    wanted = (-width / 2, -height / 2, width / 2, height / 2)
    if any(
        not math.isclose(a, b, rel_tol=0, abs_tol=1e-6)
        for a, b in zip((*start, *end), wanted, strict=True)
    ):
        raise ValueError("footprint T491 courtyard dimensions differ from nominal reflow")
    if _one(rectangle, "fill") != ["none"]:
        raise ValueError("footprint courtyard must be an unfilled outline")


def validate_footprint(footprint: str, content: str) -> tuple[FootprintPad, ...]:
    """Reject drift in inspected pad geometry; return data, never release approval.

    The footprint's local front-view frame is fixed. Nonpolar two-terminal pad
    swaps, definition order, equivalent numeric spelling and rectangle quarter
    turns are harmless. Whole-footprint rotation/mirroring requires re-review.
    Graphics, 3D models, mask/stencil process and PCB placement are NOT checked.
    """
    expected = _expected(footprint)
    root = _root(footprint, content)
    actual = [_pad(form) for form in _children(root, "pad")]
    if len(actual) != len(expected) or {p.number for p in actual} != {p.number for p in expected}:
        raise ValueError("footprint pad numbers/count differ (including duplicates)")
    nonpolar = footprint in _NONPOLAR
    unmatched = list(expected)
    for pad in actual:
        # Inspected lands are far apart relative to representation tolerance.
        # Each must match exactly once; two near-coincident nonpolar pads must
        # not both consume the same expected land and leave the other absent.
        matches = [i for i, other in enumerate(unmatched) if _same(pad, other, nonpolar)]
        if len(matches) != 1:
            raise ValueError(f"footprint {footprint} pad {pad.number}: inspected geometry differs")
        unmatched.pop(matches[0])
    return tuple(sorted(actual, key=lambda pad: int(pad.number)))
