# L2: keep the 1 MHz SPI protocol; qualify the complete electrical channel separately

2026-10-08. Baseline main `9af4a71c1f2895d4c9e8517ffae3f2cb58f26bd5`,
tree `42c3e2a08a2bf50ece59038a1ce997ec7cd02c26` (L1 / PR94).

**Decision: retain 1 MHz, MSB-first, SPI mode 1 and the existing command delays.**
This audit finds no protocol reason to change the sampling edge, add dummy clocks,
switch SPI libraries, or reduce speed merely because the channel includes a cable.
It does NOT close timing/hold or signal-integrity acceptance for the assembled
channel. The data-sheet delay sum is conditional, not an actual cable-load bound.
No resistor value, new component, firmware change or release approval is selected.

This is one complete read-channel review, not a new simulator or measurement API.
Use B2's existing run card for the eventual waveform evidence and B3 for its
rail-sense access limits. B3 sense tails are NOT qualified high-speed logic probes.

## 1. Trace the actual channel, not only the repaired clock segment

The current profile selects SCLK GPIO12, MOSI GPIO11, MISO GPIO13 and CS GPIO10.
Physical header numbers are different. The two frozen native netlists and authored
PCB pads were cross-checked at 25 terminals for these four signal paths.

| Direction | Actual native terminal chain (separate boards are named) |
|---|---|
| Clock outward | MCU GPIO12 / DevKit J1.18 -> AUX J102.18 -> U102.2 -> U102.13 -> AUX J101.1 -> K1 contact1 -> AFE J1.1 -> U1.40 |
| Data return | AFE U1.43 -> AFE J1.5 -> K1 contact5 -> AUX J101.5 -> U102.10 -> U102.5 -> AUX J102.19 -> DevKit J1.19 / GPIO13 |
| Data outward | MCU GPIO11 / DevKit J1.17 -> AUX J102.17 -> U102.3 -> U102.12 -> AUX J101.3 -> K1 contact3 -> AFE J1.3 -> U1.34 |
| Chip select | MCU GPIO10 / DevKit J1.16 -> AUX J102.16 -> U102.4 -> U102.11 -> AUX J101.7 -> K1 contact7 -> AFE J1.7 -> U1.39 |

U102 is TXU0304PWR: three A-to-B channels and a separate B-to-A return channel,
with MCU and AFE supplies on their respective sides. It re-drives signals; a
resistor at the MCU does not damp a newly launched edge at U102.13. The console's
ISO7721 is not in this SPI path. K1's individually identified return conductors
remain required; C4 feed/sense wiring is not an interchangeable signal return.

Read-only total trace centreline lengths (mm, including branches where present):

| Signal | AUX MCU-side net | AUX AFE-side net | AFE net |
|---|---:|---:|---:|
| SCLK | 71.875 | 26.504 | 32.277 |
| MOSI | 63.572 | 22.631 | 32.986 |
| MISO | 66.709 | 19.276 | 35.742 |
| CS | 61.615 | 22.803 | 28.107 |

These are inventories, not extracted delay or point-to-point impedance. They omit
vertical barrels, package paths, DevKit routing/fanout wires and the K1 cable.
K1 already specifies a nominal 101.6 mm cable; the fanout geometry, actual loading,
edge rates and job-specific stack are not established. Do not turn trace-length
matching or the previous 71.875 mm clock repair into full-channel acceptance.

## 2. Which event samples data?

The sketch's `SPISettings(1000000, MSBFIRST, SPI_MODE1)` agrees with TI's CPOL=0,
CPHA=1 interface: SCLK idles low; DOUT changes following a rising SCLK edge and
DIN is accepted on a falling edge [1]. The MCU's logical receive event is the
opposite, falling edge, not the moment C++ returns from `SPI.transfer()`.

The pinned Arduino-ESP32 **3.3.12** implementation was inspected, not an assumed
current ESP-IDF example. `SPIClass::beginTransaction()` passes the selected mode
to `spiTransaction()`, which sets `ck_idle_edge=0`, `ck_out_edge=1` and commits
the configuration for S3. `spiTransferByteNL()` requests eight bits, starts the
hardware transaction, waits for completion, then reads its data buffer [3].
No added dummy cycle or per-slave `input_delay_ns` is configured in this path.
ESP-IDF's separate driver guidance is not evidence that Arduino silently performs
that compensation [4]. Do not import an original ESP32 GPIO-matrix delay limit
as an ESP32-S3 specification or claim a measured internal sampling aperture.

The distributed `BOARD_PROFILE_REVIEWED=false` build still halts before this
acquisition path. No board was operated and no review gate changed.

## 3. What the timing numbers establish, and what they do not

TI's ADC table for 2.7-3.6 V DVDD gives 17 ns maximum rising-SCLK-to-DOUT delay,
10 ns minimum DOUT hold after falling SCLK, 10 ns DIN setup/hold, 15 ns minimum
SCLK high/low and 50 ns minimum SCLK period. CS-low setup is 6 ns; final-clock
to CS-high and command decode require 4 tCLK, while CS-high requires 2 tCLK [1].
These are receiver-local requirements; actual ground differences still apply.

At both TXU rails 3.3 +/-0.3 V, each direction has 0.5-11 ns propagation delay
under the stated temperature/test conditions. Importantly, the propagation test
uses **5 pF including probe/jig**, S1 open, and specified input transitions [2].
Do not substitute S2's assumed 100 pF load into that test or promote 11 ns to a
complete loaded-cable bound. VCC/temperature/edge/load applicability must be met.

For an IDEAL 50%-duty 1 MHz clock, one rising-to-falling interval is 500 ns:

    Conditional component subtotal = 11 + 17 + 11 = 39 ns
    Unallocated ideal interval     = 500 - 39 = 461 ns

**461 ns is not measured timing margin.** Interconnect flight time, real load and
threshold crossing, MCU input path/setup, phase error and uncertainty are still
unbudgeted. The 39 ns sum is not a whole-channel worst case. In particular, a
large nominal setup interval says nothing by itself about hold or repeated
threshold crossings from ringing.

Use the following endpoint definitions to avoid mixing clock locations. Let H
be MCU-pin rising-to-falling time. Let c_up/c_down be delays from those MCU-pin
clock edges to the ADC clock pin, including the forward buffer and interconnect;
r be ADC-DOUT-to-MCU-input delay, including the return buffer and interconnect.
Let delta be the internal MCU sampling-event displacement from the corresponding
MCU-pin falling clock edge, and s/h the MCU input setup/hold requirements.
Conservative sufficient checks, with all bounds applicable to the same setup:

    SETUP: c_up_max + tDOPD_max + r_max + s <= H_min + delta_min
    HOLD:  c_down_min + tDOHD_min + r_min >= delta_max + h

Input-path timing must be accounted for exactly once in delta/s/h. The ADC's
10 ns output-hold minimum cannot be replaced with an assumed extra half-cycle.
No complete numerical MCU/load/interconnect bounds were established here, so
neither inequality is declared passed. Measurement timing must reference actual
receiver-local rails/thresholds, not just a 50% cursor on an upstream waveform.

For outgoing MOSI, check DIN setup/hold at the ADC against the clock arriving
there, including MCU launch skew and differential buffer/interconnect delays.
MOSI remains zero during data reads but carries nonconstant register/command
bits at startup: it cannot be dismissed as an unused line. Different propagation
bounds on CS and SCLK likewise affect the ADC-local CS guard interval.

## 4. Commands and whole-frame timing are separate from bit timing

`selectChip()` asserts CS and requests a 3 us delay. `releaseChip()` requests
3 us before deassertion and another 3 us afterward. Register commands include
3 us gaps between their command bytes. Even using the ADC table's slowest allowed
master-clock period, 666 ns, 4 tCLK is 2.664 us; the programmed 3 us leaves
336 ns before interconnect skew and implementation/timing uncertainty [1].
That is a source-code guard comparison, not a measured receiver timing pass.
The 1 MHz serial clock and the ADC's internal nominal 2.048 MHz master clock are
DIFFERENT clocks. Do not interpret 4 tCLK as four microseconds of SPI clock.

Four channels produce 3 status + 12 channel bytes: 120 SCLK cycles, or 120 us of
clocking per nominal 4 ms conversion interval. CS delays, inter-byte software
checks, interrupts and scheduling add time. A 3% clock occupancy does not prove
an entire transaction deadline. RDATAC reads must finish before the relevant
conversion-update window [1]. Inspect actual last-clock/next-DRDY separation;
interrupt timestamps are not zero-latency measurements of ADC-pin DRDY.

The sketch discards a candidate when its DRDY count changes during the read and
checks the native status prefix, but those guards are NOT a CRC and do not detect
every corrupted sample bit or missed physical edge. Do not add SPI dummy clocks
as a generic latency fix: they would shift the ADS frame unless the protocol is
redesigned and reviewed. Retain existing register readback and overrun reporting.

## 5. Finite electrical acceptance and termination decision

Retain the existing protocol for design continuation. Do not change SPI software
or add a guessed 22/33/47-ohm resistor to turn missing evidence into a pass.
The existing 42.2-kohm pulldowns set states; they are not source line termination.
Lowering the clock rate does not necessarily slow the electrical edges, and
Schmitt inputs do not establish freedom from ringing or over/undershoot [2].

Before the affected manufacturing release, choose explicitly between accepted
channel evidence and a bounded pilot with a reviewed rework/termination-provision
plan. This note does NOT choose that risk on the user's behalf. If damping is
required, address the actual driving end of each separately driven segment:
MCU-to-U102, U102-to-ADC, ADC-to-U102, and U102-to-MCU. Avoid stubs and arbitrary
parallel loads that would invalidate the existing DC/current/partial-power budget.
A source-series value depends on drive and interconnect impedance; those are not
specified by the clock frequency or the footprint name alone.

Add only the following evidence to the EXISTING B2 record for authorized testing:
receiver-local SCLK monotonic crossings/high-low widths and input excursions;
ADC DIN/CS setup/hold; returning MISO validity around the MCU sampling interval;
full-frame DRDY clearance; actual supply/return state and probe loading. Keep
both endpoints time-aligned where a propagation/hold claim needs them. Clips or
long B3 rail-sense tails must not be treated as transparent logic probes. First
register readback/internal-test success is useful function evidence, not whole
SI, noise, partial-rail or body-use qualification. No testing is authorized here.

**Next independent before-fabrication decision:** disposition the existing six
AFE upstream coupling pairs as one coordinated item for the limited internal-test
pilot, preserving their original guards and the separate external E1 criteria.
Do not repeat L1 or build a generic SPI simulator; actual channel/fixture evidence
remains attached to its dependent release stage. Moscow/no deep pricing remains.

## Sources and verification scope

[1] TI ADS1299-x SBAS499C, p12 timing tables; sections 9.4.4 and 9.5 serial
interface/read modes. Parsed manufacturer text checked on 2026-10-08. The timing
page screenshot and direct local PDF download failed; no fresh visual inspection
of that page is claimed. https://www.ti.com/lit/ds/symlink/ads1299.pdf

[2] TI TXU0304 SCES935A, section 7.11 p14 and section 8.1 p18. Page14 image
inspected; p18 loading text parsed, screenshot unavailable. These are stated
source/test conditions, not a measured assembled load.
https://www.ti.com/lit/ds/symlink/txu0304.pdf

[3] Espressif Arduino-ESP32 tag3.3.12: `libraries/SPI/src/SPI.cpp` Git blob
`e2237f1e5645cb276567a56d804087107617223d` (lines195-231), and
`cores/esp32/esp32-hal-spi.c` blob `07e016e240ad9f01134d52f9b8ed4b88ba7d3b61`
(lines750-957,1320-1454). Source read through GitHub; library API is not a
measured electrical timing specification.
https://github.com/espressif/arduino-esp32/tree/3.3.12

[4] Espressif ESP-IDF SPI master documentation, read 2026-10-08, comparison of
its separate `input_delay_ns`/dummy-cycle interface only, not the pinned Arduino
HAL implementation. https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/peripherals/spi_master.html

Read-only source/netlist arithmetic, not a new native CAD/EM run or physical test.
The 25 terminal identities, four signal inventories, existing mode/delays/frame
source and unchanged quote hashes were checked. No project tests/code, BOM,
PCBs, dependencies, guards or qualification fields changed. Local locked install
failed DNS; hosted results must be read on the actual new head, not inferred from
PR94. #45/#48 and all purchase/fabrication/powering/body-use gates remain open.
