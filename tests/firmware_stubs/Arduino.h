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
#define INPUT_PULLDOWN 3
#define FALLING 2
constexpr unsigned SERIAL_8N1=0x800001c;
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
// A settled C2 latch model for software traces only; no rail/threshold timing model.
inline int levels[40]{};
inline int lastRead[40]{};
inline bool hasRead[40]{};
inline bool rails=true, latched=false, ignoreArm=false, stuckArmed=false, stuckReady=false;
inline bool completeSpi=false;
inline std::uint64_t deadline=2000000;
inline void (*tickHook)()=nullptr;
inline std::uint8_t (*transferHook)(std::uint8_t)=nullptr;
inline void (*transactionHook)()=nullptr;
inline void (*writeHook)()=nullptr;
inline void tick() {
    if(tickHook)tickHook();
    if(!rails || !levels[14])latched=false;
}
inline void pinWritten(int pin,int value) {
    tick();
    const int previous=levels[pin];levels[pin]=value;
    if(pin==14 && !value)latched=false;
    if(pin==9 && value && !previous && levels[14] && rails && !ignoreArm)latched=true;
}

}
struct SerialDouble {
    void begin(unsigned baud,unsigned config=SERIAL_8N1,int rx=-1,int tx=-1) {
        hostbench::record("console-baud",-1,static_cast<int>(baud));
        hostbench::record("console-format",-1,static_cast<int>(config));
        hostbench::record("console-rx",rx);
        hostbench::record("console-tx",tx);
    }
    int available() { return static_cast<int>(hostbench::input.size()); }
    int read() {
        if(hostbench::input.empty())return -1;
        char c=hostbench::input.front();hostbench::input.pop_front();
        hostbench::record("read",-1,c);return c;
    }
    void print(const char* text) { hostbench::printed(text); }
    void println(const char* text) { hostbench::printed(text); }
    template<class... Args> void printf(const char*, Args...) {}
    std::size_t write(const std::uint8_t*, std::size_t n) {
        hostbench::record("packet",-1,static_cast<int>(n));
        if(hostbench::writeHook)hostbench::writeHook();
        return n;
    }
};
inline SerialDouble Serial;
inline void delay(unsigned ms) {
    hostbench::elapsed+=1000ULL*ms;
    hostbench::tick();
    if(hostbench::elapsed>hostbench::deadline)throw hostbench::Stop{};
}
inline void delayMicroseconds(unsigned us) { hostbench::elapsed+=us;hostbench::tick(); }
inline std::uint32_t micros() { return static_cast<std::uint32_t>(hostbench::elapsed); }
inline std::uint32_t millis() { return micros()/1000; }
inline void digitalWrite(int pin,int value) { hostbench::record("write",pin,value);hostbench::pinWritten(pin,value); }
inline void pinMode(int pin,int mode) { hostbench::record("mode",pin,mode); }
inline int digitalPinToInterrupt(int pin) { return pin; }
inline void attachInterrupt(int,void (*)(),int) { hostbench::record("interrupt"); }

inline int digitalRead(int pin) {
    hostbench::tick();
    const int value=pin==15 ? ((hostbench::rails && hostbench::levels[14]) || hostbench::stuckReady) :
                    pin==16 ? (hostbench::latched || hostbench::stuckArmed) : hostbench::levels[pin];
    if(!hostbench::hasRead[pin] || hostbench::lastRead[pin]!=value) {
        hostbench::record("read-pin",pin,value);
        hostbench::lastRead[pin]=value;hostbench::hasRead[pin]=true;
    }
    return value;
}
inline void detachInterrupt(int pin) { hostbench::record("detach",pin); }
