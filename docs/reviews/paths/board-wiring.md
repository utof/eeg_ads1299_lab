---
id: board-wiring
code: WIRE
title: Board-to-board wiring
status: partial
stage: before-fab
reviewed_at: 79d0c9f
reviewed_on: 2026-11-15
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
| WIRE-03 | open (low) | Solder-tail lands have no silk numbering or polarity; J105.1 = TARGET_VIN5 with no reverse-polarity part, so swapped J105 tails put reversed 5 V on DevKit and AFE. Add silk "+5V / GND" on J105 and pin numbers on J102 when WIRE-01 touches the board | `auxiliary/Aux_Lands.pretty/SolderTails_*.kicad_mod`; J105 at `auxiliary/auxiliary.kicad_pcb:13763` (at 79d0c9f) |
| WIRE-04 | open (cosmetic) | SN74LVC1G97 symbol pin names swapped: pin 1 named IN0, pin 3 IN1; TI SCES416N has In1 = pin 1, In0 = pin 3. Wiring by pin number matches TI Fig. 4 AND gate, so CLR_N/ARM_CLK behave as intended; only labels (symbol and contract) are wrong | `auxiliary/RevA.kicad_sym:59,61`; `auxiliary/arming.kicad_sch:27,29`; `auxiliary/contract.json:848,891` (at 79d0c9f) |

## Not yet covered

- Samtec IDSD-10-S-04.00-T-G-ST4: conductor n to socket position n assumed
  from IDC convention, not read from the Samtec print (continuity check
  already required by `docs/REV_A_CONNECTOR_K1.md`).
- ISO7721/TXU0304 checked against mirrored TI PDFs (ISO772x-Q1; TXU0304
  original SCES935), not current ti.com revisions (ti.com unreachable).
- `auxiliary.kicad_sch` and `digital.kicad_sch` not compared line by line
  (PCB pads, contract and symbols were).
- Physical: real DevKit pin-1 end, JST XH footprint vs JST drawing, crimp,
  strain relief, keying.

## Log

- 2026-11-01, 652193d, two Opus reviews. All 22 J102 positions compared with
  the DevKit J1 table: 21 match, pin 1 does not (WIRE-01; orchestrator
  re-checked contract and `harness.py`). J101 <-> AFE J1 and J3 <-> J104 maps
  match. No existing test cross-checks the contract against `_DEVKIT_J1`
  (`tests/test_firmware_interlock.py:48-53` checks only pins 20/15/8/9).
- 2026-11-15, 79d0c9f, one Fable review. No new critical defect. WIRE-01
  re-confirmed against Espressif's V1.1 schematic (J1.1/J1.2 = ESP_3V3);
  all other J102 pads match. Design uses J1 only; firmware GPIOs 4-18 avoid
  strapping/USB/PSRAM pins. AFE J1 <-> J101 (20 positions), J3 <-> J104 and
  C4 match; J103 <-> Adafruit 5335 matches its EAGLE schematic (TXD/RXD
  directions correct, USB 5 V unused, HOST_GND separate). ISO7721 and
  TXU0304 pinouts, channel directions and OE default-off (R109) match.
  J105/J106 maps consistent. Unkeyed K1 reversal (pin n -> 21-n) already
  handled by `docs/REV_A_CONNECTOR_K1.md`. Orchestrator spot-checked
  WIRE-04 symbol names.
