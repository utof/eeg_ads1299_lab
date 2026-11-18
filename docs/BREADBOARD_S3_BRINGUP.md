# Breadboard ADS1299 + ESP32-S3: bring-up card

A step-by-step card for a hand-soldered **ADS1299-4** (TQFP-64) on an adapter,
wired on a breadboard to an **ESP32-S3-DevKitC-1** (N8R8 or N16R8: same
build command), powered only from a
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
   from a laptop running on battery (charger unplugged). With this firmware the
   laptop is always on the USB cable for the console prompts, so this applies
   every time.
   No wall charger, monitor/HDMI, Ethernet, powered USB hub, oscilloscope, bench
   supply or soldering iron may be connected to, or touching, the rig while it
   runs. Unplug the iron and put it away.
2. **5 V only.** Many power banks, fast-charge ones included, can give 9-12 V on
   their USB-A ports, but only when the plugged device asks for it over the D+
   and D- contacts. The USB-A plug board leaves D+ and D- unconnected (their
   breadboard rows stay empty), so the port stays at 5 V. Never connect D+ or
   D-, never use the bank's USB-C port, never use a PD/QC charger or a
   "trigger"/"decoy" board (they can give 9-20 V; the chip dies above 5.5 V).
   Measure the 5 V every session before you connect the chip: it must read
   **positive** (a minus sign means the plug board is in back to front: stop).
   On a manual-range meter take this reading on a range above 6 V (for example
   60 V). An over-range display (`OL`, or a lone `1`) on a 6 V range means more
   than 6 V: unplug at once.
3. **Never pull out the chip's 3V3 (DVDD) or ground wire while the DevKit is
   on:** the ESP32 would push 3.3 V into an unpowered chip. Unplugging the bank
   (the AFE 5 V) is the normal way to switch off. Order: bank out, then DevKit
   out; disconnect wires only with both off.
4. **The bias electrode lead gets 1 Mohm, not 4.7 kohm.** That limits what the
   bias output can push into a person to about 5 uA (5 V / 1 Mohm), even if you
   touch the laptop or board.
5. **Never turn on the chip's lead-off currents with a person attached.** The
   firmware keeps them off (LOFF_SENSP = LOFF_SENSN = LOFF_FLIP = 0x00); do not
   change that. (The LOFF register itself only sets threshold, current size and
   frequency; it does not switch the currents on or off.)
6. Wear the wrist strap when you handle the chip (it is static-sensitive).
7. Not a medical device. Nobody with a pacemaker or implant. Clean, intact skin
   only. Stop if you feel tingling or itching, or see redness.

## 2. Wiring: DevKit to chip

DevKit pin numbers count from the **3V3 end** of header J1 (J1.1 = 3V3, J1.3 = RST,
J1.21 = 5V, J1.22 = GND). The board prints GPIO numbers, not pin numbers. Check
them on your actual board; clones can differ.

| Chip leg | Signal | S3 GPIO | DevKit pin | Parts on the breadboard | Notes |
|---|---|---|---|---|---|
| 40 | SCLK | GPIO12 | J1.18 | 1 kohm in series + 47 kohm to GND at the chip | SPI clock |
| 34 | DIN | GPIO11 | J1.17 | 1 kohm in series + 47 kohm to GND | ESP32 to chip (MOSI) |
| 43 | DOUT | GPIO13 | J1.19 | plain wire (optional 33-100 ohm at the chip) | chip to ESP32 (MISO) |
| 39 | CS | GPIO10 | J1.16 | 1 kohm in series + 47 kohm to GND | chip select |
| 47 | DRDY | GPIO4 | J1.4 | plain wire | "data ready", an input |
| 36 | RESET | GPIO5 | J1.5 | 1 kohm in series + 47 kohm to GND | **not** the DevKit's RST pin (J1.3) |
| 38 | START | GPIO6 | J1.6 | 1 kohm in series + 47 kohm to GND | stays low; conversions start by command |
| 35 | PWDN | GPIO7 | J1.7 | 1 kohm in series + 47 kohm to GND | low = chip powered down |
| 52 | CLKSEL | GPIO8 | J1.12 | 1 kohm in series + 47 kohm to GND | replaces the guide's 10 kohm to 3.3 V |
| 48, 50 | DVDD | 3V3 | J1.1 | 100 ohm for the first-power test only, then a plain wire | DevKit regulator |
| 33, 49, 51 + all AVSS | ground | GND | J1.22 | one wire to the star point | |
| 19, 21, 22, 54, 56, 59 | AVDD 5 V | none | J1.21 left unconnected | from the power bank (section 3) | never from the DevKit 5V pin |

Fit the 47 kohm pull-downs on SCLK, DIN and CS too: they hold those lines low
while the DevKit boots, before the firmware drives them (datasheet: digital
inputs low during power-up, never floating).

Leave GPIO14 (J1.20), GPIO9 (J1.15), GPIO15 (J1.8) and GPIO16 (J1.9)
unconnected: they belong to the Rev A safety board. Avoid GPIO0, 3, 45, 46
(boot straps), 19/20 (USB), 35-37 (PSRAM), 43/44 (USB-UART bridge) and 38 (LED).

The other chip legs (all on the adapter):

- 25 (VREFN), 31 (RESV1), 41 (DAISY_IN): straight to ground.
- 37 (CLK) and 42, 44, 45, 46 (GPIO1-4): 10 kohm each to ground.
- 1-9, 11, 13, 15 (unused inputs, stage 1): tied to the 5 V bus with wire on
  the header pins, never solder across the chip's legs.
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
  (D+/D- left unconnected: stays 5 V)     |          +-- 10 uF + 100 uF to ground
                                          +-- ground star point (adapter ground bus, DevKit J1.22)

DevKit: powered ONLY through its own USB socket marked UART (COM), from the laptop
        on battery (the console prompts need it, also on the Wi-Fi route).
DevKit 3V3 (J1.1) --> DVDD legs 48, 50.        DevKit 5V (J1.21) --> NOTHING.
```

- **First power-up only:** 100 ohm instead of the 10 ohm in the AVDD feed, and
  100 ohm in the DVDD wire. They limit the current if there is a solder bridge;
  they do not stop an overvoltage (5 V on DVDD or on a digital leg), so the
  unpowered rig check in section 7 comes first.
- **Order:** DevKit first (the firmware holds every control line low), then the
  AFE 5 V, then answer `R`. Off: AFE 5 V first, then the DevKit.
- **Keep the DevKit-only state short.** DVDD comes from the DevKit, so with the
  DevKit on and the bank out AVDD - DVDD is -3.3 V, outside the recommended
  -2.1 to +3.6 V range (not an absolute maximum). Plug in the bank within a few
  seconds of the `R` prompt; at the end unplug the DevKit right after the bank.
  If the bank switches itself off, unplug the DevKit too, then start again.
- **Check every session** (black probe on ground; every reading positive, a
  minus sign means stop): VBUS at the plug board +4.85 to +5.25 V; AVDD at the
  legs +4.75 to +5.25 V (with the 100 ohm of steps 6-7 about 4.4-4.6 V after `R`
  is expected); 3V3 about +3.3 V; VCAP1 (leg 28) above 1.1 V before `V`; after
  `T` or `N`, VREFP (24 to 25) 4.45 to 4.55 V and steady.
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
| 28 (VCAP1) | 100 uF, 16 V or more: tantalum or an ordinary aluminium electrolytic, + on 28 | ground (sleeve) |
| 24 (VREFP) | 22 uF, 16 V or more: aluminium electrolytic or tantalum, + on 24, plus 0.1 uF (and, recommended, 1 uF X7R) | 25 (VREFN) |
| 61 to 63 | 1.5 nF C0G in parallel with 1 Mohm | (bias feedback) |
| 16, 14, 12, 10 (optional) | 4.7 nF C0G each | 17 (SRB1), **not** ground |

That is 11 x 1 uF (12 with the recommended one on VREFP) and 9 x 0.1 uF per
adapter. On the power rails add 10 uF + 100 uF
after the 10 ohm (AVDD) and 10 uF on 3V3 (electrolytic stripe = minus, to ground).

**Polarity marks are opposite.** On a leaded tantalum the mark (a "+", or a
stripe or bar) and the longer lead are **plus**; on an electrolytic the stripe
marks **minus**. So on legs 24-25 a 22 uF electrolytic goes stripe (minus) to
leg 25, and a 22 uF tantalum goes marked lead (plus) to leg 24. A 100 uF
electrolytic on leg 28 goes stripe to ground; a 100 uF tantalum goes "+" to
leg 28. A reversed tantalum can short or burn; a reversed electrolytic can
read correctly at first and fail slowly, so check by eye before power.

**Why an electrolytic is accepted on VREFP and VCAP1.** The datasheet asks only
for "a minimum 10-uF capacitor" from VREFP to VREFN and 100 uF on VCAP1
(SBAS499C p.7, Figure 77); it gives no capacitor type and no series-resistance
limit. TI's evaluation board uses ceramics on both (SLAU443B p.50), so an
electrolytic or a tantalum is a departure that this card accepts on a
condition: VREFP reads 4.45-4.55 V and steady in step 8. The 1 uF X7R across
24-25 gives the reference buffer a low-resistance capacitor close to the legs;
it is a recommendation of this card's review, not a datasheet requirement.
Leakage in the VCAP1 capacitor lowers VREFP (about 37 mV per 1 uA, inferred
from Figure 25): a low or creeping VREFP points at that 100 uF. The internal
test signal and the shorted-input test are nearly blind to reference noise, so
a clean capture does not prove the reference is quiet.

## 5. Firmware: build, upload, console keys

Install arduino-cli 1.3.1 ([ESP32_S3_TARGET_BUILD.md](ESP32_S3_TARGET_BUILD.md)),
then the pinned core and the laptop tools once (versions from `firmware/toolchain.json`):

```bash
arduino-cli core update-index --additional-urls https://espressif.github.io/arduino-esp32/package_esp32_index.json
arduino-cli core install esp32:esp32@3.3.12 --additional-urls https://espressif.github.io/arduino-esp32/package_esp32_index.json
uv sync --locked --all-extras
```

**Linux, once:** the serial port belongs to the `dialout` group; without it
upload and the console fail with "Permission denied". Run this yourself once,
then log out and back in (it changes your account's groups):

```bash
sudo usermod -aG dialout $USER
```

Find the port with `uv run --locked python -m serial.tools.list_ports` (or
`ls /dev/ttyUSB* /dev/ttyACM*`), DevKit unplugged and then plugged: the new
entry is yours. On Linux it is `/dev/ttyUSB0` (CP210x/CH340 bridge) or
`/dev/ttyACM0` (CH343 bridge, common on "Dual Type-C" clones); on Windows
`COM3`-style. The commands below say `/dev/ttyUSB0`: use your port in every
command. If an upload never connects: hold BOOT, press and release RST, release
BOOT, upload again. Then compile the **breadboard** build and upload it through
the DevKit's UART socket:

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

**Empty console?** Each message is printed once, when the DevKit starts. If
the screen stays empty, press the DevKit's RST button (AFE 5 V off): the banner
`ADS1299 learning lab. BENCH ONLY ...` and the next message appear. Note which
happened in step 4, because it decides the capture route in section 6:

- You had to press RST: opening the port does not restart your DevKit. The
  serial capture works.
- The banner appeared by itself: opening the port restarts your DevKit, so a
  serial capture would restart it too. Use the Wi-Fi route.

| The console says | You do | Then |
|---|---|---|
| `BREADBOARD: ADS control lines parked low. ... then type R.` | Switch on the AFE 5 V, measure AVDD and 3V3, type `R` | The chip wakes (PWDN, CLKSEL, CS, RESET high) |
| `BREADBOARD: chip awake. Measure VCAP1 ... then type V.` | Measure leg 28 above 1.1 V, type `V` | Reset pulse, then the ID is read |
| `ID=0x3c; 4 physical channels; 250 SPS; gain 24` | Check the ID ends in `c` with 4 physical channels (8-channel chip: ends in `e`, 8 channels); any first digit is fine | |
| `BREADBOARD: type T for the internal test signal or N for shorted inputs` | `T` = test signal, `N` = shorted-input noise | Registers written and read back, then data streams |

Keys may be lower case. Keys typed before a prompt are ignored. After `T` or `N`
the console fills with binary data: that is normal. To change mode or start
again: AFE 5 V off, press the DevKit's RST button, wait for the `R` prompt, AFE
5 V on within a few seconds. A line starting `HALTED` means the firmware stopped
and parked every line low; its reason names what to check (ID or readback: SPI
wires, DVDD, CLKSEL; "No valid data": DRDY wire and CLKSEL; "Invalid native
status prefix": SCLK and DOUT wires and their length; "Wi-Fi timeout" or
"Invalid UDP_HOST": the Wi-Fi settings).

The ID check uses only the low five bits (bits 7:5 are a revision number that
TI may change). A chip of another revision prints a different first digit, for
example `ID=0x5c; 4 physical channels`, and continues: that is fine. The
firmware halts only if the low bits do not name a 4- or 8-channel ADS1299.

## 6. Laptop: capture, decode, inspect

Captures go to `reports/` (ignored by Git). **Serial route** (Wi-Fi off): answer
the prompts in miniterm (after step 8 the chip is already streaming `T`), leave
it with Ctrl+], then capture:

```bash
uv run --locked python run_lab.py serial --port /dev/ttyUSB0 --seconds 30 \
  --out reports/bb_test.bin --acknowledge-bench-only
uv run --locked python run_lab.py decode reports/bb_test.bin --out reports/bb_test.csv
uv run --locked python run_lab.py inspect reports/bb_test.csv --out reports/bb_test_quality
```

If reopening the port restarts the DevKit (the capture then finds no valid
packets and the console is back at the `R` prompt), nothing is harmed: use the
Wi-Fi route.

**Wi-Fi route.** AFE 5 V off (bank out) first. On your copy of
`firmware/esp32_ads1299_bench/board_config.h` set `USE_WIFI_UDP=true`, your
private network's `WIFI_SSID`/`WIFI_PASSWORD` and `UDP_HOST` = the laptop's
address on that network (`ip addr` on Linux, `ipconfig` on Windows), then upload
(the DevKit restarts). Never commit that file. Open miniterm; at the `R` prompt
plug in the bank, type `R`, wait for VCAP1 above 1.1 V, `V`, then `N`. Wait
about 20 s: when it works nothing new is printed (the firmware joins Wi-Fi and
starts sending); a `HALTED` line (`Wi-Fi timeout`, `Invalid UDP_HOST`) means it
did not. Then start `receive`; the console stays open and the data arrives by
UDP:

```bash
uv run --locked python run_lab.py receive --host 0.0.0.0 --port 9000 --seconds 30 \
  --out reports/bb_noise_wifi.bin
uv run --locked python run_lab.py decode reports/bb_noise_wifi.bin --out reports/bb_noise_wifi.csv
uv run --locked python run_lab.py inspect reports/bb_noise_wifi.csv --out reports/bb_noise_wifi_quality
```

If nothing arrives, allow UDP port 9000 in the laptop's firewall. Never use
public Wi-Fi. `quality_report.json` in the inspect folder shows the mode
(`recording_mode`), gaps (`gap_boundaries`), peak-to-peak
(`raw_peak_to_peak_uV_by_channel`), in-band RMS (`rms_0p5_40_Hz_uV_by_channel`)
and the strongest frequency (`peak_0p5_40_Hz_by_channel`) per channel.

## 7. Bring-up order

| Step | What you do | Pass |
|---|---|---|
| 0 | Practice soldering: practice kit, then a 48-leg practice chip on an adapter | No bridges |
| 1 | Solder the ADS1299-4 (wrist strap on). Beep-map every leg to its header pin. | Each leg beeps to exactly one pin; neighbours never give a steady beep. A diode-test reading with no beep (about 0.5-0.8 V, shown as 500-800 on some meters; or `OL`), often in one probe direction only, is the chip's protection diode, not a bridge. 21-22 and 57-58 share a name and are joined by a bus in step 2 anyway |
| 2 | Fit the capacitors (section 4) and the adapter's ground and 5 V buses | No steady beep 5V-GND, 3V3-GND, 5V-3V3, 55-54, 55-56, 28-26, 28-30, 24-25, nor from each of 24, 26, 28, 30, 55 to ground (a short chirp that stops is a capacitor charging). Polarity: 22 uF plus on 24 (electrolytic: stripe on the leg-25 side; tantalum: mark on 24); 100 uF plus on 28 (electrolytic: stripe to ground) |
| 3 | Wire the breadboard. Nothing powered; DevKit **not** wired to the adapter. | 25, 31, 41 beep to ground. 37, 42, 44, 45, 46 read about 10 kohm to ground. RESET/PWDN/START/CLKSEL and DIN/CS/SCLK (34, 39, 40) legs read about 47 kohm to ground. Legs 1-9, 11, 13, 15 on 5 V; legs 10, 12, 14, 16, 17 **not** on 5 V. Only capacitors on 24, 26, 28, 30, 55 |
| 4 | Upload to the DevKit **alone** (USB to the laptop on battery). Gate still false. Then set the gate true and upload again. | Console prints the gate message (press RST if the console is empty, and note whether you had to: section 5); after the second upload it shows the `R` prompt and GPIO 5, 6, 7, 8 read 0 V |
| 5 | Power without the chip: plug board, 10 ohm, AVDD rail. Wire J1.1/J1.22 to the rails with USB unplugged, then DevKit on USB | +4.85 to +5.25 V before the 10 ohm, at least +4.75 V after it; 3V3 +3.2 to +3.4 V. A minus sign: plug board reversed, stop |
| 6 | **Current-limited first power:** 100 ohm in AVDD and in DVDD, all wires in. **Unpowered rig check** (below) first. DevKit on (prompt `R`): AVDD rail and the DVDD 100 ohm about 0 V. Then, within seconds, AFE 5 V. Type `R`. | Before `R`: AVDD at leg 19 +4.85 to +5.25 V, DVDD at leg 48 +3.2 to +3.4 V (above 3.6 V or a minus sign: unplug the bank at once); about 0 V across both 100 ohm, nothing warm. After `R`: about 0.2-0.5 V (AVDD, up to about 4 mA) and 0.05 V (DVDD); AVDD at the legs about 4.4-4.6 V, expected with the 100 ohm only. Over 1 V: switch off and look for a bridge |
| 7 | Wait for VCAP1 (usually 3-10 s), type `V` | Leg 28 above 1.1 V. Console: ID ending in `c` with `4 physical channels` (low five bits 1 1100; usually `ID=0x3c`). Stop at the mode prompt: AFE 5 V off, then the DevKit right after |
| 8 | Change to 10 ohm (AVDD) and a plain wire (DVDD). Repeat the unpowered rig check (now 0 ohm on DVDD). Power up, `R`, `V`, then `T`. | No `HALTED` (all register readbacks match). AVDD at the legs 4.75-5.25 V. VREFP (24 to 25) 4.45-4.55 V and steady; measure at the 22 uF's plus lead against the ground bus, so the probe cannot bridge legs 24-25 |
| 9 | Capture the internal test signal (`T`, already streaming from step 8) with section 6 | Square wave, period about 1.02 s (0.98 Hz), about 3.75 mV peak-to-peak: 3,500-4,000 uV in `raw_peak_to_peak_uV_by_channel`, within 2 % across channels. About 1,900 uV (half) is **not** a pass: stop and ask. Strongest frequency about 1 Hz; mode `internal_test` |
| 10 | Restart and type `N`: shorted-input noise. Capture by serial (Wi-Fi idle), then by Wi-Fi (streaming) | A few uV peak-to-peak (datasheet 0.98 uVpp typical; a breadboard is worse); `rms_0p5_40_Hz_uV_by_channel` well under 1 uV (datasheet about 0.14 uVrms); no big difference between the two; mode `internal_short` |
| 11 | **Dummy head, no person:** fit the electrode resistors (4.7 kohm signal and reference, 1 Mohm bias) and join every lead through about 10 kohm to one node | Unpowered: check the resistor values. The powered test needs the electrode mode (TODO below). Pass then: node about 2.5 V, channels near 0, under 0.1 V across the 1 Mohm, no oscillation with BIAS_SENSP 0x03 |
| 12 | Person (all section 1 rules): reference and bias on the earlobes, one channel (O1), then four | **Not implemented.** Needs your separate decision and the electrode mode |
| 13 | Stage 2: the 8-channel ADS1299 on a second adapter. Repeat 1-10; free legs 2, 4, 6, 8 from the 5 V bus | ID ending in `e` with `8 physical channels` (usually `ID=0x3e`); in step 6 up to about 0.71 V across the AVDD 100 ohm and about 0.1 V across the DVDD 100 ohm; all eight register readbacks match; test signal on all 8 |

**Unpowered rig check (before steps 6 and 8).** USB and bank both unplugged,
meter on beep or ohms. J1.21 (5V) has no wire. J1.1 to legs 48 and 50: about
100 ohm in step 6, a beep (0 ohm) in step 8. 5 V rail to 3V3 rail, 5 V to ground
and 3V3 to ground: no steady beep. J1.18 to leg 40, J1.17 to 34, J1.16 to 39,
J1.5 to 36, J1.6 to 38, J1.7 to 35 and J1.12 to 52: about 1 kohm each. J1.19 to
leg 43 and J1.4 to leg 47: beep. J1.22 to leg 33: beep. Any wrong reading: stop.

**Test-signal amplitude (step 9).** CONFIG2 = 0xD0 gives a square wave of
+/-VREF/2400 = +/-1.875 mV, i.e. 3.75 mV peak-to-peak at fCLK/2^21 = 0.977 Hz
(SBAS499C p.47; p.10 lists the test signal as "+/-1, +/-2 mV", accuracy +/-2 %).
`decode` divides by an assumed 4.5 V reference and the test signal scales with
the same reference, so the real VREF cancels; expect about 3,660-3,840 uV.

## 8. Not done yet

- **TODO (your decision): electrode-input mode.** Steps 11-12 need firmware that
  routes the electrodes to the chip: channel inputs normal (CHnSET 0x60), SRB1 on
  (MISC1 0x20), bias on (CONFIG3 0xEC) with BIAS_SENSP 0x00 first and later at
  most 0x03 (two channels), BIAS_SENSN 0x00, lead-off currents off
  (LOFF_SENSP 0x00, LOFF_SENSN 0x00, LOFF_FLIP 0x00; LOFF 0x00). It is
  deliberately absent. Adding it is a separate change you must ask for, with its
  own tests and review, done only after steps 1-10 pass.
- Nothing on this card has been built, uploaded or measured. Unknowns: the power
  bank's real voltage and low-load behaviour, your DevKit's diode drop, the
  adapter's pad fit, and breadboard noise and radio pickup.
- The firmware's checks (ID, register readback, data timeout) stop on faults.
  They do not sense voltages and are not a safety system.
