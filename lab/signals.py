"""Known-ground-truth synthetic recordings; deliberately not a brain model."""

from dataclasses import dataclass, fields
from typing import TypedDict

import numpy as np
from numpy.typing import NDArray
from scipy.signal import butter, sosfilt

from .adc import ADCConfig, behavioral_decimate, headroom_valid, quantize
from .data_types import BoolArray, CodeArray, FloatArray, IntArray, Recording, SyntheticMetadata
from .validation import boolean, float_array, integer, number, read_object, text


@dataclass(frozen=True)
class SyntheticConfig:
    seed: int = 42
    channels: int = 4
    sessions: int = 6
    blocks_per_session: int = 8
    block_seconds: int = 12
    fs_hz: int = 250
    line_hz: int = 50
    gain: int = 24
    closed_alpha_uV: float = 18.0
    open_alpha_uV: float = 5.0
    adc_noise_rms_uV: float = 0.25  # illustrative output-referred-to-input RMS, NOT a TI guarantee
    differential_offset_mV: float = 30.0
    artifact_uV: float = 200.0
    null_effect: bool = False

    @classmethod
    def from_mapping(cls, value: object) -> "SyntheticConfig":
        values = read_object(value, "SyntheticConfig")
        unknown = values.keys() - {field.name for field in fields(cls)}
        if unknown:
            raise ValueError(f"Unknown SyntheticConfig fields: {sorted(unknown)}")
        default = cls()
        return cls(
            seed=integer(values, "seed", default.seed),
            channels=integer(values, "channels", default.channels),
            sessions=integer(values, "sessions", default.sessions),
            blocks_per_session=integer(values, "blocks_per_session", default.blocks_per_session),
            block_seconds=integer(values, "block_seconds", default.block_seconds),
            fs_hz=integer(values, "fs_hz", default.fs_hz),
            line_hz=integer(values, "line_hz", default.line_hz),
            gain=integer(values, "gain", default.gain),
            closed_alpha_uV=number(values, "closed_alpha_uV", default.closed_alpha_uV),
            open_alpha_uV=number(values, "open_alpha_uV", default.open_alpha_uV),
            adc_noise_rms_uV=number(values, "adc_noise_rms_uV", default.adc_noise_rms_uV),
            differential_offset_mV=number(
                values, "differential_offset_mV", default.differential_offset_mV
            ),
            artifact_uV=number(values, "artifact_uV", default.artifact_uV),
            null_effect=boolean(values, "null_effect", default.null_effect),
        )

    def __post_init__(self) -> None:
        if self.channels not in (4, 6, 8):
            raise ValueError("channels must be 4, 6 or 8")
        if self.sessions < 3:
            raise ValueError("At least 3 independent synthetic sessions")
        if self.blocks_per_session < 4 or self.blocks_per_session % 2:
            raise ValueError("Use an even number of blocks, >=4")
        if self.block_seconds < 12:
            raise ValueError("Use blocks >=12 seconds")
        if self.fs_hz not in (250, 500):
            raise ValueError("Demo supports 250 or 500 SPS")
        if self.line_hz not in (50, 60):
            raise ValueError("line_hz must be 50 or 60")
        vals = (self.closed_alpha_uV, self.open_alpha_uV, self.adc_noise_rms_uV, self.artifact_uV)
        if any(not np.isfinite(x) or x < 0 for x in vals):
            raise ValueError("Invalid amplitude/noise")
        if not np.isfinite(self.differential_offset_mV):
            raise ValueError("Invalid offset")
        ADCConfig(gain=self.gain, fs_hz=self.fs_hz)


class _Buffers(TypedDict):
    codes: list[CodeArray]
    session: list[NDArray[np.int16]]
    block: list[NDArray[np.int16]]
    condition: list[NDArray[np.int8]]
    time_s: list[FloatArray]
    invalid: list[BoolArray]
    artifact_truth: list[BoolArray]


_DEFAULT_CONFIG = SyntheticConfig()


def generate(cfg: SyntheticConfig = _DEFAULT_CONFIG) -> Recording:
    """Generate sessions independently; filter resets do not cross sessions.

    The visual/brain-like sources are differential voltages in volts. The
    residual line sine (8 uV peak) is already differential contamination, NOT
    a prediction that 100 mV common mode becomes 8 uV. See analog.py separately.
    """
    adc = ADCConfig(gain=cfg.gain, fs_hz=cfg.fs_hz)
    rng = np.random.default_rng(cfg.seed)
    ratio = 16
    high_fs = cfg.fs_hz * ratio
    seconds = cfg.blocks_per_session * cfg.block_seconds
    samples = seconds * cfg.fs_hz
    high_n = seconds * high_fs
    arrays: _Buffers = {
        "codes": [],
        "session": [],
        "block": [],
        "condition": [],
        "time_s": [],
        "invalid": [],
        "artifact_truth": [],
    }
    for session in range(cfg.sessions):
        t: FloatArray = np.arange(high_n) / high_fs
        block: IntArray = (t // cfg.block_seconds).astype(int)
        order: IntArray = np.tile([0, 1], cfg.blocks_per_session // 2)
        rng.shuffle(order)  # conditions are balanced, not perfectly time-locked
        condition: IntArray = order[block]
        scale = rng.uniform(0.85, 1.15)
        phase: FloatArray = rng.uniform(0, 2 * np.pi, cfg.channels)
        alpha: FloatArray = (
            np.where(condition == 1, cfg.closed_alpha_uV, cfg.open_alpha_uV)
            if not cfg.null_effect
            else np.full(high_n, cfg.open_alpha_uV)
        )
        channel_weight = np.linspace(1.0, 0.65, cfg.channels)
        noise: FloatArray = rng.normal(size=(high_n, cfg.channels))
        # Colored background: engineered variability, not physiological noise.
        filtered: object = sosfilt(butter(2, 30, fs=high_fs, output="sos"), noise, axis=0)
        noise = float_array(filtered)
        noise: FloatArray = noise / (np.std(noise, axis=0, keepdims=True) + 1e-30) * 4e-6
        x: FloatArray = (
            scale
            * alpha[:, None]
            * 1e-6
            * channel_weight[None, :]
            * np.sin(2 * np.pi * 10 * t[:, None] + phase[None, :])
        )
        x += 4e-6 * np.sin(2 * np.pi * 6 * t[:, None] + phase[None, :])
        x += 2e-6 * np.sin(2 * np.pi * 20 * t[:, None] + phase[None, :])
        x += 8e-6 * np.sin(2 * np.pi * cfg.line_hz * t[:, None] + phase[None, :] / 2)
        x += noise
        truth = np.zeros(high_n, bool)
        # One event per three blocks. Its time is independent of the condition.
        for bi in range(0, cfg.blocks_per_session, 3):
            center = bi * cfg.block_seconds + rng.uniform(3, cfg.block_seconds - 3)
            pulse: FloatArray = np.exp(-0.5 * ((t - center) / 0.10) ** 2)
            x += (
                cfg.artifact_uV * 1e-6 * pulse[:, None] * np.linspace(1, 0.4, cfg.channels)[None, :]
            )
            truth |= np.abs(t - center) < 0.35
        offset: FloatArray = (cfg.differential_offset_mV * 1e-3) * np.linspace(
            0.8, 1.0, cfg.channels
        )
        x += offset[None, :]
        valid = np.asarray(headroom_valid(x, 2.5, adc), dtype=np.bool_)
        # Clip before averaging to show information loss from excessive offset.
        x: FloatArray = np.clip(x, -adc.full_scale_v, adc.full_scale_v - adc.lsb_v)
        y = behavioral_decimate(x, ratio)
        y += rng.normal(0, cfg.adc_noise_rms_uV * 1e-6, size=y.shape)
        codes_result, qclip_result = quantize(y, adc)
        codes = np.asarray(codes_result, dtype=np.int32)
        qclip = np.asarray(qclip_result, dtype=np.bool_)
        # Mark any over-range point in each output interval; conservative mask
        # does not pretend to predict silicon overload recovery.
        invalid = (~valid).reshape(samples, ratio, cfg.channels).any(axis=1) | qclip
        low_t: FloatArray = np.arange(samples) / cfg.fs_hz
        low_block: IntArray = (low_t // cfg.block_seconds).astype(int)
        arrays["codes"].append(codes)
        arrays["session"].append(np.full(samples, session, dtype=np.int16))
        arrays["block"].append((low_block + session * cfg.blocks_per_session).astype(np.int16))
        arrays["condition"].append(order[low_block].astype(np.int8))
        arrays["time_s"].append(low_t)
        arrays["invalid"].append(np.asarray(invalid, dtype=np.bool_))
        arrays["artifact_truth"].append(
            np.asarray(truth.reshape(samples, ratio).any(axis=1), dtype=np.bool_)
        )
    metadata = _metadata(cfg, adc.lsb_v, 3 * (ratio - 1) / (2 * high_fs), False)
    return {
        "codes": np.concatenate(arrays["codes"]),
        "session": np.concatenate(arrays["session"]),
        "block": np.concatenate(arrays["block"]),
        "condition": np.concatenate(arrays["condition"]),
        "time_s": np.concatenate(arrays["time_s"]),
        "invalid": np.concatenate(arrays["invalid"]),
        "artifact_truth": np.concatenate(arrays["artifact_truth"]),
        "metadata": metadata,
    }


def _metadata(
    cfg: SyntheticConfig, adc_lsb_v: float, delay_s: float, analog_network_applied: bool
) -> SyntheticMetadata:
    return {
        "seed": cfg.seed,
        "channels": cfg.channels,
        "sessions": cfg.sessions,
        "blocks_per_session": cfg.blocks_per_session,
        "block_seconds": cfg.block_seconds,
        "fs_hz": cfg.fs_hz,
        "line_hz": cfg.line_hz,
        "gain": cfg.gain,
        "closed_alpha_uV": cfg.closed_alpha_uV,
        "open_alpha_uV": cfg.open_alpha_uV,
        "adc_noise_rms_uV": cfg.adc_noise_rms_uV,
        "differential_offset_mV": cfg.differential_offset_mV,
        "artifact_uV": cfg.artifact_uV,
        "null_effect": cfg.null_effect,
        "kind": "synthetic_only",
        "adc_lsb_v": adc_lsb_v,
        "surrogate_filter_delay_s": delay_s,
        "analog_network_applied": analog_network_applied,
    }


def parse_metadata(value: object) -> SyntheticMetadata:
    values = read_object(value, "synthetic metadata")
    if text(values, "kind") != "synthetic_only":
        raise ValueError("This loader is for labeled synthetic demos, not live captures")
    names = {field.name for field in fields(SyntheticConfig)}
    missing = names - values.keys()
    if missing:
        raise ValueError(f"Synthetic metadata missing fields: {sorted(missing)}")
    cfg = SyntheticConfig.from_mapping({key: values[key] for key in names})
    return _metadata(
        cfg,
        number(values, "adc_lsb_v"),
        number(values, "surrogate_filter_delay_s"),
        boolean(values, "analog_network_applied"),
    )
