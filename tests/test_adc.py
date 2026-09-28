from typing import TypedDict

import numpy as np
import pytest

from lab.adc import (
    GAINS,
    MAX_CODE,
    MIN_CODE,
    ADCConfig,
    behavioral_decimate,
    headroom_valid,
    quantize,
    sinc3_magnitude,
    to_volts,
)


class ADCConfigOverrides(TypedDict, total=False):
    gain: int
    fs_hz: int
    avdd_v: float
    dvdd_v: float
    vref_v: float


@pytest.mark.parametrize("gain", GAINS)
def test_quantizer_round_trip_and_bounds(gain: int) -> None:
    c = ADCConfig(gain=gain)
    rng = np.random.default_rng(8)
    x = rng.uniform(-0.9, 0.9, 3000) * c.full_scale_v
    codes, clipped = quantize(x, c)
    assert not clipped.any()
    assert np.max(np.abs(to_volts(codes, c) - x)) <= c.lsb_v * 0.500001


def test_lsb_is_datasheet_equation_8() -> None:
    c = ADCConfig()
    assert c.lsb_v == pytest.approx(2.2351741790771484e-8)
    assert c.full_scale_v == 0.1875


def test_signed_endpoints_and_clipping() -> None:
    c = ADCConfig()
    x = np.array([-0.5, -0.1875, 0, 0.1875, 0.5])
    codes, clipped = quantize(x, c)
    assert list(np.atleast_1d(codes)) == [MIN_CODE, MIN_CODE, 0, MAX_CODE, MAX_CODE]
    assert list(np.atleast_1d(clipped)) == [True, False, False, True, True]


@pytest.mark.parametrize(
    "kw",
    [
        {"gain": 3},
        {"fs_hz": 256},
        {"avdd_v": 3.3},
        {"dvdd_v": 5},
        {"vref_v": -1},
        {"vref_v": float("nan")},
    ],
)
def test_bad_configuration(kw: ADCConfigOverrides) -> None:
    with pytest.raises(ValueError):
        ADCConfig(
            gain=kw.get("gain", 24),
            fs_hz=kw.get("fs_hz", 250),
            avdd_v=kw.get("avdd_v", 5.0),
            dvdd_v=kw.get("dvdd_v", 3.3),
            vref_v=kw.get("vref_v", 4.5),
        )


@pytest.mark.parametrize("x", [[float("nan")], [float("inf")]])
def test_bad_input(x: list[float]) -> None:
    with pytest.raises(ValueError):
        quantize(x)


def test_headroom_and_offset_are_checked_before_software_filtering() -> None:
    c = ADCConfig()
    assert headroom_valid(0.03, 2.5, c)
    assert not headroom_valid(0.2, 2.5, c)
    assert not headroom_valid(0.1, 0.5, c)
    assert headroom_valid(0.2, 2.5, ADCConfig(gain=12))


def test_sinc_dc_zero_and_inband_droop() -> None:
    h = np.atleast_1d(sinc3_magnitude([0, 10, 40, 250]))
    assert h[0] == pytest.approx(1)
    assert 0.99 < h[1] < 1
    assert 0.87 < h[2] < 0.9
    assert h[3] < 1e-20


def test_surrogate_sinc_matches_inband_amplitude() -> None:
    fs = 250
    ratio = 16
    f = 40
    t = np.arange(40000) / (fs * ratio)
    y = behavioral_decimate(np.sin(2 * np.pi * f * t), ratio)[500:]
    measured: np.float64 = np.std(y) * np.sqrt(2)
    expected = float(sinc3_magnitude(f, fs))
    assert measured == pytest.approx(expected, rel=0.002)
