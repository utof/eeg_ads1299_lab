import numpy as np
import pytest
from lab.adc import *

@pytest.mark.parametrize('gain',GAINS)
def test_quantizer_round_trip_and_bounds(gain):
    c=ADCConfig(gain=gain)
    rng=np.random.default_rng(8)
    x=rng.uniform(-.9,.9,3000)*c.full_scale_v
    codes,clipped=quantize(x,c)
    assert not clipped.any()
    assert np.max(np.abs(to_volts(codes,c)-x))<=c.lsb_v*.500001


def test_lsb_is_datasheet_equation_8():
    c=ADCConfig()
    assert c.lsb_v==pytest.approx(2.2351741790771484e-8)
    assert c.full_scale_v==.1875


def test_signed_endpoints_and_clipping():
    c=ADCConfig();x=np.array([-.5,-.1875,0,.1875,.5])
    codes,clipped=quantize(x,c)
    assert list(codes)==[MIN_CODE,MIN_CODE,0,MAX_CODE,MAX_CODE]
    assert list(clipped)==[True,False,False,True,True]

@pytest.mark.parametrize('kw',[{'gain':3},{'fs_hz':256},{'avdd_v':3.3},{'dvdd_v':5},{'vref_v':-1},{'vref_v':float('nan')}])
def test_bad_configuration(kw):
    with pytest.raises(ValueError):ADCConfig(**kw)

@pytest.mark.parametrize('x',[[float('nan')],[float('inf')]])
def test_bad_input(x):
    with pytest.raises(ValueError):quantize(x)


def test_headroom_and_offset_are_checked_before_software_filtering():
    c=ADCConfig()
    assert headroom_valid(.03,2.5,c)
    assert not headroom_valid(.2,2.5,c)
    assert not headroom_valid(.1,.5,c)
    assert headroom_valid(.2,2.5,ADCConfig(gain=12))


def test_sinc_dc_zero_and_inband_droop():
    h=sinc3_magnitude([0,10,40,250])
    assert h[0]==pytest.approx(1)
    assert .99<h[1]<1
    assert .87<h[2]<.9
    assert h[3]<1e-20


def test_surrogate_sinc_matches_inband_amplitude():
    fs=250;ratio=16;f=40
    t=np.arange(40000)/(fs*ratio)
    y=behavioral_decimate(np.sin(2*np.pi*f*t),ratio)[500:]
    measured=np.std(y)*np.sqrt(2)
    expected=float(sinc3_magnitude(f,fs))
    assert measured==pytest.approx(expected,rel=.002)
