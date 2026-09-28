#pragma once
// Rev A bench-only sequence. I/O is injected only to test ordering on the host.
// Confirmations are operator preconditions, NOT voltage sensing or safety gates.
#include "board_config_rev_a_s3.h"

namespace eeglab {
template<class Io>
void startRevA(Io& io) {
    constexpr int controls[] = {
        PIN_SCLK, PIN_MOSI, PIN_CS, PIN_RESET, PIN_START, PIN_PWDN, PIN_CLKSEL
    };
    // Preload every low latch before enabling outputs. Passive pulldowns are
    // still required during reset/boot, before this reviewed code can execute.
    for (int pin : controls) io.level(pin, 0);
    for (int pin : controls) io.output(pin);
    io.confirmRailsAndInputs();
    // PWDN low disables the oscillator: time spent there cannot count as tPOR.
    io.level(PIN_PWDN, 1);
    io.level(PIN_CLKSEL, 1);
    io.level(PIN_CS, 1);
    io.level(PIN_RESET, 1);
    io.waitMs(150);
    // A fixed delay is not evidence of VCAP1 voltage. Keep this second boundary.
    io.confirmVcap1();
    io.level(PIN_RESET, 0);
    io.waitUs(4);
    io.level(PIN_RESET, 1);
    io.waitUs(20);
}
} // namespace eeglab
