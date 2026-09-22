#!/usr/bin/env python3
"""One-command REAL localhost UDP test using synthetic packets and deliberate loss."""
from pathlib import Path
import json
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from lab.acquisition import replay_packets,decode_capture
from lab.inspect_capture import inspect_capture


def main():
    out=ROOT/'results/loopback';out.mkdir(parents=True,exist_ok=True)
    proc=subprocess.Popen([sys.executable,str(ROOT/'run_lab.py'),'receive','--out',str(out/'capture.bin'),
                           '--port','0','--seconds','10'],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
        line=proc.stdout.readline()
        match=re.search(r'Listening on 127\.0\.0\.1:(\d+)',line)
        if not match:raise RuntimeError('Receiver did not start: '+line)
        sent=replay_packets(port=int(match.group(1)),seconds=9,drop_every=1000)
        stdout,stderr=proc.communicate(timeout=15)
        (out/'receiver.log').write_text(line+stdout+'\n'+stderr)
        if proc.returncode:raise RuntimeError('Receiver failed; inspect receiver.log')
    finally:
        if proc.poll() is None:proc.kill();proc.wait()
    decoded=decode_capture(out/'capture.bin',out/'capture.csv')
    quality=inspect_capture(out/'capture.csv',out/'quality')
    assert decoded['accepted']==2248,decoded
    assert decoded['missing']==2,decoded
    assert quality['four_second_spectral_windows']>=1,quality
    report={'scope':'real localhost UDP; synthetic payload; NO hardware test',
            'deliberately_omitted_sequences':[1000,2000], 'sent':sent,'decoded':decoded,'quality':quality}
    (out/'LOOPBACK_REPORT.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({'accepted':decoded['accepted'],'missing':decoded['missing'],
                      'spectral_windows':quality['four_second_spectral_windows'],
                      'peak_hz':quality['peak_0p5_40_Hz_by_channel']},indent=2))
    return 0

if __name__=='__main__':sys.exit(main())
