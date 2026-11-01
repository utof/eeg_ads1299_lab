---
id: safety-stops
code: SAFE
title: Safety stops and interlock
status: partial
stage: before-power
reviewed_at: 652193d
reviewed_on: 2026-11-01
scope:
  - firmware/esp32_ads1299_bench/c2_interlock.h
  - firmware/esp32_ads1299_bench/esp32_ads1299_bench.ino
  - firmware/esp32_ads1299_bench/rev_a_startup.h
  - hardware/rev_a/auxiliary/arming.kicad_sch
  - hardware/rev_a/auxiliary/contract.json
  - tests/test_firmware_interlock.py
  - tests/native_c2_session_test.cpp
  - tests/firmware_stubs
  - docs/REV_A_BUS_INTERLOCK_C2.md
  - docs/REV_A_C2_FIRMWARE.md
---

# Safety stops and interlock

## Covers

J106 normally-open STOP contact -> C2 latch (LVC2G74 / LVC1G97, CLR_N,
BUS_OE) -> READY/ARMED feedback on GPIO15/16 -> `C2Interlock` firmware state
-> `requireBus()` gating of every bus operation -> test double and native
session tests that are supposed to catch regressions.

## Findings

| ID | Status | Summary | Where (at 652193d) |
|---|---|---|---|
| SAFE-01 | open | Two C2 guards survive deletion: removing the unsolicited-ARMED rejection and the READY term in `valid()` leaves all 62 firmware tests (native included) passing. The test double can't show ARMED high while READY is low, and `stuckArmed` is set only before `setup()`. Add late-ARMED and lost-READY scenarios | `c2_interlock.h:43,65`; `tests/firmware_stubs/Arduino.h:45,51,93-94` |
| SAFE-02 | open | Two sketch guards have no failing scenario: channel-count fail and register-readback-mismatch fail (double always returns the same ID and echoes writes) | `esp32_ads1299_bench.ino:103,207` |
| SAFE-03 | open | No interlock-only commissioning hold: firmware arms C2 then immediately raises PWDN/CLKSEL/CS/RESET. Interlock evidence must precede ADC bus enable, and reflashing means removing DevKit tails, so the first flashed image needs a console-selected "armed, ADC parked, keep polling" hold before the internal-test path | `esp32_ads1299_bench.ino:154-158,184-186`; `rev_a_startup.h:18-21`; `docs/REV_A_SPI_PROVISION_L4.md:208-209`; `docs/REV_A_OBSERVATION_B2.md:177` |
| SAFE-04 | suspected | GPIO15/16 readback lines connect straight to CLR_N/BUS_OE without series resistors; future firmware driving them as outputs would fight U109/U111. Today firmware uses `INPUT_PULLDOWN`. Confirm by computing contention current | AUX `arming.kicad_sch` |

## Not yet covered

- STOP contact electrical behavior and debounce through to the latch clear.
- Hardware latch timing (setup/hold, power-up state) against LVC2G74 datasheet.

## Log

- 2026-11-01, 652193d, Opus critical-bug review with a verification
  sub-review that ran firmware mutation tests. `BOARD_PROFILE_REVIEWED=false`
  halts before ADS pin setup; every bus operation is gated by `requireBus()`.
  SAFE-01 cause confirmed by reading the stub. The hardware flip-flop clear
  makes SAFE-01 defence-in-depth, not an immediate hazard.
