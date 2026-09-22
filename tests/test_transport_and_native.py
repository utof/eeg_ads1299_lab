from pathlib import Path
import shutil
import socket
import subprocess
import sys
import threading
import time
import pytest
from lab.protocol import Packet
from lab.acquisition import decode_capture

ROOT=Path(__file__).resolve().parents[1]

def test_native_cpp_encoder_matches_python_byte_for_byte(tmp_path):
    compiler=shutil.which('g++') or shutil.which('clang++')
    if not compiler:pytest.skip('Native C++ compiler unavailable; inspect validation scope')
    exe=tmp_path/'native_test'
    built=subprocess.run([compiler,'-std=c++17','-Wall','-Wextra','-Werror','-pedantic',
                          str(ROOT/'tests/native_core_test.cpp'),'-o',str(exe)],capture_output=True,text=True)
    assert built.returncode==0,built.stderr
    result=subprocess.run([str(exe)],capture_output=True,text=True,check=True)
    p=Packet(0xffffffff,1234567,(-8388608,-1,0,8388607),overruns=9)
    assert bytes.fromhex(result.stdout.strip())==p.encode()


def test_real_local_udp_socket_packet_exchange():
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as receiver,socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sender:
        receiver.bind(('127.0.0.1',0));receiver.settimeout(2)
        packets=[Packet(i,i*4000,(i,-i,1,-1)) for i in range(25)]
        for p in packets:
            sender.sendto(p.encode(),receiver.getsockname())
            data,_=receiver.recvfrom(1000)
            assert Packet.decode(data)==p


def test_capture_decoder_preserves_missing_samples(tmp_path):
    path=tmp_path/'test.bin';out=tmp_path/'capture.csv'
    path.write_bytes(b''.join(Packet(i,i*4000,(i,-i,0,0)).encode() for i in (0,1,3,4)))
    summary=decode_capture(path,out)
    assert summary['accepted']==4 and summary['missing']==1
    lines=out.read_text().splitlines()
    assert len(lines)==5 and 'missing_before' in lines[0]
    assert lines[3].split(',')[3]=='1'


def test_cli_help_works_from_another_directory(tmp_path):
    proc=subprocess.run([sys.executable,str(ROOT/'run_lab.py'),'--help'],cwd=tmp_path,capture_output=True,text=True)
    assert proc.returncode==0 and 'demo' in proc.stdout
