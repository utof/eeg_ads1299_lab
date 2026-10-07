// B3 read-only access study, NOT printable hardware or a released harness.
// Millimetres; existing K2 datum: PCB top z=0. OpenSCAD 2021.01.
// Inspect nominal free-space corridors, not joint/force/electrical qualification.
use <../../hardware/rev_a/mechanical/carrier_k2.scad>
mode = "view"; // view, routes, vertical_c6, vertical_c30, vertical_c31,
               // vertical_c32, vertical_c33, blocked_routes, blocked_raised

module retained_obstacles() {
    frame(); service_envelope();
    for (port=[0,1]) {
        p=ports()[port];
        translate([p[0],p[1],0]) {
            header_envelope();
            translate([0,0,2.54]) { plug(port); socket_envelope(); cable_envelope(); }
        }
        translate([p[0]-16,p[1],0]) strain_bar();
    }
    for(side=[0,1], y=contact_y(side))
        translate([side==0 ? 0 : 98,y,0])
            scale([side==0 ? 1 : -1,1,1]) edge_clip();
}
module segment(a,b,r) { hull() {
    translate(a) sphere(r=r,$fn=16);
    translate(b) sphere(r=r,$fn=16);
} }
module route(points,r) { for(i=[0:len(points)-2]) segment(points[i],points[i+1],r); }

// Each line is a PAIR corridor (two separately insulated wires), not copper.
// r=0.50 includes assumed bundle radius plus its allowed displacement.
// Local solder exits below z=5.5 are intentionally NOT validated by this model.
module pair_corridors(z=5.5) {
    route([[52.2,48.4,z],[54.5,48.4,z],[54.5,77,z]],0.5); // C6 positive exit
    route([[52.2,56.6,z],[54.5,56.6,z]],0.5); // C6 return joins insulated pair
    route([[63.0,29.5,z],[66,29.5,z],[66,31,z],[56.5,31,z],
           [56.5,28,z],[54.5,28,z],[54.5,1,z]],0.5); // C30
    route([[50.7,20,z],[53.3,20,z],[51,17,z],[51,1,z]],0.5); // C31
    route([[43,23.2,z],[45.6,23.2,z],[45,19,z],[45,1,z]],0.5); // C32
    route([[73.7,23,z],[76.3,23,z],[76.3,21,z],[57,21,z],[57,1,z]],0.5); // C33
}
module vertical_pair(ref) {
    pts = ref==6 ? [[52.2,48.45],[52.2,56.55]] :
          ref==30 ? [[63,29.5],[65.6,29.5]] :
          ref==31 ? [[50.7,20],[53.3,20]] :
          ref==32 ? [[43,23.2],[45.6,23.2]] : [[73.7,23],[76.3,23]];
    for(p=pts) translate([p[0],p[1],4.1]) cylinder(h=25.9,d=0.5,$fn=32);
}
// Disjoint 1 mm^3 witness makes an empty intersection a valid mesh.
module collision(route_mode=false,z=5.5,ref=6) {
    union() {
        translate([120,120,120]) cube(1);
        intersection() {
            if(route_mode) pair_corridors(z); else vertical_pair(ref);
            retained_obstacles();
        }
    }
}
if(mode=="view") {
    color([0.75,0.75,0.75,0.6]) retained_obstacles();
    color([0.25,0.5,0.3,0.3]) translate([10,10,-1.6]) cube([78,58,1.6]);
    color([0.9,0.4,0.1]) pair_corridors();
} else if(mode=="routes") pair_corridors();
else if(mode=="blocked_routes") collision(true);
else if(mode=="blocked_raised") collision(true,8.0);
else if(mode=="vertical_c6") collision(false,5.5,6);
else if(mode=="vertical_c30") collision(false,5.5,30);
else if(mode=="vertical_c31") collision(false,5.5,31);
else if(mode=="vertical_c32") collision(false,5.5,32);
else if(mode=="vertical_c33") collision(false,5.5,33);
else assert(false,"unknown inspection mode");
