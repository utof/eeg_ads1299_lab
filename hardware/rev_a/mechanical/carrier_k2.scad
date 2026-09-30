// K2 dimensioned FIT PROTOTYPE. Millimeters. No fabrication or safety approval.
// Datum: PCB top z=0; board coordinates retained from the authored KiCad source.
// Use from view_k2.scad or a test harness; this library emits nothing on import.
// OpenSCAD 2021.01; no external libraries or font dependencies.
function ports() = [[81.27,38.43], [16.27,43.43]];
function code_y(port) = assert(port==0 || port==1) (port==0 ? 7 : -7);
function contact_y(side) = side==0 ? [32,48] : [27,43];

module box(lo,hi) { translate(lo) cube(hi-lo); }
module hole_at(x,y,z0,z1,d) {
    translate([x,y,z0]) cylinder(h=z1-z0,d=d,$fn=32);
}

// Local port XY. Open cable side is -X; two return tabs still constrain corners.
// K1's closed ring obstructed the horizontal IDC cable. This is intentionally
// a slotted receiver, not the unmodified rectangular K1 model.
module receiver(port=0, closed_cable_wall=false, rib=true) {
    union() {
        difference() {
            box([-5.2,-15.5,9.5],[5.2,15.5,14.5]);
            box([-4.2,-14.5,9.49],[4.2,14.5,14.51]);
            if (!closed_cable_wall)
                box([-5.21,-12.8,9.49],[-4.19,12.8,14.51]);
        }
        if (rib) box([3.4,code_y(port)-1,9.5],[4.21,code_y(port)+1,14.5]);
    }
}

// Socket datum is its mating face. The end ledges are OUTSIDE the male body,
// never a washer between mating faces. Accepted socket dimensions are inspection
// requirements: width <=5.30 (REF is not a maximum), length 26.77..27.28,
// height 9.14..9.52. Real socket/cable inspection and process tolerances are OPEN.
module cartridge(port=0, groove=true) {
    difference() {
        union() {
            box([-4,-14.3,-0.6],[4,14.3,12.8]);
            // Fastening ears are above the guide even after 0.56 axial travel.
            box([-6,-14.3,12.8],[6,14.3,14.3]);
        }
        box([-2.75,-13.7,0],[2.75,13.7,14.31]);
        box([-2.75,-12.9,-0.61],[2.75,12.9,0.01]);
        // Ribbon leaves the SOCKET laterally; preserve it throughout insertion.
        box([-6.01,-12.8,6.1],[-2.74,12.8,10.1]);
        if (groove) box([3.2,code_y(port)-1.2,-0.61],[4.01,code_y(port)+1.2,12.81]);
        for (x=[-4.8,4.8], y=[-11,11]) hole_at(x,y,12.79,14.31,1.5);
    }
}

// Removable only by destroying/replacing four mechanically upset plastic rivets.
// Rivet geometry/material/process not qualified. Continuity and cable exit must
// be inspected BEFORE capture; this is not a self-verifying factory assembly.
module cap() {
    difference() {
        union() {
            box([-6,-14.3,14.3],[6,14.3,15.8]);
            for (y=[-13.0,13.0])
                box([-2.65,y-0.5,9.7],[2.65,y+0.5,14.31]);
        }
        for (x=[-4.8,4.8], y=[-11,11]) hole_at(x,y,14.29,15.81,1.5);
    }
}
module plug(port=0) { cartridge(port); cap(); }

// Nominal / bounding envelopes for fit checks, not detailed connector models.
module header_envelope() {
    box([-2.515,-12.7635,0],[2.515,12.7635,2.54]);
    for (x=[-1.27,1.27], i=[0:9])
        box([x-0.355,-11.43+2.54*i-0.355,2.54],
            [x+0.355,-11.43+2.54*i+0.355,9]);
}
module socket_envelope() { box([-2.65,-13.64,0],[2.65,13.64,9.52]); }
module cable_envelope() { box([-25,-12.7,6.2],[-2.54,12.7,7.8]); }

// M1 contact strips preserved. All other fixture support comes from OUTSIDE PCB.
// Board nominal bottom -1.6; shim support/inspect board datum for actual thickness.
module carrier() {
    union() {
        difference() {
            box([-6,4,-10],[96,74,-7]);
            // Fixture fasteners ONLY, never PCB holes.
            for (x=[0,92], y=[7,71]) hole_at(x,y,-10.1,-6.9,3.2);
        }
        for (side=[0,1]) {
            rail_x = side==0 ? 5 : 90;
            difference() {
                box([rail_x,20,-7.01],[rail_x+3,64,9.5]);
                for (y=contact_y(side)) hole_at(rail_x+1.5,y+3,-1.5,9.51,2.0);
            }
            for (y=contact_y(side)) {
                x0=side==0 ? 5 : 86.5;
                x1=side==0 ? 11.5 : 93;
                box([x0,y,-7.01],[x1,y+6,-1.6]);
            }
        }
        for (port=[0,1]) {
            p=ports()[port];
            translate([p[0],p[1],0]) receiver(port);
            // Two elevated beams carry guide and separate cable saddle.
            outside_x=port==0 ? 93 : 5;
            for (sy=[-1,1]) {
                yy=p[1]+sy*15.0;
                box([min(p[0]-20,outside_x),yy-0.5,7.0],
                    [max(p[0]+5.2,outside_x),yy+0.5,10.5]);
            }
            translate([p[0]-16,p[1],0]) saddle();
        }
    }
}

module saddle() {
    difference() {
        union() {
            box([-4,-16,7.0],[4,16,8.5]);
            for(y=[-14.8,14.8]) box([-4,y-1.2,8.49],[4,y+1.2,10.7]);
        }
        for(y=[-14.8,14.8]) hole_at(0,y,6.9,10.8,2.2);
    }
}
module strain_bar() {
    difference() {
        box([-4,-16,10.7],[4,16,12.2]);
        for(y=[-14.8,14.8]) hole_at(0,y,10.6,12.3,2.2);
    }
}

// Four separately installed cantilever hold-downs. Mirror for right edge.
// 0.10-mm nominal top gap: actual shim/retention adjustment required, not a clamp
// force specification. The column/fastener must not bottom against the board.
module edge_clip() {
    difference() {
        union() {
            box([5,0,9.5],[10.8,6,11.0]);
            box([10,0,0.10],[10.8,6,9.51]);
        }
        hole_at(6.5,3,9.4,11.1,2.2);
    }
}

// Blanket z=0..4 component allocation, EXCEPT the K1 cartridge column and M1
// contact strips. This is conservative but not detailed manufactured part CAD.
module board_and_component_allocation() {
    // Exclude only the 1-um skin of intentional bottom support contact; CGAL
    // otherwise retains zero-volume faces in STL intersections. Not fit tolerance.
    box([10,10,-1.599],[88,68,0]);
    difference() {
        box([10,10,0],[88,68,4]);
        for(p=ports()) translate([p[0],p[1],0]) box([-4,-14.3,-.01],[4,14.3,4.01]);
        for(side=[0,1], y=contact_y(side))
            box([side==0 ? 10 : 86.5,y,-.01],[side==0 ? 11.5 : 88,y+6,4.01]);
    }
}

module assembly(explode=0) {
    color([0.65,0.7,0.75]) carrier();
    color([0.15,0.4,0.25]) box([10,10,-1.6],[88,68,0]);
    for (port=[0,1]) {
        p=ports()[port];
        translate([p[0],p[1],0]) {
            color([0.25,0.25,0.25]) header_envelope();
            translate([0,0,2.54+explode]) {
                color([0.25,0.6,0.8]) cartridge(port);
                color([0.2,0.2,0.2]) socket_envelope();
                color([0.7,0.7,0.7]) cable_envelope();
                translate([0,0,explode]) color([0.3,0.6,0.8]) cap();
            }
        }
        translate([p[0]-16,p[1],explode]) color([0.6,0.6,0.6]) strain_bar();
    }
    for(side=[0,1], y=contact_y(side))
        translate([side==0 ? 0 : 98,y,explode])
            scale([side==0 ? 1 : -1,1,1]) color([0.7,0.7,0.7]) edge_clip();
}
