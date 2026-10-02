# F1: guarded C2 firmware integration

Base: merged C4 `c8c8a12cd0ca92bef0edc938794fa662a6204d61`, tree
`e956d55b655290ce1db2c3a0cc8266c25cf9a8bc`. No CAD, BOM, circuit, acquisition
format, default Wi-Fi setting, target selection or release gate changes.
`BOARD_PROFILE_REVIEWED` stays false. This implements the reviewed-branch
handshake; it does not authorize running it on unqualified hardware.

## Architecture and actual behavior

A small `C2Interlock` in `c2_interlock.h` owns the Cold/Parked/Active/Faulted
handshake. Its GPIO/time interface is injectable for host tests; it is not a
new scheduler, generic hardware framework or separate copy of the firmware.
The actual sketch's `requireBus`, `busTransfer` and bounded wait adapter guard
startup, register operations and capture. Keeping these common boundaries is
preferable to independent ad-hoc checks in each operation.

C2 uses SESSION=GPIO14, ARM_REQ=GPIO9, READY=GPIO15 and ARMED=GPIO16. Independent
tests compare those roles to the auxiliary MCU_TAILS, CLR_N and BUS_OE nets.
Before enabling the two output pins, preload SESSION and ARM low. READY/ARMED
use input pulldowns, and both must be low after a 10-us clear interval. Then
park all seven ADC control latches low and retain the existing fresh R prompt.
The distributed false review gate stops before **any** of this GPIO setup.
Original-ESP32 builds do not use the S3 C2 wiring.

After R, raise SESSION. Require actual READY high over a continuously sampled
interval of at least 10 us, rejecting unsolicited ARMED. Waiting for READY is
bounded to one second. Issue a new ARM high pulse for at least 10 us, return it
low, and require READY and ARMED high. Unsigned timer differences handle wrap.
Those selected handshake intervals are firmware bounds, not guaranteed detector
or MCU response times. Only after the handshake may the unchanged helper raise
PWDN/CLKSEL and start the clock interval, wait 150 ms, request fresh VCAP1 V
confirmation and apply the existing reset sequence. Requiring completed clock
startup before permitting those control signals would deadlock startup.

Feedback is checked around startup waits and prompts, SPI initialization,
transactions/bytes, reference settling, optional Wi-Fi setup, capture, and
packet output. Startup/reference/Wi-Fi waits are subdivided into one-ms polling
steps. The software relies on C2's actual hardware latch: after a detected rail
fault clears BUS_OE, restoring rails alone must leave ARMED low. No new status
ISR, rail-voltage measurement or guaranteed physical fault-detection envelope
is claimed. A READY disturbance that neither clears the real latch nor overlaps
a software sample may be missed.

On detected feedback loss or any existing acquisition error, `fail` invalidates
the software state and attempts to drive SESSION/ARM low **before** printing or
peripheral teardown. It detaches DRDY, closes an open SPI transaction/instance,
preloads the seven control latches low, returns configured controls to GPIO,
and clears channel/edge/sequence/overrun/timestamp state. Cleanup is best effort:
failed control power or a failed GPIO is not repaired by code. The halt is
terminal; no console command or restored supply restarts it. A full reset and
fresh reviewed startup are required.

## Limits that remain

A blocking serial/network call cannot be preempted by these polls. A detected
fault during that call is handled when control returns; hardware must stop the
bus independently. Queued/transmitted bytes cannot be recalled. The human-readable
`HALTED / ... CAPTURE INVALID` marker is not a new binary protocol event or an
implemented host-side recording-revocation mechanism. Reject the entire affected
run and retain diagnostics. Host session-disposition work remains separate.

A valid logic reading is not E1 rail/noise acceptance. Brownout, supply ramps,
floating/broken feedback, C3's narrow leakage margins, supervisor overdrive
conditions, analog-source exposure, all #45/#48 requirements and actual auxiliary
hardware qualification remain open. In particular software polling supplies no
unconditional microsecond shutdown guarantee. Auxiliary PCB placement/routing,
physical cable/assembly/fit and delivered cost are still unfinished.

## What was recovered and independently checked

Live main and the only open PR (#40, historical do-not-merge evidence) initially
showed no new firmware implementation. A further branch scan found an incomplete
transfer on `workbench/c2-firmware-publication` at `842f707a`. Its c00-c08 stream
is truncated inside object 22 of 44; the earlier part00/part01 stream is corrupt.
The complete prior commit/tree could **not** be recovered. Neither was imported
as a valid finished checkout.

An isolated recovery read the complete Git-object prefixes, checked their object
identities and recovered the C2 header, sketch and Arduino-double source. The
header/sketch are adopted from that recovered work rather than rewritten. Missing
tests are replaced by newly authored independent tests, not invented old results.
The inspection repository containing incomplete objects is not this clean source
repository. Our commits start at the real merged main and record fresh failures.
The unused partial transfer is not a dependency and contains no current PR work.

Before adopting the implementation, 16 new tests failed on the unchanged firmware
(one missing-header check and 15 actual-sketch scenarios). The expanded I/O
doubles separately passed all 20 existing sketch tests first. After adoption,
a READY-glitch scenario was added and the wait oracle made explicit about sliced
polling; 11 separately compiled mutations must fail behavioral assertions, not
merely fail compilation. These include missing SESSION/ARM, shortened stability
or pulse, lost ARMED checks, unsliced startup waiting, unchecked frame bytes,
missing post-write validation, SPI cleanup and cleared state. The modified GPIO
failure oracle still forbids enabling an ADC output after latch failure, while
allowing the newly required C2-only low output setup. The stale-response mutation
now targets the guarded drain block without deleting its behavioral requirement.

The ordinary source snapshot tests additionally produced three failures before
the new header and two test inputs were bound into schematic receipts. The same
`tools.check` entry point now executes the actual C2 sketch tests alongside the
existing console proof. New process doubles are not KiCad/hardware executions;
none of these tests is a transistor/MCU emulator or exhaustive mutation score.

```sh
uv sync --locked --all-extras
uv run --locked --all-extras python -m tools.check
uv run --locked --all-extras python -m pytest tests/test_firmware_interlock.py tests/test_firmware_sketch_startup.py -q
uv run --locked --all-extras python -m tools.check --native
uv run --locked --all-extras python -m tools.check --schematic
uv run --locked --all-extras python -m tools.check --firmware
```

Read actual final-head CI/review results, not the prior C4 counts or this
pre-CI document. Portable C++ execution and an actual ESP32-S3 compilation are
different scopes. GPIO API references inspected 2026-10-02:
https://docs.espressif.com/projects/arduino-esp32/en/latest/api/gpio.html
https://docs.espressif.com/projects/esp-idf/en/v5.3.3/esp32s3/api-reference/peripherals/gpio.html
The pinned Arduino toolchain compilation is authoritative for this project's
API compatibility; neither documentation nor compiling proves physical behavior.

**Next bounded slice: auxiliary PCB placement from the existing four-sheet C3
schematic**, preserving C1's HOST/TARGET isolation, C4's separate feed/sense,
bypasses and mounting/cable access. Do not repeat J3 or redesign pin maps. Keep
all fabrication, purchasing, powered-connection and body-use permissions false.
