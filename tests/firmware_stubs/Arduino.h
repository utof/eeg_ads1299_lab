#pragma once
// Host-only compile/execution double. No peripheral/voltage simulation.
#include <cstddef>
#include <cstdint>
#include <deque>
#include <string>
#include <vector>
#define IRAM_ATTR
#define LOW 0
#define HIGH 1
#define OUTPUT 1
#define INPUT 0
#define FALLING 2
using portMUX_TYPE = int;
constexpr int portMUX_INITIALIZER_UNLOCKED = 0;
#define portENTER_CRITICAL_ISR(p) ((void)(p))
#define portEXIT_CRITICAL_ISR(p) ((void)(p))
#define portENTER_CRITICAL(p) ((void)(p))
#define portEXIT_CRITICAL(p) ((void)(p))
namespace hostbench {
struct Event { std::string kind; int pin; int value; std::uint64_t us; };
struct Stop {};
struct SpiReached {};
extern std::vector<Event> events;
extern std::deque<char> input;
extern std::string scenario;
extern std::uint64_t elapsed;
void record(const std::string& kind, int pin = -1, int value = 0);
void printed(const char* text);
}
struct SerialDouble {
    void begin(unsigned) {}
    int available() { return static_cast<int>(hostbench::input.size()); }
    int read() {
        if(hostbench::input.empty())return -1;
        char c=hostbench::input.front();hostbench::input.pop_front();
        hostbench::record("read",-1,c);return c;
    }
    void print(const char* text) { hostbench::printed(text); }
    void println(const char* text) { hostbench::printed(text); }
    template<class... Args> void printf(const char*, Args...) {}
    std::size_t write(const std::uint8_t*, std::size_t n) { return n; }
};
inline SerialDouble Serial;
inline void delay(unsigned ms) {
    hostbench::elapsed+=1000ULL*ms;
    if(hostbench::elapsed>2000000)throw hostbench::Stop{};
}
inline void delayMicroseconds(unsigned us) { hostbench::elapsed+=us; }
inline std::uint32_t micros() { return static_cast<std::uint32_t>(hostbench::elapsed); }
inline std::uint32_t millis() { return micros()/1000; }
inline void digitalWrite(int pin,int value) { hostbench::record("write",pin,value); }
inline void pinMode(int pin,int mode) { hostbench::record("mode",pin,mode); }
inline int digitalPinToInterrupt(int pin) { return pin; }
inline void attachInterrupt(int,void (*)(),int) { hostbench::record("interrupt"); }
