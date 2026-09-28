"""Evidence shape tests use fixtures; only native-marked tests run ngspice."""

import json
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import cast

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from lab.rev_a import AnalyticOnly, NativeCompared, StudyReport, read_study, study


def _errors() -> dict[str, float]:
    return {
        f"{name}/{drive}": 0.0
        for name in ("ideal_source_limit", "balanced", "impedance_mismatch")
        for drive in ("differential", "common")
    }


@pytest.mark.parametrize("change", ["empty", "missing", "extra"])
def test_native_evidence_requires_exact_comparison_set(change: str) -> None:
    errors = _errors()
    if change == "empty":
        errors.clear()
    elif change == "missing":
        errors.pop("balanced/common")
    else:
        errors["unexpected/common"] = 0.0
    with pytest.raises(ValueError, match="six"):
        NativeCompared(errors)


@pytest.mark.parametrize("value", [-1.0, float("nan"), float("inf"), True])
def test_native_evidence_rejects_invalid_error(value: float) -> None:
    errors = _errors()
    errors["balanced/common"] = value
    with pytest.raises(ValueError, match="finite"):
        NativeCompared(errors)


def test_native_evidence_defensively_copies_errors() -> None:
    errors = _errors()
    evidence = NativeCompared(errors)
    errors.clear()
    assert len(evidence.errors) == 6
    with pytest.raises(TypeError):
        cast(dict[str, float], evidence.errors)["balanced/common"] = 1.0


def test_status_is_derived_and_json_view_is_detached(tmp_path: Path) -> None:
    analytic = study(tmp_path)
    assert isinstance(analytic.spice_evidence, AnalyticOnly)
    assert analytic.ngspice_status == "not_requested"
    assert analytic.ngspice_max_abs_error == {}
    # Artificial unit-test evidence, not a claim of simulator execution.
    native = replace(analytic, spice_evidence=NativeCompared(_errors()))
    assert native.ngspice_status == "executed_and_compared"
    payload = native.to_dict()
    errors = payload["ngspice_max_abs_error"]
    assert isinstance(errors, dict)
    errors.clear()
    assert len(native.ngspice_max_abs_error) == 6
    assert "spice_evidence" not in payload
    assert payload["body_connection_permitted"] is False
    assert payload["hardware_validated"] is False
    assert payload["clamps_fitted"] is False
    assert json.loads(json.dumps(analytic.to_dict())) == json.loads(
        (tmp_path / "runs" / analytic.run_id / "study.json").read_text(encoding="utf-8")
    )


def test_duplicate_corner_networks_are_not_a_completed_study(tmp_path: Path) -> None:
    report = study(tmp_path)
    corners = dict(report.corners)
    corners["balanced"] = [report.corners["balanced"][0]] * 8
    with pytest.raises(ValueError, match="distinct"):
        replace(report, corners=corners)


@settings(max_examples=16, deadline=None, derandomize=True)
@given(st.lists(st.booleans(), min_size=1, max_size=6))
def test_generated_success_failure_reruns_never_reuse_completion(actions: list[bool]) -> None:
    with TemporaryDirectory() as directory:
        out = Path(directory)
        marker = out / "current.json"
        previous: StudyReport | None = None
        for succeed in actions:
            before = marker.read_bytes() if marker.exists() else None
            if succeed:
                report = study(out)
                assert report.ngspice_status == "not_requested"
                assert report.ngspice_max_abs_error == {}
                assert read_study(out, expected_run_id=report.run_id) == report
                assert not list((out / "runs" / report.run_id).glob("*/*/ac.txt"))
                if previous is not None:
                    assert report.run_id != previous.run_id
                previous = report
            else:
                with pytest.raises(ValueError, match="leakage"):
                    study(out, leakage_bound_a=-1.0)
                assert (marker.read_bytes() if marker.exists() else None) == before
                if previous is not None:
                    assert read_study(out, expected_run_id=previous.run_id) == previous
