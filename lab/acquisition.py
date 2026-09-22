"""UDP/optional serial capture and replay. UDP is local-network, unencrypted.

Do not use public Wi-Fi for brain recordings. Default bind is localhost.
A native ADS frame has no CRC: transport CRC cannot detect a wrong SPI word
that the firmware itself read and then checksummed.
"""
from pathlib import Path
import csv
import json
import socket
import time
import numpy as np
from .protocol import Packet, StreamDecoder, Tracker, FLAG_SYNTHETIC
from .adc import ADCConfig, to_volts


def capture_udp(path,seconds=10,host='127.0.0.1',port=9000):
    if seconds<=0 or not 0<=port<=65535: raise ValueError('Invalid capture duration/port')
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    counts={'datagrams':0,'valid_packets':0,'invalid_packets':0}
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock, path.open('wb') as f:
        sock.bind((host,port));sock.settimeout(.2)
        print(f'Listening on {host}:{sock.getsockname()[1]} for {seconds:g} s',flush=True)
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            try: data,_=sock.recvfrom(4096)
            except socket.timeout: continue
            counts['datagrams']+=1
            try: Packet.decode(data)
            except ValueError:
                counts['invalid_packets']+=1;continue
            f.write(data);counts['valid_packets']+=1
    path.with_suffix('.capture.json').write_text(json.dumps(counts,indent=2))
    return counts


def capture_serial(path,port,seconds=10,baud=460800):
    if seconds<=0: raise ValueError('Capture duration must be positive')
    try: import serial
    except ImportError as e: raise RuntimeError('Install requirements-serial.txt to capture USB serial') from e
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    total=0
    # Bench only: disconnect EVERY body electrode, not just the signal channel.
    with serial.Serial(port,baudrate=baud,timeout=.2) as ser,path.open('wb') as f:
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            data=ser.read(max(1,ser.in_waiting))
            f.write(data);total+=len(data)
    return {'bytes':total,'transport':'serial_bench_only'}


def decode_capture(path,out_csv,vref_v=4.5):
    decoder=StreamDecoder();tracker=Tracker();records=[]
    with Path(path).open('rb') as f:
        while data:=f.read(65536):
            for p in decoder.feed(data):
                info=tracker.observe(p)
                if info is not None: records.append((p,info))
    if not records: raise ValueError('No valid forward-moving packets found')
    n=len(records[0][0].codes)
    fields=['sequence','device_time_us','elapsed_s','missing_before','flags','overruns','status']
    fields += [f'ch{i+1}_count' for i in range(n)] + [f'ch{i+1}_uV' for i in range(n)]
    out_csv=Path(out_csv);out_csv.parent.mkdir(parents=True,exist_ok=True)
    with out_csv.open('w',newline='') as f:
        writer=csv.writer(f);writer.writerow(fields)
        for p,info in records:
            adc=ADCConfig(gain=p.gain,fs_hz=p.fs_hz,vref_v=vref_v)
            uv=to_volts(np.array(p.codes,dtype=np.int32),adc)*1e6
            writer.writerow([p.sequence,p.time_us,info['elapsed_us']/1e6,info['missing_before'],
                             p.flags,p.overruns,f'{p.status:06x}',*p.codes,*uv])
    summary=tracker.summary()
    first=records[0][0]
    summary.update({'channels':n,'gain':first.gain,'fs_hz':first.fs_hz,
                    'assumed_vref_v':vref_v,'discarded_bytes':decoder.discarded_bytes,
                    'invalid_candidates':decoder.invalid_candidates,'trailing_bytes':len(decoder.buffer),
                    'last_device_overruns':records[-1][0].overruns,
                    'flags':first.flags,'gap_policy':'retain gaps; do not interpolate or bridge for FFT',
                    'recording_mode':('synthetic' if first.flags&4 else 'internal_test' if first.flags&1 else 'internal_short' if first.flags&2 else 'external_unreviewed')})
    out_csv.with_suffix('.json').write_text(json.dumps(summary,indent=2))
    return summary


def replay_packets(host='127.0.0.1',port=9000,seconds=3,channels=4,fs_hz=250,drop_every=0):
    if channels not in (4,6,8) or seconds<=0 or drop_every<0:
        raise ValueError('Invalid replay options')
    end=int(seconds*fs_hz)
    start=time.monotonic()
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock:
        for seq in range(end):
            deadline=start+seq/fs_hz
            wait=deadline-time.monotonic()
            if wait>0: time.sleep(wait)
            if drop_every and seq and seq%drop_every==0: continue
            codes=tuple(int(500*np.sin(2*np.pi*10*seq/fs_hz+.1*c)) for c in range(channels))
            p=Packet(seq,int(seq*1e6/fs_hz)&0xFFFFFFFF,codes,fs_hz=fs_hz,flags=FLAG_SYNTHETIC)
            sock.sendto(p.encode(),(host,port))
    return {'generated_samples':end,'synthetic':True}
