# Hardware guide: buy the right thing, then test it in layers

**Current status (Rev A): the component baseline is selected, but no physical circuit has been tested.** See [HARDWARE_BASELINE_REV_A.md](HARDWARE_BASELINE_REV_A.md) and `hardware/rev_a/` for the exact ADS1299-4 + ESP32-S3 devkit decision, BOM, proposed pin map, provenance, and fail-closed review gates. The generic/original-ESP32 material below remains useful background; where it conflicts with Rev A, the Rev A baseline is authoritative for new simulation and schematic work. This document separates a concrete digital bench example from the connections that cannot yet be specified responsibly.

The included firmware is deliberately restricted to the ADS1299's **internal test signal or internally shorted inputs**. There is no external-electrode acquisition mode to enable. An acquisition waveform is not evidence of electrical safety.

## 1. The $100 decision

Do not buy a bare ADS1299 chip just because the software mentions it. A chip, a breakout adapter, an evaluation board, and a protected assembled recorder are four different purchases.

At the research check, DigiKey listed the full eight-channel ADS1299IPAGR at **$88.58 for one bare chip**, with zero immediate stock on that listing. Its related four-channel ADS1299-4PAGR listing showed **$44.99**. Prices, availability, taxes and shipping are not fixed [S9, S10]. Neither price includes a usable front-end PCB, input protection, regulators, assembly, connectors, enclosure or battery.

**A documented assembled ADS1299 system delivered for under $100 has not been verified here.** The earlier reports' custom-PCBA numbers were engineering estimates, not complete purchasing quotations. A one-off manufacturing order also has minimum quantities, shipping and the possibility of a revision.

A useful spending rule is to reserve roughly $35–40 of your ceiling for power, connectors, enclosure, consumables, delivery and contingencies. That leaves roughly $60–65 for an assembled front-end board. These are **budget allocations, not market prices**. A missing multimeter, unsuitable electrode connectors, or additional shipping reduces that board ceiling further. Obtain a complete quote before spending.

Your existing ESP32 and electrodes may avoid some purchases, but their exact models and connector/material details still need checking. Do not assume they are Ag/AgCl electrodes merely because the older report discussed that type.

For now: run the lab, identify the boards, and keep the $100 unspent. A four-channel ADS1299-4 board is a reasonable candidate to investigate; a cheap anonymous listing is not automatically a good choice. More physical channels do not fix poor documentation, noisy inputs or an unsafe power arrangement.

## 2. Before paying: the board worksheet

Save the listing, schematic and board revision. Fill in `configs/board_profile.example.json`. This is a human review worksheet; it is not automatically consumed by the firmware.

| Required information | Why it matters |
|---|---|
| Manufacturer, model, revision and clear photographs | Similar-looking boards can expose different supplies and connectors. |
| Exact ADC variant: 4, 6 or 8 channels | Determines native frame length and available channels. |
| Full schematic, not just a sales diagram | Needed to check supplies, reference, clock, input paths and bias. |
| Board supply input and every regulator/rail | A connector marked “5V” may be a regulator input, not a chip pin. |
| Digital interface voltage | Our bench example requires compatible 3.3-V logic. |
| Clock source and CLKSEL arrangement | The sketch assumes the internal oscillator is selected. |
| Internal-reference support and capacitors | Register settings alone cannot install missing components. |
| CS, DRDY, RESET, START and PWDN straps/headers | Do not drive a signal that is hard-strapped incompatibly. |
| Input protection, reference routing and bias circuit | These are board-specific and cannot be inferred from “ADS1299.” |
| Compatible electrode connectors and enclosure | Loose temporary jumpers are not a finished wearable interface. |

A seller saying “EEG” or “medical chip” does not settle those questions. TI explicitly describes its own evaluation platform as laboratory engineering equipment, not a direct patient interface [S2].

## 3. Power: the connection deliberately left blank

The ADS1299's recommended analog supply span is 4.75–5.25 V; its digital supply is a different domain. The chip supports 1.8–3.6 V digital supplies, and the present ESP32 wiring example requires **3.3-V-compatible digital signaling** [S1, S4].

**Do not simply connect ESP32 3V3 to ADS1299 AVDD. Do not simply connect 5 V to a pin labeled DVDD. Do not infer the board's power input from a chip-level diagram.**

Examples of chip analog rails include a 0/5-V arrangement or a bipolar arrangement with approximately a 5-V span. This statement is not a prescription for your board. Its regulators, reference, input common mode and digital return must be checked together.

No battery or power-pin wiring is provided until that board is known. Use an appropriate documented power source and enclosure for the selected board; do not improvise a loose lithium-cell charging arrangement. All power measurements in the initial stage are made **with no person connected**.

## 4. Conditional digital bench wiring

**This table is for an original ESP32/WROOM-32-style board, not ESP32-C3, S2, S3, C6 or an arbitrary development board. Numbers are GPIO identifiers, not physical header positions.** The SPI signal choices follow the original ESP32 example; the other GPIO assignments are choices made for this project [S4].

The ADS board must expose these signals and use compatible 3.3-V digital levels. Inspect its schematic before moving any wire. Disconnect power while changing wiring.

| Original ESP32 GPIO | Direction | ADS1299-board signal | Meaning |
|---|---|---|---|
| 18 | ESP32 → ADC | SCLK | Serial clock |
| 23 | ESP32 → ADC | DIN / MOSI | Commands and register writes |
| 19 | ADC → ESP32 | DOUT / MISO | Register values and conversion data |
| 27 | ESP32 → ADC | /CS | Select this ADC for an SPI transaction |
| 26 | ADC → ESP32 | /DRDY | A new simultaneous sample frame is ready |
| 25 | ESP32 → ADC | /RESET | Reset control, if exposed and not conflicting with straps |
| 32 | ESP32 → ADC | START | Held low; this sketch uses START/STOP commands |
| 33 | ESP32 → ADC | /PWDN | Power-down control, if exposed and not conflicting with straps |
| Circuit digital return | Shared | DGND / documented digital return | Logic reference within the bench circuit, **not household earth** |

Power and electrode connections are intentionally **not rows in this pin map**. A GPIO table does not define the complete circuit.

Do not put the Uno's 5-V outputs onto this 3.3-V interface. This project does not include a reviewed level-shifter design for the Uno. Use your breadboards for basic passive lessons and low-risk digital bench interconnects; do not make a solderless-breadboard front end your body-connected endpoint.

## 5. Firmware: what it does and does not promise

The folder `firmware/esp32_ads1299_bench` is an Arduino sketch. `portable_core.h` was compiled and tested with native C++ against the Python packet encoder. **The entire sketch was not compiled for ESP32 or run on an ESP32 in this environment.** Native compilation does not validate Arduino API compatibility, GPIO behavior, interrupt timing, power, SPI or Wi-Fi performance.

The sketch initially refuses to configure ADS control pins because `BOARD_PROFILE_REVIEWED` is false. After the bench schematic/power review, the remaining intended sequence is: compile for the exact supported ESP32, upload with no body electrodes connected, then inspect the serial startup diagnostics.

The sketch reads the ADC ID, determines the physical channel count, sets and checks registers, selects internal test or internal short, waits for reference settling, and acquires at a nominal 250 samples/s and gain 24. It uses SPI mode 1 at 1 MHz. An invalid frame prefix, failed register readback, or data timeout halts and asserts power-down. Read the actual source rather than copying isolated register numbers [S1].

`USE_INTERNAL_TEST = true` selects the approximately 0.9766-Hz internal test waveform at the nominal 2.048-MHz clock. `false` selects internally shorted inputs. **Neither setting is an external EEG mode.** Bias derivation, bias drive and lead-off excitation remain disabled.

`USE_WIFI_UDP = false` sends a custom binary USB serial stream for bench use. It is not Arduino Serial Plotter CSV. Optional Python support requires:

```bash
python -m pip install -r requirements-serial.txt
python run_lab.py serial --port /dev/ttyUSB0 --seconds 30 \
  --out results/internal_test.bin --acknowledge-bench-only
python run_lab.py decode results/internal_test.bin --out results/internal_test.csv
python run_lab.py inspect results/internal_test.csv --out results/internal_test_quality
```

The serial device name is an example; Windows often uses a `COM` name. Every body lead, including reference and bias, must be disconnected throughout USB bench capture. That acknowledgement flag is not an isolation mechanism.

The optional UDP path is still bench-only in this firmware. Set the private Wi-Fi credentials and computer address explicitly. Do not assume radio performance is validated simply because localhost passed. Wi-Fi may introduce interference or scheduling delays; the counter checks help reveal acquisition losses but cannot prove analog quality.

## 6. Bench gates, in order

| Gate | Test with no person connected | Proceed only when |
|---|---|---|
| A: Documentation | Inspect board identity, schematic and assembly | Power, reference, clock, input paths and interface levels are understood. |
| B: Power | Check for shorts with power off; measure documented rails/reference after powering | Measurements match the selected board's documentation; nothing overheats. |
| C: Digital identity | Read ID and configuration registers | ID/channel count and register readback are repeatable, not random or all-zero/all-one. |
| D: Internal waveform | Capture the on-chip test signal | Frequency, sign, channel framing, code scale and counters are plausible and repeatable. |
| E: Internal short | Capture a longer baseline in internal-short mode | There is a stable quantified noise spectrum and no unexplained railing or packet loss. |
| F: External dummy network | After a separate external-input firmware/design review, use resistors and known test signals, never a person | Known amplitudes, offsets, input/common-mode limits and interference behavior have been measured. |
| G: Body-interface review | Review physical input protection, bias stability/current limiting, enclosure, power and all possible connections | A competent reviewer or appropriately documented finished system supports the intended body-connected arrangement. |

The current deliverable can support the software and internal bench stages. It does not supply a reviewed implementation for gates F or G. Merely enabling normal-input mux codes would not complete them.

For a future external calibration, amplitude must be small enough **and centered at a valid analog common mode**. Grounding both inputs to 0 V on a unipolar 0/5-V design is not automatically a valid low-noise input condition. This is why the first short test uses the chip's internal mux rather than an invented external jumper.

A grounded function generator or oscilloscope can be used for bench-only dummy tests, but it must never remain electrically connected when a person is connected. Do not place mains voltage on the dummy network to “simulate interference.” Use a properly limited bench test source after reviewing the circuit.

No fixed “noise below X means safe/good” threshold is prescribed here. Noise depends on gain, rate, bandwidth, source impedance, reference, layout and implementation. A quiet internal-short recording does not characterize the complete electrode-connected system.

## 7. The body-connection boundary

For eventual body-connected recording, the acquisition side must have a reviewed body interface, appropriate battery operation, and wireless-only communication in this project plan. OpenBCI's documented battery-only Cyton is a useful architectural precedent, not certification of a different homemade board [S11].

**While any electrode is attached: no USB cable, charger, oscilloscope, function generator, wired debugger, grounded accessory, or other unreviewed conductive connection.** A battery-powered laptop connected by USB is not a substitute for a properly assessed body interface. A cheap USB isolator is not automatically a medically suitable barrier.

Battery and wireless operation remove some hazardous paths; they do not check every component fault, current path, bias-loop instability or construction defect. None of the numerical tests here assesses those hazards. Do not connect the current breadboard or unreviewed module to your body.

Use recording-only experiments. Do not repurpose the bias circuit or electrode wiring for stimulation. Avoid broken or irritated skin and stop on discomfort. This is a learning/research project, not diagnosis or treatment.

## 8. What comes next

Rev A removes the need to keep shopping among MCU/AFE architectures. The immediate engineering task is to implement the selected 4.99 kΩ / 4.7 nF differential input network in ngspice, preserve the existing educational circuit as a regression fixture, and sweep source/electrode impedance imbalance, component tolerance, cable capacitance, 50/60-Hz common mode, and bounded clamp leakage.

After that: BIAS/power modeling, a reviewed KiCad schematic, and an explicit ESP32-S3 firmware profile. Purchasing remains blocked until the schematic is reviewed and a complete delivered parts/fabrication/assembly quote is obtained. External-input and body-connected work remain separate later gates.

References marked `[S#]` are linked in [SOURCES.md](SOURCES.md); Rev A source provenance is in `hardware/rev_a/sources.json`.
