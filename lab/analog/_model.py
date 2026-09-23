"""Illustrative passive component values; NOT a certified protection design."""

from dataclasses import asdict, dataclass
from typing import Literal, TypeAlias

import numpy as np

Drive: TypeAlias = Literal["differential", "common"]


@dataclass(frozen=True)
class InputNetwork:
    r_electrode_p: float = 10_000
    r_electrode_n: float = 10_000
    c_electrode_p: float = 100e-9
    c_electrode_n: float = 100e-9
    r_series_p: float = 10_000
    r_series_n: float = 10_000
    r_input_p: float = 1e9
    r_input_n: float = 1e9
    c_common_p: float = 100e-12
    c_common_n: float = 100e-12
    c_differential: float = 1e-9

    def __post_init__(self) -> None:
        parameters: dict[str, float] = asdict(self)
        for k, v in parameters.items():
            if not np.isfinite(v) or v < 0 or (k.startswith("r_") and v == 0):
                raise ValueError(f"Invalid component: {k}={v}")
