# Rev A physical harness and application console — review candidate

This closes the logical-GPIO-to-physical-header gap after PR #43. It does not
release a cable, PCB, console adapter or live setup. All existing hardware,
purchasing, external-input and body-use gates remain false. Component families,
ADS GPIO assignments, native schematic, input/BIAS networks and rail topology
are unchanged. The new application-console assignment is an explicit firmware
change: UART0 is remapped to RX GPIO17 / TX GPIO18 only on the reviewed S3 path.

## Why not simply plug in USB or another adapter?

Espressif lists USB power, header 5 V power and header 3.3 V power as mutually
exclusive alternatives [1]. Rev A uses the external regulated 5 V alternative;
normal USB cables into either DevKit socket are therefore excluded during the
proposed acquisition setup. Do not power AVDD from the DevKit's diode-dropped
USB supply instead: that is not the selected regulated analog power path.

The V1.1 manufacturer schematic [2, sheet 2] shows the onboard CP2102N powered
from VCC_3V3, its TXD connected through R9 to U0RXD, and its RXD connected through
R7 to U0TXD. Those same nets appear on DevKit J3 pads 3 and 2. Thus attaching a
second transmitter to GPIO44 would share a net with the onboard bridge's output.
Unplugged USB is not evidence that this powered chip's output is high impedance.
We avoid that shared output rather than assume it is inactive.

A VBUS-cut USB cable is not an established fix either. The DevKit's VBUS divider
feeds the CP2102N VBUS-sense input [2]; Silicon Labs specifies that input for USB
connection detection [3]. My inference from those connections is that retaining
only D+/D-/ground does not preserve the specified detection arrangement. No
board modification, modified USB cable or USB compliance claim is made here.

## Separate programming and acquisition arrangements

| Arrangement | DevKit power and connection | Application console |
|---|---|---|
| DevKit-only programming / default review-stop inspection | DevKit USB-to-UART port; AFE, external supply and external header interface all disconnected | Existing onboard UART0. The distributed `BOARD_PROFILE_REVIEWED=false` sketch keeps the ordinary default console and never configures the external console or ADS control pins. |
| Proposed reviewed, person-disconnected acquisition | One regulated bench 5 V source branches to AFE and DevKit header; both DevKit USB sockets disconnected | Separately qualified 3.3 V UART interface: TX to GPIO17, RX from GPIO18, common return. No interface power, DTR or RTS connection. Still blocked until actual board/interface/startup review. |

Do not switch between these arrangements by hot-plugging power or signal leads.
An interface connected to the host can drive its TX while the DevKit is off;
DevKit TX can likewise drive an unpowered interface. Removing an adapter's VCC
wire does **not** prevent this signal-pin back-powering. The actual interface
must have documented compatible 3.3 V levels and powered-off behavior, or a
separately reviewed isolation/buffering arrangement, including target power loss.
No interface MPN is selected or purchased in this slice. An unknown USB adapter,
a 5 V TTL adapter or RS-232-level port is not an approved substitute.

## Numbered connection worksheet

`AFE.<ref>.<pad>` uses the **native reference from the validated KiCad export**;
currently AFE.J1 is ContractRef J_DIG. `DEVKIT.J1.<pad>` is the physical V1.1
DevKit header pad from the manufacturer, not the GPIO number. The boards both
use the reference J1: the board prefix must never be dropped. INTERFACE denotes
an unqualified external UART interface, not a specific product.

Signal rows put the transmitter first. The 5 V and common-return rows are
common-node membership, not series power routing. In particular the external
supply branches to each board; the daughterboard's regulator never powers the
MCU. Ten AFE ground contacts remain accounted for. Their physical fan-out,
return geometry, cable length, connector retention and current rating require
review; a common-net list cannot establish those properties.

<!-- generated-harness-table: checked against the source in ordinary tests -->
| Function | Board-qualified endpoints on the same net |
|---|---|
| SCLK / GPIO12 | `DEVKIT.J1.18`, `AFE.J1.1` |
| MOSI / GPIO11 | `DEVKIT.J1.17`, `AFE.J1.3` |
| MISO / GPIO13 | `AFE.J1.5`, `DEVKIT.J1.19` |
| CS / GPIO10 | `DEVKIT.J1.16`, `AFE.J1.7` |
| DRDY / GPIO4 | `AFE.J1.9`, `DEVKIT.J1.4` |
| RESET / GPIO5 | `DEVKIT.J1.5`, `AFE.J1.11` |
| START / GPIO6 | `DEVKIT.J1.6`, `AFE.J1.13` |
| PWDN / GPIO7 | `DEVKIT.J1.7`, `AFE.J1.15` |
| CLKSEL / GPIO8 | `DEVKIT.J1.12`, `AFE.J1.19` |
| Console receive / GPIO17 | `INTERFACE.TX_3V3`, `DEVKIT.J1.10` |
| Console transmit / GPIO18 | `DEVKIT.J1.11`, `INTERFACE.RX_3V3` |
| External regulated 5 V | `SUPPLY.+5V`, `AFE.J1.17`, `DEVKIT.J1.21` |
| Common return | `SUPPLY.RETURN`, `DEVKIT.J1.22`, `INTERFACE.GND`, `AFE.J1.2`, `AFE.J1.4`, `AFE.J1.6`, `AFE.J1.8`, `AFE.J1.10`, `AFE.J1.12`, `AFE.J1.14`, `AFE.J1.16`, `AFE.J1.18`, `AFE.J1.20` |
<!-- end-generated-harness-table -->

Important distinctions: SCLK GPIO12 reaches **DevKit J1 pad18**, not pad12.
CLKSEL GPIO8 reaches DevKit J1 pad12. ADS RESET uses GPIO5 / DevKit J1 pad5,
not the DevKit's own RST/EN pad3. GPIO17 is application RX despite the
manufacturer table listing its native U1TXD function: the sketch explicitly
maps **UART0** through the GPIO matrix, rather than relying on that alternate
function label [4]. The console transmit signal similarly uses GPIO18.

### Orientation and mating view

The DevKit guide's front/top view and schematic share the same header numbering
[1, 2]. Locate the 3V3 end of DevKit J1 (pads1/2); pad3 is RST. The opposite end
has 5V pad21 and ground pad22. Confirm against the actual PCB revision and clear
photographs, not the direction of a USB cable or an unidentified clone's label.

The AFE footprint is a 2x10 header, NOT the DevKit's 1x22. In the assigned KiCad
footprint's local top-view coordinates, pad1 starts the odd column, pad2 the even
column; the next row is pads3/4. A plug's mating face or the board's solder-side
view is mirrored relative to the board top. Use numbered continuity checks;
never infer a mating connector's cavity order from a top-view image. The authored
layout now places AFE J1 pad1 at (80,27) mm and AFE J2 pad1 at (15,32) mm, both
at zero footprint rotation; rows advance in +y and odd pins occupy the lower-x
column. These are top-view board coordinates, not a plug mating-face diagram.
See `REV_A_MECHANICAL_ENVELOPE.md` for the source-bound envelope and the TSW
assembly-process restriction. Actual polarized mates, cable/strain relief and
process qualification remain open under #45. No connector or pin mapping changed.

## Firmware and recording behavior

`bench_console.h` owns RX17, TX18 and 460800 baud. The reviewed S3 branch calls
`Serial.begin(baud, SERIAL_8N1, rx, tx)` with explicit arguments. With CDC-on-boot
zero, the pinned core maps Serial to Serial0/UART0 [4]. `CDCOnBoot=default` is
now explicit in the existing FQBN, and an S3 compile with CDC enabled fails with
a diagnostic instead of silently selecting a different Serial implementation.
The original ESP32 path retains its prior default-UART behavior.

The false review-stop path **does not configure GPIO17/18**; it keeps the onboard
UART0 diagnostic. Reaching the new header route requires the existing exact-board
review, now explicitly including this console interface and its power states.
No production bypass macro or extra acquisition mode was added. Boot-ROM output
and bootloader programming remain on their existing paths, not this remapped
application console. Opening the new interface must not toggle DevKit EN/BOOT:
DTR/RTS are absent from the proposed connection list.

The same UART carries prompts, fresh `R`/`V` acknowledgments and the unchanged
binary stream. A serial terminal can provide the measured acknowledgments;
close it before opening the existing serial capture command on that interface.
Samples emitted during that handoff are not recorded. This is not a lossless
start-of-acquisition workflow; the existing sequence numbers describe received
packets, not proof that initial packets were captured. No host handshake/capture
controller or physical baud-rate/throughput validation is claimed here.

## Checks, evidence and remaining stop conditions

Run the existing entry point:

```sh
uv run --locked python -m tools.check --native --schematic
uv run --locked python -m tools.check --firmware
```

Ordinary tests check the independent manufacturer pad expectations, every AFE
header contact, both console directions, excluded power/reset paths, source
rejection and this worksheet. The actual-sketch host double records baud,
format, RX and TX and checks the review-stop path, reviewed path and legacy
ESP32 stop. Mutations swap console pins, restore implicit defaults, change baud
or configure the external console before review; each must compile then fail.
These are call-order tests, not UART or voltage emulation. The actual S3 build
remains a separate hosted target-compilation job.

The native schematic gate derives `harness.json` from the freshly validated
netlist/profile/BOM and the console header. Before publishing it, even standalone
`--schematic` requires a C++ compiler and runs the existing 22 focused native
cases: actual-sketch startup/console cases plus the CDC header checks. These
are a subset of the 88 native/integration cases, not 22 new tests. A missing
compiler or failed route proof prevents the harness/success marker. Compiler
version, logs, JUnit and disposable test inputs are retained. The schematic CI
job installs g++ explicitly; no ngspice dependency is added to that job.

The 43-input before/after snapshot binds the actual sketch, all six local
firmware source files, toolchain settings, the two invoked test files, native
C++ oracle, five stub headers, pytest configuration and prior CAD/contract inputs.
The five main artifacts remain ERC/XML/PDF/CSV/harness. Header parsing still
checks only a closed literal contract, not C++ semantics; executing the real
sketch is what ties those literals to the claimed application route. This is
host call-order evidence, not peripheral or electrical behavior. The separate
pinned S3 target build remains required. No new registry, simulator, dependency
or verification orchestrator is introduced.

This ordering fixes an independent-review finding on the first candidate: a
standalone native schematic run could publish GPIO17/18 even after the sketch's
explicit pin arguments were removed. A real KiCad diagnostic reproduced that
false positive (ordinary stages were omitted to isolate the native path). Four
new software gate regressions then failed before correction: ignored route
failure, missing compiler, changed sketch and changed S3 profile. The corrected
path reuses the existing executable oracle instead of adding a text-only
`Serial.begin` assertion or claiming that source hashes prove execution.

Still required before any live setup: actual PCB/module revision confirmation;
qualified interface/cable and pin-one orientation; unpowered continuity and
short checks; passive analog-input startup fixture; measured low ADS inputs
through rail ramp, continuous clock-start interval, VCAP1 and reset timing;
and boot/reset/brownout/loss-of-rail back-power review. An operator acknowledgment
is not an interlock. STOP on uncertain interface levels, unspecified powered-off
outputs, unidentified board revision or simultaneous supply inputs. The ordinary
checks do not authorize changing a review gate.

Package dimensions/polarity/land-pattern review and connector mechanics remain
next, followed by PCB placement/layout, DRC and schematic parity, delivered
quotes, and staged person-disconnected bench work. No body-connected use.

## Primary references

[1] Espressif, ESP32-S3-DevKitC-1 v1.1 user guide: J1 header table, front view,
ordering code and mutually exclusive power alternatives (checked 2026-09-26).
https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide_v1.1.html

[2] Espressif, ESP32-S3-DevKitC-1 V1.1 schematic, 2022-11-30, sheet2: J1/J3,
CP2102N U3 and R7/R9, VCC_3V3 supply, VBUS divider and USB diode power paths.
The sheet was visually checked; it is not a photograph of the user's board.
https://dl.espressif.com/dl/schematics/SCH_ESP32-S3-DevKitC-1_V1.1_20221130.pdf

[3] Silicon Labs CP2102N datasheet Rev1.5, section2.3 and QFN28 pin8 definition:
VBUS sensing for bus connection. Used to assess the VBUS-cut assumption, not to
claim a particular assembled board enumerated or failed an actual USB test.
https://www.silabs.com/documents/public/data-sheets/cp2102n-datasheet.pdf

[4] Pinned Arduino-ESP32 3.3.12 HardwareSerial.h: explicit begin(rx,tx), detaching
previous pins and Serial-to-UART0/USB selection. The generic API documentation
also describes GPIO routing. The version pin, not current documentation alone,
is the target build basis.
https://github.com/espressif/arduino-esp32/blob/3.3.12/cores/esp32/HardwareSerial.h
https://docs.espressif.com/projects/arduino-esp32/en/latest/api/serial.html
