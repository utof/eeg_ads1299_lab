#pragma once
// C2/C3 handshake only. Valid control power and the real latched BUS_OE are
// prerequisites. Polling does not qualify brownout timing or broken feedback.
#include <cstdint>

namespace eeglab {
constexpr int C2_SESSION = 14;
constexpr int C2_ARM_REQ = 9;
constexpr int C2_READY = 15;
constexpr int C2_ARMED = 16;

class C2Interlock {
    enum class Phase { Cold, Parked, Active, Faulted };
    Phase phase_=Phase::Cold;
    template<class Io> bool reject(Io& io) {
        phase_=Phase::Faulted;
        io.level(C2_SESSION,0);io.level(C2_ARM_REQ,0);
        return false;
    }
public:
    bool started() const { return phase_!=Phase::Cold; }
    bool monitoring() const { return phase_==Phase::Active || phase_==Phase::Faulted; }
    void invalidate() { phase_=Phase::Faulted; }
    template<class Io> bool prepare(Io& io) {
        if(started())return reject(io);
        phase_=Phase::Parked;
        io.level(C2_SESSION,0);io.level(C2_ARM_REQ,0);
        io.output(C2_SESSION);io.output(C2_ARM_REQ);
        io.inputPulldown(C2_READY);io.inputPulldown(C2_ARMED);
        io.waitUs(10); // establish clear and an explicit low arm before any request
        if(io.read(C2_READY) || io.read(C2_ARMED))return reject(io);
        return true;
    }
    template<class Io> bool arm(Io& io) {
        if(phase_!=Phase::Parked)return reject(io);
        if(io.read(C2_READY) || io.read(C2_ARMED))return reject(io);
        io.level(C2_SESSION,1);
        const std::uint32_t begin=io.nowUs();
        std::uint32_t highSince=begin;
        bool high=false;
        for(;;) {
            const auto now=io.nowUs();
            if(io.read(C2_ARMED))return reject(io); // no unsolicited/stale latch
            if(io.read(C2_READY)) {
                const auto observed=io.nowUs();
                if(!high){high=true;highSince=observed;}
                if(std::uint32_t(observed-highSince)>=10)break;
            } else high=false;
            // A bounded software wait, NOT a supervisor shutdown guarantee.
            if(std::uint32_t(now-begin)>=1000000)return reject(io);
            io.waitUs(1);
        }
        io.level(C2_ARM_REQ,1);
        const std::uint32_t pulse=io.nowUs();
        while(std::uint32_t(io.nowUs()-pulse)<10) {
            if(!io.read(C2_READY))return reject(io);
            io.waitUs(1);
        }
        io.level(C2_ARM_REQ,0);
        if(!io.read(C2_READY) || !io.read(C2_ARMED))return reject(io);
        phase_=Phase::Active;
        return true;
    }
    template<class Io> bool valid(Io& io) const {
        return phase_==Phase::Active && io.read(C2_READY) && io.read(C2_ARMED);
    }
};
} // namespace eeglab
