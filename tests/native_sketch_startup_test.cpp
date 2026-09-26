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
void check(bool spi) {
    using namespace hostbench;
    if(scenario=="guard") {
        require(!spi && events.empty(),"review guard allowed hardware operations");return;
    }
    if(scenario=="gpio-failure") {
        require(!spi,"GPIO failure allowed SPI");
        for(const auto& e:events)require(e.kind=="latch" && e.value==0,"GPIO failure enabled an output");
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
