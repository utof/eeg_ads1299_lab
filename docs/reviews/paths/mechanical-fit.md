---
id: mechanical-fit
code: MECH
title: Mechanical fit
status: partial
stage: before-fab
reviewed_at: 79d0c9f
reviewed_on: 2026-11-15
scope:
  - hardware/rev_a/mechanical
  - docs/REV_A_CARRIER_K2.md
  - docs/REV_A_MECHANICAL_ENVELOPE.md
  - tests/test_carrier_cad.py
  - tests/test_carrier_l5.py
---

# Mechanical fit

## Covers

K2 carrier and coded captures, AUX/DevKit/HOST supports, board thickness,
header and ribbon fit, probe access envelopes.

## Findings

| ID | Status | Summary | Where (at 79d0c9f unless noted) |
|---|---|---|---|
| MECH-01 | open (low) | 1.6 mm board bottom is hard-coded; the Russian fab candidate offers 1.5 mm. Review: absorbed (supports are the datum; retainer gap 0.10 -> 0.20 mm, ear margin 0.84 -> 0.74, ribbon-to-saddle 0.24 -> 0.14) | `hardware/rev_a/mechanical/carrier_k2.scad:80-109,188` (at 652193d) |
| MECH-02 | fixed 87f81ef | **IDSD socket with its factory ribbon cannot be loaded into the cartridge.** Pocket loads from the top, but the -X cable window is a closed hole (z=6.1..10.1); wall/ears are solid above it to 14.3. The ribbon leaves the socket 6.2..7.8 mm above its face with 0.1 mm side gap, so during insertion it must pass through solid wall (OpenSCAD intersection 0 at seat, 22 mm3 at 3 mm lift, 98 mm3 at 6). Bottom entry blocked by end ledges. Tests check the seated pose only. Fix: open the window to the top (slot) or split the wall. Quote item A05 asks for this CAD | `carrier_k2.scad:41-48,77`; `docs/REV_A_CARRIER_K2.md:160`; `tests/test_carrier_cad.py:194-205` |
| MECH-03 | open (not critical) | Carrier does not locate the board in Y (0 mm3 at +-20 mm shift) and X play is +-0.5 mm against ~0.2 mm cartridge/socket clearance; at +0.5 mm X the opposite 0.8 mm retainer fingers hold 0.3 mm of edge. Side load on header joints, not a short | `carrier_k2.scad:22-23,41,92-96,155-161` |
| MECH-04 | open (check integrity) | No CAD test derives a dimension from either PCB: header centres, board box, strips, J3 envelope are literals; the link is a whole-file SHA256 fixed by pasting a new hash, and that test is `native`-marked so the ordinary gate never runs it. Literals match the PCB today | `carrier_k2.scad:5-9,84-85,170,176-188`; `tests/test_carrier_cad.py:13,164-165,213-220`; `tools/check.py:74` |
| MECH-05 | suspected (medium) | J1 ribbon may not reach AUX J101: both cartridges force a -X exit, so J1's cable crosses the whole AFE, must fold/arc over the J2 bridge, leaving ~15-35 mm of the 101.6 mm cable to reach J101 and fan out 24 -> 48 mm. No drawing places AUX relative to the carrier. Paper mock-up or combined layout would settle it. The ribbon also ends ~9 mm above U1/input network (analog path) | `carrier_k2.scad:16,28,48,77`; `docs/REV_A_AUXILIARY_PLACEMENT_P1.md:133-136`; J101 at (28,8) in `auxiliary.kicad_pcb` |
| MECH-06 | suspected (low-medium) | J1 receiver and saddle hang on two 1 x 2.5 mm arms; a broken arm puts cable load on the header (strength already declared unqualified) | `carrier_k2.scad:127-131` |
| MECH-07 | suspected (low) | 0.10 mm retainer gap is below typical +-10 % FR4 thickness tolerance (assumed, no fab drawing); a thick 1.6 mm board would be pressed. Doc already says shim | `carrier_k2.scad:155,161` |
| MECH-08 | suspected (low) | Samtec catalog lists IDSD mates as TST/HTST/ZST/EJH, HTSW only under IDSS/IDMS/IDMD; same 0.025 in posts, probably a listing detail. Confirm with Samtec before ordering | https://suddendocs.samtec.com/catalog_english/idsd.pdf |

## Not yet covered

- AUX, DevKit, HOST 5335, J105/J106 mechanics: no CAD or drawing exists
  (bare solder-tail lands plus four 2.7 mm holes at (5,5), (85,5), (5,70),
  (86.5,70)).
- Samtec IDSX drawing AE and HTSW print (exact cable exit height, ribbon
  thickness/width tolerance); JST XH drawing (J3 fit used recalled dims).
- Inner-layer copper under supports, AUX copper near its holes, B2 probe
  access beyond B3.
- Tolerance, print, force and strength analysis.

## Log

- 2026-11-01: MECH-01 from the remaining-work audit, not a path review.
- 2026-11-15, 79d0c9f, one Fable review with ~25 OpenSCAD 2021.01 CGAL
  probes (`pcbnew` absent; PCBs parsed as text). Consistent: AFE outline
  (10,10)-(88,68); J1/J2 grid centres (81.27,38.43)/(16.27,43.43); J3 pin 1
  (75,15) inside its envelope; nearest copper >= 2.0 mm from supports
  (J3 pad 0.65 mm, documented); only J1/J2/J3 exceed the 4 mm blanket;
  keying engages 5 mm before pin contact; B3 access volumes reproduced.
  Orchestrator re-read the cartridge window geometry for MECH-02.
- 2026-11-15, 87f81ef: MECH-02 fixed. Cartridge -X slot now open to the top
  (y=+/-12.8, z=6.1..14.3); the -X cover rivet pair moved from (-4.8,+/-11),
  inside the slot span, to end lugs at (0,+/-15.1) on cartridge and cover.
  New `test_socket_with_factory_ribbon_loads_into_uncovered_cartridge` (both
  ports, continuous vertical hull sweep, cover as blocking control) failed at
  204.28 mm3 on the old solid, passes now; carrier CAD + L5 native suite
  61 passed, service-access native 6 passed, OpenSCAD 2021.01-6build4 (same
  package as CI). Seated geometry unchanged. Not re-reviewed end to end.
