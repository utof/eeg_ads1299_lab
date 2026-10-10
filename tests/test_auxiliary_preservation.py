"""L5 exceptions cannot hide unrelated edits or partial/corrupted local changes."""

import copy
import json

import pytest

from tests.auxiliary_preservation import DELTA, copper_records, legacy_auxiliary_records
from tests.test_auxiliary_placement import BOARD


def _candidate_records() -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    actual = copper_records(BOARD.read_text())
    raw: object = json.loads(DELTA.read_text())
    assert isinstance(raw, dict)
    old: object = raw["before"]
    new: object = raw["after"]
    assert isinstance(old, dict) and isinstance(new, dict)
    affected = old.keys() | new.keys()
    retained = {ident: record for ident, record in actual.items() if ident not in affected}
    states = []
    for value in (old, new):
        state = copy.deepcopy(retained)
        items: dict[object, object] = value
        for ident, record in items.items():
            assert isinstance(ident, str) and isinstance(record, dict)
            kind: object = record["type"]
            digest: object = record["sha256"]
            assert isinstance(kind, str) and isinstance(digest, str)
            state[ident] = {"type": kind, "sha256": digest}
        states.append(state)
    return states[0], states[1]


def test_legacy_mapping_preserves_the_original_records_and_does_not_mutate() -> None:
    before, candidate = _candidate_records()
    saved = copy.deepcopy(candidate)
    assert legacy_auxiliary_records(before) == before
    assert legacy_auxiliary_records(candidate) == before
    assert candidate == saved


def test_every_l5_delta_object_rejects_a_changed_hash() -> None:
    before, candidate = _candidate_records()
    changes = [ident for ident, row in candidate.items() if before.get(ident) != row]
    assert len(changes) == 41
    for ident in changes:
        changed = copy.deepcopy(candidate)
        changed[ident]["sha256"] = "0" * 64
        with pytest.raises(AssertionError, match="unreviewed or partial"):
            legacy_auxiliary_records(changed)


@pytest.mark.parametrize("mode", ["missing", "mixed", "resurrect"])
def test_l5_mapping_rejects_partial_application(mode: str) -> None:
    before, candidate = _candidate_records()
    common = next(
        ident for ident in before if ident in candidate and candidate[ident] != before[ident]
    )
    if mode == "missing":
        del candidate[common]
    elif mode == "mixed":
        candidate[common] = before[common]
    else:
        deleted = next(ident for ident in before if ident not in candidate)
        candidate[deleted] = before[deleted]
    with pytest.raises(AssertionError, match="unreviewed or partial"):
        legacy_auxiliary_records(candidate)


@pytest.mark.parametrize("mode", ["changed", "added", "removed"])
def test_unrelated_records_are_never_hidden_by_the_l5_exception(mode: str) -> None:
    before, candidate = _candidate_records()
    original = next(ident for ident in before if candidate.get(ident) == before[ident])
    if mode == "changed":
        candidate[original] = {"type": "footprint", "sha256": "0" * 64}
    elif mode == "added":
        candidate["unreviewed-extra-object"] = {"type": "segment", "sha256": "0" * 64}
    else:
        del candidate[original]
    result = legacy_auxiliary_records(candidate)
    assert result != before, "legacy guard must still see the unrelated fault"


def test_duplicate_source_ids_are_not_collapsed_by_the_hash_reader() -> None:
    duplicate = '(segment (net 1) (uuid "duplicate"))'
    with pytest.raises(AssertionError, match="duplicate source UUID"):
        copper_records(duplicate + duplicate)
