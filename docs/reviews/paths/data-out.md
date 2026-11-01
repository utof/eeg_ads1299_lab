---
id: data-out
code: DATA
title: ADC data to saved file
status: partial
stage: before-power
reviewed_at: 652193d
reviewed_on: 2026-11-01
scope:
  - firmware/esp32_ads1299_bench/esp32_ads1299_bench.ino
  - firmware/esp32_ads1299_bench/portable_core.h
  - firmware/esp32_ads1299_bench/bench_console.h
  - hardware/rev_a/kicad/digital.kicad_sch
  - hardware/rev_a/auxiliary/bus.kicad_sch
  - lab/protocol.py
  - lab/acquisition.py
  - lab/adc.py
  - lab/recording.py
  - lab/validation.py
  - lab/inspect_capture.py
  - tools/run_loopback.py
---

# ADC data to saved file

## Covers

ADS1299 DOUT -> MISO_DRV -> R24 -> AFE J1 -> ribbon -> AUX J101 -> R120 /
TXU0304 -> ESP32 SPI (mode 1, 1 MHz) -> DRDY-counted frames ->
`portable_core.h` packet (header, CRC-16/CCITT-FALSE) -> serial ->
`lab.protocol` decode -> gap tracking -> recording/inspection.

## Findings

| ID | Status | Summary | Where (at 652193d) |
|---|---|---|---|
| DATA-01 | suspected | Pass criteria use bare `assert`, so they would pass under `PYTHONOPTIMIZE`. CI doesn't set it. Confirm with `PYTHONOPTIMIZE=1` and a sabotaged drop | `tools/run_loopback.py:57-59` |
| DATA-02 | open (not critical) | Inspection reports values but has no expected internal-test values (~0.977 Hz, +/-1.875 mV input-referred at gain 24 / 4.5 V ref, equal on 4 channels; noise bound for input-short) | `lab/inspect_capture.py` |

The hardware path is currently open at five DNP series resistors; tracked as
FAB-01 in [design-to-factory](design-to-factory.md).

## Not yet covered

- Real ADC frames (only synthetic and compiled-encoder cross-checks).
- Hardware signal integrity of the SPI channel (L6 accepted for an
  internal-test-only pilot; no measured evidence).
- Host-side session helper that sends R/hold/V keys and timestamps prompts
  (`capture_serial` only reads).

## Log

- 2026-11-01, 652193d, Opus critical-bug review. The real `portable_core.h`
  `packet()` was compiled with g++ and decoded with `lab.protocol`: header
  layout, little-endian metadata, CRC, 24-bit two's complement at +1/-1/+FS/-FS
  and status prefix match; the stream decoder resyncs after text junk. The
  firmware sequence number is the DRDY edge count, so discarded frames show as
  gaps; the tracker handles uint32 wrap, duplicates and stale packets. LSB =
  VREF/(gain x 2^23) per SBAS499C Eq. 8. `inspect_capture` splits on sequence
  and time gaps. The 27-byte frame buffer covers 8 channels. Nothing critical.
