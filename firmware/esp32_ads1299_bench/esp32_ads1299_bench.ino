/*
  BENCH ONLY. No electrode on a person, including bias/reference electrodes.
  Requires a fully populated, documented ADS1299-x AFE board, 3.3-V digital
  interface, internal oscillator and internal-reference support. The board's
  analog power arrangement is NOT supplied by this sketch or pin map.

  Validation scopes: portable helper tests, target compilation and physical
  measurements are separate. See docs/ESP32_S3_TARGET_BUILD.md for exact build
  evidence. No "passed tests" claim authorizes GPIO or human connection.
*/
#include <Arduino.h>
#include <SPI.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include "board_config.h"
#include "portable_core.h"
#if defined(EEGLAB_REV_A_S3)
#include <driver/gpio.h>
#include "rev_a_startup.h"
#include "c2_interlock.h"
#endif

// Target guards live with the explicit profile selection in board_config.h.

SPISettings settings(1000000,MSBFIRST,SPI_MODE1);
WiFiUDP udp;
IPAddress host;
portMUX_TYPE irqMux=portMUX_INITIALIZER_UNLOCKED;
volatile uint32_t edgeCount=0,edgeMicros=0;
uint32_t consumed=0,overruns=0,lastGoodMs=0;
uint8_t channels=0;
bool spiOpened=false,transactionOpen=false;
#if defined(EEGLAB_REV_A_S3)
eeglab::C2Interlock interlock;
bool controlsConfigured=false;
#endif
void requireBus();
[[noreturn]] void fail(const char* why);
void waitBenchMs(unsigned value) {
    for(unsigned i=0;i<value;++i){requireBus();delay(1);}
    requireBus();
}


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
[[noreturn]] void fail(const char* why) {
#if defined(EEGLAB_REV_A_S3)
    // Drop SESSION BEFORE potentially blocking console or peripheral teardown.
    // Best-effort GPIO cleanup is not protection against a failed MCU/rail.
    if(interlock.started()) {
        interlock.invalidate();
        gpio_set_level(static_cast<gpio_num_t>(eeglab::C2_SESSION),0);
        gpio_set_level(static_cast<gpio_num_t>(eeglab::C2_ARM_REQ),0);
        detachInterrupt(digitalPinToInterrupt(PIN_DRDY));
        if(transactionOpen){SPI.endTransaction();transactionOpen=false;}
        if(spiOpened){SPI.end();spiOpened=false;}
        constexpr int controls[]={PIN_SCLK,PIN_MOSI,PIN_CS,PIN_RESET,PIN_START,PIN_PWDN,PIN_CLKSEL};
        for(int pin:controls)gpio_set_level(static_cast<gpio_num_t>(pin),0);
        if(controlsConfigured)for(int pin:controls)pinMode(pin,OUTPUT);
        portENTER_CRITICAL(&irqMux);
        edgeCount=0;edgeMicros=0;
        portEXIT_CRITICAL(&irqMux);
        channels=0;consumed=0;overruns=0;lastGoodMs=0;
    }
#else
    digitalWrite(PIN_START,LOW);
    digitalWrite(PIN_PWDN,LOW); // START low alone does not cancel a command-started conversion
    #endif
    Serial.print("\nHALTED / BENCH ONLY; CAPTURE INVALID: ");Serial.println(why);
    while(true)delay(1000);
}
void selectChip() {
    requireBus();SPI.beginTransaction(settings);transactionOpen=true;
    requireBus();digitalWrite(PIN_CS,LOW);delayMicroseconds(3);
}
void releaseChip() {
    requireBus();delayMicroseconds(3);requireBus();digitalWrite(PIN_CS,HIGH);
    SPI.endTransaction();transactionOpen=false;delayMicroseconds(3);requireBus();
}
uint8_t busTransfer(uint8_t value) {
    requireBus();const auto received=SPI.transfer(value);requireBus();return received;
}
void command(uint8_t op) { selectChip();busTransfer(op);delayMicroseconds(3);releaseChip(); }
void writeReg(uint8_t addr,uint8_t value) {
    selectChip();busTransfer(0x40|addr);delayMicroseconds(3);
    busTransfer(0);delayMicroseconds(3);busTransfer(value);delayMicroseconds(3);releaseChip();
}
uint8_t readReg(uint8_t addr) {
    selectChip();busTransfer(0x20|addr);delayMicroseconds(3);
    busTransfer(0);delayMicroseconds(3);uint8_t r=busTransfer(0);releaseChip();return r;
}
void checkedReg(uint8_t addr,uint8_t value,uint8_t mask=0xff) {
    writeReg(addr,value);
    if((readReg(addr)&mask)!=(value&mask))fail("Register readback mismatch; inspect supply/clock/SPI.");
}
#if defined(EEGLAB_REV_A_S3)
struct C2Io {
    void level(int pin,int value) {
        const auto status=gpio_set_level(static_cast<gpio_num_t>(pin),value);
        if(status!=ESP_OK)fail("C2 GPIO latch operation failed.");
    }
    void output(int pin) { pinMode(pin,OUTPUT); }
    void inputPulldown(int pin) { pinMode(pin,INPUT_PULLDOWN); }
    bool read(int pin) { return digitalRead(pin)==HIGH; }
    uint32_t nowUs() { return micros(); }
    void waitUs(unsigned value) { delayMicroseconds(value); }
};
C2Io c2io;
#endif
void requireBus() {
#if defined(EEGLAB_REV_A_S3)
    if(!interlock.valid(c2io))fail("C2 not armed or rail fault; restart the complete reviewed sequence.");
#endif
}
#if defined(EEGLAB_REV_A_S3)
void awaitBenchKey(char key, const char* message) {
    // Ignore queued acknowledgments: each measurement needs a fresh response.
    while(Serial.available()>0) {
        if(interlock.monitoring())requireBus();
        Serial.read();
    }
    if(interlock.monitoring())requireBus();
    Serial.println(message);
    while(true) {
        if(interlock.monitoring())requireBus();
        if(Serial.available()>0 && Serial.read()==key) {
            if(interlock.monitoring())requireBus();
            return;
        }
        delay(10);
    }
}
struct RevAStartupIo {
    void level(int pin, int value) {
        if(value || interlock.monitoring())requireBus();
        // ESP-IDF permits setting the output latch before pinMode enables it.
        // Arduino digitalWrite before pinMode is not a portable substitute.
        if(gpio_set_level(static_cast<gpio_num_t>(pin),value)!=ESP_OK) {
            fail("GPIO latch operation failed.");
        }
    }
    void output(int pin) { pinMode(pin,OUTPUT); }
    void waitMs(unsigned value) { waitBenchMs(value); }
    void waitUs(unsigned value) { requireBus();delayMicroseconds(value);requireBus(); }
    void confirmRailsAndInputs() {
        controlsConfigured=true;
        awaitBenchKey('R',"BENCH: verify ADS rails stable and passive startup fixture holds analog inputs low; then type R. No body or powered source.");
        if(!interlock.arm(c2io))fail("C2 fresh arm failed; no automatic retry.");
    }
    void confirmVcap1() {
        awaitBenchKey('V',"BENCH: measure VCAP1 > 1.1 V with ADS rails still stable; then type V. This firmware does not sense those voltages.");
    }
};
#endif
void setup() {
#if defined(EEGLAB_REV_A_S3)
    // The distributed false review gate retains the onboard UART console.
    // External-console pins are not configured before exact interface review.
    if(BOARD_PROFILE_REVIEWED) {
        Serial.begin(CONSOLE_BAUD, SERIAL_8N1, CONSOLE_RX, CONSOLE_TX);
    } else {
        Serial.begin(460800);
    }
#else
    Serial.begin(460800);
#endif
    delay(500);
    Serial.println("ADS1299 learning lab. BENCH ONLY; remove ALL body electrodes.");
    if(!BOARD_PROFILE_REVIEWED) {
        // No ADS control pin is configured until this gate is acknowledged.
        Serial.println("Set BOARD_PROFILE_REVIEWED only after reviewing your exact board and power rails.");
        while(true)delay(1000);
    }
#if defined(EEGLAB_REV_A_S3)
    if(!interlock.prepare(c2io))fail("C2 did not clear while SESSION was low.");
    RevAStartupIo startup;
    eeglab::startRevA(startup);
#else
    pinMode(PIN_CS,OUTPUT);digitalWrite(PIN_CS,HIGH);
    pinMode(PIN_START,OUTPUT);digitalWrite(PIN_START,LOW);
    pinMode(PIN_RESET,OUTPUT);digitalWrite(PIN_RESET,LOW);
    pinMode(PIN_PWDN,OUTPUT);digitalWrite(PIN_PWDN,HIGH);
#endif
    pinMode(PIN_DRDY,INPUT);
    requireBus();
    SPI.begin(PIN_SCLK,PIN_MISO,PIN_MOSI,PIN_CS);
    spiOpened=true;
    requireBus();
#if !defined(EEGLAB_REV_A_S3)
    delay(500);digitalWrite(PIN_RESET,HIGH);delay(500);
#endif
    command(0x11); // SDATAC: stop read-data-continuous before register access
    command(0x0a); // STOP: pin START is held low; START/STOP commands control conversion
    const uint8_t id=readReg(0);
    if((id&0x1c)!=0x1c||(id&3)==3)fail("Not a recognized ADS1299-x ID.");
    channels=4+2*(id&3);
#if defined(EEGLAB_REV_A_S3)
    if(channels!=EXPECTED_ADS_CHANNELS)fail("Selected Rev A profile requires ADS1299-4.");
#endif
    Serial.printf("ID=0x%02x; %u physical channels; 250 SPS; gain 24\n",id,channels);
    checkedReg(0x01,0x96); // 250 SPS at 2.048-MHz clock, clock output disabled
    checkedReg(0x02,USE_INTERNAL_TEST?0xd0:0xc0); // ~0.9765625-Hz internal test, or test off
    checkedReg(0x03,0xe0,0xfe); // internal reference ON; bias driver OFF; ignore read-only BIAS_STAT
    checkedReg(0x04,0); // no lead-off excitation
    for(uint8_t i=0;i<channels;++i)checkedReg(0x05+i,USE_INTERNAL_TEST?0x65:0x61);
    for(uint8_t addr=0x0d;addr<=0x11;++addr)checkedReg(addr,0); // bias and lead-off sense OFF
    checkedReg(0x15,0); // SRB1 OFF
    checkedReg(0x17,0); // continuous conversions, lead-off comparator OFF
    waitBenchMs(500); // reference settling; verify actual reference capacitors/voltage on bench
    if(USE_WIFI_UDP) {
        if(!host.fromString(UDP_HOST))fail("Invalid UDP_HOST");
        requireBus();WiFi.mode(WIFI_STA);WiFi.begin(WIFI_SSID,WIFI_PASSWORD);requireBus();
        uint32_t start=millis();
        while(WiFi.status()!=WL_CONNECTED&&millis()-start<15000)waitBenchMs(100);
        if(WiFi.status()!=WL_CONNECTED)fail("Wi-Fi timeout");
        requireBus();WiFi.setSleep(false);requireBus();
        if(!udp.begin(9001))fail("UDP initialization failed");
        requireBus();
    }
    attachInterrupt(digitalPinToInterrupt(PIN_DRDY),onDataReady,FALLING);
    command(0x10); // RDATAC
    command(0x08); // START while physical START stays low
    requireBus();lastGoodMs=millis();
}
void loop() {
    requireBus();
    uint32_t seq,tick;snapshot(seq,tick);
    if(seq==consumed) {
        if(millis()-lastGoodMs>2000)fail("No valid data for 2 s; inspect DRDY and clock.");
        delayMicroseconds(50);return;
    }
    overruns+=(seq-consumed)-1; // DRDY edges not serviced are never silently invented
    consumed=seq;
    uint8_t frame[27];
    selectChip();
    for(uint8_t i=0;i<3+3*channels;++i)frame[i]=busTransfer(0);
    releaseChip();
    uint32_t after,afterTick;snapshot(after,afterTick);
    if(after!=seq){++overruns;return;} // conversion changed while reading: discard candidate
    if((frame[0]&0xf0)!=0xc0)fail("Invalid native status prefix; SPI frame alignment failed.");
    uint8_t wire[eeglab::MAX_PACKET_SIZE];
    const uint8_t flags=(USE_INTERNAL_TEST?1:2)|(overruns?8:0);
    const std::size_t size=eeglab::packet(wire,sizeof(wire),frame,channels,24,250,flags,seq,tick,overruns);
    if(size==0)fail("Packet encoding failed");
    requireBus();
    if(USE_WIFI_UDP) {
        if(udp.beginPacket(host,UDP_PORT)) {
            requireBus();udp.write(wire,size);requireBus();udp.endPacket();
        }
        // Loss in radio/network is detected from DRDY-derived sequence numbers.
    } else {
        Serial.write(wire,size); // binary stream, not a Serial Plotter CSV
    }
    requireBus();lastGoodMs=millis();
}
