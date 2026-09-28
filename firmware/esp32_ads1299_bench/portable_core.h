#ifndef EEG_LAB_PORTABLE_CORE_H
#define EEG_LAB_PORTABLE_CORE_H
#include <cstddef>
#include <cstdint>

namespace eeglab {
constexpr std::size_t HEADER_SIZE=20;
constexpr std::size_t MAX_PACKET_SIZE=49;
inline uint16_t crc16(const uint8_t* data,std::size_t len) {
    uint16_t crc=0xffff;
    for(std::size_t i=0;i<len;++i) {
        crc^=static_cast<uint16_t>(data[i])<<8;
        for(int b=0;b<8;++b)
            crc=static_cast<uint16_t>((crc&0x8000)?(crc<<1)^0x1021:(crc<<1));
    }
    return crc;
}
inline int32_t decode24(const uint8_t* p) {
    uint32_t x=(static_cast<uint32_t>(p[0])<<16)|(static_cast<uint32_t>(p[1])<<8)|p[2];
    return static_cast<int32_t>(static_cast<int64_t>(x)-((x&0x800000)?0x1000000:0));
}
inline void put16(uint8_t* p,uint16_t x) {
    p[0]=static_cast<uint8_t>(x);p[1]=static_cast<uint8_t>(x>>8);
}
inline void put32(uint8_t* p,uint32_t x) {
    for(unsigned i=0;i<4;++i)p[i]=static_cast<uint8_t>(x>>(8*i));
}
inline std::size_t packet(uint8_t* out,std::size_t capacity,const uint8_t* frame,
                           uint8_t channels,uint8_t gain,uint16_t fs,uint8_t flags,
                           uint32_t seq,uint32_t tick,uint32_t overruns) {
    if(channels!=4&&channels!=6&&channels!=8)return 0;
    const std::size_t payload=3+3*channels,size=HEADER_SIZE+payload+2;
    if(capacity<size||(frame[0]&0xf0)!=0xc0)return 0;
    out[0]='E';out[1]='9';out[2]=1;out[3]=channels;out[4]=flags;out[5]=gain;
    put16(out+6,fs);put32(out+8,seq);put32(out+12,tick);put32(out+16,overruns);
    for(std::size_t i=0;i<payload;++i)out[HEADER_SIZE+i]=frame[i];
    put16(out+size-2,crc16(out,size-2));return size;
}
}
#endif
