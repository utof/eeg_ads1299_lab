// The actual sketch, breadboard build (EEGLAB_BREADBOARD_S3), against the shared
// host doubles and a minimal ADS1299 register file. It records software calls
// only: not MCU, SPI timing, voltage, wiring or chip-behaviour emulation.
#include <iostream>
#include <stdexcept>
#include "esp32_ads1299_bench.ino"
namespace hostbench {
std::vector<Event> events;
std::deque<char> input;
std::string scenario;
std::uint64_t elapsed = 0;
bool halted = false, frames = false;
unsigned packets = 0;
int lastPacket = 0;
std::uint8_t chipId = 0x3c;
std::uint8_t regs[32]{};
unsigned pos = 0;
std::uint8_t opcode = 0;
void record(const std::string& kind, int pin, int value) {
    events.push_back({kind, pin, value, elapsed});
    if (kind == "packet") { ++packets; lastPacket = value; }
}
void answerMode() {
    if (scenario == "short-8") input.push_back('N');
    else if (scenario == "mode-retry") { input.push_back('x'); input.push_back('\n'); input.push_back('t'); }
    else input.push_back('T');
}
void printed(const char* text) {
    const std::string s(text);
    if (s.find("type R") != std::string::npos) {
        record("prompt", -1, 'R');
        if (scenario != "no-input" && scenario != "queued") input.push_back('R');
    }
    if (s.find("type V") != std::string::npos) {
        record("prompt", -1, 'V');
        if (scenario != "only-R") input.push_back('V');
    }
    if (s.find("type T") != std::string::npos) { record("prompt", -1, 'M'); answerMode(); }
    if (s.find("HALTED") != std::string::npos) { halted = true; record("halt", -1, 0); deadline = elapsed + 20000; }
}
void transaction() { pos = 0; }
std::uint8_t transfer(std::uint8_t value) {
    if (frames) return pos++ == 0 ? 0xc0 : 0x00; // RDATAC frame: valid status prefix
    const auto index = pos++;
    if (index == 0) {
        opcode = value;
        if (value < 0x20 || value >= 0x60) record("ads-command", value, 0);
        return 0;
    }
    if (index != 2) return 0;
    const int address = opcode & 0x1f;
    if ((opcode & 0xe0) == 0x40) { regs[address] = value; record("ads-write", address, value); return 0; }
    if ((opcode & 0xe0) != 0x20) return 0;
    std::uint8_t reply = address == 0 ? chipId : regs[address];
    if (scenario == "readback-fault" && address == 0x01) reply ^= 0x01;
    record("ads-read", address, reply);
    return reply;
}
} // namespace hostbench

using hostbench::events;
const int CONTROLS[] = {12, 11, 10, 5, 6, 7, 8};
void require(bool ok, const char* why) {
    if (!ok) throw std::runtime_error(why);
}
bool has(const std::string& kind, int pin, int value) {
    for (const auto& e : events) if (e.kind == kind && e.pin == pin && e.value == value) return true;
    return false;
}
std::size_t at(const std::string& kind, int pin, int value, std::size_t from = 0) {
    for (std::size_t i = from; i < events.size(); ++i)
        if (events[i].kind == kind && events[i].pin == pin && events[i].value == value) return i;
    throw std::runtime_error("required trace event missing");
}
void checkConsoleAndPins() {
    require(events.size() >= 4 && events[0].kind == "console-baud" && events[0].value == 460800, "console baud");
    require(events[2].pin == -1 && events[3].pin == -1, "console must stay on the DevKit's own UART0 pins");
    for (const auto& e : events)
        for (int pin : {9, 14, 15, 16})
            require(!(e.pin == pin && (e.kind == "mode" || e.kind == "latch" || e.kind == "write" ||
                                       e.kind == "read-pin")),
                    "breadboard build touched a Rev A C2 interlock pin");
    require(!has("latch", 6, 1) && !has("write", 6, 1), "START pin raised; START is a command");
}
void checkParked() {
    const auto rails = at("prompt", -1, 'R');
    for (int pin : CONTROLS) {
        const auto low = at("latch", pin, 0), output = at("mode", pin, OUTPUT);
        require(low < output && output < rails, "control not latched low before output and the R prompt");
    }
    for (std::size_t i = 0; i < rails; ++i)
        require(!(events[i].kind == "latch" && events[i].value != 0), "control raised before R");
}
void checkWakeAndReset() {
    const auto rails = at("prompt", -1, 'R'), vcap = at("prompt", -1, 'V');
    const auto wake = at("latch", 7, 1), clock = at("latch", 8, 1);
    require(rails < wake && rails < clock && wake < vcap && clock < vcap, "wake order differs");
    require(events[vcap].us - events[wake].us >= 132000 && events[vcap].us - events[clock].us >= 132000,
            "tPOR before the VCAP1 prompt too short");
    const auto low = at("latch", 5, 0, at("latch", 5, 1) + 1), high = at("latch", 5, 1, low + 1);
    const auto spi = at("spi", -1, 0);
    require(vcap < low && events[high].us - events[low].us >= 2, "reset pulse missing or too short");
    require(high < spi && events[spi].us - events[high].us >= 10, "SPI before reset recovery");
    const int pins[] = {12, 13, 11, 10};
    for (int i = 0; i < 4; ++i) require(at("spi-pin", i, pins[i]) < spi, "SPI pin tuple differs");
}
std::vector<hostbench::Event> adsTrace() {
    std::vector<hostbench::Event> ads;
    for (const auto& e : events) if (e.kind.rfind("ads-", 0) == 0) ads.push_back(e);
    return ads;
}
void checkRegisters(int channels, int config2, int chnset) {
    std::vector<std::pair<int, int>> want{{0x01, 0x96}, {0x02, config2}, {0x03, 0xe0}, {0x04, 0x00}};
    for (int c = 0; c < channels; ++c) want.push_back({0x05 + c, chnset});
    for (int a : {0x0d, 0x0e, 0x0f, 0x10, 0x11, 0x15, 0x17}) want.push_back({a, 0x00});
    const auto ads = adsTrace();
    require(ads.size() >= 3 && ads[0].kind == "ads-command" && ads[0].pin == 0x11, "SDATAC is not the first SPI command");
    require(ads[1].kind == "ads-command" && ads[1].pin == 0x0a, "STOP does not follow SDATAC");
    require(ads[2].kind == "ads-read" && ads[2].pin == 0, "ID is not read before any write");
    std::vector<std::pair<int, int>> got;
    for (std::size_t i = 3; i < ads.size(); ++i) {
        if (ads[i].kind != "ads-write") continue;
        require(i + 1 < ads.size() && ads[i + 1].kind == "ads-read" && ads[i + 1].pin == ads[i].pin, "write without readback");
        got.push_back({ads[i].pin, ads[i].value});
        if (ads[i].pin == 0x0f || ads[i].pin == 0x10) require(ads[i].value == 0, "lead-off current source enabled");
    }
    require(got == want, "register writes differ from the breadboard plan");
}
void checkStreaming(int channels, int flags) {
    const auto mode = at("prompt", -1, 'M');
    for (std::size_t i = 0; i < mode; ++i) require(events[i].kind != "ads-write", "register written before the mode was chosen");
    std::size_t last = 0;
    for (std::size_t i = 0; i < events.size(); ++i) if (events[i].kind == "ads-write") last = i;
    const auto rdatac = at("ads-command", 0x10, 0, last), start = at("ads-command", 0x08, 0, rdatac);
    require(at("interrupt", -1, 0) < rdatac && rdatac < start, "RDATAC/START order differs");
    require(hostbench::packets == 1 && hostbench::lastPacket == 20 + 3 + 3 * channels + 2,
            "packet length does not carry the chip's channel count");
    require(::channels == channels && breadboardFlags == flags, "channel count or mode flag differs");
}
void checkHalted() {
    require(hostbench::halted, "fault did not halt");
    for (int pin : CONTROLS) require(hostbench::levels[pin] == 0, "control not parked low after the fault");
    if (has("spi", -1, 0)) require(has("spi-end", -1, 0), "SPI not ended after the fault");
    require(!has("ads-command", 0x10, 0) && hostbench::packets == 0, "streaming after the fault");
    require(::channels == 0, "capture state survived the fault");
}
void checkWaiting() {
    require(!hostbench::halted && !has("spi", -1, 0), "proceeded without fresh answers");
    checkParked();
    const auto& s = hostbench::scenario;
    if (s == "only-R") {
        const auto vcap = at("prompt", -1, 'V');
        for (std::size_t i = vcap; i < events.size(); ++i)
            require(!(events[i].kind == "latch" && events[i].pin == 5 && events[i].value == 0), "reset without V");
        return;
    }
    for (const auto& e : events) require(e.kind != "latch" || e.value == 0, "control raised without a fresh R");
}
void check(bool finished) {
    const auto& s = hostbench::scenario;
    checkConsoleAndPins();
    if (s == "guard") {
        require(!finished && events.size() == 4, "closed wiring gate allowed pin or SPI operations");
        return;
    }
    if (s == "gpio-failure") {
        checkHalted();
        require(!has("mode", 12, OUTPUT) && !has("mode", 8, OUTPUT), "GPIO failure enabled an output");
        return;
    }
    if (s == "six-channel" || s == "bad-id" || s == "readback-fault") { checkHalted(); return; }
    if (s == "no-input" || s == "queued" || s == "only-R") { require(!finished, "setup finished"); checkWaiting(); return; }
    require(finished && !hostbench::halted, "good breadboard scenario did not stream");
    checkParked();
    checkWakeAndReset();
    const int channels = s == "short-8" ? 8 : 4;
    const bool test = s != "short-8";
    checkRegisters(channels, test ? 0xd0 : 0xc0, test ? 0x65 : 0x61);
    checkStreaming(channels, test ? 1 : 2);
}
int main(int argc, char** argv) {
    try {
        require(argc == 2, "scenario argument required");
        using namespace hostbench;
        scenario = argv[1];
        completeSpi = true;
        transferHook = transfer;
        transactionHook = transaction;
        chipId = scenario == "short-8" ? 0x3e : scenario == "revision-id" ? 0xbc
               : scenario == "six-channel" ? 0x3d : scenario == "bad-id" ? 0x00 : 0x3c;
        if (scenario == "queued") input = {'R', 'V', 'T'};
        bool finished = false;
        try {
            setup();
            frames = true;
            onDataReady();
            loop();
            finished = true;
        } catch (const Stop&) {}
        check(finished);
    } catch (const std::exception& error) {
        std::cerr << "BREADBOARD_ASSERTION: " << error.what() << '\n';
        return 1;
    }
    std::cout << "breadboard sketch scenario passed\n";
}
