"""Cross-export evidence: frozen native CSV, not a BOM synthesized by its checker."""

import csv
import gzip
import io
from dataclasses import replace
from pathlib import Path

import pytest

from hardware.rev_a import (
    load_documents,
    parse_schematic_xml,
    validate_schematic,
    validate_schematic_bom,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"
BOM_CSV = (FIXTURES / "rev_a_bom.csv").read_text()
NETLIST = parse_schematic_xml(
    gzip.decompress((FIXTURES / "rev_a_netlist.xml.gz").read_bytes()).decode()
)


def _write(rows: list[list[str]]) -> str:
    output = io.StringIO(newline="")
    csv.writer(output).writerows(rows)
    return output.getvalue()


def test_native_bom_fixture_matches_validated_xml_and_json() -> None:
    profile, bom, _ = load_documents()
    assert validate_schematic(NETLIST, profile, bom) == []
    rows = list(csv.DictReader(io.StringIO(BOM_CSV)))
    assert len(rows) == 70
    assert sum(row["DNP"] == "DNP" for row in rows) == 8
    assert [row["Reference"] for row in rows if row["OffBoard"]] == ["MOD1"]
    validate_schematic_bom(BOM_CSV, NETLIST)


@pytest.mark.parametrize("column", range(8))
def test_every_csv_field_is_compared_with_the_xml(column: int) -> None:
    rows = list(csv.reader(io.StringIO(BOM_CSV)))
    rows[1][column] = "CORRUPTED"
    with pytest.raises(ValueError, match="BOM CSV"):
        validate_schematic_bom(_write(rows), NETLIST)


@pytest.mark.parametrize("row_index", range(1, len(list(csv.reader(io.StringIO(BOM_CSV))))))
def test_every_component_including_dnp_and_offboard_must_be_present(row_index: int) -> None:
    rows = list(csv.reader(io.StringIO(BOM_CSV)))
    del rows[row_index]
    with pytest.raises(ValueError, match="incomplete"):
        validate_schematic_bom(_write(rows), NETLIST)


@pytest.mark.parametrize(
    "fault",
    [
        "duplicate-row",
        "duplicate-native-reference",
        "grouped-references",
        "header-only",
        "missing-column",
        "extra-column",
        "duplicate-column",
        "missing-cell",
        "extra-cell",
        "unknown-reference",
        "dnp-not-marked",
        "offboard-not-marked",
        "fitted-marked-dnp",
        "onboard-marked-offboard",
    ],
)
def test_malformed_or_mismatched_native_csv_fails(fault: str) -> None:
    rows = list(csv.reader(io.StringIO(BOM_CSV)))
    if fault == "duplicate-row":
        rows.append(rows[1])
    elif fault == "duplicate-native-reference":
        rows[2][0] = rows[1][0]
    elif fault == "grouped-references":
        rows[1][0] = "C1,C2"
        del rows[2]
    elif fault == "header-only":
        rows = rows[:1]
    elif fault == "missing-column":
        rows[0].pop()
    elif fault == "extra-column":
        rows[0].append("UNEXPECTED")
    elif fault == "duplicate-column":
        rows[0][-1] = rows[0][-2]
    elif fault == "missing-cell":
        rows[1].pop()
    elif fault == "extra-cell":
        rows[1].append("EXTRA")
    elif fault == "unknown-reference":
        rows[1][1] = "R_INVENTED"
    else:
        _change_flag(rows, fault)
    with pytest.raises(ValueError, match="BOM CSV"):
        validate_schematic_bom(_write(rows), NETLIST)


def _change_flag(rows: list[list[str]], fault: str) -> None:
    if fault == "dnp-not-marked":
        next(row for row in rows if row[0] == "D1")[6] = ""
    elif fault == "offboard-not-marked":
        next(row for row in rows if row[0] == "MOD1")[7] = ""
    elif fault == "fitted-marked-dnp":
        rows[1][6] = "DNP"
    else:
        rows[1][7] = "Excluded from board"


@pytest.mark.parametrize(
    "content", ["", "junk", '"unterminated', BOM_CSV + '"unterminated', "x" * 2_000_001]
)
def test_csv_syntax_size_and_empty_output_rejected(content: str) -> None:
    with pytest.raises(ValueError, match="BOM CSV"):
        validate_schematic_bom(content, NETLIST)


def test_empty_expected_xml_is_not_vacuously_valid() -> None:
    with pytest.raises(ValueError, match="empty"):
        validate_schematic_bom(BOM_CSV.splitlines()[0], replace(NETLIST, parts={}))


def test_row_column_order_and_csv_quoting_are_not_electrical_meaning() -> None:
    rows = list(csv.reader(io.StringIO(BOM_CSV)))
    reordered = [list(reversed(row)) for row in [rows[0], *reversed(rows[1:])]]
    validate_schematic_bom("\n" + _write(reordered) + "\n", NETLIST)
