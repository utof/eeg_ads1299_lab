# Frozen native export, not fresh CAD evidence

`rev_a_netlist.xml.gz` is an unmodified KiCad 9.0.2 XML export, compressed only
for fixture size. It is used for ordinary parser/topology fault tests. Its dated
source paths and timestamps are historical, not evidence about a later checkout.
The explicit schematic gate re-exports the actual source with the native CLI;
its native regression compares the parsed graph to this fixture. Neither the
fixture nor a matching graph approves physical hardware.

## Updated native export for local T491 land selection

Generated with actual KiCad 9.0.2 on 2026-09-27 after introducing the two local
T491 nominal reflow footprints. The complete parsed graph differs from the
previous fixture only in C_REF/C_VCAP1 footprint IDs. All nets, terminals and
other component fields are unchanged; see `docs/REV_A_TANTALUM_LANDS.md`.

Uncompressed XML SHA-256: `ca9ccef463e1ab31426ae3afdc9744bd085a6b5bfde18fe231871228ce91fea2`.

`rev_a_bom.csv` is the corresponding unmodified native CSV: 69 rows, eight DNP
packages and off-board MOD1. SHA-256:
`87460b3c87d06f3ad077e5521f7b06665c0a19cd4e16f3d25169e1603e2c3c22`.

Prior PR #43 fixture provenance remains in Git history. These updated fixtures
are not fresh-run evidence about a later checkout and approve no assembly.
