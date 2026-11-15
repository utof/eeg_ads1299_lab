// Portable breadboard rules against independent expected tables. Host-only:
// no ESP32, SPI, voltage or chip behaviour is emulated here.
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <vector>
#include "breadboard_modes.h"

using eeglab::BreadboardMode;
struct Write {
    int address, value, mask;
    bool operator==(const Write& other) const {
        return address == other.address && value == other.value && mask == other.mask;
    }
};
void expect(bool ok, const char* why) {
    if (!ok) throw std::runtime_error(why);
}
std::vector<Write> plan(BreadboardMode mode, int channels,
                        std::size_t capacity = eeglab::MAX_BREADBOARD_WRITES) {
    eeglab::RegisterWrite out[eeglab::MAX_BREADBOARD_WRITES + 4]{};
    const auto n = eeglab::breadboardRegisterPlan(mode, static_cast<std::uint8_t>(channels), out,
                                                  capacity);
    std::vector<Write> result;
    for (std::size_t i = 0; i < n; ++i) result.push_back({out[i].address, out[i].value, out[i].mask});
    return result;
}
// Independent expectation: the Rev A bench sketch's register writes, in order,
// with CONFIG2/CHnSET chosen at run time instead of by USE_INTERNAL_TEST.
std::vector<Write> expected(int config2, int chnset, int channels) {
    std::vector<Write> writes{{0x01, 0x96, 0xff}, {0x02, config2, 0xff}, {0x03, 0xe0, 0xfe},
                              {0x04, 0x00, 0xff}};
    for (int channel = 0; channel < channels; ++channel) writes.push_back({0x05 + channel, chnset, 0xff});
    for (int address : {0x0d, 0x0e, 0x0f, 0x10, 0x11}) writes.push_back({address, 0x00, 0xff});
    writes.push_back({0x15, 0x00, 0xff});
    writes.push_back({0x17, 0x00, 0xff});
    return writes;
}
// Datasheet bit meanings (SBAS499C register map), checked separately from the table.
void neverExcites(const std::vector<Write>& writes) {
    for (const auto& w : writes) {
        if (w.address == 0x0f || w.address == 0x10) expect(w.value == 0, "lead-off current source enabled");
        if (w.address == 0x04 || w.address == 0x11) expect(w.value == 0, "lead-off setting changed");
        if (w.address == 0x17) expect((w.value & 0x02) == 0, "lead-off comparators powered");
        if (w.address == 0x0d || w.address == 0x0e) expect(w.value == 0, "bias sensing enabled");
        if (w.address == 0x03) expect((w.value & 0x04) == 0 && (w.value & 0x80), "bias on or reference off");
        if (w.address == 0x15) expect(w.value == 0, "SRB1 switched on");
        if (w.address >= 0x05 && w.address <= 0x0c) {
            const int mux = w.value & 0x07;
            expect(mux == 1 || mux == 5, "channel mux is not test signal or shorted input");
            expect((w.value & 0x80) == 0 && ((w.value >> 4) & 0x07) == 6, "channel not on at gain 24");
        }
    }
}
void ids() {
    const int table[][2] = {{0x3c, 4}, {0x1c, 4}, {0xbc, 4}, {0x3e, 8}, {0xfe, 8}, {0x3d, 0},
                            {0x3f, 0}, {0x00, 0}, {0xff, 0}, {0x38, 0}, {0x2c, 0}, {0x12, 0}};
    for (const auto& row : table)
        expect(eeglab::breadboardChannels(static_cast<std::uint8_t>(row[0])) == row[1],
               "ID register mapped to the wrong channel count");
}
void keys() {
    expect(eeglab::breadboardKey('R', "R") == 'R' && eeglab::breadboardKey('r', "R") == 'R', "R key");
    expect(eeglab::breadboardKey('V', "R") == 0 && eeglab::breadboardKey(-1, "R") == 0, "wrong key accepted");
    expect(eeglab::breadboardKey('t', eeglab::BREADBOARD_MODE_KEYS) == 'T', "t key");
    expect(eeglab::breadboardKey('N', eeglab::BREADBOARD_MODE_KEYS) == 'N', "N key");
    for (int raw : {'\r', '\n', 'x', 'R', 0})
        expect(eeglab::breadboardKey(raw, eeglab::BREADBOARD_MODE_KEYS) == 0, "junk accepted as a mode");
    expect(eeglab::breadboardModeFromKey('T') == BreadboardMode::TestSignal, "T is the test signal");
    expect(eeglab::breadboardModeFromKey('N') == BreadboardMode::ShortedInputs, "N is shorted inputs");
    // docs/PROTOCOL.md flag bits: 1 internal test, 2 internal short.
    expect(eeglab::breadboardFlags(BreadboardMode::TestSignal) == 1, "test flag");
    expect(eeglab::breadboardFlags(BreadboardMode::ShortedInputs) == 2, "short flag");
}
void plans() {
    const struct { BreadboardMode mode; int config2, chnset; } modes[] = {
        {BreadboardMode::TestSignal, 0xd0, 0x65}, {BreadboardMode::ShortedInputs, 0xc0, 0x61}};
    for (const auto& m : modes) {
        for (int channels : {4, 8}) {
            const auto writes = plan(m.mode, channels);
            expect(writes == expected(m.config2, m.chnset, channels), "register plan differs");
            neverExcites(writes);
        }
        expect(plan(m.mode, 6).empty() && plan(m.mode, 0).empty(), "unsupported channel count planned");
    }
    expect(plan(BreadboardMode::ShortedInputs, 8, 18).empty(), "8-channel plan overflowed");
    expect(plan(BreadboardMode::TestSignal, 4, 14).empty(), "4-channel plan overflowed");
    expect(plan(BreadboardMode::TestSignal, 4, 15).size() == 15, "exact capacity refused");
}
int main() {
    try {
        ids();
        keys();
        plans();
    } catch (const std::exception& error) {
        std::cerr << "BREADBOARD_MODES_ASSERTION: " << error.what() << '\n';
        return 1;
    }
    std::cout << "breadboard helper tables passed\n";
}
