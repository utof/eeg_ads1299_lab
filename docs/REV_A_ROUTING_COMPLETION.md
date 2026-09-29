# Connected Rev A routing draft — not a fabrication release

**Checkpoint: 2026-09-29.** This continues the exact ground/power board at local
`37afa0c656769ab0c1cc71465b47de93435436be`. The editable source is still
`hardware/rev_a/layout/rev_a.kicad_pcb`; it was not regenerated from the parking-grid
importer. The full circuit, component placements, values, MPNs, population flags,
pad assignments and previously completed input/reference/VCAP/power copper are
unchanged. Only the status comment, new signal copper and recomputed ground fill
change in the board file.

## Concrete routing milestone

All 35 previously unfinished connections across 25 nets are now routed:

- The eight `CH1..4P/N_DUMMY` connections run from J2 to their series resistors.
  The existing ADC-side differential filter routes remain intact. This makes
  physical connections, not permission to attach a source or a person.
- SCLK, MOSI, MISO, CS, DRDY, RESET, START, PWDN and CLKSEL reach the existing
  digital header and/or their required pull resistors. CLK and GPIO1..4 reach
  their unchanged pulldowns. No MCU GPIO, pull value or startup policy changed.
- BIASINV and BIASOUT connect the existing local feedback network; the separate
  1 MOhm output resistor leads to the dummy connector. Firmware BIAS remains off.
  Routing the feedback does not qualify its real-board stability or body use.

There are **579 segments, 126 vias and one filled In1.Cu GND zone**. The increment
adds 280 segments and 23 vias. All 68 footprints and 245 pads remain. New digital
routes use 0.15 mm copper, including explicitly planned pin escapes; the new
input/BIAS routes use 0.20 mm. Added vias retain the existing 0.60/0.30 mm
pad/drill dimensions. No signals were added on In1.Cu. Four enabled copper layers
and the provisional 78 x 58 mm outline remain; these are not a vendor-approved
stackup or final mechanical design.

The narrow digital escapes were planned together so routing one pin could not
box in its neighbor. The same-net drill-spacing problem found in an intermediate
attempt was corrected in the copper, not by suppressing a rule. Earlier candidate
DRCs and authoring diagnostics remain separate from the final result.

## What the native result establishes

After an actual KiCad 9.0.2 zone refill, the complete board produces:

| Native result | Prior ground/power board | Connected draft |
|---|---:|---:|
| Schematic parity findings | 0 | 0 |
| Other DRC findings | 0 | 0 |
| Unconnected items | 35 | 0 |
| DRC process exit | 5 | 0 |

The source GND outline/settings are unchanged. The native fill still has one
connected region and all ground pads remain connected. Native DRC establishes
only the checks implemented by KiCad under the current project rules. It does
not prove RF/return impedance, analog noise, component derating, powered-off
behavior, solderability, or suitability of the actual fabricator's process.

The checker now requires the process status to agree with its fresh native
report: **exit 0 only with no findings, exit 5 with findings**. Other exits fail.
Five software-only controls reject contradictory exit/report pairs. The older
import-stage parking-grid test still correctly expects unconnected routing and
exit 5; it must not be confused with the authored board's zero-findings result.
No exclusions, severity settings, clearance rules or native tolerances changed.

## Test-first and destructive checks

Before adding copper, 26 new native assertions failed on the unchanged 35-airwire
board: one for each unfinished signal net and one for complete routing. The
failing-test commit is retained independently of implementation.

After routing, 25 separately edited copies each lose one exposed track on a
newly completed net. Every copy is refilled and checked by the native engine;
the named net must become disconnected while schematic parity stays unchanged.
The existing power, input, reference and eight capacitor-return cut tests remain
active. A correct schematic can coexist with a physically broken connection.
Track UUIDs in the tests identify destructive probe locations, not a second
source of electrical connectivity or a manufacturing rule.

The unchanged canonical native report is reused within each test module; mutated
boards are independent. Counts of parameterized tests are not counts of separate
physical measurements. Software process doubles are not native execution.

The routes were authored with temporary geometry-assisted planning from the
actual footprint/copper geometry and then checked in native KiCad. Those local
planning scripts are retained as evidence only, not a new project dependency,
autorouter framework or generator that should overwrite future layout edits.
`tools.check` remains the existing verification entry point:

```sh
uv run --locked python -m tools.check --native --schematic
```

## Still open before manufacturing

This is the first completely connected routing candidate, not the final layout
review. In particular:

- Input paths are not length/parasite balanced or impedance qualified. Recorded
  new copper lengths differ between some P/N paths; do not add arbitrary matching
  meanders merely to create equal-looking numbers. Review symmetry, routing
  layers and coupling against the intended analog/dummy setup.
- Digital fanout, return transitions and the existing AVDD1 bypass loop need an
  independent electrical placement/return-path review. A connected GND polygon
  does not establish that every high-frequency return has a good path.
- Final stackup, mounting, enclosure/connector clearance, test access, current
  component/lifecycle/assembly decisions, and actual console/power-loss behavior
  remain unresolved in the existing roadmap/issues. No obsolete part was silently
  replaced, and no protective circuit was inferred from a 0-error DRC.
- The actual published full source needs independent review and current-head
  hosted checks. The historical importer PR's approval does not approve this
  later local board. Manufacturing exports/quote and staged no-person bring-up
  come after those decisions, not automatically after zero airwires.

No BOM, schematic, firmware, simulation inputs, dependencies, purchasing,
hardware-release or body-connection approval changed. Keep the visible bench-only
and do-not-fabricate markings until a separately reviewed release decision.
