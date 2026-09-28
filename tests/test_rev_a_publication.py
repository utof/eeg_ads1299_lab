"""Generation identity and filesystem failures, not simulator authenticity."""

import hashlib
import json
from pathlib import Path

import pytest

from lab import rev_a
from lab.validation import read_object

_FIRST = "1" * 32
_SECOND = "2" * 32


def _complete(out: Path) -> rev_a.StudyReport:
    return rev_a.study(out, run_id=_FIRST)


def test_complete_generation_has_exact_inventory_and_verified_reader(tmp_path: Path) -> None:
    result = _complete(tmp_path)
    root = tmp_path / "runs" / _FIRST
    manifest = read_object(json.loads((root / "manifest.json").read_text()), "manifest")
    files = read_object(manifest["files"], "files")
    tools = read_object(manifest["tools"], "tools")
    assert result.run_id == _FIRST
    assert manifest["run_id"] == _FIRST
    assert manifest["baseline_sha256"] == result.baseline.documents_sha256
    assert manifest["request"] == {"require_ngspice": False, "leakage_bound_a": 1e-9}
    assert len(files) == 10
    for name, digest in files.items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
    assert tools["ngspice"] is None
    assert rev_a.read_study(tmp_path, expected_run_id=_FIRST) == result
    assert not (tmp_path / "study.json").exists()
    assert not (tmp_path / ".writer.lock").exists()


@pytest.mark.parametrize(
    "arguments", [["--leakage-bound-na", "bad"], ["--unknown"], ["--leakage-bound-na"], ["--help"]]
)
def test_rejected_cli_preserves_history_but_cannot_satisfy_new_request(
    tmp_path: Path, arguments: list[str]
) -> None:
    previous = _complete(tmp_path)
    pointer = (tmp_path / "current.json").read_bytes()
    with pytest.raises(SystemExit):
        rev_a.main(["--out", str(tmp_path), "--run-id", _SECOND, *arguments])
    assert (tmp_path / "current.json").read_bytes() == pointer
    assert rev_a.read_study(tmp_path, expected_run_id=_FIRST) == previous
    with pytest.raises(ValueError, match="run identity"):
        rev_a.read_study(tmp_path, expected_run_id=_SECOND)


def test_failed_calculation_retains_previous_run_and_rejects_new_identity(tmp_path: Path) -> None:
    previous = _complete(tmp_path)
    with pytest.raises(ValueError, match="leakage"):
        rev_a.study(tmp_path, run_id=_SECOND, leakage_bound_a=-1)
    assert rev_a.read_study(tmp_path, expected_run_id=_FIRST) == previous
    with pytest.raises(ValueError, match="run identity"):
        rev_a.read_study(tmp_path, expected_run_id=_SECOND)


@pytest.mark.parametrize("operation", ["write", "directory_rename", "pointer_replace"])
def test_publication_failure_never_advances_current(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, operation: str
) -> None:
    previous = _complete(tmp_path)
    pointer = (tmp_path / "current.json").read_bytes()
    original_write = Path.write_text
    original_rename = Path.rename
    original_replace = Path.replace

    def fail_write(self: Path, data: str, *args: object, **kwargs: object) -> int:
        if self.name == "manifest.json":
            raise OSError("injected manifest failure")
        # Only our JSON writer uses this patched method during the attempt.
        return original_write(self, data, encoding="utf-8")

    def fail_rename(self: Path, target: str | Path) -> Path:
        if self.name == _SECOND:
            raise OSError("injected directory rename failure")
        return original_rename(self, target)

    def fail_replace(self: Path, target: str | Path) -> Path:
        if Path(target).name == "current.json":
            raise OSError("injected pointer replace failure")
        return original_replace(self, target)

    if operation == "write":
        monkeypatch.setattr(Path, "write_text", fail_write)
    elif operation == "directory_rename":
        monkeypatch.setattr(Path, "rename", fail_rename)
    else:
        monkeypatch.setattr(Path, "replace", fail_replace)
    with pytest.raises(OSError, match="injected"):
        rev_a.study(tmp_path, run_id=_SECOND)
    assert (tmp_path / "current.json").read_bytes() == pointer
    assert rev_a.read_study(tmp_path, expected_run_id=_FIRST) == previous
    assert not (tmp_path / ".writer.lock").exists()
    assert (tmp_path / ".pending" / _SECOND).exists() or (tmp_path / "runs" / _SECOND).exists()


def test_run_ids_cannot_be_reused(tmp_path: Path) -> None:
    previous = _complete(tmp_path)
    with pytest.raises((ValueError, FileExistsError), match=r"exists|reus"):
        rev_a.study(tmp_path, run_id=_FIRST)
    assert rev_a.read_study(tmp_path, expected_run_id=_FIRST) == previous


@pytest.mark.parametrize("run_id", ["../outside", "", "A" * 32, "1" * 31])
def test_invalid_run_identity_does_not_touch_output(tmp_path: Path, run_id: str) -> None:
    out = tmp_path / "new"
    with pytest.raises(ValueError, match="run identity"):
        rev_a.study(out, run_id=run_id)
    assert not out.exists()


def test_existing_writer_is_rejected_without_deleting_its_lock(tmp_path: Path) -> None:
    _complete(tmp_path)
    lock = tmp_path / ".writer.lock"
    lock.write_text("other writer")
    with pytest.raises(RuntimeError, match="writer"):
        rev_a.study(tmp_path, run_id=_SECOND)
    assert lock.read_text() == "other writer"
    assert not (tmp_path / "runs" / _SECOND).exists()


@pytest.mark.parametrize(
    "name", ["study.json", "balanced/response.csv", "balanced/common/network.cir"]
)
def test_reader_detects_changed_artifact(tmp_path: Path, name: str) -> None:
    _complete(tmp_path)
    artifact = tmp_path / "runs" / _FIRST / name
    artifact.write_bytes(artifact.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="digest"):
        rev_a.read_study(tmp_path, expected_run_id=_FIRST)


def test_reader_rejects_stale_pointer_and_parameter_mismatch(tmp_path: Path) -> None:
    _complete(tmp_path)
    old_pointer = (tmp_path / "current.json").read_bytes()
    rev_a.study(tmp_path, run_id=_SECOND, leakage_bound_a=2e-9)
    with pytest.raises(ValueError, match="request"):
        rev_a.read_study(tmp_path, expected_run_id=_SECOND)
    assert (
        rev_a.read_study(tmp_path, expected_run_id=_SECOND, leakage_bound_a=2e-9).run_id == _SECOND
    )
    (tmp_path / "current.json").write_bytes(old_pointer)
    with pytest.raises(ValueError, match="run identity"):
        rev_a.read_study(tmp_path, expected_run_id=_SECOND, leakage_bound_a=2e-9)


def test_reader_rejects_symlink_and_unlisted_file(tmp_path: Path) -> None:
    _complete(tmp_path)
    root = tmp_path / "runs" / _FIRST
    extra = root / "unlisted.txt"
    extra.write_text("not in manifest")
    with pytest.raises(ValueError, match="inventory"):
        rev_a.read_study(tmp_path, expected_run_id=_FIRST)
    extra.unlink()
    response = root / "balanced" / "response.csv"
    target = tmp_path / "outside.csv"
    response.rename(target)
    response.symlink_to(target)
    with pytest.raises(ValueError, match="symlink"):
        rev_a.read_study(tmp_path, expected_run_id=_FIRST)


def test_second_success_preserves_first_generation_bytes(tmp_path: Path) -> None:
    first = _complete(tmp_path)
    before = {
        p.relative_to(tmp_path / "runs" / _FIRST): p.read_bytes()
        for p in (tmp_path / "runs" / _FIRST).rglob("*")
        if p.is_file()
    }
    second = rev_a.study(tmp_path)
    assert second.run_id != first.run_id
    assert before == {
        p.relative_to(tmp_path / "runs" / _FIRST): p.read_bytes()
        for p in (tmp_path / "runs" / _FIRST).rglob("*")
        if p.is_file()
    }
    assert rev_a.read_study(tmp_path, expected_run_id=second.run_id) == second


def test_cli_publishes_an_identifiable_generation(tmp_path: Path) -> None:
    assert rev_a.main(["--out", str(tmp_path), "--run-id", _FIRST]) == 0
    assert (tmp_path / "current.json").is_file()
    assert not (tmp_path / "study.json").exists()
    assert rev_a.read_study(tmp_path, expected_run_id=_FIRST).run_id == _FIRST


def _rewrite_manifest(out: Path, manifest: dict[str, object]) -> None:
    """Exercise schema validation even when envelope digests are internally consistent."""
    path = out / "runs" / _FIRST / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    pointer = {
        "schema_version": 1,
        "run_id": _FIRST,
        "manifest_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    (out / "current.json").write_text(json.dumps(pointer), encoding="utf-8")


@pytest.mark.parametrize(
    ("key", "replacement"),
    [
        ("schema_version", True),
        ("schema_version", 2),
        ("study", "other"),
        ("run_id", _SECOND),
        ("request", {}),
        ("request", {"require_ngspice": 0, "leakage_bound_a": 1e-9}),
        ("request", {"require_ngspice": False, "leakage_bound_a": float("nan")}),
        ("baseline_sha256", "not a digest"),
        ("baseline_sha256", "a" * 64),
        ("outcome", "executed_and_compared"),
        ("source", {"commit": "wrong", "worktree_dirty": False}),
        ("source", {"commit": "a" * 40, "worktree_dirty": "false"}),
        ("tools", {"python": 3.13, "numpy": "2.3.5", "ngspice": None}),
        ("tools", {"python": "3.13", "numpy": "2.3.5", "ngspice": "fabricated"}),
        ("files", {"../../outside": "a" * 64}),
    ],
)
def test_reader_checks_manifest_schema_and_request_not_only_hashes(
    tmp_path: Path, key: str, replacement: object
) -> None:
    _complete(tmp_path)
    path = tmp_path / "runs" / _FIRST / "manifest.json"
    manifest = read_object(json.loads(path.read_text()), "manifest")
    manifest[key] = replacement
    _rewrite_manifest(tmp_path, manifest)
    with pytest.raises(ValueError):
        rev_a.read_study(tmp_path, expected_run_id=_FIRST)


@pytest.mark.parametrize(
    ("key", "replacement"),
    [
        ("schema_version", 2),
        ("schema_version", True),
        ("manifest_sha256", "bad"),
        ("manifest_sha256", "a" * 64),
        ("extra", 1),
    ],
)
def test_reader_rejects_bad_pointer(tmp_path: Path, key: str, replacement: object) -> None:
    _complete(tmp_path)
    path = tmp_path / "current.json"
    pointer = read_object(json.loads(path.read_text()), "pointer")
    pointer[key] = replacement
    path.write_text(json.dumps(pointer))
    with pytest.raises(ValueError):
        rev_a.read_study(tmp_path, expected_run_id=_FIRST)


@pytest.mark.parametrize(
    ("key", "replacement"),
    [
        ("hardware_validated", 0),
        ("body_connection_permitted", True),
        ("limitations", "not a list"),
        ("limitations", [1]),
        ("cases", {}),
        ("corners", {"balanced": 1}),
        ("ngspice_status", "executed_and_compared"),
        ("ideal_source_pole_hz", -1),
        ("run_id", _SECOND),
        ("leakage_bound_a", 2e-9),
        ("leakage_bound_a", True),
    ],
)
def test_reader_reconstructs_valid_domain_values_even_with_rehashed_bad_report(
    tmp_path: Path, key: str, replacement: object
) -> None:
    _complete(tmp_path)
    root = tmp_path / "runs" / _FIRST
    report = read_object(json.loads((root / "study.json").read_text()), "report")
    report[key] = replacement
    (root / "study.json").write_text(json.dumps(report))
    manifest = read_object(json.loads((root / "manifest.json").read_text()), "manifest")
    files = read_object(manifest["files"], "files")
    files["study.json"] = hashlib.sha256((root / "study.json").read_bytes()).hexdigest()
    manifest["files"] = files
    _rewrite_manifest(tmp_path, manifest)
    with pytest.raises(ValueError):
        rev_a.read_study(tmp_path, expected_run_id=_FIRST)


def test_interleaved_writer_is_actually_excluded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = Path.write_text
    blocked: list[bool] = []

    def interleave(self: Path, data: str, *args: object, **kwargs: object) -> int:
        if self.name == "manifest.json":
            with pytest.raises(RuntimeError, match="writer"):
                rev_a.study(tmp_path, run_id=_SECOND)
            blocked.append(True)
        return original(self, data, encoding="utf-8")

    monkeypatch.setattr(Path, "write_text", interleave)
    result = _complete(tmp_path)
    assert blocked == [True]
    assert rev_a.read_study(tmp_path, expected_run_id=_FIRST) == result


def test_preexisting_partial_identity_is_not_reused(tmp_path: Path) -> None:
    partial = tmp_path / ".pending" / _FIRST
    partial.mkdir(parents=True)
    with pytest.raises(ValueError, match="reused"):
        _complete(tmp_path)
    assert partial.is_dir()
    assert not (tmp_path / "current.json").exists()


@pytest.mark.parametrize("name", ["runs", ".pending"])
def test_reserved_directory_symlink_is_rejected(tmp_path: Path, name: str) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / name).symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        _complete(tmp_path)
    assert not list(outside.iterdir())


def test_legacy_flat_output_is_never_treated_as_current(tmp_path: Path) -> None:
    legacy = tmp_path / "study.json"
    legacy.write_text('{"ngspice_status":"executed_and_compared"}')
    with pytest.raises(FileNotFoundError):
        rev_a.read_study(tmp_path, expected_run_id=_FIRST)
    _complete(tmp_path)
    assert legacy.read_text() == '{"ngspice_status":"executed_and_compared"}'


def test_request_validation_rejects_truthy_nonboolean_without_output(tmp_path: Path) -> None:
    from collections.abc import Callable
    from typing import cast

    call = cast(Callable[..., rev_a.StudyReport], rev_a.study)
    out = tmp_path / "new"
    with pytest.raises(ValueError, match="boolean"):
        call(out, require_ngspice="false")
    assert not out.exists()
