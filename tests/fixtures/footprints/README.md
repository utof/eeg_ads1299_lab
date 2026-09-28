# Frozen footprint sources, not assembly approval

Seven `.kicad_mod.gz` files are unmodified KiCad footprint sources from Debian
`kicad-footprints 9.0.2-1`. Copyright KiCad library contributors, CC-BY-SA-4.0
with the KiCad design exception; see LICENSE.md and retained file attribution.
https://gitlab.com/kicad/libraries/kicad-footprints

The two files under RevA_Passives.pretty are frozen project-authored T491 nominal
reflow footprints, under the project's MIT license, not KiCad upstream originals.
Gzip compression alone is applied with zero timestamps. Their editable sources
are in hardware/rev_a/kicad/RevA_Passives.pretty. Independent copper and courtyard
expectations follow KEMET Table 2; see docs/REV_A_TANTALUM_LANDS.md.

These are ordinary-test fixtures, not the production library. The native gate
reads actually selected installed and project-local files. The fixture helper
expands trusted version-controlled files into test directories without runtime
downloads or tar extraction. Source checks are not assembly qualification.
