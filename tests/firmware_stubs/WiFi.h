#pragma once
constexpr int WIFI_STA=1;
constexpr int WL_CONNECTED=1;
struct IPAddress { bool fromString(const char*) { return true; } };
struct WiFiDouble {
    void mode(int) {}
    void begin(const char*,const char*) {}
    int status() { return WL_CONNECTED; }
    void setSleep(bool) {}
};
inline WiFiDouble WiFi;
