#include "../firmware/esp32_ads1299_bench/portable_core.h"
#include <cassert>
#include <cstdio>
#include <cstring>
int main() {
    const uint8_t check[]="123456789";
    assert(eeglab::crc16(check,9)==0x29b1);
    const uint8_t raw[]={0xc0,0,0,0x80,0,0,0xff,0xff,0xff,0,0,0,0x7f,0xff,0xff};
    assert(eeglab::decode24(raw+3)==-8388608);
    assert(eeglab::decode24(raw+6)==-1);
    assert(eeglab::decode24(raw+9)==0);
    assert(eeglab::decode24(raw+12)==8388607);
    uint8_t out[49]={0};
    assert(eeglab::packet(out,2,raw,4,24,250,4,0,0,0)==0);
    assert(eeglab::packet(out,sizeof(out),raw,5,24,250,4,0,0,0)==0);
    auto n=eeglab::packet(out,sizeof(out),raw,4,24,250,4,0xffffffff,1234567,9);
    assert(n==37);
    for(std::size_t i=0;i<n;++i)std::printf("%02x",out[i]);
    std::puts("");
}
