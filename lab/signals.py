"""Known-ground-truth synthetic recordings; deliberately not a brain model."""
from dataclasses import dataclass, asdict
import numpy as np
from scipy.signal import butter, sosfilt
from .adc import ADCConfig, behavioral_decimate, headroom_valid, quantize

@dataclass(frozen=True)
class SyntheticConfig:
    seed:int=42
    channels:int=4
    sessions:int=6
    blocks_per_session:int=8
    block_seconds:int=12
    fs_hz:int=250
    line_hz:int=50
    gain:int=24
    closed_alpha_uV:float=18.
    open_alpha_uV:float=5.
    adc_noise_rms_uV:float=.25  # illustrative output-referred-to-input RMS, NOT a TI guarantee
    differential_offset_mV:float=30.
    artifact_uV:float=200.
    null_effect:bool=False

    def __post_init__(self):
        if self.channels not in (4,6,8): raise ValueError('channels must be 4, 6 or 8')
        if self.sessions<3: raise ValueError('At least 3 independent synthetic sessions')
        if self.blocks_per_session<4 or self.blocks_per_session%2:
            raise ValueError('Use an even number of blocks, >=4')
        if self.block_seconds<12: raise ValueError('Use blocks >=12 seconds')
        if self.fs_hz not in (250,500): raise ValueError('Demo supports 250 or 500 SPS')
        if self.line_hz not in (50,60): raise ValueError('line_hz must be 50 or 60')
        vals=(self.closed_alpha_uV,self.open_alpha_uV,self.adc_noise_rms_uV,self.artifact_uV)
        if any(not np.isfinite(x) or x<0 for x in vals): raise ValueError('Invalid amplitude/noise')
        if not np.isfinite(self.differential_offset_mV): raise ValueError('Invalid offset')
        ADCConfig(gain=self.gain,fs_hz=self.fs_hz)


def generate(cfg=SyntheticConfig()):
    """Generate sessions independently; filter resets do not cross sessions.

    The visual/brain-like sources are differential voltages in volts. The
    residual line sine (8 uV peak) is already differential contamination, NOT
    a prediction that 100 mV common mode becomes 8 uV. See analog.py separately.
    """
    adc=ADCConfig(gain=cfg.gain,fs_hz=cfg.fs_hz)
    rng=np.random.default_rng(cfg.seed)
    ratio=16; high_fs=cfg.fs_hz*ratio
    seconds=cfg.blocks_per_session*cfg.block_seconds
    samples=seconds*cfg.fs_hz
    high_n=seconds*high_fs
    arrays={k:[] for k in ('codes','session','block','condition','time_s','invalid','artifact_truth')}
    for session in range(cfg.sessions):
        t=np.arange(high_n)/high_fs
        block=(t//cfg.block_seconds).astype(int)
        order=np.tile([0,1],cfg.blocks_per_session//2)
        rng.shuffle(order)  # conditions are balanced, not perfectly time-locked
        condition=order[block]
        scale=rng.uniform(.85,1.15)
        phase=rng.uniform(0,2*np.pi,cfg.channels)
        alpha=(np.where(condition==1,cfg.closed_alpha_uV,cfg.open_alpha_uV)
               if not cfg.null_effect else np.full(high_n,cfg.open_alpha_uV))
        channel_weight=np.linspace(1.,.65,cfg.channels)
        noise=rng.normal(size=(high_n,cfg.channels))
        # Colored background: engineered variability, not physiological noise.
        noise=sosfilt(butter(2,30,fs=high_fs,output='sos'),noise,axis=0)
        noise=noise/(np.std(noise,axis=0,keepdims=True)+1e-30)*4e-6
        x=(scale*alpha[:,None]*1e-6*channel_weight[None,:]
           *np.sin(2*np.pi*10*t[:,None]+phase[None,:]))
        x+=4e-6*np.sin(2*np.pi*6*t[:,None]+phase[None,:])
        x+=2e-6*np.sin(2*np.pi*20*t[:,None]+phase[None,:])
        x+=8e-6*np.sin(2*np.pi*cfg.line_hz*t[:,None]+phase[None,:]/2)
        x+=noise
        truth=np.zeros(high_n,bool)
        # One event per three blocks. Its time is independent of the condition.
        for bi in range(0,cfg.blocks_per_session,3):
            center=bi*cfg.block_seconds+rng.uniform(3,cfg.block_seconds-3)
            pulse=np.exp(-.5*((t-center)/.10)**2)
            x+=cfg.artifact_uV*1e-6*pulse[:,None]*np.linspace(1,.4,cfg.channels)[None,:]
            truth |= np.abs(t-center)<.35
        offset=(cfg.differential_offset_mV*1e-3)*np.linspace(.8,1.,cfg.channels)
        x+=offset[None,:]
        valid=headroom_valid(x,2.5,adc)
        # Clip before averaging to show information loss from excessive offset.
        x=np.clip(x,-adc.full_scale_v,adc.full_scale_v-adc.lsb_v)
        y=behavioral_decimate(x,ratio)
        y+=rng.normal(0,cfg.adc_noise_rms_uV*1e-6,size=y.shape)
        codes,qclip=quantize(y,adc)
        # Mark any over-range point in each output interval; conservative mask
        # does not pretend to predict silicon overload recovery.
        invalid=(~valid).reshape(samples,ratio,cfg.channels).any(axis=1)|qclip
        low_t=np.arange(samples)/cfg.fs_hz
        low_block=(low_t//cfg.block_seconds).astype(int)
        arrays['codes'].append(codes)
        arrays['session'].append(np.full(samples,session,dtype=np.int16))
        arrays['block'].append((low_block+session*cfg.blocks_per_session).astype(np.int16))
        arrays['condition'].append(order[low_block].astype(np.int8))
        arrays['time_s'].append(low_t)
        arrays['invalid'].append(invalid)
        arrays['artifact_truth'].append(truth.reshape(samples,ratio).any(axis=1))
    out={k:np.concatenate(v) for k,v in arrays.items()}
    out['metadata']=asdict(cfg)
    out['metadata']['kind']='synthetic_only'
    out['metadata']['adc_lsb_v']=adc.lsb_v
    out['metadata']['surrogate_filter_delay_s']=3*(ratio-1)/(2*high_fs)
    out['metadata']['analog_network_applied']=False
    return out
