"""Offline epoch analysis and session-held-out toy machine learning."""

from collections.abc import Iterator

import numpy as np
from numpy.typing import ArrayLike
from scipy.signal import butter, sosfiltfilt, welch
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, confusion_matrix
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import StandardScaler

from .adc import ADCConfig, to_volts
from .data_types import (
    AnalysisReport,
    BoolArray,
    CrossValidationReport,
    EpochRow,
    FloatArray,
    FloatResult,
    FoldReport,
    IntArray,
    QualityFlags,
    Recording,
)
from .validation import float_array

BANDS = {"theta": (4, 8), "alpha": (8, 13), "beta": (13, 30)}


def psd(x: ArrayLike, fs: int) -> tuple[FloatArray, FloatArray]:
    x = np.asarray(x, float)
    if x.ndim not in (1, 2) or len(x) < fs or not np.all(np.isfinite(x)):
        raise ValueError("PSD requires at least 1 s of finite time-first samples")
    nperseg = min(len(x), 4 * fs)
    frequency, power = welch(
        x,
        fs=fs,
        window="hann",
        nperseg=nperseg,
        noverlap=nperseg // 2,
        detrend="constant",
        axis=0,
        scaling="density",
    )
    return np.asarray(frequency, dtype=np.float64), np.asarray(power, dtype=np.float64)


def bandpower(x: ArrayLike, fs: int, low: float, high: float) -> FloatResult:
    if not 0 <= low < high < fs / 2:
        raise ValueError("Invalid frequency band")
    f, p = psd(x, fs)
    select = (f >= low) & (f <= high)
    return np.trapezoid(p[select], f[select], axis=0)


def quality_flags(
    x: ArrayLike, invalid: ArrayLike | None = None, threshold_uV: float = 150
) -> QualityFlags:
    """Heuristic peak-to-peak screen, not comprehensive artifact removal.

    Operates on raw differential voltages before bandpass. Unknown artifacts
    can pass. Constant electrode offset alone is not an artifact.
    """
    x = np.asarray(x, float)
    if x.ndim != 2 or not np.all(np.isfinite(x)):
        return {
            "nonfinite_or_shape": True,
            "overrange": True,
            "large_excursion": True,
            "flat": True,
        }
    centered: FloatArray = x - np.median(x, axis=0)
    peak_to_peak: FloatArray = np.ptp(centered, axis=0)
    std: FloatArray = np.std(centered, axis=0)
    return {
        "nonfinite_or_shape": False,
        "overrange": bool(np.any(invalid)) if invalid is not None else False,
        "large_excursion": bool(np.max(peak_to_peak) > threshold_uV * 1e-6),
        "flat": bool(np.any(std < 0.01e-6)),
    }


def epoch_features(data: Recording) -> tuple[FloatArray, IntArray, IntArray, list[EpochRow]]:
    """4-s nonoverlapping windows, discard 2 s at each block boundary.

    Each candidate is locally demeaned/filtered; no filter bridges train/test
    sessions. Quality rules are fixed before labels are read. Condition and
    session IDs are NEVER features. Split by session, not window.
    """
    cfg = data["metadata"]
    fs = cfg["fs_hz"]
    adc = ADCConfig(gain=cfg["gain"], fs_hz=fs)
    x = np.asarray(to_volts(data["codes"], adc), dtype=np.float64)
    features: list[FloatArray] = []
    labels: list[int] = []
    groups: list[int] = []
    rows: list[EpochRow] = []
    raw_sos: object = butter(4, [1, 40], fs=fs, btype="bandpass", output="sos")
    sos = float_array(raw_sos)
    window = 4 * fs
    for block in np.unique(data["block"]):
        same_block: BoolArray = data["block"] == block
        indices = np.flatnonzero(same_block)
        # Dataset uses contiguous blocks; refusing otherwise prevents bridging.
        if not np.all(np.diff(indices) == 1):
            raise ValueError("Noncontiguous block")
        for offset in range(2 * fs, len(indices) - 2 * fs - window + 1, window):
            idx = indices[offset : offset + window]
            raw = x[idx]
            flags = quality_flags(raw, data["invalid"][idx])
            accepted = not any(flags.values())
            row: EpochRow = {
                "block": int(block),
                "session": int(data["session"][idx[0]]),
                "start_s": float(data["time_s"][idx[0]]),
                "condition": int(data["condition"][idx[0]]),
                "accepted": accepted,
                "nonfinite_or_shape": flags["nonfinite_or_shape"],
                "overrange": flags["overrange"],
                "large_excursion": flags["large_excursion"],
                "flat": flags["flat"],
            }
            if accepted:
                centered: FloatArray = raw - np.mean(raw, axis=0)
                filtered_raw: object = sosfiltfilt(sos, centered, axis=0)
                filtered = float_array(filtered_raw)
                powers = [np.atleast_1d(bandpower(filtered, fs, *band)) for band in BANDS.values()]
                feat = np.log10(np.maximum(np.concatenate(powers), 1e-24))
                features.append(feat)
                labels.append(row["condition"])
                groups.append(row["session"])
                row["alpha_uV2"] = float(np.mean(powers[1]) * 1e12)
            rows.append(row)
    if not features:
        raise ValueError("All epochs rejected; inspect raw data and range/quality flags")
    return (
        np.asarray(features, dtype=np.float64),
        np.asarray(labels, dtype=np.int64),
        np.asarray(groups, dtype=np.int64),
        rows,
    )


def _cross_validate(X: FloatArray, y: IntArray, groups: IntArray) -> CrossValidationReport:
    if len(np.unique(groups)) < 3 or len(np.unique(y)) != 2:
        raise ValueError("Need >=3 groups and both conditions")
    predictions = np.empty_like(y)
    baseline = np.empty_like(y)
    folds: list[FoldReport] = []
    splits: Iterator[tuple[IntArray, IntArray]] = LeaveOneGroupOut().split(X, y, groups)
    for train, test in splits:
        if len(np.unique(y[train])) != 2 or len(np.unique(y[test])) != 2:
            raise ValueError("Each held-out session and training set must contain both conditions")
        if set(groups[train]) & set(groups[test]):
            raise AssertionError("Session leakage")
        model: Pipeline = make_pipeline(
            StandardScaler(), LogisticRegression(max_iter=2000, random_state=0)
        )
        model.fit(X[train], y[train])
        predictions[test] = model.predict(X[test])
        dummy = DummyClassifier(strategy="most_frequent").fit(X[train], y[train])
        baseline[test] = dummy.predict(X[test])
        folds.append(
            {
                "held_out_session": int(groups[test][0]),
                "train_sessions": sorted(int(z) for z in np.unique(groups[train])),
                "train_epochs": len(train),
                "test_epochs": len(test),
                "balanced_accuracy": float(balanced_accuracy_score(y[test], predictions[test])),
            }
        )
    return {
        "balanced_accuracy": float(balanced_accuracy_score(y, predictions)),
        "baseline_balanced_accuracy": float(balanced_accuracy_score(y, baseline)),
        "confusion_matrix": confusion_matrix(y, predictions, labels=[0, 1]).tolist(),
        "folds": folds,
    }


def analyze(data: Recording, permutations: int = 20) -> tuple[AnalysisReport, list[EpochRow]]:
    X, y, g, rows = epoch_features(data)
    result = _cross_validate(X, y, g)
    accepted = [r for r in rows if r["accepted"]]
    block_ids: IntArray = np.array([r["block"] for r in accepted])
    rng = np.random.default_rng(data["metadata"]["seed"] + 17)
    null: list[float] = []
    for _ in range(permutations):
        yp = _permute_blocks(y, g, block_ids, rng)
        null.append(_cross_validate(X, yp, g)["balanced_accuracy"])
    by_condition = {
        str(k): float(np.median([r["alpha_uV2"] for r in accepted if r["condition"] == k]))
        for k in (0, 1)
    }
    report: AnalysisReport = {
        "balanced_accuracy": result["balanced_accuracy"],
        "baseline_balanced_accuracy": result["baseline_balanced_accuracy"],
        "confusion_matrix": result["confusion_matrix"],
        "folds": result["folds"],
        "kind": "synthetic_pipeline_test_not_neuroscience_evidence",
        "candidate_epochs": len(rows),
        "accepted_epochs": len(accepted),
        "rejected_epochs": len(rows) - len(accepted),
        "alpha_median_uV2": by_condition,
        "closed_open_alpha_ratio": by_condition["1"] / by_condition["0"],
        "block_permutation_scores": null,
        "block_permutation_mean": float(np.mean(null)) if null else None,
        "block_permutation_p": float(
            (1 + sum(s >= result["balanced_accuracy"] for s in null)) / (1 + len(null))
        )
        if null
        else None,
        "feature_names": [
            f"log10_{band}_V2_ch{c + 1}"
            for band in BANDS
            for c in range(data["metadata"]["channels"])
        ],
    }
    return report, rows


def _permute_blocks(
    y: IntArray, groups: IntArray, block_ids: IntArray, rng: np.random.Generator
) -> IntArray:
    """Exchange whole blocks within sessions, preserving the original RNG order."""
    permuted: IntArray = y.copy()
    sessions: list[int] = np.unique(groups).tolist()
    for session in sessions:
        in_session: BoolArray = groups == session
        blocks: IntArray = np.unique(block_ids[in_session])
        block_list: list[int] = blocks.tolist()
        values: IntArray = np.array([y[block_ids == block][0] for block in block_list])
        rng.shuffle(values)
        labels: list[int] = values.tolist()
        for block, label in zip(block_list, labels, strict=True):
            permuted[block_ids == block] = label
    return permuted
