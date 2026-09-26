// Executes the production sequencing helper against a recording I/O double.
// This is not ESP32 GPIO emulation, voltage measurement, or a safety test.
#include <algorithm>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
#include "rev_a_startup.h"

struct Event {
    std::string kind;
    int pin;
    int value;
    std::uint64_t us;
};
struct Waiting {};
struct Trace {
    std::string stop;
    std::vector<Event> events;
    std::uint64_t us = 0;
    void level(int pin, int value) { events.push_back({"level", pin, value, us}); }
    void output(int pin) { events.push_back({"output", pin, 0, us}); }
    void waitMs(unsigned value) { us += 1000ULL * value; }
    void waitUs(unsigned value) { us += value; }
    void confirmRailsAndInputs() {
        events.push_back({"rails", -1, 0, us});
        if (stop == "rails") throw Waiting{};
    }
    void confirmVcap1() {
        events.push_back({"vcap", -1, 0, us});
        if (stop == "vcap") throw Waiting{};
    }
};
void expect(bool ok, const char* why) {
    if (!ok) throw std::runtime_error(why);
}
std::size_t locate(const Trace& trace, const std::string& kind, int pin, int value,
                   std::size_t from = 0) {
    for (std::size_t i = from; i < trace.events.size(); ++i) {
        const auto& e = trace.events[i];
        if (e.kind == kind && e.pin == pin && e.value == value) return i;
    }
    throw std::runtime_error("required event absent");
}
void checkLowPreparation(const Trace& trace) {
    const int expected[] = {12, 11, 10, 5, 6, 7, 8};
    const auto rails = locate(trace, "rails", -1, 0);
    std::vector<int> outputs;
    for (std::size_t i = 0; i < rails; ++i) {
        const auto& e = trace.events[i];
        expect(e.kind != "level" || e.value == 0, "high output before rail confirmation");
        if (e.kind == "output") {
            expect(locate(trace, "level", e.pin, 0) < i, "output enabled before low latch");
            outputs.push_back(e.pin);
        }
    }
    std::vector<int> required(std::begin(expected), std::end(expected));
    std::sort(required.begin(), required.end());
    std::sort(outputs.begin(), outputs.end());
    expect(outputs == required, "missing, duplicate, or unexpected startup output");
}
void checkPoweredPhase(const Trace& trace) {
    const auto rails = locate(trace, "rails", -1, 0);
    const auto wake = locate(trace, "level", 7, 1);
    const auto clock = locate(trace, "level", 8, 1);
    const auto vcap = locate(trace, "vcap", -1, 0);
    expect(rails < wake && rails < clock, "wake or clock precedes rail confirmation");
    expect(wake < vcap && clock < vcap, "VCAP confirmation precedes wake or clock");
    // 2^18 cycles / (2.048 MHz * 0.975) + 20 us oscillator startup < 132 ms.
    const auto clockReadyAt = std::max(trace.events[wake].us, trace.events[clock].us);
    expect(trace.events[vcap].us - clockReadyAt >= 132000, "tPOR begins before wake/clock");
    expect(locate(trace, "level", 10, 1) > rails, "CS not deselected after rails");
    for (const auto& e : trace.events)
        expect(!(e.kind == "level" && e.pin == 6 && e.value == 1), "START asserted");
}
void runCase(const std::string& stop) {
    Trace trace{stop, {}, 0};
    bool returned = false;
    try { eeglab::startRevA(trace); returned = true; } catch (const Waiting&) {}
    expect(returned == stop.empty(), "confirmation wait did not stop sequencing");
    checkLowPreparation(trace);
    if (stop == "rails") {
        for (const auto& e : trace.events)
            expect(e.kind != "level" || e.value == 0, "high output while rails unconfirmed");
        return;
    }
    checkPoweredPhase(trace);
    const auto resetHigh = locate(trace, "level", 5, 1);
    const auto vcap = locate(trace, "vcap", -1, 0);
    expect(resetHigh < vcap, "reset not released during oscillator wake");
    if (stop == "vcap") {
        expect(trace.events.back().kind == "vcap", "reset after unconfirmed VCAP1");
        return;
    }
    const auto resetLow = locate(trace, "level", 5, 0, resetHigh + 1);
    const auto resetEnd = locate(trace, "level", 5, 1, resetLow + 1);
    expect(vcap < resetLow, "reset pulse precedes VCAP1 confirmation");
    expect(trace.events[resetEnd].us - trace.events[resetLow].us >= 2, "reset pulse too short");
    expect(trace.us - trace.events[resetEnd].us >= 10, "SPI permitted before reset recovery");
    expect(trace.events.back().pin == 5 && trace.events.back().value == 1, "unexpected final output");
}
int main() {
    try {
        runCase("rails");
        runCase("vcap");
        runCase("");
    } catch (const std::exception& error) {
        std::cerr << "STARTUP_ASSERTION: " << error.what() << '\n';
        return 1;
    }
    std::cout << "startup sequence and both blocked prefixes passed\n";
}
