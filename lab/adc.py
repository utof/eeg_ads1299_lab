"""ADS1299 behavioral limits, quantization and digital-filter approximations.

TI SBAS499C: §9.3.1.3.1 (PGA headroom), §9.3.2 (digital filter),
§9.5.1 Eq.8 (LSB). This is NOT a transistor model or device certification.
"""
from dataclasses import dataclass
import numpy as np
from scipy.signal import lfilter

MIN_CODE = -(1 << 23)
MAX_CODE = (1 << 23) - 1
GAINS = (1, 2, 4, 6, 8, 12, 24)
RATES = (250, 500, 1000, 2000, 4000, 8000, 16000)

@dataclass(frozen=True)
class ADCConfig:
    gain: int = 24
    vref_v: float = 4.5
    fs_hz: int = 250
    avdd_v: float = 5.0
    avss_v: float = 0.0
    dvdd_v: float = 3.3

    def __post_init__(self):
        if self.gain not in GAINS or self.fs_hz not in RATES:
            raise ValueError("Unsupported ADS1299 gain or sample rate")
        vals = (self.vref_v, self.avdd_v, self.avss_v, self.dvdd_v)
        if not all(np.isfinite(x) for x in vals):
            raise ValueError("ADC configuration must be finite")
        if not (4.75 <= self.avdd_v-self.avss_v <= 5.25):
            raise ValueError("ADS1299 recommended analog rail span is 4.75–5.25 V")
        if not 1.8 <= self.dvdd_v <= 3.6:
            raise ValueError("ADS1299 recommended DVDD is 1.8–3.6 V")
        if not 0 < self.vref_v <= self.avdd_v-self.avss_v:
            raise ValueError("Invalid reference voltage")

    @property
    def full_scale_v(self):
        return self.vref_v / self.gain

    @property
    def lsb_v(self):
        # Equation 8, not the widespread 2**23 - 1 scaling convention.
        return self.vref_v / (self.gain * (1 << 23))


def quantize(v_diff, cfg=ADCConfig()):
    """Nearest-code ideal quantizer; rail flags are conservative.

    Returns int32 codes and a mask where the true input is outside the
    representable ideal code interval. Noise must be supplied separately.
    """
    x = np.asarray(v_diff, dtype=float)
    if not np.all(np.isfinite(x)):
        raise ValueError("Input contains NaN or infinity")
    low, high = MIN_CODE*cfg.lsb_v, MAX_CODE*cfg.lsb_v
    clipped = (x < low) | (x > high)
    codes = np.rint(np.clip(x, low, high)/cfg.lsb_v).astype(np.int32)
    return codes, clipped


def to_volts(codes, cfg=ADCConfig()):
    x = np.asarray(codes)
    if not np.issubdtype(x.dtype, np.integer):
        raise ValueError("ADC codes must be integers")
    if np.any(x < MIN_CODE) or np.any(x > MAX_CODE):
        raise ValueError("Code outside signed 24-bit range")
    return x.astype(float)*cfg.lsb_v


def headroom_valid(v_diff, v_cm, cfg=ADCConfig()):
    """True only within simplified PGA headroom and ADC differential limits.

    This screening model excludes fault conditions, input clamps, stability,
    protection leakage and many other real device effects.
    """
    d, c = np.broadcast_arrays(np.asarray(v_diff, float), np.asarray(v_cm, float))
    margin = cfg.gain*np.abs(d)/2
    return (np.isfinite(d) & np.isfinite(c)
            & (c > cfg.avss_v+0.2+margin)
            & (c < cfg.avdd_v-0.2-margin)
            & (np.abs(d) < cfg.full_scale_v))


def sinc3_magnitude(f_hz, fs_hz=250, fmod_hz=1_024_000):
    """Magnitude of normalized 3rd-order CIC/sinc response at nominal clock.

    For zero denominator at integer multiples of fmod, use the limiting
    value. The useful plotted range here is DC through a few output rates.
    """
    f = np.asarray(f_hz, float)
    if fs_hz not in RATES or fmod_hz <= 0:
        raise ValueError("Invalid sample/modulator rate")
    r = fmod_hz/fs_hz
    if not np.isclose(r, round(r)):
        raise ValueError("Decimation ratio must be integral")
    # Reduce around modulator-rate images before evaluation to avoid 0/0.
    fr = (f + fmod_hz/2) % fmod_hz - fmod_hz/2
    return np.abs(np.sinc(fr/fs_hz)/np.sinc(fr/fmod_hz))**3


def behavioral_decimate(high_rate_v, ratio=16):
    """Three moving averages, then decimation: low-rate sinc3 surrogate.

    Input is already a real-valued analog surrogate, not a delta-sigma
    bitstream. Ratio=16 approximates in-band shape; silicon uses 4096 at
    250 SPS. It does NOT model RF aliasing, modulator noise shaping or startup.
    """
    x = np.asarray(high_rate_v, float)
    if x.ndim not in (1, 2) or len(x) == 0 or not np.all(np.isfinite(x)):
        raise ValueError("Expected nonempty finite time-first array")
    if not isinstance(ratio, int) or ratio < 2:
        raise ValueError("ratio must be an integer >=2")
    y = x.copy()
    taps = np.ones(ratio)/ratio
    for _ in range(3):
        y = lfilter(taps, [1.0], y, axis=0)
    return y[::ratio]
