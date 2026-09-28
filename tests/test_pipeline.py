from pathlib import Path

import numpy as np
import pytest

from lab.dsp import analyze, bandpower, psd, quality_flags
from lab.pipeline import load_data, save_data
from lab.signals import SyntheticConfig, generate


def test_known_sine_power_and_peak() -> None:
    fs = 250
    t = np.arange(2500) / fs
    x = 10e-6 * np.sin(2 * np.pi * 10 * t)
    assert bandpower(x, fs, 8, 13) == pytest.approx(50e-12, rel=0.002)
    f, p = psd(x, fs)
    assert f[np.argmax(p)] == 10


def test_fixed_artifact_rule() -> None:
    x = np.random.default_rng(9).normal(0, 3e-6, (1000, 4))
    assert not any(quality_flags(x).values())
    x[300, 0] = 200e-6
    assert quality_flags(x)["large_excursion"]
    assert quality_flags(np.zeros((1000, 4)))["flat"]


def test_deterministic_generation_metadata_and_raw_storage(tmp_path: Path) -> None:
    cfg = SyntheticConfig(sessions=3, blocks_per_session=4)
    a = generate(cfg)
    b = generate(cfg)
    np.testing.assert_array_equal(a["codes"], b["codes"])
    save_data(a, tmp_path / "raw.npz")
    c = load_data(tmp_path / "raw.npz")
    np.testing.assert_array_equal(a["codes"], c["codes"])
    assert c["metadata"]["kind"] == "synthetic_only"


def test_session_held_out_pipeline_recovers_designed_effect() -> None:
    data = generate(SyntheticConfig(sessions=3, blocks_per_session=4))
    result, _rows = analyze(data, permutations=2)
    assert result["closed_open_alpha_ratio"] > 5
    assert result["balanced_accuracy"] > 0.8
    assert result["rejected_epochs"] > 0
    for fold in result["folds"]:
        assert fold["held_out_session"] not in fold["train_sessions"]
    assert all("condition" not in s and "session" not in s for s in result["feature_names"])


def test_excessive_offset_cannot_be_repaired_by_filter() -> None:
    data = generate(SyntheticConfig(sessions=3, blocks_per_session=4, differential_offset_mV=300))
    assert data["invalid"].mean() > 0.9
    with pytest.raises(ValueError, match="All epochs rejected"):
        analyze(data, permutations=0)
