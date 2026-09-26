# Frozen native export, not fresh CAD evidence

`rev_a_netlist.xml.gz` is an unmodified KiCad 9.0.2 XML export, compressed only
for fixture size. It is used for ordinary parser/topology fault tests. Its dated
source paths and timestamps are historical, not evidence about a later checkout.
The explicit schematic gate re-exports the actual source with the native CLI;
its native regression compares the parsed graph to this fixture. Neither the
fixture nor a matching graph approves physical hardware.

Uncompressed SHA-256: `7fd9dcd3cf7c8a07c90d22866c942743316491769d9f521802fb8011a0899c48`.

## Native BOM CSV fixture

`rev_a_bom.csv` is the unmodified KiCad 9.0.2 CSV from the first hosted
Schematic run for PR #43 at `970ccbd914758f87edf71d932fb73e05570a5422`
(run `36261244786`, artifact `10911929888`). It contains 69 component rows,
including eight DNP diode packages and the explicitly off-board controller.
SHA-256: `15bf930be3c86fa1dbff665a9219194e73167535a67aad9ac4012eabeda6c683`.

Ordinary tests use this frozen export only as a fixture, corrupting/omitting
rows and fields. The native gate independently exports a fresh CSV and compares
all its fields to the already-validated XML inventory; no fixture is accepted
as evidence about a later source revision. No assembly or purchase is approved.
