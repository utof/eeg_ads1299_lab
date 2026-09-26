// Execute the actual .ino against host doubles, stopping at first SPI.begin.
// Never enable a production gate: pytest changes only a temporary header copy.
#include <iostream>
#include <stdexcept>
#include "esp32_ads1299_bench.ino"
namespace hostbench {
std::vector<Event> events;
std::deque<char> input;
std::string scenario;
std::uint64_t elapsed=0;
void record(const std::string& kind,int pin,int value) {
    events.push_back({kind,pin,value,elapsed});
}
void printed(const char* text) {
    const std::string message(text);
    if(message.find("BENCH: verify ADS rails")!=std::string::npos) {
        record("prompt",-1,'R');
        if(scenario=="fresh" || scenario=="only-R" || scenario=="early-V")input.push_back('R');
        if(scenario=="early-V")input.push_back('V');
    }
    if(message.find("BENCH: measure VCAP1")!=std::string::npos) {
        record("prompt",-1,'V');
        if(scenario=="fresh")input.push_back('V');
    }
}
}
void require(bool condition,const char* message) {
    if(!condition)throw std::runtime_error(message);
}
std::size_t event(const std::string& kind,int pin,int value,std::size_t start=0) {
    for(std::size_t i=start;i<hostbench::events.size();++i) {
        const auto& e=hostbench::events[i];
        if(e.kind==kind && e.pin==pin && e.value==value)return i;
    }
    throw std::runtime_error("required actual-sketch event missing");
}
void checkConsole() {
    using namespace hostbench;
    require(events.size()>=4,"console initialization missing");
    require(event("console-baud",-1,460800)==0,"console baud or initialization order differs");
    require(event("console-format",-1,SERIAL_8N1)==1,"console format differs");
#if defined(EEGLAB_REV_A_S3)
    const int rx = scenario=="guard" ? -1 : 17;
    const int tx = scenario=="guard" ? -1 : 18;
#else
    const int rx = -1, tx = -1;
#endif
    require(event("console-rx",rx,0)==2,"wrong console RX or early external pin enable");
    require(event("console-tx",tx,0)==3,"wrong console TX or early external pin enable");
}
void check(bool spi) {
    checkConsole();
    using namespace hostbench;
    if(scenario=="guard") {
        require(!spi && events.size()==4,"review guard allowed hardware operations");return;
    }
    if(scenario=="gpio-failure") {
        require(!spi,"GPIO failure allowed SPI");
        for(std::size_t i=4;i<events.size();++i)
            require(events[i].kind=="latch" && events[i].value==0,"GPIO failure enabled an output");
        return;
    }
    const auto rails=event("prompt",-1,'R');
    for(int pin:{12,11,10,5,6,7,8}) {
        const auto low=event("latch",pin,0);
        const auto output=event("mode",pin,OUTPUT);
        require(low<output && output<rails,"actual adapter did not preload low before output");
    }
    if(scenario=="no-input" || scenario=="queued") {
        require(!spi,"missing or stale rail reply allowed SPI");
        for(const auto& e:events)
            require(e.kind!="latch" || e.value==0,"missing or stale rail reply allowed high output");
        return;
    }
    const auto clock=event("latch",8,1);
    const auto wake=event("latch",7,1);
    const auto vcap=event("prompt",-1,'V');
    require(rails<clock && rails<wake && clock<vcap && wake<vcap,"actual wake order differs");
    require(events[vcap].us-events[clock].us>=132000,"actual tPOR too short");
    require(events[vcap].us-events[wake].us>=132000,"actual PWDN wake interval too short");
    const auto released=event("latch",5,1);
    if(scenario=="only-R" || scenario=="early-V") {
        require(!spi,"missing or queued VCAP reply allowed SPI");
        for(std::size_t i=released+1;i<events.size();++i)
            require(!(events[i].kind=="latch" && events[i].pin==5),"reset without fresh VCAP reply");
        return;
    }
    require(spi,"fresh replies did not reach first SPI initialization");
    const auto low=event("latch",5,0,released+1);
    const auto high=event("latch",5,1,low+1);
    const auto spiAt=event("spi",-1,0);
    // Independent expected tuple, not the production constants under test.
    const int expectedSpiPins[]={12,13,11,10};
    for(int i=0;i<4;++i) {
        const auto argument=event("spi-pin",i,expectedSpiPins[i]);
        require(high<argument && argument<spiAt,"SPI pin tuple or boundary order differs");
    }
    require(vcap<low && low<high && high<spiAt,"actual reset/SPI ordering differs");
    require(events[high].us-events[low].us>=2,"actual reset pulse too short");
    require(events[spiAt].us-events[high].us>=10,"actual reset recovery too short");
}
int main(int argc,char** argv) {
    try {
        require(argc==2,"scenario argument required");
        hostbench::scenario=argv[1];
        if(hostbench::scenario=="queued")hostbench::input={'R','V'};
        bool spi=false;
        try { setup(); throw std::runtime_error("setup returned instead of stopping or reaching SPI"); }
        catch(const hostbench::SpiReached&) { spi=true; }
        catch(const hostbench::Stop&) {}
        check(spi);
    } catch(const std::exception& error) {
        std::cerr<<"SKETCH_ASSERTION: "<<error.what()<<'\n';return 1;
    }
    std::cout<<"actual sketch startup boundary passed\n";
}
