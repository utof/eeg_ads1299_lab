"""Reproducible demo outputs. All plot titles label synthetic/model results."""
from pathlib import Path
from dataclasses import asdict
import csv
import json
import numpy as np
from .signals import generate,SyntheticConfig
from .adc import ADCConfig,to_volts,sinc3_magnitude
from .dsp import analyze,psd
from .analog import InputNetwork,transfer


def save_data(data,path):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    arrays={k:v for k,v in data.items() if k!='metadata'}
    np.savez_compressed(path,**arrays,metadata_json=np.array(json.dumps(data['metadata'])))


def load_data(path):
    with np.load(path,allow_pickle=False) as f:
        out={k:f[k] for k in f.files if k!='metadata_json'}
        out['metadata']=json.loads(str(f['metadata_json']))
    if out['metadata'].get('kind')!='synthetic_only':
        raise ValueError('This loader is for labeled synthetic demos, not live captures')
    return out


def make_plots(data,report,rows,out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    cfg=data['metadata'];fs=cfg['fs_hz']
    x=to_volts(data['codes'],ADCConfig(gain=cfg['gain'],fs_hz=fs))*1e6
    # Independent figures, matplotlib default colors/style.
    fig,ax=plt.subplots(figsize=(10,4.6),layout='constrained')
    idx=(data['session']==0)&(data['time_s']>=2)&(data['time_s']<26)
    ax.plot(data['time_s'][idx],x[idx,0]-np.median(x[idx,0]),linewidth=.75)
    ax.set(xlabel='Time within synthetic session (s)',ylabel='Channel 1, DC removed (µV)',
           title='Synthetic recording: brain-like waves, residual line noise, artifacts')
    fig.savefig(out/'synthetic_trace.png',dpi=155);plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,4.8),layout='constrained')
    # Average PSDs of individual clean 4-s windows; never concatenate separated blocks.
    for label,name in [(0,'Eyes-open label'),(1,'Eyes-closed label')]:
        spectra=[]
        for row in rows:
            if not row['accepted'] or row['condition']!=label:continue
            idx=np.flatnonzero((data['session']==row['session']) &
                              (data['time_s']>=row['start_s']) &
                              (data['time_s']<row['start_s']+4))
            f,p=psd(x[idx,0],fs);spectra.append(p)
        ax.semilogy(f,np.mean(spectra,axis=0),label=name)
    ax.set(xlim=(1,65),xlabel='Frequency (Hz)',ylabel='Power spectral density (µV²/Hz)',
           title='Synthetic ground truth: deliberately stronger 10-Hz activity when “closed”')
    ax.legend();fig.savefig(out/'synthetic_psd.png',dpi=155);plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,4.8),layout='constrained')
    groups=report['folds'];sessions=[r['held_out_session'] for r in groups]
    scores=[r['balanced_accuracy'] for r in groups]
    ax.bar(sessions,scores,label='Session-held-out toy classifier')
    ax.axhline(.5,linestyle='--',label='Two-class chance reference')
    ax.set(ylim=(0,1.08),xlabel='Held-out synthetic session',ylabel='Balanced accuracy',
           title='Software plumbing test — not demonstrated brain-decoding performance')
    ax.legend(loc='lower right');fig.savefig(out/'synthetic_ml.png',dpi=155);plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,4.8),layout='constrained')
    f=np.linspace(.1,125,700)
    ax.plot(f,20*np.log10(np.maximum(sinc3_magnitude(f,fs),1e-14)),label='Nominal ADS1299 sinc³ shape')
    ax.plot(f,20*np.log10(np.maximum(np.abs(transfer(f,InputNetwork())),1e-14)),label='Illustrative passive input network')
    ax.set(xlabel='Frequency (Hz)',ylabel='Gain (dB)',ylim=(-15,1),
           title='Two different filters: external passive network vs. ADC digital filter')
    ax.legend();fig.savefig(out/'model_filter_response.png',dpi=155);plt.close(fig)


def run_demo(out,cfg=SyntheticConfig(),permutations=20,plots=True):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    data=generate(cfg)
    report,rows=analyze(data,permutations)
    report['configuration']=asdict(cfg)
    save_data(data,out/'synthetic_recording.npz')
    (out/'analysis_report.json').write_text(json.dumps(report,indent=2))
    keys=sorted(set().union(*(r.keys() for r in rows)))
    with (out/'epoch_quality.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader();writer.writerows(rows)
    with (out/'events.csv').open('w',newline='') as f:
        writer=csv.writer(f);writer.writerow(['session','block','onset_s','duration_s','condition'])
        for block in np.unique(data['block']):
            idx=np.flatnonzero(data['block']==block)[0]
            writer.writerow([int(data['session'][idx]),int(block),float(data['time_s'][idx]),
                             cfg.block_seconds,'eyes_closed' if data['condition'][idx] else 'eyes_open'])
    if plots: make_plots(data,report,rows,out)
    return report
