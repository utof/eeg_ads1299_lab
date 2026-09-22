"""Bench capture quality report. Never interpolate gaps into a spectrum."""
import csv
import json
from pathlib import Path
import numpy as np
from .dsp import psd


def inspect_capture(csv_path, out_dir):
    csv_path, out_dir = Path(csv_path), Path(out_dir)
    metadata_path = csv_path.with_suffix('.json')
    if not metadata_path.exists():
        raise ValueError('Keep the metadata JSON created by decode beside this CSV')
    metadata = json.loads(metadata_path.read_text())
    fs, n = int(metadata['fs_hz']), int(metadata['channels'])
    with csv_path.open(newline='') as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError('Empty capture CSV')
    x = np.array([[float(r[f'ch{c+1}_uV']) for c in range(n)] for r in rows])
    counts = np.array([[int(r[f'ch{c+1}_count']) for c in range(n)] for r in rows])
    times = np.array([float(r['elapsed_s']) for r in rows])
    sequence = np.array([int(r['sequence']) for r in rows], dtype=np.uint64)
    if not np.all(np.isfinite(x)) or not np.all(np.isfinite(times)):
        raise ValueError('Nonfinite capture data')
    # Both counters and device timing must remain continuous. uint32 wrap is OK.
    ds = (sequence[1:].astype(np.int64)-sequence[:-1].astype(np.int64)) % (2**32)
    dt = np.diff(times)
    boundaries = np.flatnonzero((ds != 1) | (np.abs(dt-1/fs) > max(.0005,.1/fs)))+1
    runs = np.split(np.arange(len(x)), boundaries)
    spectra = []
    segment_size = 4*fs
    for run in runs:
        for offset in range(0, len(run)-segment_size+1, segment_size):
            idx = run[offset:offset+segment_size]
            f, power = psd(x[idx]*1e-6, fs)
            spectra.append(power)
    result = {
        'kind': 'bench_signal_quality_not_human_EEG_validation',
        'source': csv_path.name,
        'recording_mode': metadata['recording_mode'],
        'samples': len(x), 'channels': n, 'fs_hz': fs,
        'assumed_vref_v': metadata['assumed_vref_v'],
        'gap_boundaries': len(boundaries),
        'longest_contiguous_seconds': max(map(len,runs))/fs,
        'mean_uV_by_channel': np.mean(x,axis=0).tolist(),
        'raw_peak_to_peak_uV_by_channel': np.ptp(x,axis=0).tolist(),
        'rail_code_samples_by_channel': np.sum((counts == -(2**23)) | (counts == 2**23-1),axis=0).tolist(),
        'four_second_spectral_windows': len(spectra),
        'cautions': ['ADC rail-code check cannot detect every analog common-mode violation.',
                     'Internal-short spectra are not electrode-connected system noise.',
                     'No gaps interpolated; incomplete four-second windows excluded.',
                     'DC offsets are reported before detrending. Spectrum alone hides DC.',
                     'Voltage scale uses supplied reference and gain, not bench calibration.'],
    }
    out_dir.mkdir(parents=True,exist_ok=True)
    if spectra:
        power=np.mean(spectra,axis=0)
        np.savetxt(out_dir/'spectrum.csv',np.column_stack((f,power*1e12)),delimiter=',',
                   header='frequency_hz,'+','.join(f'ch{c+1}_uV2_per_Hz' for c in range(n)),comments='')
        inband=(f>=.5)&(f<=40)
        result['rms_0p5_40_Hz_uV_by_channel']=np.sqrt(np.trapezoid(power[inband],f[inband],axis=0)*1e12).tolist()
        result['peak_0p5_40_Hz_by_channel']=f[inband][np.argmax(power[inband],axis=0)].tolist()
    else:
        result['spectral_status']='not_computed: need at least one uninterrupted four-second interval'
    (out_dir/'quality_report.json').write_text(json.dumps(result,indent=2))
    return result
