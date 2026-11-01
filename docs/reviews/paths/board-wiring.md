---
id: board-wiring
code: WIRE
title: Board-to-board wiring
status: partial
stage: before-fab
reviewed_at: 652193d
reviewed_on: 2026-11-01
scope:
  - hardware/rev_a/harness.py
  - hardware/rev_a/auxiliary/contract.json
  - hardware/rev_a/auxiliary/auxiliary.kicad_sch
  - hardware/rev_a/auxiliary/RevA.kicad_sym
  - hardware/rev_a/auxiliary/auxiliary.kicad_pcb
  - hardware/rev_a/kicad/digital.kicad_sch
  - hardware/rev_a/layout/rev_a.kicad_pcb
  - hardware/rev_a/service_c4.json
  - docs/REV_A_PILOT_QUOTE_PACKET.md
  - docs/REV_A_CONTROLLER_INTERFACE_C1.md
  - docs/REV_A_SPI_PROVISION_L4.md
  - tests/test_firmware_interlock.py
---

# Board-to-board wiring

## Covers

Every pin map between boards and modules: AUX J102 <-> DevKit J1 (numbered
tails), AFE J1 <-> AUX J101 and AFE J3 <-> AUX J104 (K1 ribbons), AUX J103 <->
Adafruit 5335 HOST, J105 source pair, J106 STOP contact, C4 service cable.

## Findings

| ID | Status | Summary | Where (at 652193d) |
|---|---|---|---|
| WIRE-01 | open, confirmed | **J102.1 is TARGET_GND, but it mates one-to-one with DevKit J1.1 = 3V3.** Wired as documented, tail 1 shorts the DevKit 3V3 rail at first power; the MCU and everything on MCU_3V3 stay unpowered. Fix: make J102.1 no-connect in symbol, schematic, contract and PCB pad (pad reaches ground only through the In1 plane, so a zone refill, not a reroute); keep ground on J102.22 and move the ERC `power_out` role there; re-point B2 O6/F1 to J102.22; add a test that every J102 pin n matches `_DEVKIT_J1[n-1]` | `auxiliary/contract.json:127-131`; `auxiliary/auxiliary.kicad_sch:228-229`; `auxiliary/RevA.kicad_sym:129`; `auxiliary/auxiliary.kicad_pcb:739/745`; DevKit table `harness.py:16-39`; one-to-one rule `docs/REV_A_SPI_PROVISION_L4.md:154`, `docs/REV_A_PILOT_QUOTE_PACKET.md:231-233`; `docs/REV_A_OBSERVATION_B2.md:47,51` |
| WIRE-02 | open (not critical) | Decide on a removable 1x22 DevKit adapter before the harness is built; otherwise every reflash needs all tails reworked | `docs/REV_A_FITTED_PILOT_BUILD.md` section 5 |

## Not yet covered

- Adafruit 5335, ISO7721 and TXU0304 pinouts re-checked against current
  datasheets (consistent with docs; not independently verified).
- DevKit J1 table against the Espressif V1.1 schematic itself (the critical
  review used Espressif's user-guide J1 table plus the repo table).
- J105/J106 and C4 physical keying, crimp and strain-relief details.

## Log

- 2026-11-01, 652193d, two Opus reviews. All 22 J102 positions compared with
  the DevKit J1 table: 21 match, pin 1 does not (WIRE-01; orchestrator
  re-checked contract and `harness.py`). J101 <-> AFE J1 and J3 <-> J104 maps
  match. No existing test cross-checks the contract against `_DEVKIT_J1`
  (`tests/test_firmware_interlock.py:48-53` checks only pins 20/15/8/9).
