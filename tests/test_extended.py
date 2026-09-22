from pathlib import Path
import json
import subprocess
import sys
import numpy as np
import pytest
from lab.adc import ADCConfig,quantize
from lab.protocol import Packet, FLAG_SYNTHETIC
from lab.acquisition import decode_capture
from lab.inspect_capture import inspect_capture
from lab.signals import SyntheticConfig,generate
from lab.dsp import analyze

@pytest.mark.parametrize('channels,line,fs', [(6,60,250),(8,50,500)])
def test_other_variants_end_to_end(channels,line,fs):
    data=generate(SyntheticConfig(channels=channels,line_hz=line,fs_hz=fs,sessions=3,blocks_per_session=4))
    report,_=analyze(data,permutations=0)
    assert report['balanced_accuracy']>.8
    assert len(report['feature_names'])==3*channels

def test_null_effect_is_not_a_perfect_decoder():
    # A negative control, not a confidence bound on arbitrary datasets.
    report,_=analyze(generate(SyntheticConfig(null_effect=True)),permutations=0)
    assert .7 < report['closed_open_alpha_ratio'] < 1.3
    assert .25 < report['balanced_accuracy'] < .75


def make_capture(tmp_path,drop_every=0):
    cfg=ADCConfig();t=np.arange(8*cfg.fs_hz)/cfg.fs_hz
    codes,_=quantize(10e-6*np.sin(2*np.pi*10*t),cfg)
    raw=tmp_path/'test.bin'
    with raw.open('wb') as f:
        for i,code in enumerate(codes):
            if drop_every and i and i%drop_every==0:continue
            f.write(Packet(i,i*4000,(int(code),)*4,flags=FLAG_SYNTHETIC).encode())
    csv=tmp_path/'test.csv'
    decode_capture(raw,csv)
    return csv


def test_capture_inspection_preserves_units(tmp_path):
    report=inspect_capture(make_capture(tmp_path),tmp_path/'inspect')
    assert report['four_second_spectral_windows']==2
    assert report['peak_0p5_40_Hz_by_channel']==[10.]*4
    assert report['rms_0p5_40_Hz_uV_by_channel'][0]==pytest.approx(10/np.sqrt(2),rel=.002)
    assert report['rail_code_samples_by_channel']==[0]*4


def test_capture_inspection_does_not_bridge_gaps(tmp_path):
    report=inspect_capture(make_capture(tmp_path,drop_every=100),tmp_path/'inspect')
    assert report['gap_boundaries']==19
    assert report['four_second_spectral_windows']==0
    assert 'not_computed' in report['spectral_status']


def test_capture_inspection_requires_metadata(tmp_path):
    p=tmp_path/'missing.csv';p.write_text('')
    with pytest.raises(ValueError,match='metadata JSON'):inspect_capture(p,tmp_path/'inspect')


def test_firmware_is_bench_gated_and_halt_powers_down():
    root=Path(__file__).resolve().parents[1]
    config=(root/'firmware/esp32_ads1299_bench/board_config.h').read_text()
    source=(root/'firmware/esp32_ads1299_bench/esp32_ads1299_bench.ino').read_text()
    assert 'BOARD_PROFILE_REVIEWED=false' in config.replace(' ', '')
    fail=source[source.index('void fail'):source.index('void selectChip')]
    assert 'digitalWrite(PIN_PWDN,LOW)' in fail
    assert 'USE_INTERNAL_TEST?0x65:0x61' in source


def test_cli_rejects_negative_permutation_count(tmp_path):
    root=Path(__file__).resolve().parents[1]
    result=subprocess.run([sys.executable,str(root/'run_lab.py'),'demo','--permutations','-1','--out',str(tmp_path)],capture_output=True,text=True)
    assert result.returncode==2
    assert 'permutations must be' in result.stderr
