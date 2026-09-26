"""Software-only structural fixtures; native KiCad acceptance is tested separately."""

import shutil
from pathlib import Path

import pytest

from hardware.rev_a import schematic_source_snapshot

CAD = Path(__file__).resolve().parents[1] / "hardware/rev_a/kicad"
BODY = '(property "Value" "R") (symbol "R_1_1" (pin passive line (number "1")))'
LOCAL = f'(symbol "R" {BODY})'
EMBEDDED = f'(symbol "RevA:R" {BODY})'
INSTANCE = '(symbol (lib_id "RevA:R"))'


def _sheet(cache: str = EMBEDDED, instance: str = INSTANCE) -> str:
    return f"(kicad_sch (lib_symbols {cache}) {instance})"


def _candidate(tmp_path: Path, library: str, sheet: str) -> Path:
    target = tmp_path / "cad"
    shutil.copytree(CAD, target)
    (target / "RevA.kicad_sym").write_text(library)
    for name in ("power.kicad_sch", "digital.kicad_sch"):
        (target / name).write_text(_sheet())
    # Keep the real root's two declared dependencies, but no CAD semantics are
    # claimed for these minimal token-tree fixtures.
    root = sheet.rsplit(")", 1)
    (target / "rev_a.kicad_sch").write_text(
        root[0]
        + ' (property "Sheetfile" "power.kicad_sch")'
        + ' (property "Sheetfile" "digital.kicad_sch"))'
        + root[1]
    )
    return target


@pytest.mark.parametrize(
    "library",
    [
        "(kicad_symbol_lib)",
        f"(kicad_symbol_lib {LOCAL} {LOCAL})",
        f'(kicad_symbol_lib (symbol "Other" {BODY}))',
        f'(kicad_symbol_lib (symbol "" {BODY}))',
        f"(kicad_symbol_lib (symbol R {BODY}))",
        f"(kicad_symbol_lib (symbol (nested) {BODY}))",
        "(kicad_symbol_lib (symbol))",
        f'(kicad_symbol_lib (symbol "R" (extends "Parent") {BODY}))',
        f"(wrong_root {LOCAL})",
        f"(kicad_symbol_lib {LOCAL}) (extra)",
        f"(kicad_symbol_lib {LOCAL}))",
        f"(kicad_symbol_lib {LOCAL}",
        '(kicad_symbol_lib (symbol "unterminated))',
        '(kicad_symbol_lib "unterminated',
        "plain_atom",
        "()",
        "(" * 65 + "deep" + ")" * 65,
    ],
)
def test_library_structure_and_identity_fail_closed(tmp_path: Path, library: str) -> None:
    target = _candidate(tmp_path, library, _sheet())
    with pytest.raises(ValueError, match="symbol"):
        schematic_source_snapshot(target)


@pytest.mark.parametrize(
    "sheet",
    [
        _sheet().replace("kicad_sch", "wrong_root", 1),
        f"(kicad_sch {INSTANCE})",
        f"(kicad_sch (lib_symbols {EMBEDDED}) (lib_symbols {EMBEDDED}) {INSTANCE})",
        _sheet(cache=""),
        _sheet(cache=EMBEDDED + EMBEDDED),
        _sheet(cache=LOCAL),
        _sheet(cache=EMBEDDED.replace('"RevA:R"', '"RevA:"', 1)),
        _sheet(instance=INSTANCE + "(symbol)"),
        _sheet(instance='(symbol (lib_id "RevA:R") (lib_id "RevA:R"))'),
        _sheet(instance='(symbol (lib_id "RevA:R" "extra"))'),
        _sheet(cache=EMBEDDED.replace('"Value" "R"', '"Value" "Wrong"')),
        _sheet(cache=EMBEDDED + '(symbol "RevA:Unused" (property "Value" "extra"))'),
        _sheet(instance=INSTANCE + '(symbol (lib_id "RevA:Missing"))'),
    ],
)
def test_cache_structure_and_placed_inventory_fail_closed(tmp_path: Path, sheet: str) -> None:
    target = _candidate(tmp_path, f"(kicad_symbol_lib {LOCAL})", sheet)
    with pytest.raises(ValueError, match="symbol"):
        schematic_source_snapshot(target)


def test_symbol_comparison_is_not_a_fixed_hash_allowlist(tmp_path: Path) -> None:
    target = _candidate(tmp_path, f"(kicad_symbol_lib {LOCAL})", _sheet())
    before = schematic_source_snapshot(target)
    # Parentheses, spaces and escaped quotes inside a quoted property are data,
    # not new expressions. A synchronized edit must not be rejected as drift.
    for path in target.iterdir():
        if path.suffix in {".kicad_sym", ".kicad_sch"}:
            path.write_text(
                path.read_text().replace('"Value" "R"', r'"Value" "R (reviewed) \"label\""')
            )
    after = schematic_source_snapshot(target)
    assert len(after) == 7 and after != before


def test_definition_order_and_external_whitespace_are_immaterial(tmp_path: Path) -> None:
    second = '(symbol "Second" (property "Value" "second"))'
    library = f"(kicad_symbol_lib {second} {LOCAL})"
    sheet = _sheet(
        cache=EMBEDDED + second.replace('"Second"', '"RevA:Second"', 1),
        instance=INSTANCE + '(symbol (lib_id "RevA:Second"))',
    )
    target = _candidate(tmp_path, library, sheet)
    before = schematic_source_snapshot(target)
    path = target / "RevA.kicad_sym"
    path.write_text(f"(kicad_symbol_lib\n\t{LOCAL}\n {second})\n")
    after = schematic_source_snapshot(target)
    assert after["RevA.kicad_sym"] != before["RevA.kicad_sym"]
    assert len(after) == 7
