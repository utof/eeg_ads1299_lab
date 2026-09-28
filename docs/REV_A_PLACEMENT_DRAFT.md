# Rev A native placement and ADC-side input routing draft

**2026-09-28.** This is a real editable PCB source at
`hardware/rev_a/layout/rev_a.kicad_pcb`, continuing merged PR #58's checked import.
It is no longer a parking grid. It is **not** a finished PCB, an approved
manufacturing stackup, or permission to power hardware or connect a person.
The schematic under `hardware/rev_a/kicad/` remains the electrical source of truth.

## Concrete changes

The draft puts all 68 on-board parts (60 fitted, eight DNP) inside a provisional
78 x 58 mm rectangular outline. The ADS1299 is central, its four input networks
and dummy-input header are to the left, digital pulldowns and the DevKit header
are to the right, and supply/reference/VCAP parts surround the corresponding
chip edges. The MCU remains off-board. The outline is a **proposed working area**,
not a user-specified enclosure or a fit-checked mounting arrangement. No mounting
holes or new electrical/test-point components are invented.

Four copper layers are enabled. In1 is reserved for a future continuous ground
plane; In2 remains available for later power/routing decisions. The retained
1.6 mm thickness and enabled layers are not a factory-approved dielectric/copper
stackup, impedance calculation, or an implemented return plane. **There are no
zones or planes in this draft.** Neither the source nor the tests claim otherwise.

The eight ADC-side nets `IN1P/N` through `IN4P/N` now connect each ADS pad to its
series resistor, differential capacitor and optional-clamp signal pad. The draft
contains 56 track segments and 16 through vias. The main resistor/capacitor-to-ADC
fanout is front copper; each DNP clamp branch uses a short back-copper crossing
under its series resistor. This is a layout choice needing parasitic/return-path
review, not a claim that those stubs are electrically ideal or that fitting the
clamps is approved. The eight clamps remain DNP.

**The input connector-to-resistor nets are still unrouted.** Power, reference,
VCAP, BIAS, ground and digital interconnects also remain unfinished. There is no
complete powered circuit or external-input acquisition path yet. Net names must
not be confused with a claim that the entire input path or board is complete.

## Preserved electrical and package identity

The draft starts from the actual native PR #58 import. It preserves all 245 pad
numbers, local pad coordinates, copper dimensions/shapes/layers/drills, component
values and MPNs, native reference/ContractRef, native symbol paths, pin functions,
net assignments, population choices and local courtyard geometry. Moving and
rotating components does not renumber their terminals. No BOM, schematic,
firmware, simulation input, component choice or project dependency changed.

Board-instance display text is deliberately edited: references are centered in
F.Fab, the old duplicate reference/value labels are hidden, and the two tantalum
positive silkscreen marks are enlarged from 0.5 to 0.8 mm. The B-case mark is moved
outward to avoid its outline. Pad 1 remains positive. These are board-instance
presentation overrides; the checked library copper/courtyard and library files
are unchanged. Updating the placed footprints from the original library can
reintroduce the small text; rerun the native checks after any such update.
Silkscreen designators and assembly readability are not finalized by this draft.

## Independent native evidence and its limits

The existing `tools.check --schematic` runs four new native cases on copies of
this PCB and the current schematic. KiCad 9.0.2 checks both DRC and schematic
parity, with all severities and no exclusions. On the canonical draft:

- The schematic-parity array is empty.
- The geometry/clearance/courtyard/silkscreen violation array is empty.
- There are **163 unconnected items**, down from the import's 187. None involves
  an ADC-side `IN1P/N` through `IN4P/N` net. This count is a dated observation,
  not an allowed failure budget for fabrication.
- DRC returns **exit 5**, because the remaining unconnected items are real errors.
  It is never reported as a clean whole-board DRC result.

Three separate copies challenge the checks. Overlapping R1 with R2 produces
geometry findings without a schematic mismatch; assigning C1's positive pad to
GND produces schematic/shorting findings; removing an IN1P track produces an
input airwire and a dangling-track finding even though schematic parity stays
empty. Thus an empty parity array cannot hide a broken physical route.

The ordinary missing-board test failed before this file existed. Two additional
software-only faults demonstrated that changing the board or its native test
source during the schematic gate was not originally detected. Both files now
join that gate's before/after input snapshot (47 inputs). The test doubles are
not described as native execution. There is no new production verification
framework or altered numerical/coverage threshold.

## Open and verify without duplicating the schematic

Repository storage keeps the editable board separate from the existing closed
schematic directory. For native GUI work or parity checking, copy the contents of
`hardware/rev_a/kicad/` to a disposable working directory, then copy
`hardware/rev_a/layout/rev_a.kicad_pcb` alongside `rev_a.kicad_sch`. The delivered
native-project ZIP already has that arrangement. Keep the **tracked layout file**
as the authoritative board, copying intentional edits back after review; do not
regenerate the PR #58 parking grid over placement/routing work.

```sh
uv sync --locked --all-extras
uv run --locked python -m tools.check --schematic --out reports/placement-review
```

The tests retain their copied project, JSON DRC and logs in that report's native
test directories. The board is source-hashed, but the main schematic marker still
has its original five output artifacts and does not certify a routed PCB.

## Next design work

Close the pending ceramic part and console/power-loss/interface decisions in
issues #45/#48 before freezing those affected routes. Complete the intended
stackup, ground returns and placement optimization, especially local supply,
reference and VCAP routes. Then route the remaining required nets and resolve
all DRC/parity findings. Mounting, mating clearance, final silkscreen/assembly
views, source-consistent fabrication exports and an actual delivered quote remain
required. No ordering, flashing, power-up or body connection is authorized here.

## Primary design/tool basis

TI ADS1299 SBAS499C, printed pages 72-73, section 12 and Figures 79-80, visually
checked in this continuation: analog/digital separation, return-path attention,
near-pin same-layer bypassing, and differential input capacitors. The provisional
outline, coordinates and routing above are our design choices, not TI dimensions.
https://www.ti.com/lit/ds/symlink/ads1299.pdf

KiCad 9 CLI documentation: native `pcb drc --schematic-parity`, JSON reporting and
violation exit status. The actual execution pin is 9.0.2, not the latest release.
https://docs.kicad.org/9.0/en/cli/cli.html
