import binascii
import random
import numpy as np
import pytest
from lab.protocol import *

@pytest.mark.parametrize('n',[4,6,8])
def test_native_and_packet_roundtrip(n):
    values=tuple(np.random.default_rng(n).integers(-(1<<23),(1<<23),n).tolist())
    p=Packet(0xffffffff,0xffffff00,values,flags=4,overruns=11)
    raw=p.encode();q=Packet.decode(raw)
    assert q==p and len(raw)==25+3*n
    assert parse_native(native_frame(values),n)[1]==values

@pytest.mark.parametrize('value',[-8388608,-123,-1,0,1,123,8388607])
def test_sign_extension(value):
    assert signed24((value&0xffffff).to_bytes(3,'big'))==value


def test_crc_known_vector():assert binascii.crc_hqx(b'123456789',0xffff)==0x29b1


def test_corrupted_truncated_and_wrong_native_status_rejected():
    raw=bytearray(Packet(1,4000,(1,2,3,4)).encode())
    for i in range(len(raw)):
        broken=raw.copy();broken[i]^=1
        with pytest.raises(ValueError):Packet.decode(broken)
    with pytest.raises(ValueError):Packet.decode(raw[:-1])
    with pytest.raises(ValueError):parse_native(bytes(15),4)


def test_stream_chunking_noise_and_resynchronization():
    packets=[Packet(i,i*4000,(i,-i,0,3)) for i in range(20)]
    bad=bytearray(packets[3].encode());bad[-1]^=3
    stream=b'boot banner\n'+b''.join(p.encode() for p in packets[:10])+bytes(bad)+b'noise'+b''.join(p.encode() for p in packets[10:])
    decoder=StreamDecoder();out=[];rng=random.Random(4);offset=0
    while offset<len(stream):
        n=rng.randrange(1,50);out+=decoder.feed(stream[offset:offset+n]);offset+=n
    assert out==packets
    assert decoder.discarded_bytes>0 and decoder.invalid_candidates>0


def test_gap_duplicate_out_of_order_and_counter_wrap():
    tr=Tracker()
    seq=[0xfffffffe,0xffffffff,0,2,2,1,3]
    times=[0xffffe0c0,0xfffff060,0,8000,8000,4000,12000]
    for s,t in zip(seq,times):tr.observe(Packet(s,t,(0,0,0,0)))
    assert tr.accepted==5 and tr.missing==1 and tr.duplicates==1 and tr.stale==1
    assert tr.elapsed_us==20000


def test_configuration_changes_require_new_capture():
    tr=Tracker();tr.observe(Packet(0,0,(0,0,0,0)))
    with pytest.raises(ValueError):tr.observe(Packet(1,4000,(0,0,0,0),gain=12))
