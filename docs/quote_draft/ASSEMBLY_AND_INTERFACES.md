# Assembly scope and interfaces — QUOTATION ONLY

Read `REQUEST.md` first. Baseline `399677407a159ad10c766b4575b65aabc8bd3057`.
The following is a cost/DFM specification, not a released assembly or power-up
instruction. Embedded native PCB lands and current contracts take precedence
for inspection; explicitly proposed capacitor identities are pricing alternatives.

## Boards and exact source paths

| Board | Native paths below `hardware/rev_a/` | Quantity per set / construction |
|---|---|---|
| AFE | `layout/rev_a.kicad_pcb`; `kicad/rev_a.kicad_pro` and root/power/digital sheets; `kicad/RevA_Passives.pretty` | 1; 78 x 58 mm, four layers, 1.6 mm nominal; no added PCB mounting holes |
| AUX | `auxiliary/auxiliary.kicad_pro`, PCB, root/bus/supervision/arming sheets, `.kicad_dru`, `Aux_Lands.pretty` | 1; 90 x 75 mm, four layers, 1.6 mm nominal; four 2.7 mm NPTH mounting holes |

Use KiCad 9.0.2 for the retained project. AFE's authored PCB is in `layout/`, not
beside the schematic project; open that file explicitly. Do not run the parking-
grid importer, update the PCB from the schematic or regenerate footprints to
create a new candidate. All electronic component lands are on F.Cu. Both boards
also contain inner-layer routes: In2 is NOT a continuous ground/power plane.
AFE's In1 has one GND region. AUX's In1 has separate HOST_GND/TARGET_GND regions.
Keep the AUX x=20.5..23.5 mm all-layer no-copper strip and 3 mm domain-separation
rule intact. This is not certified mains/medical insulation. Inspect edge/annulus
and solder-side clearances in the actual files, not screenshots.

AUX H4 is deliberately offset after cable-access review: use all four actual CAD
coordinates. The 0.5 mm planned mounting/access gap is not a tolerance guarantee.
Do not add AFE mounting holes or let fasteners/shields/support metal join domains.

## Electrical purchasing boundaries

The CSV has 34 grouped rows. Buy/fit 61 AFE and 43 AUX parts per set, not the count
of all footprints. Eight AFE BAV199 sites are DNP; keep empty pads in the design.
AUX J101/J102/J103/J105/J106 are PCB solder-wire lands, not orderable connectors.
They need termination labor and insulation, not five generic headers. J104 IS an
orderable XH header. MOD1 is one external commercial DevKit, not a PCB-mounted
part. Its module, regulator, LEDs and USB bridge are included in that module,
not extra BOM lines. The external console board is separately listed below;
AUX U101 already includes ISO7721DR, so do not buy a second isolator board.

## Accessories and assemblies not covered by the board-fit quantities

| ID | Per-set quotation scope | Defined identity / remaining detail |
|---|---|---|
| A1 | 1 external controller | ESP32-S3-DevKitC-1-N8R8, already costed as CSV MOD1; record actual PCB revision, prefer official v1.1. Price owner-supplied alternative separately, not as a duplicate |
| A2 | 1 host console module | Adafruit CP2102N Friend, product 5335; host-side USB data cable of actual matching type/length is a separate item; inspect revision before termination |
| A3 | 2 single-ended 20-contact ribbon assemblies | Samtec IDSD-10-S-04.00-T-G-ST4; two differently coded K2 cartridges, one AFE J1 and one J2. Nominal 101.6 +/-3.175 mm; ST4 nominal 6.35 mm stripped/tinned tails, not insulated plugs. Confirm configured supply and free-end termination process |
| A4 | 1 C4 service harness | 2 XHP-6 housings, 10 SXH-001T-P0.6 contacts (NOT the N suffix), five AWG24 conductors, insulation OD 0.9-1.9 mm, 150 +/-5 mm between housing wire faces. These are cable parts; both B6B headers are already in the board BOM |
| A5 | 1 controller fanout lead set | Captive numbered wires from AUX J102 to selected DevKit J1 tail pads; lead grade/length and independent restraint to be proposed and recorded, no loose unkeyed adapter substituted |
| A6 | 1 console lead set | Four separately identified host-domain conductors to AUX J103; include insulation and independent strain relief |
| A7 | 1 source lead pair | To AUX J105; regulated 5 V source class with output-enable/current limiting, actual instrument and lead model TBD. Include outgoing AND return interfaces; no powered test settings selected |
| A8 | 1 STOP contact assembly | Normally-open dry contact and two target-domain leads to AUX J106; exact switch, location and wire/retention proposal required. Not a qualified emergency-stop channel |
| A9 | 1 K2/C4 AFE carrier set | Base, J1/J2 coded bridges, two cartridge bodies, two covers, four edge clips and two cable bars per existing SCAD. Include C4 backing blocks integral to the current carrier |
| A10 | 1 fixture/fastener kit | K2 fasteners/nonconductive captive rivets/liners/shims plus independently supported AUX and DevKit; actual material, hardware and mounting design still to be accepted |
| A11 | 1 passive analog-startup fixture | Separate cost/proposal for holding used analog inputs low before reviewed startup. J2 cable alone is not this fixture; E1 external stimulus/calibration apparatus is later scope, quote separately |
| A12 | Shared bench equipment and consumables | Supply, meter/current measurement and later scope/probes/calibrated dummy equipment; list borrowed/owned versus new cash costs. These are not automatically multiplied by board quantity |

## Termination requirements for quotation and traceable assembly review

- **Digital AFE J1 to AUX J101:** K1 identified contact n to landing n, all 20
  contacts preserved; ten individual even-numbered returns. Active signals are
  buffered on AUX; older direct MCU wiring prose is superseded by the actual
  auxiliary contract. Do not short extra conductors together at a cable end.
- **AUX J102 to DevKit J1:** numbered landing n to the corresponding header-tail
  identity n for every connected pin in `auxiliary/contract.json`. Leave native
  NC positions unconnected and guarded. These are physical header positions,
  not GPIO numbers. No ten-wire bundle into one DevKit solder pad.
- **AUX J103 / Adafruit 5335:** pin 1 HOST_3V3 to JP4.2, pin 2 HOST_GND to
  JP1.1, pin 3 HOST_TX to JP1.4 (TXD), pin 4 HOST_RX to JP1.5 (RXD).
  JP1.3 USB 5 V is NOT the 3.3 V connection. Check actual supplied labels/revision.
- **C4 J3 to J104:** 1->1 return, 2->2 AFE DVDD feed OUT, 3->3 separate DVDD
  sense, 4->4 AVDD sense after R11, 5->5 return; cavity 6 empty at both ends.
  Feed/sense join only on the AFE, not in the cable or auxiliary. Detached cable
  continuity/short inspection must precede assembled continuity, because the
  board intentionally joins some rails and could hide a swap.
- **AFE J2 dummy cable:** contacts 1-8 are the four P/N inputs, 9 is disabled
  BIAS-after-1M, 10 is return, 11-20 NC. Insulate BIAS/unused tails individually;
  no connection to a person, powered source or controller. Startup fixture is
  a separate unresolved requirement, not an implicit short of every contact.
- **AUX J105:** 1 TARGET_VIN5, 2 TARGET_GND. **J106:** 1 STOP_N, 2 TARGET_GND;
  a normally-open contact closes these only in its intended STOP operation.
  Verify the exact nets against the frozen native contract before releasing wiring.

Both DevKit USB connections remain excluded with accessories attached. The
separately powered console's HOST and TARGET sides must not be tied by a shield,
bench instrument or supply jumper. Remove power before every mate/unmate; no
power-loss behavior or safety rating follows from physical keying.

## Mechanical reference, not a released print

Open `hardware/rev_a/mechanical/view_k2.scad` with OpenSCAD 2021.01 and the adjacent
`carrier_k2.scad`. The assembly includes illustrative hardware envelopes, not one
printable object. Quote named pieces, never print the entire assembly mesh.
The maximum bulk-capacitor body is 1.35 mm, maximum KEMET family allowance 0.95 mm;
mounted height adds solder. K2's 4 mm component allocation is NOT measured clearance.
Preserve full socket seating, captive port-specific keys, removable bridges,
separate cable bars and C4 support; no load carried only by PCB solder joints.
Fasteners/rivets/liners, socket width, print tolerance, cable bends, clamp/pull
forces and actual fit remain open. No redesign is requested absent a concrete
DFM conflict. Quote feasibility/change proposals separately from accepted work.

## Applicable existing decisions (frozen baseline paths)

`docs/REV_A_STACKUP_BENCH_REQUIREMENTS.md`, `REV_A_AUXILIARY_PLACEMENT_P1.md`,
`REV_A_AUXILIARY_ROUTING_P3.md`, `REV_A_P3_CLOCK_REVIEW.md`,
`REV_A_CONNECTOR_K1.md`, `REV_A_CONTROLLER_INTERFACE_C1.md`, `REV_A_SERVICE_C4.md`,
`REV_A_CARRIER_K2.md`, `REV_A_PILOT_CAPACITOR_DISPOSITION.md`,
`REV_A_100NF_REUSE_DECISION.md`, and `hardware/rev_a/service_c4.json`.
Earlier documents describe historical missing stages: the current native design,
contracts and present handoff control what is already implemented. Do not repeat
old placement/routing/handshake tasks just because a dated document says pending.
