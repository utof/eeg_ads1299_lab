"""Linear two-node electrode/input network, solved from Kirchhoff's laws.

This is our own frequency-domain nodal solver, NOT ngspice and NOT an
ADS1299 macromodel. The .cir export represents the SAME passive network.
All component values are illustrative. None is a certified protection value.
"""
from dataclasses import dataclass, asdict, replace
from pathlib import Path
import json
import shutil
import subprocess
import numpy as np

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

    def __post_init__(self):
        for k,v in asdict(self).items():
            if not np.isfinite(v) or v < 0 or (k.startswith('r_') and v == 0):
                raise ValueError(f"Invalid component: {k}={v}")


def transfer(freq_hz, network=InputNetwork(), drive='differential'):
    """Return differential input voltage / unit differential or common drive.

    CM drive means both skin sources = 1 V relative to local analog midpoint.
    Differential drive means +0.5 V / -0.5 V. No body-bias feedback is assumed.
    """
    f = np.atleast_1d(np.asarray(freq_hz, float))
    if not np.all(np.isfinite(f)) or np.any(f < 0):
        raise ValueError("Frequencies must be finite and nonnegative")
    if drive not in ('differential', 'common'):
        raise ValueError("Unknown drive")
    p = network
    s = 2j*np.pi*f
    zp = p.r_series_p + 1/(1/p.r_electrode_p + s*p.c_electrode_p)
    zn = p.r_series_n + 1/(1/p.r_electrode_n + s*p.c_electrode_n)
    yp, yn = 1/zp, 1/zn
    yg_p = 1/p.r_input_p + s*p.c_common_p
    yg_n = 1/p.r_input_n + s*p.c_common_n
    yd = s*p.c_differential
    a = np.empty((len(f),2,2), complex)
    a[:,0,0], a[:,1,1] = yp+yg_p+yd, yn+yg_n+yd
    a[:,0,1] = a[:,1,0] = -yd
    vp,vn = (0.5,-0.5) if drive=='differential' else (1.,1.)
    b = np.column_stack([yp*vp, yn*vn])
    x = np.linalg.solve(a,b[...,None])[...,0]
    return x[:,0]-x[:,1]


def export_spice(path, network=InputNetwork(), drive='differential'):
    """Write a self-contained AC netlist; only passive parts and sources."""
    if drive not in ('differential','common'):
        raise ValueError("Unknown drive")
    path = Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    p = network
    # Negative amplitude expressed as 180-degree phase, portable AC syntax.
    sources = ('AC 0.5', 'AC 0.5 180') if drive=='differential' else ('AC 1','AC 1')
    text = f'''Illustrative EEG passive input network -- NOT A HUMAN-USE SCHEMATIC
* 0 denotes local analog midpoint for small-signal AC, NOT protective earth.
* No ADS1299 silicon, input clamps, body-bias loop, or safety analysis included.
Vp skinp 0 {sources[0]}
Vn skinn 0 {sources[1]}
Rep skinp ep {p.r_electrode_p:.12g}
Cep skinp ep {p.c_electrode_p:.12g}
Ren skinn en {p.r_electrode_n:.12g}
Cen skinn en {p.c_electrode_n:.12g}
Rsp ep inp {p.r_series_p:.12g}
Rsn en inn {p.r_series_n:.12g}
Rip inp 0 {p.r_input_p:.12g}
Rin inn 0 {p.r_input_n:.12g}
Ccp inp 0 {p.c_common_p:.12g}
Ccn inn 0 {p.c_common_n:.12g}
Cd inp inn {p.c_differential:.12g}
.control
set wr_singlescale
set wr_vecnames
set numdgt=15
ac dec 40 0.1 100000
let h = v(inp)-v(inn)
let hr = real(h)
let hi = imag(h)
wrdata ac.txt hr hi
quit
.endc
.end
'''
    path.write_text(text)
    return path


def run_ngspice(netlist, output_dir):
    """Execute external ngspice or raise; absence is never silently a pass."""
    exe = shutil.which('ngspice')
    if not exe:
        raise RuntimeError("ngspice executable is absent; install it, then rerun --require-ngspice")
    output_dir=Path(output_dir).resolve()
    output_dir.mkdir(parents=True,exist_ok=True)
    netlist=Path(netlist).resolve()
    result=subprocess.run([exe,'-b',str(netlist)],cwd=output_dir,
                          capture_output=True,text=True,timeout=45,check=False)
    (output_dir/'ngspice.log').write_text(result.stdout+'\n'+result.stderr)
    if result.returncode != 0 or not (output_dir/'ac.txt').exists():
        raise RuntimeError(f"ngspice failed: see {output_dir/'ngspice.log'}")
    data=np.loadtxt(output_dir/'ac.txt',skiprows=1)
    if data.ndim!=2 or data.shape[1]!=3 or not np.all(np.isfinite(data)):
        raise RuntimeError("Unexpected ngspice wrdata format (expected f, real, imag)")
    return data[:,0], data[:,1]+1j*data[:,2]


def circuit_report(out, seed=42, require_ngspice=False):
    out=Path(out); out.mkdir(parents=True,exist_ok=True)
    f=np.geomspace(.1,100_000,241)
    balanced=InputNetwork()
    mismatch=replace(balanced,r_electrode_n=50_000)
    hd=transfer(f,balanced)
    hc=transfer(f,mismatch,'common')
    rows=np.column_stack([f,np.abs(hd),np.abs(hc)])
    np.savetxt(out/'circuit_response.csv',rows,delimiter=',',
               header='frequency_hz,differential_gain,common_to_differential_gain',comments='')
    rng=np.random.default_rng(seed)
    trial=[]
    for _ in range(200):
        # Independent uniform tolerances; this is an assumption, not measured yield.
        d=asdict(balanced)
        for k in d:
            tolerance=.01 if k.startswith('r_') else .05
            d[k]*=rng.uniform(1-tolerance,1+tolerance)
        n=InputNetwork(**d)
        trial.append([abs(transfer([10],n)[0]),abs(transfer([50],n,'common')[0])])
    np.savetxt(out/'tolerance_trials.csv',trial,delimiter=',',
               header='gain_10hz,common_to_diff_50hz',comments='')
    report={
        'model':'independent linear nodal solve; passive network only',
        'parameters':asdict(balanced),
        'differential_gain_10hz':float(abs(transfer([10],balanced)[0])),
        'balanced_cm_leakage_50hz':float(abs(transfer([50],balanced,'common')[0])),
        'mismatch_cm_leakage_50hz':float(abs(transfer([50],mismatch,'common')[0])),
        'mismatch_differential_uV_for_100mV_common':float(abs(transfer([50],mismatch,'common')[0])*100_000),
        'monte_carlo_trials':len(trial),
        'tolerance_gain_10hz_minmax':[float(np.min(np.array(trial)[:,0])),float(np.max(np.array(trial)[:,0]))],
        'ngspice':{'status':'not_run','reason':'ngspice not installed'},
        'safety_validation':False,
    }
    for name,n,drive in [('balanced',balanced,'differential'),('mismatch',mismatch,'common')]:
        net=export_spice(out/f'{name}.cir',n,drive)
        if shutil.which('ngspice'):
            sf,sh=run_ngspice(net,out/f'ngspice_{name}')
            expected=transfer(sf,n,drive)
            error=float(np.max(np.abs(sh-expected)))
            if not np.allclose(sh,expected,atol=1e-8,rtol=1e-4):
                raise AssertionError(f'ngspice/nodal disagreement in {name}: {error}')
            report.setdefault('ngspice_comparisons',{})[name]=error
            report['ngspice']={'status':'executed_and_compared'}
    (out/'circuit_report.json').write_text(json.dumps(report,indent=2))
    if require_ngspice and not shutil.which('ngspice'):
        raise RuntimeError('Native SPICE validation required but ngspice unavailable; no SPICE pass claimed.')
    return report
