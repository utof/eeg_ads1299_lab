/*
  BENCH ONLY. No electrode on a person, including bias/reference electrodes.
  Requires a fully populated, documented ADS1299-x AFE board, 3.3-V digital
  interface, internal oscillator and internal-reference support. The board's
  analog power arrangement is NOT supplied by this sketch or pin map.

  Validation: portable_core.h is native-C++ compiled/tested. This entire sketch
  has NOT been compiled for ESP32 or exercised on hardware in the supplied run.
  Read docs/RESULTS.md. No "passed tests" claim authorizes human connection.
*/
#include <Arduino.h>
#include <SPI.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include "board_config.h"
#include "portable_core.h"

#if !defined(CONFIG_IDF_TARGET_ESP32)
#error "Example pin map is for original ESP32 only. Review/port it for your exact MCU."
#endif

SPISettings settings(1000000,MSBFIRST,SPI_MODE1);
WiFiUDP udp;
IPAddress host;
portMUX_TYPE irqMux=portMUX_INITIALIZER_UNLOCKED;
volatile uint32_t edgeCount=0,edgeMicros=0;
uint32_t consumed=0,overruns=0,lastGoodMs=0;
uint8_t channels=0;

void IRAM_ATTR onDataReady() {
    portENTER_CRITICAL_ISR(&irqMux);
    ++edgeCount;edgeMicros=micros();
    portEXIT_CRITICAL_ISR(&irqMux);
}
void snapshot(uint32_t &count,uint32_t &tick) {
    portENTER_CRITICAL(&irqMux);
    count=edgeCount;tick=edgeMicros;
    portEXIT_CRITICAL(&irqMux);
}
void fail(const char* why) {
    digitalWrite(PIN_START,LOW);
    digitalWrite(PIN_PWDN,LOW); // START low alone does not cancel a command-started conversion
    Serial.print("\nHALTED / BENCH ONLY: ");Serial.println(why);
    while(true)delay(1000);
}
void selectChip() { SPI.beginTransaction(settings);digitalWrite(PIN_CS,LOW);delayMicroseconds(3); }
void releaseChip() { delayMicroseconds(3);digitalWrite(PIN_CS,HIGH);SPI.endTransaction();delayMicroseconds(3); }
void command(uint8_t op) { selectChip();SPI.transfer(op);delayMicroseconds(3);releaseChip(); }
void writeReg(uint8_t addr,uint8_t value) {
    selectChip();SPI.transfer(0x40|addr);delayMicroseconds(3);
    SPI.transfer(0);delayMicroseconds(3);SPI.transfer(value);delayMicroseconds(3);releaseChip();
}
uint8_t readReg(uint8_t addr) {
    selectChip();SPI.transfer(0x20|addr);delayMicroseconds(3);
    SPI.transfer(0);delayMicroseconds(3);uint8_t r=SPI.transfer(0);releaseChip();return r;
}
void checkedReg(uint8_t addr,uint8_t value,uint8_t mask=0xff) {
    writeReg(addr,value);
    if((readReg(addr)&mask)!=(value&mask))fail("Register readback mismatch; inspect supply/clock/SPI.");
}
void setup() {
    Serial.begin(460800);delay(500);
    Serial.println("ADS1299 learning lab. BENCH ONLY; remove ALL body electrodes.");
    if(!BOARD_PROFILE_REVIEWED) {
        // No ADS control pin is configured until this gate is acknowledged.
        Serial.println("Set BOARD_PROFILE_REVIEWED only after reviewing your exact board and power rails.");
        while(true)delay(1000);
    }
    pinMode(PIN_CS,OUTPUT);digitalWrite(PIN_CS,HIGH);
    pinMode(PIN_START,OUTPUT);digitalWrite(PIN_START,LOW);
    pinMode(PIN_RESET,OUTPUT);digitalWrite(PIN_RESET,LOW);
    pinMode(PIN_PWDN,OUTPUT);digitalWrite(PIN_PWDN,HIGH);
    pinMode(PIN_DRDY,INPUT);
    SPI.begin(PIN_SCLK,PIN_MISO,PIN_MOSI,PIN_CS);
    delay(500);digitalWrite(PIN_RESET,HIGH);delay(500);
    command(0x11); // SDATAC: stop read-data-continuous before register access
    command(0x0a); // STOP: pin START is held low; START/STOP commands control conversion
    const uint8_t id=readReg(0);
    if((id&0x1c)!=0x1c||(id&3)==3)fail("Not a recognized ADS1299-x ID.");
    channels=4+2*(id&3);
    Serial.printf("ID=0x%02x; %u physical channels; 250 SPS; gain 24\n",id,channels);
    checkedReg(0x01,0x96); // 250 SPS at 2.048-MHz clock, clock output disabled
    checkedReg(0x02,USE_INTERNAL_TEST?0xd0:0xc0); // ~0.9765625-Hz internal test, or test off
    checkedReg(0x03,0xe0,0xfe); // internal reference ON; bias driver OFF; ignore read-only BIAS_STAT
    checkedReg(0x04,0); // no lead-off excitation
    for(uint8_t i=0;i<channels;++i)checkedReg(0x05+i,USE_INTERNAL_TEST?0x65:0x61);
    for(uint8_t addr=0x0d;addr<=0x11;++addr)checkedReg(addr,0); // bias and lead-off sense OFF
    checkedReg(0x15,0); // SRB1 OFF
    checkedReg(0x17,0); // continuous conversions, lead-off comparator OFF
    delay(500); // reference settling; verify actual reference capacitors/voltage on bench
    if(USE_WIFI_UDP) {
        if(!host.fromString(UDP_HOST))fail("Invalid UDP_HOST");
        WiFi.mode(WIFI_STA);WiFi.begin(WIFI_SSID,WIFI_PASSWORD);
        uint32_t start=millis();
        while(WiFi.status()!=WL_CONNECTED&&millis()-start<15000)delay(100);
        if(WiFi.status()!=WL_CONNECTED)fail("Wi-Fi timeout");
        WiFi.setSleep(false);
        if(!udp.begin(9001))fail("UDP initialization failed");
    }
    attachInterrupt(digitalPinToInterrupt(PIN_DRDY),onDataReady,FALLING);
    command(0x10); // RDATAC
    command(0x08); // START while physical START stays low
    lastGoodMs=millis();
}
void loop() {
    uint32_t seq,tick;snapshot(seq,tick);
    if(seq==consumed) {
        if(millis()-lastGoodMs>2000)fail("No valid data for 2 s; inspect DRDY and clock.");
        delayMicroseconds(50);return;
    }
    overruns+=(seq-consumed)-1; // DRDY edges not serviced are never silently invented
    consumed=seq;
    uint8_t frame[27];
    selectChip();
    for(uint8_t i=0;i<3+3*channels;++i)frame[i]=SPI.transfer(0);
    releaseChip();
    uint32_t after,afterTick;snapshot(after,afterTick);
    if(after!=seq){++overruns;return;} // conversion changed while reading: discard candidate
    if((frame[0]&0xf0)!=0xc0)fail("Invalid native status prefix; SPI frame alignment failed.");
    uint8_t wire[eeglab::MAX_PACKET_SIZE];
    const uint8_t flags=(USE_INTERNAL_TEST?1:2)|(overruns?8:0);
    const std::size_t size=eeglab::packet(wire,sizeof(wire),frame,channels,24,250,flags,seq,tick,overruns);
    if(size==0)fail("Packet encoding failed");
    if(USE_WIFI_UDP) {
        if(udp.beginPacket(host,UDP_PORT)) {udp.write(wire,size);udp.endPacket();}
        // Loss in radio/network is detected from DRDY-derived sequence numbers.
    } else {
        Serial.write(wire,size); // binary stream, not a Serial Plotter CSV
    }
    lastGoodMs=millis();
}
