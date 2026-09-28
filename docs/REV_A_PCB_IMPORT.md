# Native PCB import: first board artifact, deliberately unrouted

This advances the existing hardware roadmap's schematic-to-PCB boundary after
merged PR #57. It does not add another electrical model. `make_pcb_seed()` in
`hardware.rev_a` imports the already checked native XML and selected footprint
sources into an editable KiCad board. It is a one-shot import, not an autorouter
or a generator to run over later manual placement work.

## What the board contains

All 68 daughterboard footprints are present: 60 fitted and eight DNP. The logical
off-board ESP32 module is excluded. All 245 physical pads retain their source
net assignments, pin functions and pin types (the schematic's 256 terminals
also include 11 off-board module terminals). Native reference/value, ContractRef,
MPN, BOM_ID, population and tolerance fields are preserved. Native symbol paths
connect the board instances back to the root and child schematic sheets.

The complete library bodies, including pad, fabrication and courtyard geometry,
are copied rather than redrawn from a second package table. The existing graph
and footprint validators reject inconsistent inputs first. The two project-local
T491 definitions selected in #57 are used unchanged. Import accepts exactly the
nine selected definition sources; extra/missing or unreviewed packages fail.
Deterministic UUIDs and a deterministic parking grid make reruns reviewable.

**The grid is not component placement.** There is no chosen outline, mounting
scheme, enclosure, copper plane, track, via or routed connection. Two copper
layers and 1.6 mm thickness are file-initialization defaults, not a manufacturing
stackup decision. This oversized parking arrangement must not be sent to a fab.
Every generated board is titled `UNROUTED IMPORT - NOT FOR FABRICATION`.

## Independent native check

The existing `tools.check --schematic` runs the new native tests. They copy the
actual CAD, export fresh XML with KiCad, read the selected installed/project-local
footprints and import that export. KiCad then loads the resulting board and runs:

```sh
kicad-cli pcb drc --format json --schematic-parity --severity-all \
  --exit-code-violations -o board-drc.json rev_a.kicad_pcb
```

On the canonical import, the native `schematic_parity` array is empty. Separate
copies with a changed reference, missing component or C_REF positive pad assigned
to GND instead of VREFP produce parity findings. These are actual native checks,
not a same-code parser asserting its own output. The ordinary suite independently
checks every imported component's identity, population and pad inventory.

The unrouted canonical board deliberately returns exit 5, not a clean-DRC pass.
The first pinned 9.0.2 run reports 187 unconnected items and three other findings:
no board outline, and two inherited T491 positive-marker texts of height 0.5 mm
below the board default of 0.8 mm. The checker neither suppresses these nor changes
the already reviewed footprint to manufacture a pass. Placement/printing review
must resolve the text sizing before release. Exact finding counts describe this
source/tool revision, not a future acceptance allowance.

This native comparison proves the supported import cases, not every property
that KiCad's parity engine might omit. No zero-parity result establishes routing,
clearance, plane continuity, signal integrity, electrical isolation or safety.
The future routed board requires its own full DRC and placement/electrical review.

## Reproduce and open

Use the pinned environment and ordinary entry point:

```sh
uv sync --locked --all-extras
uv run --locked python -m tools.check --schematic --out reports/pcb-import
```

The canonical native test retains a complete copied project with `rev_a.kicad_pcb`
under `reports/pcb-import/schematic-tests/test_actual_pcb_import_parity_0/cad/`.
That exact path is pytest's current parameterized case name, not a permanent
publication API. Open the retained board in KiCad PCB Editor; its embedded
footprint geometry is editable. The associated copied root/child sheets and local
symbol/passive libraries accompany it. Copy the project to a new working location
before placement. Do not edit a pytest temporary directory and then rerun tests.

The public `make_pcb_seed(netlist_xml, schematic, footprint_sources, profile, bom)`
returns text and performs no file/network writes. `schematic` supplies the root
UUID; the XML supplies native component/sheet paths. It expects the project's
validated source bundle. The native parity test is still required: the function
alone cannot establish that an unrelated schematic text describes the same graph.
There is no automatic overwrite or regeneration command in the design workflow.

The new importer is included in the schematic gate's before/after source snapshot.
Generated boards and DRC/fault results live in its retained native test artifacts,
not among the five existing schematic evidence outputs. The implementation has
no new external dependencies, simulator wrapper, parallel BOM or GPIO registry.

## Scope and next boundary

No netlist fixture, BOM, circuit, firmware, power rail, component selection, model
parameter, package geometry or dependency changed. All purchasing, release,
physical-hardware and body-use approvals remain false. No fabrication outputs
are produced or approved by this import step.

Next: settle the limited outstanding component/interface/mechanical decisions,
choose a stackup and actual outline, then place and route this native board.
Simulation refinements must answer those design decisions rather than postpone
PCB work indefinitely. The remaining acceptance list and estimated substantial
work slices are in `REV_A_COMPLETION_ROADMAP.md`.

Primary tool basis: KiCad 9 CLI documents `pcb drc --schematic-parity`, JSON output
and the violation exit code. The actual executed pin remains KiCad 9.0.2, not a
claim about the newest release:
https://docs.kicad.org/9.0/en/cli/cli.html
https://dev-docs.kicad.org/en/file-formats/sexpr-pcb/
