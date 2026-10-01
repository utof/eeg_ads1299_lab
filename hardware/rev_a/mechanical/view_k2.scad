// Open this file in OpenSCAD. F6 is a solid render, not mechanical qualification.
use <carrier_k2.scad>
part = "assembly"; // [assembly,exploded,carrier,bridge_J1,bridge_J2,cartridge_J1,cartridge_J2,cap,edge_clip,strain_bar]
if (part=="assembly") assembly();
else if (part=="exploded") assembly(10);
else if (part=="carrier") carrier();
else if (part=="bridge_J1") bridge(0);
else if (part=="bridge_J2") bridge(1);
else if (part=="cartridge_J1") cartridge(0);
else if (part=="cartridge_J2") cartridge(1);
else if (part=="cap") cap();
else if (part=="edge_clip") edge_clip();
else if (part=="strain_bar") strain_bar();
else assert(false,"unknown K2 part");
