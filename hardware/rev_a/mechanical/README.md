# K2 carrier CAD — unapproved fit prototype

Open **view_k2.scad** in OpenSCAD 2021.01. Select `assembly` or `exploded` in
Customizer, or an individual part. F6 renders solids. The library is
**carrier_k2.scad**; dimensions are millimeters in the PCB coordinate system,
with PCB top z=0. No fonts or external CAD library are needed.

See [the dimension/assembly/validation record](../../../docs/REV_A_CARRIER_K2.md)
before editing or interpreting meshes. The rendered board and connectors are
reference envelopes. The assembly is not one printable part. Export only a
named part after the separate prototype/process approvals; STL export alone
is not fabrication permission.

The base has no fasteners through the PCB. Remove the raised bridges for board
installation. J1/J2 bridge fastener spacings differ (30/36 mm). Socket cartridges
have different ribs/grooves, side cable windows and permanently captured cover
concepts. Remove/release the independent cable clamp BEFORE withdrawal. Real
socket orientation, printed dimensions, capture strength and mating behavior
are not verified by a picture or finite collision samples.

The native project gate now includes actual OpenSCAD collision/mesh checks:

```sh
uv run --locked python -m tools.check --native
```

It requires the documented native tools, including OpenSCAD 2021.01; no missing-
renderer skip is a pass. All purchasing, fabrication, powered-connection and
body-use gates remain unchanged. Current PCB source identity is recorded in
the linked document and checked by the tests.
