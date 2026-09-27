# Frozen KiCad footprint fixtures, not assembly approval

The nine `.kicad_mod.gz` files contain unmodified UTF-8 footprint sources from
Debian `kicad-footprints 9.0.2-1`. Gzip compression alone is new; its timestamp
is zero. Copyright KiCad library contributors; CC-BY-SA-4.0 with the KiCad
design exception (see LICENSE.md). Original attribution and descriptions
remain inside each footprint. Source project:
https://gitlab.com/kicad/libraries/kicad-footprints

These are ordinary-test fixtures, not the production library. The native gate
reads actually installed selected files. `tests/footprint_fixtures.py` expands
the nine files in test temporary directories; there is no tar extraction or
runtime download. These frozen inputs are trusted version-controlled fixtures.

The regression contract freezes inspected local pad geometry. It does NOT
assert equality with every manufacturer's land example or qualify assembly.
See `docs/REV_A_FOOTPRINT_REVIEW.md` for comparisons and open decisions.
