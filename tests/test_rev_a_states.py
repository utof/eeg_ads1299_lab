"""Completed study values must not carry contradictory or mutable evidence."""

from dataclasses import replace
from pathlib import Path
from typing import cast

import pytest

from lab.rev_a import CaseResult, StudyReport, study


@pytest.fixture(scope="module")
def completed(tmp_path_factory: pytest.TempPathFactory) -> StudyReport:
    return study(tmp_path_factory.mktemp("completed-state"))


def test_success_label_cannot_be_set_without_native_evidence(completed: StudyReport) -> None:
    with pytest.raises((TypeError, ValueError)):
        replace(completed, ngspice_status="executed_and_compared")


def test_simulation_cannot_grant_body_approval(completed: StudyReport) -> None:
    with pytest.raises((TypeError, ValueError)):
        replace(completed, body_connection_permitted=True)


def test_case_mapping_is_read_only(completed: StudyReport) -> None:
    mutable = cast(dict[str, CaseResult], completed.cases)
    with pytest.raises(TypeError):
        mutable["balanced"] = completed.cases["ideal_source_limit"]


def test_constructor_snapshots_case_mapping(completed: StudyReport) -> None:
    incoming = dict(completed.cases)
    result = replace(completed, cases=incoming)
    incoming.clear()
    assert len(result.cases) == 3


def test_constructor_snapshots_nested_corner_sequences(completed: StudyReport) -> None:
    incoming = {name: list(values) for name, values in completed.corners.items()}
    result = replace(completed, corners=incoming)
    incoming["balanced"].clear()
    assert len(result.corners["balanced"]) == 8


def test_corner_sequences_are_immutable(completed: StudyReport) -> None:
    assert isinstance(completed.corners["balanced"], tuple)


@pytest.mark.parametrize("value", [-1.0, float("nan"), float("inf")])
def test_completed_metrics_reject_invalid_values(completed: StudyReport, value: float) -> None:
    with pytest.raises(ValueError, match=r"finite|nonnegative"):
        replace(completed.cases["balanced"], leakage_dc_bound_v=value)


@pytest.mark.parametrize("value", [-1.0, float("nan"), float("inf")])
def test_completed_report_rejects_invalid_leakage(completed: StudyReport, value: float) -> None:
    with pytest.raises(ValueError, match=r"finite|nonnegative"):
        replace(completed, leakage_bound_a=value)


def test_completed_report_requires_all_scenarios(completed: StudyReport) -> None:
    with pytest.raises(ValueError, match="scenario"):
        replace(completed, cases={})


def test_completed_report_requires_all_corners(completed: StudyReport) -> None:
    incoming = dict(completed.corners)
    incoming.pop("balanced")
    with pytest.raises(ValueError, match=r"corner|scenario"):
        replace(completed, corners=incoming)


def test_failed_rerun_has_no_completion_marker(tmp_path: Path) -> None:
    study(tmp_path)
    with pytest.raises(ValueError):
        study(tmp_path, leakage_bound_a=-1.0)
    assert not (tmp_path / "study.json").exists()
