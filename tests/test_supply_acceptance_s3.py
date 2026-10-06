"""Conditional voltage windows must not erase unknown loss or ground terms."""

import itertools
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from lab.validation import read_object
from tools import dc_budget

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/REV_A_SUPPLY_ACCEPTANCE_S3.md"
MODEL = ROOT / "docs/studies/s3_acceptance.json"


def test_signed_interval_corners_and_subdivision() -> None:
    # V=source-loss+ground; independently enumerate every endpoint combination.
    terms = {"loss": (-0.15, -0.05), "ground": (-0.02, 0.03)}
    corners = [sum(c) for c in itertools.product((4.95, 5.05), *terms.values())]
    expected = (min(corners), max(corners))
    assert dc_budget.voltage_bounds((4.95, 5.05), terms) == pytest.approx(expected)
    split = {"a": (-0.10, -0.04), "b": (-0.05, -0.01), "ground": (-0.02, 0.03)}
    assert dc_budget.voltage_bounds((4.95, 5.05), split) == pytest.approx(expected)


def test_missing_is_not_zero_and_other_inputs_still_validate() -> None:
    assert dc_budget.voltage_bounds((4.95, 5.05), {"return": None}) is None
    assert dc_budget.voltage_bounds(None, {}) is None
    assert dc_budget.voltage_bounds((3.3, 3.3), {}) == (3.3, 3.3)
    with pytest.raises(ValueError):
        dc_budget.voltage_bounds(None, {"missing": None, "bad": (0.0, math.nan)})


@pytest.mark.parametrize("bad", [(1.0, 0.0), (0.0, math.inf), (False, 0.0), (math.nan, 0.0)])
def test_invalid_interval_rejected(bad: tuple[float, float]) -> None:
    with pytest.raises(ValueError):
        dc_budget.voltage_bounds(bad, {})
    with pytest.raises(ValueError):
        dc_budget.voltage_bounds((0.0, 0.0), {"bad": bad})


def test_overflow_and_empty_term_name_are_not_evidence() -> None:
    with pytest.raises(ValueError):
        dc_budget.voltage_bounds((1e308, 1e308), {"offset": (1e308, 1e308)})
    with pytest.raises(ValueError):
        dc_budget.voltage_bounds((3.0, 3.0), {"": (0.0, 0.0)})


def _run(model: Path, log: Path, optimization: str = "normal") -> dict[str, object]:
    assert DOC.is_file(), "missing source-bound S3 acceptance worksheet"
    blocks = re.findall(r"```python\n(.*?)\n```", DOC.read_text(), re.DOTALL)
    assert len(blocks) == 1
    environment = dict(os.environ)
    if optimization == "env":
        environment["PYTHONOPTIMIZE"] = "1"
    arguments = [sys.executable]
    if optimization == "flag":
        arguments.append("-O")
    run = subprocess.run(
        [*arguments, "-c", blocks[0], str(model)],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    log.write_text(run.stdout + run.stderr)
    assert run.returncode == 0, run.stderr
    return read_object(json.loads(run.stdout), "S3 result")


def test_default_worksheet_cannot_approve_missing_bounds(tmp_path: Path) -> None:
    result = _run(MODEL, tmp_path / "worksheet.log")
    assert result["physical_qualification"] is False
    rows = read_object(result["windows"], "windows")
    assert set(rows) == {
        "AVDD",
        "DVDD_AFE",
        "DVDD_U102",
        "DVDD_U103",
        "DVDD_U104",
        "MCU_3V3",
        "DVDD_SENSE",
        "AVDD_SENSE",
    }
    for raw in rows.values():
        row = read_object(raw, "window")
        assert row["voltage_V"] is None
        assert row["margins_V"] is None
        assert row["missing_terms"]
    example = read_object(result["hypothesis_only"], "example")
    assert example["remaining_before_all_other_losses_V"] == pytest.approx(0.099)
    assert example["with_assumed_110mV_common_loss_V"] == pytest.approx(4.739)


def test_filled_hypotheses_check_ground_sign_and_do_not_qualify(tmp_path: Path) -> None:
    assert MODEL.is_file(), "missing S3 model"
    data = read_object(json.loads(MODEL.read_text()), "model")
    terms = read_object(data["bounds_V"], "terms")
    for key in terms:
        terms[key] = [0.0, 0.0]
    terms.update(
        {
            "source_error": [-0.01, 0.01],
            "common_pair": [0.02, 0.04],
            "afe_5v_feed": [0.01, 0.02],
            "r11": [0.099, 0.101],
            "avdd_distribution": [0.001, 0.002],
            "g_analog": [-0.003, 0.004],
            "regulator": [3.25, 3.35],
            "dvdd_feed_U104": [0.02, 0.04],
            "g_U104": [-0.004, 0.006],
            "dvdd_sense": [0.001, 0.002],
            "g_dvdd_sense": [-0.004, 0.006],
        }
    )
    data["bounds_V"] = terms
    path = tmp_path / "hypotheses.json"
    path.write_text(json.dumps(data))
    result = _run(path, tmp_path / "filled.log")
    assert result["physical_qualification"] is False
    rows = read_object(result["windows"], "rows")
    avdd = read_object(rows["AVDD"], "AVDD")
    assert avdd["voltage_V"] == pytest.approx([4.773, 4.933])
    assert avdd["margins_V"] == pytest.approx([0.023, 0.317])
    delivered = read_object(rows["DVDD_U104"], "delivered")
    sensed = read_object(rows["DVDD_SENSE"], "sensed")
    assert delivered["voltage_V"] == pytest.approx([3.206, 3.336])
    assert sensed["voltage_V"] == pytest.approx([3.244, 3.355])
    assert sensed["margins_V"] is None  # monitor not a downstream acceptance meter


def test_upper_limit_is_checked_too(tmp_path: Path) -> None:
    data = read_object(json.loads(MODEL.read_text()), "model")
    terms = read_object(data["bounds_V"], "terms")
    for key in terms:
        terms[key] = [0.0, 0.0]
    terms["source_error"] = [0.3, 0.3]
    data["bounds_V"] = terms
    path = tmp_path / "high.json"
    path.write_text(json.dumps(data))
    row = read_object(
        read_object(_run(path, tmp_path / "high.log")["windows"], "rows")["AVDD"], "AVDD"
    )
    assert row["margins_V"] == pytest.approx([0.5, -0.1])


@pytest.mark.parametrize("change", ["permission", "missing", "extra", "hash"])
def test_bad_worksheet_is_rejected(tmp_path: Path, change: str) -> None:
    assert MODEL.is_file(), "missing S3 model"
    data = read_object(json.loads(MODEL.read_text()), "model")
    if change == "permission":
        data["physical_qualification"] = True
    elif change == "hash":
        hashes = read_object(data["input_sha256"], "hashes")
        hashes["hardware/rev_a/board_profile.json"] = "0" * 64
        data["input_sha256"] = hashes
    else:
        terms = read_object(data["bounds_V"], "terms")
        if change == "missing":
            del terms["g_analog"]
        else:
            terms["unmodeled_return"] = [0, 0]
        data["bounds_V"] = terms
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(data))
    with pytest.raises(AssertionError):
        _run(path, tmp_path / "invalid.log")


def test_worksheet_anchors_and_limits_match_frozen_native_contracts() -> None:
    import gzip
    import xml.etree.ElementTree as ET

    from hardware.rev_a import load_documents, parse_auxiliary_contract

    profile, bom, _ = load_documents()
    assert (profile["power"]["avdd_operating_min_v"], profile["power"]["avdd_operating_max_v"]) == (
        4.75,
        5.25,
    )
    r11 = next(row for row in bom["line_items"] if row["id"] == "analog_feed")
    assert r11["spec"]["resistance_ohm"] == 10 and r11["spec"]["tolerance_fraction"] == 0.01
    xml = ET.fromstring(
        gzip.decompress((ROOT / "tests/fixtures/rev_a_netlist.xml.gz").read_bytes())
    )
    nets = xml.find("nets")
    assert nets is not None
    nodes = {n.attrib["name"]: {(x.attrib["ref"], x.attrib["pin"]) for x in n} for n in nets}
    assert {("U2", "5"), ("U1", "48"), ("U1", "50")} <= nodes["DVDD"]
    assert {("R11", "2"), ("J3", "4"), ("U1", "54")} <= nodes["AVDD"]
    assert {("U2", "2"), ("U1", "33"), ("U1", "53")} <= nodes["GND"]
    aux = parse_auxiliary_contract((ROOT / "hardware/rev_a/auxiliary/contract.json").read_text())
    parts = {part.reference: part for part in aux.parts.values()}
    for ref in ("U102", "U103", "U104"):
        assert parts[ref].pins["14"].net == "AFE_DVDD"
        assert parts[ref].pins["7"].net == "TARGET_GND"
    assert parts["U106"].pins["1"].net == "AFE_DVDD_SENSE"
    assert parts["U107"].pins["1"].net == "AFE_AVDD_SENSE"
    assert parts["J105"].pins["2"].net == "TARGET_GND"


@pytest.mark.parametrize("optimization", ["flag", "env"])
def test_optimized_valid_worksheet_keeps_all_unknowns(tmp_path: Path, optimization: str) -> None:
    result = _run(MODEL, tmp_path / "optimized.log", optimization)
    assert result["physical_qualification"] is False
    for raw in read_object(result["windows"], "windows").values():
        assert read_object(raw, "window")["voltage_V"] is None


@pytest.mark.parametrize("optimization", ["flag", "env"])
@pytest.mark.parametrize(
    "field,value",
    [
        ("schema", "unapproved"),
        ("scope", "physical_release"),
        ("physical_qualification", True),
        ("evidence_status", "measurements_accepted"),
        ("source_commit", "HEAD"),
        ("source_tree", "0" * 40),
        ("input_sha256", {}),
        ("measurement_records", [{"claimed": "physical"}]),
    ],
)
def test_optimized_worksheet_rejects_fabricated_provenance(
    tmp_path: Path, optimization: str, field: str, value: object
) -> None:
    data = read_object(json.loads(MODEL.read_text()), "model")
    data[field] = value
    path = tmp_path / "fabricated.json"
    path.write_text(json.dumps(data))
    with pytest.raises(AssertionError):
        _run(path, tmp_path / "fabricated.log", optimization)
