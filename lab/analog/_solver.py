"""Independent Kirchhoff nodal solution, not an ADS1299 silicon model."""

import numpy as np
from numpy.typing import ArrayLike

from ..data_types import ComplexArray
from ._model import Drive, InputNetwork

_DEFAULT_CONFIG = InputNetwork()


def transfer(
    freq_hz: ArrayLike, network: InputNetwork = _DEFAULT_CONFIG, drive: Drive = "differential"
) -> ComplexArray:
    """Return differential input voltage / unit differential or common drive.

    CM drive means both skin sources = 1 V relative to local analog midpoint.
    Differential drive means +0.5 V / -0.5 V. No body-bias feedback is assumed.
    """
    f = np.atleast_1d(np.asarray(freq_hz, float))
    if not np.all(np.isfinite(f)) or np.any(f < 0):
        raise ValueError("Frequencies must be finite and nonnegative")
    if drive not in ("differential", "common"):
        raise ValueError("Unknown drive")
    p = network
    s: ComplexArray = 2j * np.pi * f
    zp: ComplexArray = p.r_series_p + 1 / (1 / p.r_electrode_p + s * p.c_electrode_p)
    zn: ComplexArray = p.r_series_n + 1 / (1 / p.r_electrode_n + s * p.c_electrode_n)
    yp: ComplexArray = 1 / zp
    yn: ComplexArray = 1 / zn
    yg_p = 1 / p.r_input_p + s * p.c_common_p
    yg_n = 1 / p.r_input_n + s * p.c_common_n
    yd = s * p.c_differential
    a = np.empty((len(f), 2, 2), complex)
    a[:, 0, 0], a[:, 1, 1] = yp + yg_p + yd, yn + yg_n + yd
    a[:, 0, 1] = a[:, 1, 0] = -yd
    vp, vn = (0.5, -0.5) if drive == "differential" else (1.0, 1.0)
    b = np.column_stack([yp * vp, yn * vn])
    x = np.asarray(np.linalg.solve(a, b[..., None])[..., 0], dtype=np.complex128)
    return x[:, 0] - x[:, 1]
