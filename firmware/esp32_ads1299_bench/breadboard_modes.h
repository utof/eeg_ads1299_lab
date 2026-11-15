#ifndef EEG_LAB_BREADBOARD_MODES_H
#define EEG_LAB_BREADBOARD_MODES_H
// Breadboard build only: portable rules shared by the sketch and host tests.
// Only the chip's internal mux paths exist here (test signal, shorted inputs).
// There is deliberately NO electrode-input mode; adding one is a separate,
// explicitly approved change (see docs/BREADBOARD_S3_BRINGUP.md).
#include <cstddef>
#include <cstdint>

namespace eeglab {
enum class BreadboardMode : std::uint8_t { TestSignal, ShortedInputs };
constexpr char BREADBOARD_MODE_KEYS[] = "TN";
constexpr std::size_t MAX_BREADBOARD_WRITES = 19; // 11 fixed + 8 CHnSET

struct RegisterWrite {
    std::uint8_t address;
    std::uint8_t value;
    std::uint8_t mask;
};

// ID bits 7:5 are a revision that may change; bits 4:0 name the part:
// 0x1C = ADS1299-4, 0x1E = ADS1299 (8 channels). The 6-channel part is refused.
constexpr std::uint8_t breadboardChannels(std::uint8_t id) {
    return (id & 0x1f) == 0x1c ? 4 : (id & 0x1f) == 0x1e ? 8 : 0;
}

// A console byte as the upper-case key it names if `accepted` lists it, else 0.
constexpr char breadboardKey(int raw, const char* accepted) {
    const int key = raw >= 'a' && raw <= 'z' ? raw - 'a' + 'A' : raw;
    for (; *accepted != '\0'; ++accepted)
        if (key == *accepted) return *accepted;
    return 0;
}

// Only called with a key accepted from BREADBOARD_MODE_KEYS.
constexpr BreadboardMode breadboardModeFromKey(char key) {
    return key == 'T' ? BreadboardMode::TestSignal : BreadboardMode::ShortedInputs;
}

// Packet flag bits (docs/PROTOCOL.md): 1 internal test, 2 internal short.
constexpr std::uint8_t breadboardFlags(BreadboardMode mode) {
    return mode == BreadboardMode::TestSignal ? 1 : 2;
}

// The Rev A bench writes in the same order, with CONFIG2/CHnSET chosen at run
// time. The sketch checks each by readback. Returns 0 and writes nothing for an
// unsupported channel count or a buffer that is too small.
inline std::size_t breadboardRegisterPlan(BreadboardMode mode, std::uint8_t channels,
                                          RegisterWrite* out, std::size_t capacity) {
    if ((channels != 4 && channels != 8) || capacity < 11u + channels) return 0;
    const bool test = mode == BreadboardMode::TestSignal;
    const auto chnset = static_cast<std::uint8_t>(test ? 0x65 : 0x61); // gain 24; test or shorted mux
    std::size_t n = 0;
    out[n++] = {0x01, 0x96, 0xff}; // CONFIG1: 250 SPS, clock output off
    out[n++] = {0x02, static_cast<std::uint8_t>(test ? 0xd0 : 0xc0), 0xff}; // ~0.98 Hz test signal on/off
    out[n++] = {0x03, 0xe0, 0xfe}; // reference buffer on, bias amplifier off; bit 0 is read-only
    out[n++] = {0x04, 0x00, 0xff}; // LOFF: no lead-off settings
    for (std::uint8_t channel = 0; channel < channels; ++channel)
        out[n++] = {static_cast<std::uint8_t>(0x05 + channel), chnset, 0xff};
    // BIAS_SENSP/N, LOFF_SENSP/N (lead-off current sources), LOFF_FLIP: all off.
    for (std::uint8_t address = 0x0d; address <= 0x11; ++address)
        out[n++] = {address, 0x00, 0xff};
    out[n++] = {0x15, 0x00, 0xff}; // MISC1: SRB1 off
    out[n++] = {0x17, 0x00, 0xff}; // CONFIG4: continuous, lead-off comparators off
    return n;
}
} // namespace eeglab
#endif
