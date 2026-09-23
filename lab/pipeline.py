"""Reproducible demo outputs. All plot titles label synthetic/model results."""

import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import TypeVar

import numpy as np
from numpy.lib.npyio import NpzFile
from numpy.typing import NDArray

from .adc import ADCConfig, sinc3_magnitude, to_volts
from .analog import InputNetwork, transfer
from .data_types import AnalysisReport, BoolArray, EpochRow, FloatArray, Recording
from .dsp import analyze, psd
from .signals import SyntheticConfig, generate, parse_metadata
from .validation import stored_array

_DEFAULT_CONFIG = SyntheticConfig()


def save_data(data: Recording, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        codes=data["codes"],
        session=data["session"],
        block=data["block"],
        condition=data["condition"],
        time_s=data["time_s"],
        invalid=data["invalid"],
        artifact_truth=data["artifact_truth"],
        metadata_json=np.array(json.dumps(data["metadata"])),
    )


def load_data(path: str | Path) -> Recording:
    archive: NpzFile
    with np.load(path, allow_pickle=False) as archive:
        metadata_raw: object = archive["metadata_json"]
        metadata_text = str(metadata_raw)
        metadata_value: object = json.loads(metadata_text)
        data: Recording = {
            "codes": _stored(archive, "codes", np.int32, 2),
            "session": _stored(archive, "session", np.int16, 1),
            "block": _stored(archive, "block", np.int16, 1),
            "condition": _stored(archive, "condition", np.int8, 1),
            "time_s": _stored(archive, "time_s", np.float64, 1),
            "invalid": _stored(archive, "invalid", np.bool_, 2),
            "artifact_truth": _stored(archive, "artifact_truth", np.bool_, 1),
            "metadata": parse_metadata(metadata_value),
        }
    samples = len(data["codes"])
    expected = (samples, data["metadata"]["channels"])
    if data["codes"].shape != expected or data["invalid"].shape != expected:
        raise ValueError("codes/invalid: channel or sample count mismatch")
    for name in ("session", "block", "condition", "time_s", "artifact_truth"):
        # All arrays in this tuple are explicitly known 1-D contracts.
        lengths = {
            "session": len(data["session"]),
            "block": len(data["block"]),
            "condition": len(data["condition"]),
            "time_s": len(data["time_s"]),
            "artifact_truth": len(data["artifact_truth"]),
        }
        if lengths[name] != samples:
            raise ValueError(f"{name}: sample count mismatch")
    return data


def make_plots(
    data: Recording, report: AnalysisReport, rows: list[EpochRow], out: str | Path
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    cfg = data["metadata"]
    fs = cfg["fs_hz"]
    x: FloatArray = np.asarray(to_volts(data["codes"], ADCConfig(gain=cfg["gain"], fs_hz=fs))) * 1e6
    # Independent figures, matplotlib default colors/style.
    fig, ax = plt.subplots(figsize=(10, 4.6), layout="constrained")
    idx: BoolArray = (data["session"] == 0) & (data["time_s"] >= 2) & (data["time_s"] < 26)
    trace: FloatArray = x[idx, 0] - np.median(x[idx, 0])
    ax.plot(data["time_s"][idx], trace, linewidth=0.75)
    ax.set(
        xlabel="Time within synthetic session (s)",
        ylabel="Channel 1, DC removed (µV)",
        title="Synthetic recording: brain-like waves, residual line noise, artifacts",
    )
    fig.savefig(out / "synthetic_trace.png", dpi=155)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(9, 4.8), layout="constrained")
    # Average PSDs of individual clean 4-s windows; never concatenate separated blocks.
    for label, name in [(0, "Eyes-open label"), (1, "Eyes-closed label")]:
        frequencies, power = _condition_psd(data, rows, label, x, fs)
        ax.semilogy(frequencies, power, label=name)
    ax.set(
        xlim=(1, 65),
        xlabel="Frequency (Hz)",
        ylabel="Power spectral density (µV²/Hz)",
        title="Synthetic ground truth: deliberately stronger 10-Hz activity when “closed”",
    )
    ax.legend()
    fig.savefig(out / "synthetic_psd.png", dpi=155)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(9, 4.8), layout="constrained")
    groups = report["folds"]
    sessions = [r["held_out_session"] for r in groups]
    scores = [r["balanced_accuracy"] for r in groups]
    ax.bar(sessions, scores, label="Session-held-out toy classifier")
    ax.axhline(0.5, linestyle="--", label="Two-class chance reference")
    ax.set(
        ylim=(0, 1.08),
        xlabel="Held-out synthetic session",
        ylabel="Balanced accuracy",
        title="Software plumbing test — not demonstrated brain-decoding performance",
    )
    ax.legend(loc="lower right")
    fig.savefig(out / "synthetic_ml.png", dpi=155)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(9, 4.8), layout="constrained")
    f = np.linspace(0.1, 125, 700)
    sinc_db: FloatArray = 20 * np.log10(np.maximum(sinc3_magnitude(f, fs), 1e-14))
    passive_db: FloatArray = 20 * np.log10(np.maximum(np.abs(transfer(f, InputNetwork())), 1e-14))
    ax.plot(
        f,
        sinc_db,
        label="Nominal ADS1299 sinc³ shape",
    )
    ax.plot(
        f,
        passive_db,
        label="Illustrative passive input network",
    )
    ax.set(
        xlabel="Frequency (Hz)",
        ylabel="Gain (dB)",
        ylim=(-15, 1),
        title="Two different filters: external passive network vs. ADC digital filter",
    )
    ax.legend()
    fig.savefig(out / "model_filter_response.png", dpi=155)
    plt.close(fig)


def run_demo(
    out: str | Path,
    cfg: SyntheticConfig = _DEFAULT_CONFIG,
    permutations: int = 20,
    plots: bool = True,
) -> AnalysisReport:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    data = generate(cfg)
    report, rows = analyze(data, permutations)
    report["configuration"] = asdict(cfg)
    save_data(data, out / "synthetic_recording.npz")
    (out / "analysis_report.json").write_text(json.dumps(report, indent=2))
    keys = sorted(set().union(*(r.keys() for r in rows)))
    with (out / "epoch_quality.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)
    with (out / "events.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["session", "block", "onset_s", "duration_s", "condition"])
        blocks: list[int] = np.unique(data["block"]).tolist()
        for block in blocks:
            idx = np.flatnonzero(data["block"] == block)[0]
            writer.writerow(
                [
                    int(data["session"][idx]),
                    block,
                    float(data["time_s"][idx]),
                    cfg.block_seconds,
                    "eyes_closed" if data["condition"][idx] else "eyes_open",
                ]
            )
    if plots:
        make_plots(data, report, rows, out)
    return report


def _condition_psd(
    data: Recording, rows: list[EpochRow], label: int, x: FloatArray, fs: int
) -> tuple[FloatArray, FloatArray]:
    spectra: list[FloatArray] = []
    frequencies: FloatArray | None = None
    for row in rows:
        if not row["accepted"] or row["condition"] != label:
            continue
        selected: BoolArray = (
            (data["session"] == row["session"])
            & (data["time_s"] >= row["start_s"])
            & (data["time_s"] < row["start_s"] + 4)
        )
        indices = np.flatnonzero(selected)
        frequencies, power = psd(x[indices, 0], fs)
        spectra.append(power)
    if frequencies is None:
        raise ValueError(f"No accepted epochs for condition {label}")
    mean: FloatArray = np.mean(spectra, axis=0)
    return frequencies, mean


Scalar = TypeVar("Scalar", bound=np.generic)


def _stored(archive: NpzFile, name: str, dtype: type[Scalar], ndim: int) -> NDArray[Scalar]:
    value: object = archive[name]
    return stored_array(value, dtype, ndim, name)
