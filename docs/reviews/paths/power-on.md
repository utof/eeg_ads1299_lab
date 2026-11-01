---
id: power-on
code: PWR
title: Power-on sequence
status: partial
stage: before-power
reviewed_at: 652193d
reviewed_on: 2026-11-01
scope:
  - firmware/esp32_ads1299_bench/esp32_ads1299_bench.ino
  - firmware/esp32_ads1299_bench/rev_a_startup.h
  - firmware/esp32_ads1299_bench/board_config.h
  - firmware/esp32_ads1299_bench/board_config_rev_a_s3.h
  - hardware/rev_a/kicad/power.kicad_sch
  - hardware/rev_a/auxiliary/supervision.kicad_sch
  - hardware/rev_a/auxiliary/contract.json
  - hardware/rev_a/board_profile.json
  - lab/rev_a_power.py
  - lab/rev_a_supply.py
  - tools/dc_budget.py
  - docs/REV_A_STARTUP_SEQUENCE.md
  - docs/REV_A_OBSERVATION_B2.md
---

# Power-on sequence

## Covers

J105 regulated 5 V -> R11 -> AVDD and TPS7A2033 LDOs -> TPS3703A5500 window
supervisors -> C2 arm -> firmware gate `BOARD_PROFILE_REVIEWED` -> ADS1299
PWDN/CLKSEL/CS/RESET -> 150 ms -> VCAP1 > 1.1 V -> reset -> register setup.
The DevKit is also fed from J105 through J102.21. The B2 run card's H1 limits
belong here.

## Findings

| ID | Status | Summary | Where (at 652193d) |
|---|---|---|---|
| PWR-01 | open | B2 H1 numeric limits are blank, so the board can't be powered (by design). Derive staged current limits, rail windows and abort criteria from datasheets and S1 load allocations (AFE ~27 mA; DevKit 100-500 mA dominates) | `docs/REV_A_OBSERVATION_B2.md:124` |
| PWR-02 | suspected | TPS3703A5500 undervoltage (~4.75 V) watches AVDD after 10 ohm R11, leaving tens of mV margin at a 4.95 V source; the board may never arm (safe but unusable). Confirm with the supply setpoint vs threshold tolerance, then measure at AFE C32 | `docs/REV_A_SUPPLY_RETURN_S1.md:168-170`, `docs/REV_A_BENCH_FIRST.md` section 2 |

## Not yet covered

- TPS7A20 startup/enable behavior and its interaction with the supervisors
  (open experiment PR34/PR40 is related history; do not merge them).
- SPICE power/supply models versus datasheets (`lab/rev_a_power.py`,
  `lab/rev_a_supply.py` numerics).
- DevKit USB/5 V backfeed when J105 and USB coexist (USB ports are excluded
  by procedure, not checked by design).

## Log

- 2026-11-01, 652193d, two Opus reviews (critical-bug review; remaining-work
  audit). Firmware startup order checked against TI SBAS499C: outputs preloaded
  low -> pins enabled -> `R` ack -> C2 arm -> PWDN/CLKSEL/CS/RESET high ->
  150 ms (> t_POR 128 ms) -> `V` ack -> 4 us RESET pulse (min ~1 us) -> 20 us
  (> 18 t_CLK). `BOARD_PROFILE_REVIEWED=false` halts before any ADS pin setup.
  A proposed reordering (150 ms before CS/RESET high) was rejected: the current
  order meets the datasheet. Board-side supply chain only partly read; H1
  limits absent. Nothing critical in firmware.
