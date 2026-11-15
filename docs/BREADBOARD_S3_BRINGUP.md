# Breadboard ADS1299 + ESP32-S3: bring-up card

A step-by-step card for a hand-soldered **ADS1299-4** (TQFP-64) on an adapter,
wired on a breadboard to an **ESP32-S3-DevKitC-1-N8R8**, powered only from a
battery power bank. It reuses this repository's firmware (the separate
breadboard build) and laptop tools. It comes from a review of the original build
guide against the TI ADS1299 datasheet (SBAS499C) and Espressif's DevKitC-1 v1.1
documents. **Nothing here has been built or measured yet.** The Rev A PCB is a
separate, later design; its firmware build and gates are unchanged.

New to the multimeter or breadboard? Do the two short exercises in
[BREADBOARD_FIRST_STEPS.md](BREADBOARD_FIRST_STEPS.md) first (continuity mapping
and DC volts). You need the meter's beeper and DC volts here all the time.

> **Electrode recording on a person is not implemented.** The firmware has only
> two modes, both inside the chip: the internal test signal and shorted inputs.
> An electrode mode needs your separate, explicit decision first (see the TODO at
> the end). Until then no electrode goes on a person.

## 1. Safety rules (read first)

1. **Battery only.** The chip's 5 V comes from a power bank. The DevKit gets power
   from a laptop running on battery (charger unplugged) or from the power bank.
   No wall charger, monitor/HDMI, Ethernet, powered USB hub, oscilloscope, bench
   supply or soldering iron may be connected to, or touching, the rig while it
   runs. Unplug the iron and put it away.
2. **Plain 5 V only.** Use a plain USB-A port of the power bank. Never a
   fast-charge (PD/QC) adapter or a "trigger"/"decoy" board: 9-12 V destroys the
   chip at once (absolute maximum 5.5 V). Measure the 5 V every session before
   you connect the chip.
3. **Never pull out only the chip's power wires while the signal wires are
   still in.** The ESP32 would push 3.3 V into an unpowered chip. Disconnect all
   wires or none. To switch off: AFE 5 V first, then the DevKit.
4. **The bias electrode lead gets 1 Mohm, not 4.7 kohm.** That keeps any steady
   current into a person below about 5 uA, even if you touch the laptop or board.
5. **Never turn on the chip's lead-off currents with a person attached.** The
   firmware keeps them off (LOFF_SENSP/LOFF_SENSN = 0x00); do not change that.
6. Wear the wrist strap when you handle the chip (it is static-sensitive).
7. Not a medical device. Nobody with a pacemaker or implant. Clean, intact skin
   only. Stop if you feel tingling or itching, or see redness.

## 2. Wiring: DevKit to chip

DevKit pin numbers count from the **3V3 end** of header J1 (J1.1 = 3V3, J1.3 = RST,
J1.21 = 5V, J1.22 = GND). The board prints GPIO numbers, not pin numbers. Check
them on your actual board; clones can differ.

| Chip leg | Signal | S3 GPIO | DevKit pin | Parts on the breadboard | Notes |
|---|---|---|---|---|---|
| 40 | SCLK | GPIO12 | J1.18 | 1 kohm in series; optional 47 kohm to GND at the chip | SPI clock |
| 34 | DIN | GPIO11 | J1.17 | 1 kohm in series; optional 47 kohm to GND | ESP32 to chip (MOSI) |
| 43 | DOUT | GPIO13 | J1.19 | plain wire (optional 33-100 ohm at the chip) | chip to ESP32 (MISO) |
| 39 | CS | GPIO10 | J1.16 | 1 kohm in series; optional 47 kohm to GND | chip select |
| 47 | DRDY | GPIO4 | J1.4 | plain wire | "data ready", an input |
| 36 | RESET | GPIO5 | J1.5 | 1 kohm in series + 47 kohm to GND | **not** the DevKit's RST pin (J1.3) |
| 38 | START | GPIO6 | J1.6 | 1 kohm in series + 47 kohm to GND | stays low; conversions start by command |
| 35 | PWDN | GPIO7 | J1.7 | 1 kohm in series + 47 kohm to GND | low = chip powered down |
| 52 | CLKSEL | GPIO8 | J1.12 | 1 kohm in series + 47 kohm to GND | replaces the guide's 10 kohm to 3.3 V |
| 48, 50 | DVDD | 3V3 | J1.1 | 100 ohm for the first-power test only, then a plain wire | DevKit regulator |
| 33, 49, 51 + all AVSS | ground | GND | J1.22 | one wire to the star point | |
| 19, 21, 22, 54, 56, 59 | AVDD 5 V | none | J1.21 left unconnected | from the power bank (section 3) | never from the DevKit 5V pin |

Leave GPIO14 (J1.20), GPIO9 (J1.15), GPIO15 (J1.8) and GPIO16 (J1.9)
unconnected: they belong to the Rev A safety board. Avoid GPIO0, 3, 45, 46
(boot straps), 19/20 (USB), 35-37 (PSRAM), 43/44 (USB-UART bridge) and 38 (LED).

The other chip legs (all on the adapter):

- 25 (VREFN), 31 (RESV1), 41 (DAISY_IN): straight to ground.
- 37 (CLK) and 42, 44, 45, 46 (GPIO1-4): 10 kohm each to ground.
- 1-9, 11, 13, 15 (unused inputs, stage 1): tied to the 5 V bus.
- 17 (SRB1): to the reference electrode through 4.7 kohm. 18 (SRB2): open.
- 61-63: 1 Mohm in parallel with 1.5 nF C0G (bias feedback). 63 (BIASOUT):
  through **1 Mohm** to the bias electrode. 60 and 62 (BIASREF, BIASIN): open.
- 16, 14, 12, 10 (channels 1-4): through 4.7 kohm to their electrodes.
- 27, 29 (NC) and 64 (RESERVED): open.

Electrode jacks and their series resistors go on their own small perfboard,
soldered to the jack wires, never in breadboard rows (one row off lands on 5 V).
Keep the DevKit's antenna end at least 10-15 cm from the adapter and the leads.

## 3. Power

```
power bank USB-A port --USB-A plug board--+--10 ohm--+-- AVDD rail (legs 19,21,22,54,56,59)
  (plain 5 V, no PD/QC; D+/D- unused)     |          +-- 10 uF + 100 uF to ground
                                          +-- ground star point (adapter ground bus, DevKit J1.22)

DevKit: powered ONLY through its own USB socket marked UART (COM), from the laptop
        on battery (console) or from a second power bank port (Wi-Fi only).
DevKit 3V3 (J1.1) --> DVDD legs 48, 50.        DevKit 5V (J1.21) --> NOTHING.
```

- **First power-up only:** 100 ohm instead of the 10 ohm in the AVDD feed, and
  100 ohm in the DVDD wire. They limit the current if there is a solder bridge.
- **Order:** DevKit first (the firmware holds every control line low), then the
  AFE 5 V, then answer `R`. Off: AFE 5 V first, then the DevKit.
- **Check every session:** AVDD at the legs 4.75-5.25 V; 3V3 about 3.3 V; VCAP1
  (leg 28) above 1.1 V before `V`; after `T` or `N`, VREFP (24 to 25) about 4.5 V.
- If the power bank switches the AFE port off (the chip draws only about 5 mA),
  use the bank's low-current mode if it has one, or feed the plug board from a
  second USB port of the laptop on battery. Measure again.

## 4. Capacitors at the chip's legs

Use X7R/X5R ceramics rated 25 V (16 V minimum), C0G/NP0 for the nF parts.
Sleeve every lead that crosses another pin (heat-shrink or PTFE wire).

| Leg | Part | Other end |
|---|---|---|
| 19, 22, 56, 59 (AVDD) | 1 uF + 0.1 uF each | nearest AVSS: 20, 23, 57, 58 |
| 21 (AVDD) | 1 uF | 20 or 23 |
| 54 (AVDD1) | 1 uF + 0.1 uF | 53 (AVSS1) |
| 48, 50 (DVDD) | 1 uF + 0.1 uF each | 49, 51 (DGND) |
| 55 (VCAP3) | 1 uF + 0.1 uF | ground (leads cross 54/56: sleeve them) |
| 26 (VCAP4) | 1 uF | 25 (VREFN) |
| 30 (VCAP2) | 1 uF | 31 (RESV1) |
| 28 (VCAP1) | 100 uF tantalum 16 V (low-leakage electrolytic acceptable), + on 28 | ground (sleeve) |
| 24 (VREFP) | 22 uF tantalum 16 V, + on 24, plus 0.1 uF | 25 (VREFN) |
| 61 to 63 | 1.5 nF C0G in parallel with 1 Mohm | (bias feedback) |
| 16, 14, 12, 10 (optional) | 4.7 nF C0G each | 17 (SRB1), **not** ground |

That is 11 x 1 uF and 9 x 0.1 uF per adapter. On the power rails add 10 uF + 100 uF
after the 10 ohm (AVDD) and 10 uF on 3V3.

## 5. Firmware: build, upload, console keys

Install arduino-cli 1.3.1 ([ESP32_S3_TARGET_BUILD.md](ESP32_S3_TARGET_BUILD.md)),
then the pinned core and the laptop tools once (versions from `firmware/toolchain.json`):

```bash
arduino-cli core update-index --additional-urls https://espressif.github.io/arduino-esp32/package_esp32_index.json
arduino-cli core install esp32:esp32@3.3.12 --additional-urls https://espressif.github.io/arduino-esp32/package_esp32_index.json
uv sync --locked --all-extras
```

Find the port (`/dev/ttyUSB0` or `/dev/ttyACM0` on Linux, `COM3`-style on Windows)
with `uv run --locked python -m serial.tools.list_ports`. Then compile the
**breadboard** build and upload it through the DevKit's UART socket:

```bash
arduino-cli compile --fqbn esp32:esp32:esp32s3:FlashSize=8M,PSRAM=opi,CDCOnBoot=default \
  --build-property compiler.cpp.extra_flags=-DEEGLAB_BREADBOARD_S3 \
  --upload -p /dev/ttyUSB0 firmware/esp32_ads1299_bench
```

Do not use `-DEEGLAB_REV_A_S3`: that is the Rev A build, which needs the Rev A
safety board. Without either flag the S3 compile stops with an error.

**The wiring gate.** As shipped, `BREADBOARD_WIRING_CHECKED = false` in
`firmware/esp32_ads1299_bench/board_config_breadboard_s3.h`; the firmware then
touches no chip pin and prints `Breadboard build: set BREADBOARD_WIRING_CHECKED
only after ...`. After steps 1-3 pass, set it to `true` **on your copy only** and
upload again. Never commit that change.

**Console.** Open it at 460800 baud (exit with Ctrl+]):

```bash
uv run --locked python -m serial.tools.miniterm /dev/ttyUSB0 460800
```

| The console says | You do | Then |
|---|---|---|
| `BREADBOARD: ADS control lines parked low. ... then type R.` | Switch on the AFE 5 V, measure AVDD and 3V3, type `R` | The chip wakes (PWDN, CLKSEL, CS, RESET high) |
| `BREADBOARD: chip awake. Measure VCAP1 ... then type V.` | Measure leg 28 above 1.1 V, type `V` | Reset pulse, then the ID is read |
| `ID=0x3c; 4 physical channels; 250 SPS; gain 24` | Check the ID (0x3e and 8 channels for the 8-channel chip) | |
| `BREADBOARD: type T for the internal test signal or N for shorted inputs` | `T` = test signal, `N` = shorted-input noise | Registers written and read back, then data streams |

Keys may be lower case. Keys typed before a prompt are ignored. After `T` or `N`
the console fills with binary data: that is normal. To change mode or start
again: AFE 5 V off, press the DevKit's RST button, wait for the `R` prompt, AFE
5 V on. A line starting `HALTED` means the firmware stopped and parked every line
low; its reason names what to check (ID or readback: SPI wires, DVDD, CLKSEL;
"No valid data": DRDY wire and CLKSEL).

## 6. Laptop: capture, decode, inspect

Captures go to `reports/` (ignored by Git). **Serial route** (Wi-Fi off): answer
the prompts in miniterm, leave it with Ctrl+], then capture:

```bash
uv run --locked python run_lab.py serial --port /dev/ttyUSB0 --seconds 30 \
  --out reports/bb_test.bin --acknowledge-bench-only
uv run --locked python run_lab.py decode reports/bb_test.bin --out reports/bb_test.csv
uv run --locked python run_lab.py inspect reports/bb_test.csv --out reports/bb_test_quality
```

If reopening the port restarts the DevKit (the capture then finds no valid
packets and the console is back at the `R` prompt), nothing is harmed: use the
Wi-Fi route.

**Wi-Fi route.** On your copy of `firmware/esp32_ads1299_bench/board_config.h` set
`USE_WIFI_UDP=true`, your private network's `WIFI_SSID`/`WIFI_PASSWORD` and
`UDP_HOST` = the laptop's address on that network (`ip addr` on Linux, `ipconfig`
on Windows), then upload. Never commit that file. The console stays open for the
prompts; the data arrives by UDP:

```bash
uv run --locked python run_lab.py receive --host 0.0.0.0 --port 9000 --seconds 30 \
  --out reports/bb_noise_wifi.bin
uv run --locked python run_lab.py decode reports/bb_noise_wifi.bin --out reports/bb_noise_wifi.csv
uv run --locked python run_lab.py inspect reports/bb_noise_wifi.csv --out reports/bb_noise_wifi_quality
```

If nothing arrives, allow UDP port 9000 in the laptop's firewall. Never use
public Wi-Fi. `quality_report.json` in the inspect folder shows the mode, gaps,
peak-to-peak and the strongest frequency per channel.

## 7. Bring-up order

| Step | What you do | Pass |
|---|---|---|
| 0 | Practice soldering: practice kit, then a 48-leg practice chip on an adapter | No bridges |
| 1 | Solder the ADS1299-4 (wrist strap on). Beep-map every leg to its header pin. | Each leg beeps to exactly one pin; neighbours never beep together |
| 2 | Fit the capacitors (section 4) and the adapter's ground and 5 V buses | No beep 5V-GND, 3V3-GND, 5V-3V3, 55-54, 55-56, 28-26, 28-30, 24-25 (a short chirp that stops is a capacitor charging). Tantalum + on 24 and 28 |
| 3 | Wire the breadboard. Nothing powered; DevKit **not** wired to the adapter. | 25, 31, 41 beep to ground. 37, 42, 44, 45, 46 read about 10 kohm to ground. RESET/PWDN/START/CLKSEL legs read about 47 kohm to ground. Legs 1-9, 11, 13, 15 on 5 V. Only capacitors on 24, 26, 28, 30, 55 |
| 4 | Upload to the DevKit **alone** (USB to the laptop on battery). Gate still false. Then set the gate true and upload again. | Console prints the gate message; after the second upload it shows the `R` prompt and GPIO 5, 6, 7, 8 read 0 V |
| 5 | Power without the chip: plug board, 10 ohm, AVDD rail; DevKit on USB | 4.85-5.25 V before the 10 ohm, at least 4.75 V after it; 3V3 3.2-3.4 V |
| 6 | **Current-limited first power:** 100 ohm in AVDD and in DVDD, all wires in. DevKit on (prompt `R`), then AFE 5 V. Type `R`. | Before `R`: about 0 V across both 100 ohm, nothing warm. After `R`: about 0.4 V (AVDD) and 0.05 V (DVDD). Over 1 V: switch off and look for a bridge |
| 7 | Wait for VCAP1, type `V` | Leg 28 above 1.1 V. Console: `ID=0x3c` (low five bits 1 1100). Stop at the mode prompt: AFE 5 V off, then the DevKit |
| 8 | Change to 10 ohm (AVDD) and a plain wire (DVDD). Power up, `R`, `V`, then `T`. | No `HALTED` (all register readbacks match). AVDD at the legs 4.75-5.25 V. VREFP (24 to 25) about 4.5 V |
| 9 | Capture the internal test signal (`T`) with section 6 | Square wave, period about 1.02 s (0.98 Hz), 1.9-3.75 mV peak-to-peak (about 1900-3800 uV in the report), the same on every channel; strongest frequency about 1 Hz; mode `internal_test` |
| 10 | Restart and type `N`: shorted-input noise. Capture by serial (Wi-Fi idle), then by Wi-Fi (streaming) | A few uV peak-to-peak (datasheet 0.98 uVpp typical; a breadboard is worse); no big difference between the two; mode `internal_short` |
| 11 | **Dummy head, no person:** fit the electrode resistors (4.7 kohm signal and reference, 1 Mohm bias) and join every lead through about 10 kohm to one node | Unpowered: check the resistor values. The powered test needs the electrode mode (TODO below). Pass then: node about 2.5 V, channels near 0, under 0.1 V across the 1 Mohm, no oscillation with BIAS_SENSP 0x03 |
| 12 | Person (all section 1 rules): reference and bias on the earlobes, one channel (O1), then four | **Not implemented.** Needs your separate decision and the electrode mode |
| 13 | Stage 2: the 8-channel ADS1299 on a second adapter. Repeat 1-10; free legs 2, 4, 6, 8 from the 5 V bus | `ID=0x3e; 8 physical channels`; all eight register readbacks match; test signal on all 8 |

## 8. Not done yet

- **TODO (your decision): electrode-input mode.** Steps 11-12 need firmware that
  routes the electrodes to the chip: channel inputs normal (CHnSET 0x60), SRB1 on
  (MISC1 0x20), bias on (CONFIG3 0xEC) with BIAS_SENSP 0x00 first and later at
  most 0x03 (two channels), BIAS_SENSN 0x00, lead-off off (LOFF 0x00). It is
  deliberately absent. Adding it is a separate change you must ask for, with its
  own tests and review, done only after steps 1-10 pass.
- Nothing on this card has been built, uploaded or measured. Unknowns: the power
  bank's real voltage and low-load behaviour, your DevKit's diode drop, the
  adapter's pad fit, breadboard noise and radio pickup, and whether the test
  signal reads 1.9 or 3.75 mV peak-to-peak.
- The firmware's checks (ID, register readback, data timeout) stop on faults.
  They do not sense voltages and are not a safety system.
