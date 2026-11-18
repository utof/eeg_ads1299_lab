#pragma once
// Breadboard build: ESP32-S3-DevKitC-1 wired to a hand-soldered ADS1299-4 or
// ADS1299 adapter (docs/BREADBOARD_S3_BRINGUP.md). Not the Rev A PCB. There is
// no Rev A supervisor here, so the C2 interlock and its GPIO 9/14/15/16 are
// compiled out; series resistors and pull-downs on the breadboard stand in.
#if !defined(CONFIG_IDF_TARGET_ESP32S3)
#error "EEGLAB_BREADBOARD_S3 requires CONFIG_IDF_TARGET_ESP32S3."
#endif

// Same nine GPIOs as the Rev A map, reused as is. Its EXPECTED_ADS_CHANNELS
// is not used by this build: the breadboard accepts ID 0x3C (4 ch) or 0x3E
// (8 ch). The console stays on the DevKit's own USB-UART socket (UART0).
#include "board_config_rev_a_s3.h"

// Its own gate, separate from BOARD_PROFILE_REVIEWED. Set true only on your
// local copy, after the unpowered continuity checks (bring-up steps 1-3)
// pass. It acknowledges your wiring only; it is NOT a human-use switch.
constexpr bool BREADBOARD_WIRING_CHECKED = false;
// USE_INTERNAL_TEST in board_config.h is ignored here: choose T or N at the
// console. USE_WIFI_UDP and the Wi-Fi settings there still apply.
