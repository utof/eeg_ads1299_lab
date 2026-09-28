"""The deliberately closed three-sheet KiCad input boundary, without a CAD framework."""

import hashlib
import json
import os
import re
import stat
from pathlib import Path

from .check_schematic import FOOTPRINTS
from .footprint_geometry import validate_footprint
from .schematic_symbols import validate_symbol_caches

CAD_FILES = frozenset(
    {
        "rev_a.kicad_sch",
        "power.kicad_sch",
        "digital.kicad_sch",
        "RevA.kicad_sym",
        "rev_a.kicad_pro",
        "sym-lib-table",
        "fp-lib-table",
    }
)
SHEET_FILES = frozenset({"rev_a.kicad_sch", "power.kicad_sch", "digital.kicad_sch"})
FOOTPRINT_LIBRARIES = frozenset(
    {
        "Package_QFP",
        "Package_TO_SOT_SMD",
        "Resistor_SMD",
        "Capacitor_SMD",
        "RevA_Passives",
        "Connector_PinHeader_2.54mm",
    }
)


def read_schematic_file(path: Path) -> str:
    """Bounded regular-file read; reject links/FIFOs before consuming any data."""
    if path.is_symlink():
        raise ValueError(f"symbolic link is not a declared CAD input: {path}")
    flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
    with os.fdopen(os.open(path, flags), "rb") as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("CAD input must be a regular file")
        content = stream.read(2_000_001)
        after = os.fstat(stream.fileno())
    if len(content) > 2_000_000 or (before.st_size, before.st_mtime_ns) != (
        after.st_size,
        after.st_mtime_ns,
    ):
        raise ValueError("CAD input oversized or changed during read")
    return content.decode("utf-8")


def _object(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{label}: expected object")
    result: dict[str, object] = {}
    items: dict[object, object] = value
    for key, item in items.items():
        if not isinstance(key, str):
            raise ValueError(f"{label}: non-string key")
        result[key] = item
    return result


def _strings(pattern: str, content: str) -> list[str]:
    # Only inspect named filename/library tokens; KiCad remains the format parser.
    result: list[str] = []
    for value in re.findall(pattern + r'\s+("(?:[^"\\]|\\.)*")', content):
        decoded: object = json.loads(value)
        if not isinstance(decoded, str):
            raise ValueError("CAD filename must be a string")
        result.append(decoded)
    return result


def _footprint_uri(name: str) -> str:
    variable = "KIPRJMOD" if name == "RevA_Passives" else "KICAD9_FOOTPRINT_DIR"
    return f"${{{variable}}}/{name}.pretty"


def _dependencies(contents: dict[str, str]) -> None:
    declared = _strings(r'\(property\s+"Sheetfile"', contents["rev_a.kicad_sch"])
    if sorted(declared) != ["digital.kicad_sch", "power.kicad_sch"]:
        raise ValueError("root must declare exactly the two snapshotted child sheets")
    for name in ("power.kicad_sch", "digital.kicad_sch"):
        if _strings(r'\(property\s+"Sheetfile"', contents[name]):
            raise ValueError("undeclared nested sheet dependency")
    for name in SHEET_FILES:
        ids = _strings(r"\(lib_id", contents[name])
        if not ids or any(not value.startswith("RevA:") for value in ids):
            raise ValueError("sheet uses an unsnapshotted symbol library")
    symbols = contents["sym-lib-table"]
    if _strings(r"\(name", symbols) != ["RevA"] or _strings(r"\(uri", symbols) != [
        "${KIPRJMOD}/RevA.kicad_sym"
    ]:
        raise ValueError("symbol table must resolve only the snapshotted local library")
    footprints = contents["fp-lib-table"]
    names = _strings(r"\(name", footprints)
    uris = _strings(r"\(uri", footprints)
    expected = {_footprint_uri(name) for name in FOOTPRINT_LIBRARIES}
    if (
        set(names) != FOOTPRINT_LIBRARIES
        or len(names) != len(expected)
        or set(uris) != expected
        or len(uris) != len(expected)
    ):
        raise ValueError("unexpected footprint library dependency")
    if any(uri != _footprint_uri(name) for name, uri in zip(names, uris, strict=True)):
        raise ValueError("footprint library name is paired with the wrong URI")


def schematic_source_snapshot(
    directory: Path, footprint_root: Path | None = None
) -> dict[str, str]:
    """Hash the complete declared native source set; reject hidden file dependencies.

    This is a project-specific closed inventory, not a general S-expression parser.
    Expanding the hierarchy/library set requires an explicit reviewed code change.
    """
    if directory.is_symlink():
        raise ValueError("CAD directory must not be a symbolic link")
    actual = {
        p.name
        for p in directory.iterdir()
        if p.suffix.startswith(".kicad_") or p.name.endswith("-lib-table")
    }
    if actual != CAD_FILES:
        raise ValueError("missing or extra native CAD source files")
    contents = {name: read_schematic_file(directory / name) for name in sorted(CAD_FILES)}
    _dependencies(contents)
    validate_symbol_caches(
        contents["RevA.kicad_sym"], {name: contents[name] for name in sorted(SHEET_FILES)}
    )
    project = _object(json.loads(contents["rev_a.kicad_pro"]), "project")
    erc = _object(project.get("erc"), "erc configuration")
    if erc != {"erc_exclusions": [], "rule_severities": {}}:
        raise ValueError("ERC exclusions/severity overrides are not permitted in this candidate")
    result = {name: hashlib.sha256(text.encode()).hexdigest() for name, text in contents.items()}
    result.update(_local_footprints(directory))
    if footprint_root is not None:
        result.update(_footprints(footprint_root))
    return result


def _local_footprints(cad: Path) -> dict[str, str]:
    library = cad / "RevA_Passives.pretty"
    expected = {
        name.split(":")[1] + ".kicad_mod"
        for name in FOOTPRINTS.values()
        if name.startswith("RevA_Passives:")
    }
    if library.is_symlink() or not library.is_dir():
        raise ValueError("local footprint library must be a real directory")
    if {path.name for path in library.iterdir()} != expected:
        raise ValueError("local footprint inventory is incomplete or contains extras")
    result = {}
    for name in sorted(expected):
        content = read_schematic_file(library / name)
        validate_footprint("RevA_Passives:" + name.removesuffix(".kicad_mod"), content)
        result["footprints/RevA_Passives.pretty/" + name] = hashlib.sha256(
            content.encode()
        ).hexdigest()
    return result


def _footprints(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for footprint in sorted(set(FOOTPRINTS.values()) - {""}):
        if footprint.startswith("RevA_Passives:"):
            continue
        library, name = footprint.split(":")
        relative = Path(library + ".pretty") / (name + ".kicad_mod")
        if root.is_symlink() or (root / relative.parent).is_symlink():
            raise ValueError("footprint library directory must not be a link")
        text = read_schematic_file(root / relative)
        validate_footprint(footprint, text)
        result["footprints/" + relative.as_posix()] = hashlib.sha256(text.encode()).hexdigest()
    return result


def validate_erc(content: str) -> None:
    """Require the complete, clean three-sheet native ERC report, including warnings."""
    report = _object(json.loads(content), "ERC report")
    if report.get("kicad_version") != "9.0.2" or report.get("source") != "rev_a.kicad_sch":
        raise ValueError("ERC source/version differs from the pinned candidate")
    sheets = report.get("sheets")
    if not isinstance(sheets, list):
        raise ValueError("ERC sheets must be an array")
    rows: list[object] = sheets
    paths = []
    for row in rows:
        sheet = _object(row, "ERC sheet")
        path = sheet.get("path")
        if not isinstance(path, str) or sheet.get("violations") != []:
            raise ValueError("malformed ERC sheet or nonempty violations (including excluded)")
        paths.append(path)
    if sorted(paths) != ["/", "/DIGITAL/", "/POWER/"]:
        raise ValueError("ERC did not cover exactly the three declared sheets")
