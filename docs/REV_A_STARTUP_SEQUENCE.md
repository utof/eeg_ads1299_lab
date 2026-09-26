# Controlled Rev A startup: software ordering, not electrical qualification

## Why this slice exists

At PR #39 head `7d61786cb8e6ec490b7154474fc2a88e5fa1afe3`, the declarative
hardware map added controlled CLKSEL on GPIO8 and changed CS/CLKSEL to pulldowns,
but the S3 firmware header and sketch did not drive that new signal. The unchanged
locked quality gate reproduced the exact-map failure: 612 passed, one failed.
Codex independently identified the missing clock drive and the unsupported claim
that digital controls alone address analog-input startup.

The existing ADS1299-4, TPS7A2033PDBVR (ADS DVDD only), separate analog supply,
input filter, BIAS network, firmware modes and all false approval gates remain.
The baseline JSON's historical `existing_firmware_modified: false` is not a claim
that this later firmware slice leaves the sketch byte-identical.

## Explicit preconditions and sequence

`BOARD_PROFILE_REVIEWED` remains false. The distributed sketch stops before any
ADS control GPIO setup. The following candidate is reachable only after a
separate exact-board review; this change does not grant that review.

1. Passive pulldowns must hold the digital controls low during boot. A separately
   reviewed passive startup fixture must hold the used analog inputs low during
   the rail ramp. No person or powered external signal source may be attached.
   The R/C input network alone does not provide that termination.
2. The reviewed S3 path preloads all seven output latches low before enabling
   them. A fresh `R` response acknowledges measured stable ADS rails and the
   passive analog startup condition. It is not power-good sensing.
3. Release PWDN, enable CLKSEL (GPIO8), deselect CS and release RESET. PWDN low
   disables the ADS oscillator, so delays before this point do not count.
4. Wait 150 ms. Then require a fresh `V` response acknowledging measured
   VCAP1 > 1.1 V while both rails remain stable. A fixed delay does not establish
   the VCAP1 voltage. Responses already queued before each prompt are discarded.
5. Pulse RESET low for 4 us, release it and wait another 20 us. Only then initialize
   SPI and run the existing internal-test/internal-short register configuration.
   START stays low; the later existing START command controls conversion.

The operator confirmations are deliberately narrow bench preconditions, not
hardware interlocks, automated measurement or protection against subsequent rail
collapse. Wrong acknowledgments, boot-ROM GPIO behavior, brownouts, fixture
errors and digital back-powering still require board-specific electrical review.
Do not lift any hardware, external-input, purchasing or body-use gate on this basis.
An internal-short MUX setting after SPI initialization cannot terminate inputs
before power-up; short-to-ground is also not a general unipolar external-signal
noise-test setup. This slice specifies startup only.

## Basis and implementation seam

TI ADS1299 Rev. C, section 11.1 / Figure 76 / Table 30, requires supply
stabilization before clocking, then `2^18 * tCLK` and VCAP1 > 1.1 V, whichever is
later, before reset. Table 30 requires a reset pulse of at least 2 clock periods
and 18 periods for reset recovery. The electrical table gives 2.048 MHz nominal
internal clock, a 2.5% frequency allowance and 20 us oscillator startup. The
conservative software wait is 150 ms after wake/clock, not the earlier USB delay.

Primary source (tables and Figure 76 visually checked):
https://www.ti.com/lit/ds/symlink/ads1299.pdf

`rev_a_startup.h` contains a single sequence with a small template I/O seam. It
uses the existing S3 pin header, not a second GPIO registry, and adds no framework
or dependency. The sketch adapter uses ESP-IDF `gpio_set_level` to preload the
latch before Arduino `pinMode`; in the pinned Arduino core, `digitalWrite` refuses
pins not yet registered as GPIO. The actual physical startup waveform remains
unmeasured.

Pinned Arduino source inspected:
https://github.com/espressif/arduino-esp32/blob/3.3.12/cores/esp32/esp32-hal-gpio.c
ESP-IDF GPIO API:
https://docs.espressif.com/projects/esp-idf/en/v5.5.2/esp32s3/api-reference/peripherals/gpio.html

## Tests and falsification

The test-only commit `06fe045c125ff9f036dfc310e232550295ff8a33` precedes the
implementation. Against the original PR head, the focused locked run had ten
intended failures: the sketch did not call the sequence and its header was absent.
The pre-existing map test separately detected missing CLKSEL.

The C++ trace test compiles the production sequence and records ordered pin,
confirmation and timing operations. It checks both blocked prefixes, the complete
sequence, low latches before output enable, independent expected pin numbers,
continuous oscillator wake time, reset width/recovery and START remaining low.
Mutation fixtures remove clock/wake/confirmation/reset operations, shorten waits,
assert the clock early or remove latch preloading. They must compile and then
fail behavioral assertions, not merely produce compiler errors. A benign extra
pre-wake delay must still pass.

An additional power-down-during-wait mutation initially survived the first-event
oracle. The test was corrected to measure from the most recent low-to-high
transition of PWDN/CLKSEL, catching the interrupted tPOR interval. This is a
specific oracle correction, not a claim of exhaustive mutation coverage.

Run through the locked environment:

```sh
uv run --locked python -m pytest tests/test_firmware_startup.py tests/test_firmware_s3.py -q
uv run --locked python -m tools.check
uv run --locked python -m tools.check --native
uv run --locked python -m tools.check --firmware
```

Native host execution, actual S3 target compilation, simulator execution and
physical measurement are separate evidence classes. The first command requires
a native compiler for its native cases; their skips are not passes. The ordinary
quality gate deliberately excludes native cases. Use the exact PR-head Firmware
job and the Quality native job before claiming all gates passed.

## Next boundary

This completes the software side of the controlled-clock proposal, not the
four-channel KiCad schematic. Next encode and review the real schematic/netlist,
including startup pulldowns, reference/VCAP, unused pins, inputs, BIAS, connectors
and GPIO mapping. The analog startup fixture and loss-of-rail behavior remain
explicit electrical-review items. The TPS7A20 engine-compatibility investigation
remains separate; no vendor model is modified here.
