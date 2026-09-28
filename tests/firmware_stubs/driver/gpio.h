#pragma once
#include <Arduino.h>
using gpio_num_t=int;
constexpr int ESP_OK=0;
inline int gpio_set_level(gpio_num_t pin,unsigned value) {
    hostbench::record("latch",pin,static_cast<int>(value));
    return hostbench::scenario=="gpio-failure" && pin==8 ? -1 : ESP_OK;
}
