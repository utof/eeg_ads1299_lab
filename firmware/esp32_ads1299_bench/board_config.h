#pragma once
// Do not change this until HARDWARE_GUIDE.md and your actual board schematic
// have been reviewed. This acknowledges BENCH DIGITAL wiring only; it is NOT
// a human-use enable switch. All electrode leads remain disconnected.
constexpr bool BOARD_PROFILE_REVIEWED = false;

// Selection is explicit: compiling for S3 alone does not silently choose wiring.
#if defined(EEGLAB_REV_A_S3)
#include "board_config_rev_a_s3.h"
#else
#if !defined(CONFIG_IDF_TARGET_ESP32)
#error "Original ESP32 profile only. Select EEGLAB_REV_A_S3 explicitly for the proposed S3 map."
#endif
// EXAMPLE FOR ORIGINAL ESP32 / WROOM-32 ONLY. Not ESP32-C3 / S2 / S3 / C6.
// These are GPIO numbers, never physical header positions or "D" numbers.
constexpr int PIN_SCLK=18;
constexpr int PIN_MISO=19; // ADS1299 DOUT -> ESP32 input
constexpr int PIN_MOSI=23; // ESP32 output -> ADS1299 DIN
constexpr int PIN_CS=27;
constexpr int PIN_DRDY=26;
constexpr int PIN_RESET=25;
constexpr int PIN_START=32;
constexpr int PIN_PWDN=33;

#endif

// Only the internal mux paths exist in this starter. External EEG acquisition
// needs a board-specific protection, bias and reference design/review first.
constexpr bool USE_INTERNAL_TEST=true; // false = internal input-short noise test
constexpr bool USE_WIFI_UDP=false;    // false = USB serial, BENCH ONLY
constexpr char WIFI_SSID[]="EDIT_ME";
constexpr char WIFI_PASSWORD[]="EDIT_ME";
constexpr char UDP_HOST[]="192.168.1.2"; // replace with private-LAN computer IP
constexpr unsigned short UDP_PORT=9000;
