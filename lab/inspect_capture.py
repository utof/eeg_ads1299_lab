"""Bench capture quality report. Never interpolate gaps into a spectrum."""

import csv
import json
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from .adc import RATES
from .data_types import BoolArray, FloatArray, InspectionReport, IntArray
from .dsp import psd
from .validation import integer, number, read_object, text


def inspect_capture(csv_path: str | Path, out_dir: str | Path) -> InspectionReport:
    csv_path, out_dir = Path(csv_path), Path(out_dir)
    metadata_path = csv_path.with_suffix(".json")
    if not metadata_path.exists():
        raise ValueError("Keep the metadata JSON created by decode beside this CSV")
    raw_metadata: object = json.loads(metadata_path.read_text())
    metadata = read_object(raw_metadata, "capture metadata")
    fs, n = integer(metadata, "fs_hz"), integer(metadata, "channels")
    if fs not in RATES or n not in (4, 6, 8):
        raise ValueError("Unsupported capture fs_hz/channels")
    x, counts, times, sequence = _read_capture(csv_path, n)
    # Both counters and device timing must remain continuous. uint32 wrap is OK.
    ds = (sequence[1:].astype(np.int64) - sequence[:-1].astype(np.int64)) % (2**32)
    dt = np.diff(times)
    broken: BoolArray = (ds != 1) | (np.abs(dt - 1 / fs) > max(0.0005, 0.1 / fs))
    boundaries = np.flatnonzero(broken) + 1
    runs = np.split(np.arange(len(x)), boundaries)
    frequencies, spectra = _contiguous_spectra(x, runs, fs)
    peak_to_peak: FloatArray = np.ptp(x, axis=0)
    rail_mask: BoolArray = (counts == -(2**23)) | (counts == 2**23 - 1)
    rail_counts: IntArray = np.sum(rail_mask, axis=0)
    result: InspectionReport = {
        "kind": "bench_signal_quality_not_human_EEG_validation",
        "source": csv_path.name,
        "recording_mode": text(metadata, "recording_mode"),
        "samples": len(x),
        "channels": n,
        "fs_hz": fs,
        "assumed_vref_v": number(metadata, "assumed_vref_v"),
        "gap_boundaries": len(boundaries),
        "longest_contiguous_seconds": max(map(len, runs)) / fs,
        "mean_uV_by_channel": np.mean(x, axis=0).tolist(),
        "raw_peak_to_peak_uV_by_channel": peak_to_peak.tolist(),
        "rail_code_samples_by_channel": rail_counts.tolist(),
        "four_second_spectral_windows": len(spectra),
        "cautions": [
            "ADC rail-code check cannot detect every analog common-mode violation.",
            "Internal-short spectra are not electrode-connected system noise.",
            "No gaps interpolated; incomplete four-second windows excluded.",
            "DC offsets are reported before detrending. Spectrum alone hides DC.",
            "Voltage scale uses supplied reference and gain, not bench calibration.",
        ],
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    if spectra and frequencies is not None:
        power = np.asarray(np.mean(spectra, axis=0), dtype=np.float64)
        np.savetxt(
            out_dir / "spectrum.csv",
            np.column_stack((frequencies, power * 1e12)),
            delimiter=",",
            header="frequency_hz," + ",".join(f"ch{c + 1}_uV2_per_Hz" for c in range(n)),
            comments="",
        )
        inband = (frequencies >= 0.5) & (frequencies <= 40)
        result["rms_0p5_40_Hz_uV_by_channel"] = np.sqrt(
            np.trapezoid(power[inband], frequencies[inband], axis=0) * 1e12
        ).tolist()
        result["peak_0p5_40_Hz_by_channel"] = frequencies[inband][
            np.argmax(power[inband], axis=0)
        ].tolist()
    else:
        result["spectral_status"] = (
            "not_computed: need at least one uninterrupted four-second interval"
        )
    (out_dir / "quality_report.json").write_text(json.dumps(result, indent=2))
    return result


def _contiguous_spectra(
    x: FloatArray, runs: list[IntArray], fs: int
) -> tuple[FloatArray | None, list[FloatArray]]:
    """Analyze complete windows without joining separated capture intervals."""
    spectra: list[FloatArray] = []
    frequencies: FloatArray | None = None
    segment_size = 4 * fs
    for run in runs:
        for offset in range(0, len(run) - segment_size + 1, segment_size):
            idx = run[offset : offset + segment_size]
            frequencies, power = psd(x[idx] * 1e-6, fs)
            spectra.append(power)
    return frequencies, spectra


def _read_capture(
    csv_path: Path, n: int
) -> tuple[FloatArray, IntArray, FloatArray, NDArray[np.uint64]]:
    with csv_path.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError("Empty capture CSV")
    x = np.array([[float(r[f"ch{c + 1}_uV"]) for c in range(n)] for r in rows])
    counts = np.array([[int(r[f"ch{c + 1}_count"]) for c in range(n)] for r in rows])
    times = np.array([float(r["elapsed_s"]) for r in rows])
    sequence = np.array([int(r["sequence"]) for r in rows], dtype=np.uint64)
    if not np.all(np.isfinite(x)) or not np.all(np.isfinite(times)):
        raise ValueError("Nonfinite capture data")
    return x, counts, times, sequence
