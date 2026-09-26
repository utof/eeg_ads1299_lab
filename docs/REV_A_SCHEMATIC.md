# Rev A native schematic: review candidate, not a released board

The editable source is `hardware/rev_a/kicad/rev_a.kicad_sch` with two child
sheets, `power.kicad_sch` and `digital.kicad_sch`. Open that root in KiCad.
`RevA.kicad_sym` is the project-local, three-unit ADS1299-4 symbol and small
support library. No generator, SKiDL, KiBot, IPC service or new Python dependency
is needed to edit or check the circuit. All 64 ADS package pins are explicit.

## Scope and decisions

The three sheets contain 69 BOM component instances, including the off-board
ESP32-S3 devkit and eight DNP diode packages. There are 68 daughterboard
footprints, of which 60 are fitted in this candidate. U1's three drawn units are
one physical ADS1299-4. The controller is explicitly excluded from the PCB and
has logical GPIO identifiers, **not** a mechanically validated devkit footprint
or physical header-pad map. Its 5 V and ground show the intended external bench
harness; simultaneous USB power remains prohibited.

The selected part families and firmware are unchanged. The one scoped BOM
correction removes `R_DAISY_DN`: TI's unused-input rule calls for DAISY_IN pad 41
to connect directly to DGND. CLK pad 37 retains its own 10 kOhm pulldown. Unused
SRB1/SRB2 are explicitly NC, one of the alternatives permitted by the datasheet;
no ERC pin-conflict suppression is used to justify grounding bidirectional pins.
BIASIN/BIASREF return to ground, while the existing local 1 MOhm || 1.5 nF BIAS
feedback and separate 1 MOhm dummy-output resistor remain. BIAS stays disabled.

The 100 uF VCAP1 and 22 uF reference capacitors retain their selected tantalum
packages and explicit positive pad 1. **VREFP does not connect to DVDD**: its
capacitors return to VREFN/AVSS. The differential 4.7 nF input capacitors bridge
the two post-resistor ADC inputs, not ground. DNP BAV199 pin 1 is the lower-rail
anode, pin 2 the upper-rail cathode and pin 3 the input junction. DNP footprints
are not qualified protection. The TPS7A2033PDBVR uses the DBV pinout, with EN tied
to IN and NC pad 4 left unconnected; this regulator supplies only ADS DVDD.

Native reference designators are conventional R1/C1/etc. Each component carries
a `ContractRef` field that preserves the existing functional BOM reference, such
as `R_CLK_DN`. The checker requires a bijection, matching quantities, MPN, value,
tolerance, footprint, and independent native DNP/on-board flags. This adapter is
not a second BOM. The retained CSV includes both reference names.

## Reproduce the native check

The Linux reference environment pins KiCad **9.0.2**, Debian package
`9.0.2+dfsg-1`, and footprint/symbol packages `9.0.2-1`. This is the tested
reproducibility pin, not a claim that it is the newest KiCad release. The exact
container and Actions revisions are in `.github/workflows/schematic.yml`.

```sh
uv sync --locked --all-extras
uv run --locked python -m tools.check --schematic --out reports/schematic
```

`KICAD9_FOOTPRINT_DIR` may select the installed pinned footprint directory; the
Linux default is `/usr/share/kicad/footprints`. The same gate runs in CI, checking
out the explicit PR head. It first runs the ordinary checks, then requires the
actual CLI, full-severity ERC JSON, a fresh KiCad XML netlist, project connectivity
checks, PDF/CSV exports, CSV-to-XML inventory validation and the native CAD
regression tests. Native commands pin `LC_ALL=C` and `LANG=C` so exported flag
labels do not depend on the operator's desktop language. A version string
alone is never execution evidence. Each run has a fresh output directory and an
isolated `KICAD_CONFIG_HOME`. Missing tools/artifacts, failed loads, violations,
partial reports, regression failures or changed input hashes fail the request.

The success marker is invalidated before even the ordinary checks.
`SCHEMATIC_CHECK.json` records commit, dirty-worktree status, all declared native
files, selected installed footprint files, checker/baseline hashes, artifact
hashes and counts. A dirty local run is not represented as exact-commit evidence.
The file inventory is deliberately closed: adding a child sheet or external
symbol library requires updating and reviewing the dependency contract. Library
names must match their own URIs, not merely an independent allowed set. No ERC
exclusions or severity overrides are accepted in this candidate.

## Tests and their limits

Ordinary tests use a compressed, frozen native XML export solely as a fixture.
The native suite regenerates the graph and compares it to that fixture. It also
exports six deliberately broken native source variants and checks rejection.
Wrong resistor values and fitted optional clamps still pass general ERC, but
fail the project-specific checker. An all-sheet net rename remains acceptable.

The graph fault sweep moves each of 256 terminals to every other existing net:
14,592 rejected changes. It also rejects all missing components/terminals and
polarized-capacitor reversals, while accepting 54 nonpolar passive reversals and
net renaming. These are finite connectivity-fault tests, **not** a claim of
exhaustive electrical fault coverage or a code-mutation score. Source/report
fault fixtures challenge missing caches/libraries, external/nested dependencies,
symlinks, FIFO/oversize inputs, malformed XML, stale success markers and partial
or suppressed ERC reports. Process doubles never count as native CAD evidence.

The checker encodes the selected topology with independent datasheet pad numbers;
it does not infer correctness from net-label spelling or a reference board's
unreviewed drawing. Its closed component/pin inventory makes unintended extra
connections and apparently plausible wrong rails visible before layout.

## Review corrections: BOM export and symbol-cache agreement

A clean graph is not enough to approve its accompanying review artifacts. The
first independent review found two gaps, reproduced before correction:

- A component marked `in_bom no` still appears in the XML and passes the topology
  contract, but disappears from the native CSV. The gate now parses the CSV and
  requires each of the 69 validated XML components exactly once, with matching
  native/contract references, value, MPN, footprint, population, DNP and off-board
  flags. Missing, duplicated, grouped, unknown or changed rows fail. Eight DNP
  parts and the off-board controller must remain visible; this is a review BOM,
  not an assembly release. CSV row/header order, quoting and blank lines are
  immaterial. The expected inventory comes from the already-validated XML, not
  another manually maintained component list.
- KiCad exports the embedded definitions in each sheet. Editing only the local
  ADS library can therefore leave ERC and the graph unchanged while a later
  library update would alter the design. Before exporting, the gate now compares
  each used embedded definition against `RevA.kicad_sym`, ignoring whitespace
  and only the embedded root identifier's `RevA:` prefix. The small, read-only
  token-tree comparison checks full symbol bodies, duplicate definitions, the
  cache/placed-instance inventory and bounded structure. It neither edits CAD
  nor replaces KiCad's semantic parser. Symbol inheritance is unsupported, and
  body reordering or alternate numeric spellings are conservatively rejected;
  synchronize definitions explicitly rather than adding a suppression.

Seven original regression probes failed before the fixes (five library-only
changes and two invalid CSV outputs). Additional fixtures remove every CSV row,
corrupt each exported field and challenge malformed syntax and cache inventory.
Benign synchronized symbol edits, definition ordering and outside-string
whitespace remain accepted; the checker is not a fixed source-hash allowlist.

Two real KiCad cases demonstrate why both new checks are needed: an excluded
resistor and a library-only ADC pin rename each produce zero ERC violations and
pass the existing XML graph contract, then fail the relevant new check. The
canonical native case also verifies the newly exported CSV. Together with the
existing eight native cases, these form ten actual KiCad regression cases;
software-only token/process fixtures are not counted as native execution.

## Still blocked

All hardware/firmware-port review, schematic release, purchasing and body-use
gates remain false. ERC and connectivity tests do not settle boot-ROM GPIO
behavior, brownout/back-powering, the passive analog startup fixture, effective
capacitance, leakage, real noise or BIAS stability. The existing operator
acknowledgments are not sensing/interlocks. No PCB or physical measurement was
created by this slice. Footprint identifiers are assigned, but independent
package dimensions, pin-one orientation, polarity and layout review remain next.
Then come PCB layout/DRC and schematic parity, delivered quotes, and staged
person-disconnected bench bring-up. TPS7A20 reference-engine work remains parallel.

## Primary basis

- TI ADS1299 SBAS499C: pin tables, section 10.1.1, power/reference and startup.
  https://www.ti.com/lit/ds/symlink/ads1299.pdf
- TI TPS7A20 SBVS338H: DBV pin table and section 6.3.2 EN connection.
  https://www.ti.com/lit/ds/symlink/tps7a20.pdf
- Nexperia BAV199, 1 April 2023: series-pair pinning (1=A1, 2=K2, 3=K1/A2).
  https://assets.nexperia.com/documents/data-sheet/BAV199.pdf
- KiCad 9 CLI and environment documentation: ERC JSON, XML, PDF, CSV, config.
  https://docs.kicad.org/9.0/en/cli/cli.html
  https://docs.kicad.org/9.0/en/kicad/kicad.html

External research was treated as questions to verify, not a replacement circuit
specification. In particular its VREFP-to-3.3-V recommendation was not adopted.
