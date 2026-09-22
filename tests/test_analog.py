from dataclasses import replace
import numpy as np
import pytest
from lab.analog import *


def test_matches_closed_form_symmetric_resistor_capacitor_network():
    p=InputNetwork(c_electrode_p=0,c_electrode_n=0)
    f=np.geomspace(.1,100000,100)
    r=p.r_electrode_p+p.r_series_p
    analytic=1/(1+r/p.r_input_p+2j*np.pi*f*r*(p.c_common_p+2*p.c_differential))
    np.testing.assert_allclose(transfer(f,p),analytic,rtol=1e-12)


def test_dc_voltage_divider():
    p=InputNetwork()
    expected=p.r_input_p/(p.r_input_p+p.r_series_p+p.r_electrode_p)
    assert transfer([0],p)[0].real==pytest.approx(expected)


def test_perfect_symmetry_cancels_common_mode():
    h=transfer(np.geomspace(.1,1e5,200),InputNetwork(),'common')
    assert max(abs(h))<1e-12


def test_electrode_and_capacitor_mismatch_create_differential_error():
    p=InputNetwork()
    assert abs(transfer([50],replace(p,r_electrode_n=50000),'common')[0])>1e-5
    assert abs(transfer([50],replace(p,c_common_n=200e-12),'common')[0])>1e-5

@pytest.mark.parametrize('r',[5000,10000,25000,50000,100000])
def test_electrode_sweep_remains_finite(r):
    h=transfer([.1,10,40,50,100000],replace(InputNetwork(),r_electrode_n=r))
    assert np.isfinite(h).all() and np.max(abs(h))<=1.001


def test_netlist_has_same_values_and_no_false_hardware_claim(tmp_path):
    p=replace(InputNetwork(),r_electrode_n=45678)
    t=export_spice(tmp_path/'demo.cir',p,'common').read_text()
    assert 'Ren skinn en 45678' in t
    assert 'NOT A HUMAN-USE SCHEMATIC' in t
    assert 'Vp skinp 0 AC 1' in t and '.end' in t


def test_invalid_components():
    with pytest.raises(ValueError):InputNetwork(r_series_p=-1)
    with pytest.raises(ValueError):transfer([-1])
