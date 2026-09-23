"""Shared data contracts. Array annotations describe dtype, not shape or units.

The numerical APIs continue to validate values at runtime. Float arrays in the
signal path contain volts unless their field name explicitly says otherwise.
"""

from typing import NotRequired, TypeAlias, TypedDict

import numpy as np
from numpy.typing import NDArray

FloatArray: TypeAlias = NDArray[np.float64]
ComplexArray: TypeAlias = NDArray[np.complex128]
CodeArray: TypeAlias = NDArray[np.int32]
IntArray: TypeAlias = NDArray[np.int64]
BoolArray: TypeAlias = NDArray[np.bool_]
FloatResult: TypeAlias = FloatArray | np.float64
CodeResult: TypeAlias = CodeArray | np.int32
BoolResult: TypeAlias = BoolArray | np.bool_


class SyntheticMetadata(TypedDict):
    seed: int
    channels: int
    sessions: int
    blocks_per_session: int
    block_seconds: int
    fs_hz: int
    line_hz: int
    gain: int
    closed_alpha_uV: float
    open_alpha_uV: float
    adc_noise_rms_uV: float
    differential_offset_mV: float
    artifact_uV: float
    null_effect: bool
    kind: str
    adc_lsb_v: float
    surrogate_filter_delay_s: float
    analog_network_applied: bool


class Recording(TypedDict):
    codes: CodeArray
    session: NDArray[np.int16]
    block: NDArray[np.int16]
    condition: NDArray[np.int8]
    time_s: FloatArray
    invalid: BoolArray
    artifact_truth: BoolArray
    metadata: SyntheticMetadata


class QualityFlags(TypedDict):
    nonfinite_or_shape: bool
    overrange: bool
    large_excursion: bool
    flat: bool


class EpochRow(QualityFlags):
    block: int
    session: int
    start_s: float
    condition: int
    accepted: bool
    alpha_uV2: NotRequired[float]


class FoldReport(TypedDict):
    held_out_session: int
    train_sessions: list[int]
    train_epochs: int
    test_epochs: int
    balanced_accuracy: float


class CrossValidationReport(TypedDict):
    balanced_accuracy: float
    baseline_balanced_accuracy: float
    confusion_matrix: list[list[int]]
    folds: list[FoldReport]


class AnalysisReport(CrossValidationReport):
    kind: str
    candidate_epochs: int
    accepted_epochs: int
    rejected_epochs: int
    alpha_median_uV2: dict[str, float]
    closed_open_alpha_ratio: float
    block_permutation_scores: list[float]
    block_permutation_mean: float | None
    block_permutation_p: float | None
    feature_names: list[str]
    configuration: NotRequired[dict[str, int | float | bool]]


class TrackerInfo(TypedDict):
    elapsed_us: int
    missing_before: int


class TrackerSummary(TypedDict):
    accepted: int
    missing: int
    duplicates: int
    stale: int
    timing_anomalies: int


class CaptureSummary(TrackerSummary):
    channels: int
    gain: int
    fs_hz: int
    assumed_vref_v: float
    discarded_bytes: int
    invalid_candidates: int
    trailing_bytes: int
    last_device_overruns: int
    flags: int
    gap_policy: str
    recording_mode: str


class InspectionReport(TypedDict):
    kind: str
    source: str
    recording_mode: str
    samples: int
    channels: int
    fs_hz: int
    assumed_vref_v: float
    gap_boundaries: int
    longest_contiguous_seconds: float
    mean_uV_by_channel: list[float]
    raw_peak_to_peak_uV_by_channel: list[float]
    rail_code_samples_by_channel: list[int]
    four_second_spectral_windows: int
    cautions: list[str]
    rms_0p5_40_Hz_uV_by_channel: NotRequired[list[float]]
    peak_0p5_40_Hz_by_channel: NotRequired[list[float]]
    spectral_status: NotRequired[str]
