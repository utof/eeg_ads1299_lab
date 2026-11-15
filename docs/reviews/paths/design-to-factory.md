---
id: design-to-factory
code: FAB
title: Design to factory files
status: partial
stage: before-fab
reviewed_at: 79d0c9f
reviewed_on: 2026-11-15
scope:
  - hardware/rev_a/bom.json
  - hardware/rev_a/sources.json
  - hardware/rev_a/kicad
  - hardware/rev_a/layout/rev_a.kicad_pcb
  - hardware/rev_a/auxiliary
  - hardware/rev_a/schematic_bom.py
  - hardware/rev_a/check_schematic.py
  - hardware/rev_a/check_baseline.py
  - hardware/rev_a/auxiliary.py
  - tests/fixtures/rev_a_bom.csv
  - tests/fixtures/rev_a_netlist.xml.gz
  - tests/fixtures/auxiliary_c3_netlist.xml.gz
  - docs/HARDWARE_BASELINE_REV_A.md
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
| FAB-01 | fixed 33ef3fa | Five SPI series sites are DNP / NOT_SELECTED (AFE R24; AUX R117-R120), so a board built from current files can't do any SPI transfer. Apply the chosen fit (proposed 33 ohm RC0603FR-0733RL) with the 26 capacitor identities in one coordinated revision; fold WIRE-01 in. Reviews judge Q03 not blocking (same KEMET part/land already active on AUX C101-C115) | `layout/rev_a.kicad_pcb:2803`; `auxiliary/auxiliary.kicad_pcb:17316,17321,17330,17337`; `kicad/digital.kicad_sch:593-604`; `docs/REV_A_FITTED_PILOT_BUILD.md:10,38` |
| FAB-02 | fixed 33ef3fa | Active BOM still lists discontinued GRM219R61A106KE44D and planned-stop GRM188R61E105KA12D (part of FAB-01's migration) | `bom.json:225,294,436` |
| FAB-03 | open | No fabrication outputs exist and nothing generates them: no Gerber/drill/placement/designator BOM, no `kicad-cli` export in `tools/check.py` or CI. Needs a hosted export job (KiCad 9.0.2 is already in CI), a BOM with manufacturer/MPN from `bom.json` + contract, and one page of fab notes (layer order, 1.5 or 1.6 mm, ENIG, finished-hole drills, AUX copper-free strip x20.5-23.5) | `docs/REV_A_PILOT_QUOTE_PACKET.md:116` |
| FAB-04 | open | Both boards print DO-NOT-FABRICATE text, pinned by tests; replace with a release marking at release | `layout/rev_a.kicad_pcb:4,137`; `auxiliary/auxiliary.kicad_pcb:11,14006`; `tests/test_pcb_placement.py:26`; `tests/test_auxiliary_placement.py:20` |
| FAB-05 | suspected | Vias partly overlap fitted 0603 pads (C12.1, C15.1, C15.2, C20.2) by 0.025-0.125 mm; solder-wicking risk. Confirm via fab DFM or specify via tenting/plugging | `layout/rev_a.kicad_pcb` |
| FAB-06 | suspected | 1 uF X5R 0603 (GRM188R61E105KA12D) loses capacitance at 5 V bias on AVDD/VCAP pins; confirm with Murata DC-bias curves (overlaps Q04 disposition) | `bom.json` |
| FAB-07 | open (not critical) | Silkscreen shows almost no reference designators (AFE 1 of 70, AUX 0 of 56); generate an assembly drawing from F.Fab for inspection and rework | both PCBs |
| FAB-08 | open (fold into FAB-03) | Export/fab notes must keep or refill the In1 GND fills (GND on both boards is carried by them; without the AFE fill GND splits into 55 islands) and state finished hole sizes (vias 0.3 mm, JST 0.95 mm) | both PCBs, In1 zones (at 79d0c9f) |
| FAB-09 | open (low) | U111 (SN74LVC2G74 DCU) pads are 0.15 mm apart with no mask expansion, leaving a 0.15 mm mask web a fab may drop: solder-bridge risk, not a dead board. Ask the fab or note it | `auxiliary/auxiliary.kicad_dru` U111 rule (at 79d0c9f) |

## Not yet covered

- Real KiCad ERC/DRC locally (`kicad-cli` absent; hosted CI only), incl.
  courtyard overlap; stencil/paste design; current capacity.
- TI's own recommended lands for TQFP-64 PAG, SOT-23-5 DBV, WSON-6 DSE,
  VSSOP-8 DCU (KiCad IPC-7351 library lands used); KEMET primary B-case
  table; Murata 0603/0805 table; Samtec HTSW print.
- Current Rezonit/Elektrokonnekt rule pages (Rezonit page 404; compared with
  general 4-layer standard class).
- No fiducials: ask the assembler (rails), not a design blocker.

## Log

- 2026-11-01, 652193d, two Opus reviews with sub-reviews. AFE: all 64 ADS
  pins against SBAS499C; TPS7A2033 pinout, footprints, tantalum polarity; 71
  references matched across BOM/schematic/PCB; 252 pad nets; own copper
  connectivity/clearance scan (min track 0.15 mm AFE / 0.20 mm AUX, vias
  0.6/0.3 mm, >= 0.5 mm copper to edge). AUX: schematic/contract/PCB
  agreement; ISO7721, TXU0304, TPS3703, LVC1G97, LVC2G74 pinouts. Confirmed by
  grep that no export exists.
- 2026-11-15, 79d0c9f, one Opus review (no hardware change since 652193d).
  No new critical defect. Pad = datasheet pin = symbol pin for U1 ADS1299-4
  (pin 1 top-left, CCW; spot-checked supplies/VCAP/GPIO/DOUT/DRDY), U2
  TPS7A2033, U105-U108 TPS3703 DSE, U109/U110 SN74LVC1G97 (logic correct,
  names swapped: WIRE-04), U111 SN74LVC2G74, D1-D8 BAV199 (DNP). C6 T491D and
  C7 T491B: pad 1 = "+" in footprint and symbol, on VCAP1/VREFP. T491D land
  matches KEMET density-B; JST XH 0.95 mm hole within spec. Own rule scan:
  tracks 0.15 AFE / 0.20 AUX, spacing 0.20 (0.15 at U111 by DRU rule), vias
  0.6/0.3, hole-to-hole >= 0.3, copper-to-edge >= 0.5, outlines closed, all
  SMD pads have paste and mask, committed fills short no nets and connect
  all. ti.com unreachable: TI facts from mirrors/search extracts.
- 2026-11-15, f4c4294, fixes (not a re-review; path now stale until re-read).
  FAB-01/FAB-02 `33ef3fa`: R24 and AUX R117-R120 fitted with 33 ohm
  RC0603FR-0733RL; C8-C22 -> GRM188R61C105KA12D, C23-C29 -> C0603C104K5RACTU,
  C30-C33 -> GRM21BR61C106KE15L in `bom.json`, AFE sheets and PCB properties,
  AUX contract/sheet/PCB (Value/MPN/Population/native DNP only; lands, nets and
  copper unchanged, word-diff checked). Validators now require these identities
  (`check_baseline.py`, `auxiliary.py`); `tests/test_fitted_pilot_population.py`
  failed first, then confirms 62/47/109 fitted, 8 DNP clamps, 48 capacitors.
  Native fixtures re-exported (ERC 0 on all sheets; only those 31 part records
  differ). FAB-04 markings kept (release item). FAB-06 now concerns the 16 V
  GRM188R61C105KA12D (same Q04 conditions), still suspected. FAB-08: the AUX In1
  fill was refilled with pcbnew 9.0.2 and spliced (HOST_GND fill reproduced
  byte-identically); export notes are still FAB-03. Frozen Q1 packet untouched.
