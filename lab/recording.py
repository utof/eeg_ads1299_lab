"""Synthetic recording persistence and its runtime data contract.

This is deliberately not a live-EEG importer. Arrays have one owner for dtype,
units, label consistency and continuity checks; filtering must not repair them.
"""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from .adc import MAX_CODE, MIN_CODE
from .data_types import BoolArray, Recording
from .signals import parse_metadata
from .validation import read_object, stored_array


def validate_recording(value: object) -> Recording:
    """Return a checked typed view, without copying the numerical buffers."""
    values = read_object(value, "recording")
    try:
        data: Recording = {
            "codes": stored_array(values["codes"], np.int32, 2, "codes"),
            "session": stored_array(values["session"], np.int16, 1, "session"),
            "block": stored_array(values["block"], np.int16, 1, "block"),
            "condition": stored_array(values["condition"], np.int8, 1, "condition"),
            "time_s": stored_array(values["time_s"], np.float64, 1, "time_s"),
            "invalid": stored_array(values["invalid"], np.bool_, 2, "invalid"),
            "artifact_truth": stored_array(values["artifact_truth"], np.bool_, 1, "artifact_truth"),
            "metadata": parse_metadata(values["metadata"]),
        }
    except KeyError as exc:
        raise ValueError(f"Recording missing field: {exc}") from exc
    _validate_alignment(data)
    _validate_blocks(data)
    _validate_sessions(data)
    return data


def _validate_alignment(data: Recording) -> None:
    samples = len(data["codes"])
    cfg = data["metadata"]
    expected = (samples, cfg["channels"])
    if samples == 0 or data["codes"].shape != expected or data["invalid"].shape != expected:
        raise ValueError("codes/invalid: empty recording or channel/sample count mismatch")
    lengths = {
        "session": len(data["session"]),
        "block": len(data["block"]),
        "condition": len(data["condition"]),
        "time_s": len(data["time_s"]),
        "artifact_truth": len(data["artifact_truth"]),
    }
    for name, length in lengths.items():
        if length != samples:
            raise ValueError(f"{name}: sample count mismatch")
    if np.any(data["codes"] < MIN_CODE) or np.any(data["codes"] > MAX_CODE):
        raise ValueError("counts must be signed 24-bit ADC values")
    if not np.all(np.isin(data["condition"], [0, 1])):
        raise ValueError("condition must be 0 or 1")
    if np.any(data["session"] < 0) or np.any(data["session"] >= cfg["sessions"]):
        raise ValueError("session identifier outside metadata range")
    if np.any(data["block"] < 0) or np.any(
        data["block"] >= cfg["sessions"] * cfg["blocks_per_session"]
    ):
        raise ValueError("block identifier outside metadata range")
    if np.any(data["time_s"] < 0):
        raise ValueError("time_s must be nonnegative")


def _validate_blocks(data: Recording) -> None:
    for block in np.unique(data["block"]):
        mask: BoolArray = data["block"] == block
        indices = np.flatnonzero(mask)
        if not np.all(np.diff(indices) == 1):
            raise ValueError("Noncontiguous block: identifiers must not be reused")
        if len(np.unique(data["session"][indices])) != 1:
            raise ValueError("A block must belong to exactly one session")
        if len(np.unique(data["condition"][indices])) != 1:
            raise ValueError("A block must contain exactly one condition")


def _validate_sessions(data: Recording) -> None:
    period = 1.0 / data["metadata"]["fs_hz"]
    for session in np.unique(data["session"]):
        mask: BoolArray = data["session"] == session
        indices = np.flatnonzero(mask)
        if not np.all(np.diff(indices) == 1):
            raise ValueError("Noncontiguous session: identifiers must not be reused")
        steps = np.diff(data["time_s"][indices])
        if not np.allclose(steps, period, rtol=1e-9, atol=1e-9):
            raise ValueError("time_s discontinuity: synthetic samples must be uniformly spaced")


def load_data(path: str | Path) -> Recording:
    try:
        with np.load(path, allow_pickle=False) as archive:
            names = (
                "codes",
                "session",
                "block",
                "condition",
                "time_s",
                "invalid",
                "artifact_truth",
            )
            values: dict[str, object] = {name: archive[name] for name in names}
            raw: object = archive["metadata_json"]
            if not isinstance(raw, np.ndarray) or raw.ndim != 0 or raw.dtype.kind != "U":
                raise ValueError("metadata_json must be a scalar Unicode string")
            values["metadata"] = json.loads(str(raw))
    except KeyError as exc:
        raise ValueError(f"Recording archive missing field: {exc}") from exc
    return validate_recording(values)


def save_data(data: Recording, path: str | Path) -> None:
    data = validate_recording(data)
    path = Path(path)
    if not str(path).endswith(".npz"):
        path = Path(str(path) + ".npz")
    path.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".recording-", dir=path.parent) as directory:
        staged = Path(directory) / "recording.npz"
        np.savez_compressed(
            staged,
            codes=data["codes"],
            session=data["session"],
            block=data["block"],
            condition=data["condition"],
            time_s=data["time_s"],
            invalid=data["invalid"],
            artifact_truth=data["artifact_truth"],
            metadata_json=np.array(json.dumps(data["metadata"], allow_nan=False)),
        )
        staged.replace(path)
