---
id: design-to-factory
code: FAB
title: Design to factory files
status: partial
stage: before-fab
reviewed_at: 652193d
reviewed_on: 2026-11-01
scope:
  - hardware/rev_a/bom.json
  - hardware/rev_a/kicad
  - hardware/rev_a/layout/rev_a.kicad_pcb
  - hardware/rev_a/auxiliary
  - hardware/rev_a/schematic_bom.py
  - hardware/rev_a/check_schematic.py
  - hardware/rev_a/check_baseline.py
  - docs/quote
  - docs/REV_A_FITTED_PILOT_BUILD.md
  - docs/REV_A_PILOT_QUOTE_PACKET.md
  - tools/check.py
---

# Design to factory files

## Covers

Schematic symbols and nets <-> `bom.json` / AUX contract <-> authored PCBs
(footprints, pads, DNP attributes, copper) <-> fabrication outputs (Gerber,
drill, placement, assembler BOM, fab notes) and the release marking.

## Findings

| ID | Status | Summary | Where (at 652193d) |
|---|---|---|---|
| FAB-01 | open (known) | Five SPI series sites are DNP / NOT_SELECTED (AFE R24; AUX R117-R120), so a board built from current files can't do any SPI transfer. Apply the chosen fit (proposed 33 ohm RC0603FR-0733RL) with the 26 capacitor identities in one coordinated revision; fold WIRE-01 in. Reviews judge Q03 not blocking (same KEMET part/land already active on AUX C101-C115) | `layout/rev_a.kicad_pcb:2803`; `auxiliary/auxiliary.kicad_pcb:17316,17321,17330,17337`; `kicad/digital.kicad_sch:593-604`; `docs/REV_A_FITTED_PILOT_BUILD.md:10,38` |
| FAB-02 | open | Active BOM still lists discontinued GRM219R61A106KE44D and planned-stop GRM188R61E105KA12D (part of FAB-01's migration) | `bom.json:225,294,436` |
| FAB-03 | open | No fabrication outputs exist and nothing generates them: no Gerber/drill/placement/designator BOM, no `kicad-cli` export in `tools/check.py` or CI. Needs a hosted export job (KiCad 9.0.2 is already in CI), a BOM with manufacturer/MPN from `bom.json` + contract, and one page of fab notes (layer order, 1.5 or 1.6 mm, ENIG, finished-hole drills, AUX copper-free strip x20.5-23.5) | `docs/REV_A_PILOT_QUOTE_PACKET.md:116` |
| FAB-04 | open | Both boards print DO-NOT-FABRICATE text, pinned by tests; replace with a release marking at release | `layout/rev_a.kicad_pcb:4,137`; `auxiliary/auxiliary.kicad_pcb:11,14006`; `tests/test_pcb_placement.py:26`; `tests/test_auxiliary_placement.py:20` |
| FAB-05 | suspected | Vias partly overlap fitted 0603 pads (C12.1, C15.1, C15.2, C20.2) by 0.025-0.125 mm; solder-wicking risk. Confirm via fab DFM or specify via tenting/plugging | `layout/rev_a.kicad_pcb` |
| FAB-06 | suspected | 1 uF X5R 0603 (GRM188R61E105KA12D) loses capacitance at 5 V bias on AVDD/VCAP pins; confirm with Murata DC-bias curves (overlaps Q04 disposition) | `bom.json` |
| FAB-07 | open (not critical) | Silkscreen shows almost no reference designators (AFE 1 of 70, AUX 0 of 56); generate an assembly drawing from F.Fab for inspection and rework | both PCBs |

## Not yet covered

- Real KiCad ERC/DRC locally (`kicad-cli` absent; hosted CI only).
- Land patterns against vendor tables / assembler DFM.
- No fiducials: ask the assembler (rails), not a design blocker.

## Log

- 2026-11-01, 652193d, two Opus reviews with sub-reviews. AFE: all 64 ADS
  pins against SBAS499C; TPS7A2033 pinout, footprints, tantalum polarity; 71
  references matched across BOM/schematic/PCB; 252 pad nets; own copper
  connectivity/clearance scan (min track 0.15 mm AFE / 0.20 mm AUX, vias
  0.6/0.3 mm, >= 0.5 mm copper to edge). AUX: schematic/contract/PCB
  agreement; ISO7721, TXU0304, TPS3703, LVC1G97, LVC2G74 pinouts. Confirmed by
  grep that no export exists.
- 2026-11-15: Opus review started at 79d0c9f (first Fable attempt hit the
  usage limit): IC footprint pad vs symbol pin numbering, tantalum/diode
  polarity, land patterns vs manufacturer drawings, design rules vs a
  Russian 4-layer standard class. If no later entry exists, the run was
  lost: re-run it.
