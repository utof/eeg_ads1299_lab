#pragma once
#include <Arduino.h>
#include <WiFi.h>
struct WiFiUDP {
    bool begin(unsigned) { return true; }
    bool beginPacket(const IPAddress&,unsigned) { return true; }
    void write(const std::uint8_t*,std::size_t) {}
    void endPacket() {}
};
