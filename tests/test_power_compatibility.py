"""A compatibility probe must reject plausible-looking incomplete/wrong traces."""

from pathlib import Path

import numpy as np
import pytest

from lab.rev_a_power import assess_trace, prepare_library, switch_netlist


def test_incomplete_window_cannot_be_a_pass() -> None:
    with pytest.raises(ValueError, match="window"):
        assess_trace(np.array([0.0, 0.001]), np.array([[0.0], [3.3]]), target_v=3.3)


def test_wrong_regulated_level_cannot_be_a_pass() -> None:
    times = np.linspace(0, 0.02, 201)
    with pytest.raises(ValueError, match="plateau"):
        assess_trace(times, np.full((201, 1), 0.0036), target_v=3.3)


def test_expected_plateaus_pass() -> None:
    times = np.linspace(0, 0.02, 201)
    result = assess_trace(times, np.full((201, 1), 3.3), target_v=3.3)
    assert result["window_complete"] is True


def test_model_hash_is_checked_before_any_translation(tmp_path: Path) -> None:
    archive = tmp_path / "bad.zip"
    archive.write_bytes(b"not the pinned TI artifact")
    with pytest.raises(ValueError, match="SHA-256"):
        prepare_library(archive, normalize_switch=False)


def test_switch_reproducer_is_independent_of_vendor_library() -> None:
    text = switch_netlist("inverse", 0)
    assert "Roff=1e-6 Ron=1e6" in text
    assert ".include" not in text
    assert "tran" in text


@pytest.mark.parametrize("target", [float("nan"), 0.0, -1.0, True])
def test_invalid_target_is_rejected(target: float) -> None:
    with pytest.raises(ValueError):
        assess_trace(np.array([0.0, 0.02]), np.ones((2, 1)), target_v=target)


@pytest.mark.parametrize("fault", ["nan", "order", "start", "shape", "no_plateau"])
def test_bad_trace_contract_is_rejected(fault: str) -> None:
    times = np.linspace(0, 0.02, 201)
    values = np.full((201, 1), 3.3)
    if fault == "nan":
        values[0, 0] = np.nan
    elif fault == "order":
        times[5] = times[4]
    elif fault == "start":
        times[0] = -1.0
    elif fault == "shape":
        values = values[:5]
    elif fault == "no_plateau":
        times, values = np.array([0.0, 0.02]), np.full((2, 1), 3.3)
    with pytest.raises(ValueError):
        assess_trace(times, values, target_v=3.3)


@pytest.mark.native
def test_native_handwritten_switch_endpoints_and_manifest(tmp_path: Path) -> None:
    import hashlib
    import json

    from lab.rev_a_power import run_pilot

    root = run_pilot(tmp_path)
    raw: object = json.loads((root / "pilot.json").read_text())
    assert isinstance(raw, dict)
    probes: object = raw["switch_probes"]
    assert isinstance(probes, list)
    assert len(probes) == 6
    for probe in probes:
        assert isinstance(probe, dict)
        if probe["variant"] != "inverse":
            assert probe["compatible_endpoint"] is True
    manifest: object = json.loads((root / "manifest.json").read_text())
    assert isinstance(manifest, dict)
    files: object = manifest["files"]
    assert isinstance(files, dict)
    for name, digest in files.items():
        assert isinstance(name, str)
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
    assert not list(root.rglob("*.lib"))
    assert not list(root.rglob(".spiceinit"))
