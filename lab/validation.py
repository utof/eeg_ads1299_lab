"""Runtime boundaries for JSON primitives and scientific-library array results."""

from collections.abc import Mapping
from math import isfinite
from typing import TypeVar

import numpy as np
from numpy.typing import NDArray

from .data_types import FloatArray

Scalar = TypeVar("Scalar", bound=np.generic)


def read_object(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{label}: expected an object")
    items: dict[object, object] = value
    result: dict[str, object] = {}
    for key, item in items.items():
        if not isinstance(key, str):
            raise ValueError(f"{label}: expected string keys")
        result[key] = item
    return result


def integer(values: Mapping[str, object], key: str, default: int | None = None) -> int:
    value = values.get(key, default)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{key}: expected an integer")
    return value


def number(values: Mapping[str, object], key: str, default: float | None = None) -> float:
    value = values.get(key, default)
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not isfinite(value):
        raise ValueError(f"{key}: expected a finite number")
    return float(value)


def boolean(values: Mapping[str, object], key: str, default: bool | None = None) -> bool:
    value = values.get(key, default)
    if not isinstance(value, bool):
        raise ValueError(f"{key}: expected a boolean")
    return value


def text(values: Mapping[str, object], key: str) -> str:
    value = values.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{key}: expected text")
    return value


def float_array(value: object) -> FloatArray:
    """Validate a third-party result rather than propagating its untyped return.

    Used only for real-valued SciPy filter results whose dtype is part of our
    contract. No shape claim is made here; the calling algorithm owns shape.
    """
    if not isinstance(value, np.ndarray) or value.dtype != np.dtype(np.float64):
        raise ValueError("Expected a float64 array from the numerical backend")
    return np.asarray(value, dtype=np.float64)


def stored_array(value: object, dtype: type[Scalar], ndim: int, name: str) -> NDArray[Scalar]:
    """Check a stored array before assigning its precise static dtype."""
    if not isinstance(value, np.ndarray) or value.dtype != np.dtype(dtype) or value.ndim != ndim:
        raise ValueError(f"{name}: unexpected dtype or dimensions")
    if not np.all(np.isfinite(value)):
        raise ValueError(f"{name}: nonfinite array")
    return np.asarray(value, dtype=dtype)
