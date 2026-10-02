// Actual sketch, settled latch + boundary fault injection. Not MCU/rail emulation.
#include <algorithm>
#include <iostream>
#include <stdexcept>
#include "esp32_ads1299_bench.ino"
namespace hostbench {
std::vector<Event> events;
std::deque<char> input;
std::string scenario;
std::uint64_t elapsed=0;
std::uint64_t clockAt=0, sessionAt=0, armAt=0;
bool clockSeen=false, sessionSeen=false, faulted=false, halted=false;
bool postSetup=false, transmittingFrame=false;
unsigned packets=0, spiBegins=0, reads=0;
std::uint8_t regs[32]{};
unsigned pos=0;
std::uint8_t opcode=0;
void fault() { rails=false;latched=false;faulted=true; }
void record(const std::string& kind,int pin,int value) {
    events.push_back({kind,pin,value,elapsed});
    if(kind=="latch" && pin==14 && value) {sessionAt=elapsed;sessionSeen=true;}
    if(kind=="latch" && pin==9 && value) armAt=elapsed;
    if(kind=="latch" && pin==8 && value) {clockAt=elapsed;clockSeen=true;}
    if(kind=="spi")++spiBegins;
    if(kind=="packet")++packets;
}
void printed(const char* text) {
    const std::string s(text);
    if(s.find("BENCH: verify ADS rails")!=std::string::npos)input.push_back('R');
    if(s.find("BENCH: measure VCAP1")!=std::string::npos) {
        if(scenario=="vcap-fault")fault(); else input.push_back('V');
    }
    if(s.find("HALTED")!=std::string::npos) { halted=true;rails=true;deadline=elapsed+20000; }
}
void tickFaults() {
    if(faulted || halted)return;
    if(scenario=="no-ready")rails=false;
    if(scenario=="wait-fault" && clockSeen && elapsed-clockAt>=1000)fault();
    if(scenario=="reference-fault" && regs[0x17]==0 && regs[0x03]==0xe0 && elapsed>clockAt+151000)fault();
    if(scenario=="arm-fault" && levels[9] && elapsed-armAt>=1)fault();
}
void transaction() { pos=0; if(scenario=="transaction-fault" && clockSeen)fault(); }
std::uint8_t transferByte(std::uint8_t v) {
    ++reads;
    if(transmittingFrame) {
        if(scenario=="frame-fault" && pos==5)fault();
        return pos++==0 ? 0xc0 : 0;
    }
    const auto index=pos++;
    if(index==0){opcode=v;return 0;}
    if(index==1)return 0;
    const auto address=opcode&0x1f;
    if((opcode&0xe0)==0x40){regs[address]=v;return 0;}
    if((opcode&0xe0)==0x20)return address==0 ? 0x1c : regs[address];
    return 0;
}
void writer() {if(scenario=="write-fault")fault();}
}
void require(bool ok,const char* msg){if(!ok)throw std::runtime_error(msg);}
std::size_t at(const std::string& k,int pin,int value,std::size_t first=0) {
 for(std::size_t i=first;i<hostbench::events.size();++i){auto e=hostbench::events[i];if(e.kind==k && e.pin==pin && e.value==value)return i;}
 throw std::runtime_error("missing required trace event");
}
int main(int argc,char**argv) {
 try {
    require(argc==2,"scenario needed");using namespace hostbench; scenario=argv[1];
    completeSpi=true;tickHook=tickFaults;transactionHook=transaction;transferHook=transferByte;writeHook=writer;
    if(scenario=="wrap"){elapsed=0xffffff00ULL;deadline=elapsed+3000000;}
    if(scenario=="stuck-ready")stuckReady=true;
    if(scenario=="stuck-armed")stuckArmed=true;
    if(scenario=="no-armed")ignoreArm=true;
    try {
        setup();postSetup=true;
        if(scenario=="idle-fault" || scenario=="recover-fault") {fault();if(scenario=="recover-fault")rails=true;loop();}
        else { transmittingFrame=true;onDataReady();loop(); }
    } catch(const Stop&) {}
    const bool success=scenario=="good" || scenario=="wrap";
    if(success) {
        require(postSetup && !halted && packets==1,"good handshake/capture failed");
        auto session=at("latch",14,1), arm=at("latch",9,1), drop=at("latch",9,0,arm+1);
        require(session<arm && arm<drop,"fresh arm order");
        require(events[arm].us-events[session].us>=10,"READY stability too short");
        require(events[drop].us-events[arm].us>=10,"ARM pulse too short");
        for(int pin:{12,11,10,5,6,7,8})require(at("latch",pin,0)<session,"not parked before SESSION");
        require(drop<at("latch",8,1),"clock before confirmed arm");
        require(events[at("latch",5,0,at("latch",5,1)+1)].us-clockAt>=132000,"startup interval not preserved");
    } else {
        require(halted,"fault did not halt the actual sketch");
        require(levels[14]==0 && levels[9]==0,"SESSION/ARM not cleared");
        require(!latched,"hardware latch still on");
        for(int pin:{12,11,10,5,6,7,8})require(levels[pin]==0,"bus control not parked after failure");
        require(channels==0 && consumed==0 && overruns==0 && lastGoodMs==0,"capture state survived fault");
        require(edgeCount==0 && edgeMicros==0,"DRDY state survived fault");
        require(packets==(scenario=="write-fault" ? 1u : 0u),"packet committed after fault");
        const auto count=std::count_if(events.begin(),events.end(),[](const Event&e){return e.kind=="latch"&&e.pin==9&&e.value;});
        require(count<=1,"automatic rearm after restored rails");
        if(scenario=="frame-fault")require(pos<=6,"SPI continued after fault");
    }
 }catch(const std::exception&e){std::cerr<<"C2_ASSERTION: "<<e.what()<<'\n';return 1;}
 std::cout<<"actual-sketch C2 scenario passed\n";
}
