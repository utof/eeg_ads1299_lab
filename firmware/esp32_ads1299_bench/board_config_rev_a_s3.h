#pragma once
// Proposed Rev A digital GPIO map only. No wiring, power or human-use approval.
#if !defined(CONFIG_IDF_TARGET_ESP32S3)
#error "EEGLAB_REV_A_S3 requires CONFIG_IDF_TARGET_ESP32S3."
#endif
constexpr int PIN_SCLK = 12;
constexpr int PIN_MISO = 13;
constexpr int PIN_MOSI = 11;
constexpr int PIN_CS = 10;
constexpr int PIN_DRDY = 4;
constexpr int PIN_RESET = 5;
constexpr int PIN_START = 6;
constexpr int PIN_PWDN = 7;
constexpr int PIN_CLKSEL = 8;
constexpr int EXPECTED_ADS_CHANNELS = 4;
