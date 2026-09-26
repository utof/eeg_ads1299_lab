#pragma once
#include <Arduino.h>
constexpr int MSBFIRST=1;
constexpr int SPI_MODE1=1;
struct SPISettings { SPISettings(unsigned,int,int) {} };
struct SpiDouble {
    void begin(int sclk,int miso,int mosi,int cs) {
        const int pins[]={sclk,miso,mosi,cs};
        for(int i=0;i<4;++i)hostbench::record("spi-pin",i,pins[i]);
        hostbench::record("spi");throw hostbench::SpiReached{};
    }
    void beginTransaction(const SPISettings&) {}
    void endTransaction() {}
    std::uint8_t transfer(std::uint8_t) { return 0; }
};
inline SpiDouble SPI;
