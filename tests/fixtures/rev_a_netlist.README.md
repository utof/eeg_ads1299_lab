# Frozen native export, not fresh CAD evidence

`rev_a_netlist.xml.gz` is an unmodified KiCad 9.0.2 XML export, compressed only
for fixture size. It is used for ordinary parser/topology fault tests. Its dated
source paths and timestamps are historical, not evidence about a later checkout.
The explicit schematic gate re-exports the actual source with the native CLI;
its native regression compares the parsed graph to this fixture. Neither the
fixture nor a matching graph approves physical hardware.

Uncompressed SHA-256: `7fd9dcd3cf7c8a07c90d22866c942743316491769d9f521802fb8011a0899c48`.
