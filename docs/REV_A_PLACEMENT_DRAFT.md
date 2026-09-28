# Rev A placement, input and reference/VCAP routing draft

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
series resistor, differential capacitor and optional-clamp signal pad. The first input-only draft
contained 56 track segments and 16 through vias. The current draft contains
140 track segments and 36 through vias after the reference/VCAP continuation below. The main resistor/capacitor-to-ADC
fanout is front copper; each DNP clamp branch uses a short back-copper crossing
under its series resistor. This is a layout choice needing parasitic/return-path
review, not a claim that those stubs are electrically ideal or that fitting the
clamps is approved. The eight clamps remain DNP.

**The input connector-to-resistor nets are still unrouted.** Main power, BIAS,
board-wide ground and digital interconnects remain unfinished. VREFP and VCAP1-4
now have complete positive-side copper and the local returns described below;
that does not make the whole power or ground system complete. There is no
complete powered circuit or external-input acquisition path yet.

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

## Initial input-routing evidence (before the reference/VCAP continuation)

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

## Reference and VCAP routing continuation — 28 September 2026

This slice completes five previously unrouted positive-side nets: VREFP and
VCAP1, VCAP2, VCAP3 and VCAP4. All of their copper stays on F.Cu without a via
between the chip and capacitor. The already selected capacitor values and
reference/VCAP pin assignments are unchanged. The existing ADC-side input tracks
and vias are preserved byte-for-byte.

Eight capacitor negative terminals now have short front-copper spokes to ground
vias and an explicit In1.Cu return-trace network joining the chip's GND pins.
This includes VREFN (pin 25), the AVSS pins and the existing DGND/unused-input
returns. **This is routed copper, not a filled ground plane.** Board-wide ground
is still unfinished; these local paths must not be represented as an operational
or low-impedance-qualified return system. The return vias and inner traces are
explicitly part of the provisional routing, not proof of compliance with TI's
same-layer/no-via bypass guidance for a complete current loop. Final continuous
plane fill and loop/return-impedance review remain required before release.

The two placement edits affect only previously unrouted components. C24, the
100 nF VCAP3 bypass, moves from (48, 21.8) to (51.5, 28.65) mm at 90 degrees,
beside C9. C10, the VCAP4 1 uF capacitor, moves from (49.6, 45.35) to
(49.8, 46) mm at 270 degrees to clear the pin escape. No footprint library,
local pad or courtyard geometry, symbol link, population, MPN, value or net
assignment changes. The board outline, four enabled copper layers, layer-stack
limitations and original DNP clamp/input route qualifications remain unchanged.

The first copper candidate failed actual KiCad checks: premature diagonal
fanout crossed neighboring pad clearances, a ground via crowded a VCAP trace,
and acute inner-return branches produced sliver findings. The route geometry
and two placements were corrected; no clearance setting, rule, error severity
or exclusion was changed to obtain a pass. These failure logs are retained.

On the corrected draft KiCad 9.0.2 reports:

| Native DRC result | Input-only draft | Reference/VCAP draft |
|---|---:|---:|
| Schematic parity findings | 0 | 0 |
| Other violations (clearance, shorts, courtyard, mask, silkscreen, etc.) | 0 | 0 |
| Unconnected items | 163 | 134 |

Both boards return exit 5 because of genuine unfinished connections. The count
is an observation, not a routing-completion percentage or fabrication allowance.
No remaining airwire is on an ADC-side input, VREFP or VCAP1-4 net. AVDD, DVDD,
VIN, digital, BIAS and other ground/input-connector routes still need work.

Five native missing-connection tests failed on the untouched input-only board
before routing, while its prior placement checks passed. Thirteen additional
fault controls challenge the completed result: deleting one positive trace from
each of the five sensitive nets creates the corresponding native airwire;
deleting each of the eight capacitor return spokes adds a GND airwire at that
negative terminal even though its positive net stays complete. All preserve
schematic parity, demonstrating why parity alone cannot prove routed connectivity.
These are finite physical-route fault probes, not an exhaustive mutation score.
The existing board/test source snapshots and orchestration are reused; no new
production Python module, runtime dependency or model is introduced.

The source patch and openable project are local design deliverables pending
publication, independent review and hosted checks. A prior import review cannot
be reused as approval of these new tracks. Purchasing, hardware-release and
body-connection gates remain false.

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
stackup, continuous ground returns and placement optimization, especially the
remaining AVDD/DVDD supply routes. Review local reference/VCAP loop impedance
with the final plane fill; the current routed ground network is not that plane. Then route the remaining required nets and resolve
all DRC/parity findings. Mounting, mating clearance, final silkscreen/assembly
views, source-consistent fabrication exports and an actual delivered quote remain
required. No ordering, flashing, power-up or body connection is authorized here.

## Primary design/tool basis

TI ADS1299 SBAS499C, printed page 7 pin table and page 72 section 12/Figure 79,
visually checked for the reference/VCAP continuation: analog/digital separation, return-path attention,
near-pin same-layer bypassing, and differential input capacitors. The provisional
outline, coordinates and routing above are our design choices, not TI dimensions.
https://www.ti.com/lit/ds/symlink/ads1299.pdf

KiCad 9 CLI documentation: native `pcb drc --schematic-parity`, JSON reporting and
violation exit status. The actual execution pin is 9.0.2, not the latest release.
https://docs.kicad.org/9.0/en/cli/cli.html

### Recovered source-gate fault correction

The full local gate also exposed a pre-existing software-test issue: its generic
`rglob` selection could modify an unused installed shadow of a project-local
T491 footprint instead of a consumed input. The old expected-failure case then
correctly did not invalidate a snapshot of unchanged inputs. The test now chooses
the exact installed QFP file and has a separate project-local T491 fault case.
Both failures were observed before correction; all gate-double cases pass after
it. No production source boundary, error tolerance, DRC rule or approval was
relaxed. Filesystem iteration order is no longer mistaken for dependency identity.
