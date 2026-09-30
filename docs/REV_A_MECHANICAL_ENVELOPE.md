# Rev A mechanical and assembly envelope M1

**Reviewed source:** `8c3440ed6714bfebaac74768a0d371401a22e89e`, tree
`81acc1aa34c29faa7a0305d2247826909a6c2f13`. Authored board SHA256
`5da65b4307f0336883da9aeae48711b28c1944ec587f5d3174f12db4e9921875`.
M1 is a selected mechanical planning envelope, not a released fixture or
manufacturing approval. No copper, holes, footprints, BOM or firmware change.

## Decision and concrete assembly blocker

**Retain the existing outline and use an external nonconductive edge carrier,
with independently supported controller and cable strain relief.** Four small
contact regions below pass a source-geometry screen. No new mounting hole is
required for this concept. Do not drill, clamp arbitrary edges, place metal
washers under the board, or use the headers as structural supports. Carrier
material, retention force, board deflection, contamination, dimensional
variation and physical fit still need a drawing and validation. The selection
is a way forward without rerouting, not proof that any generic holder fits.

**The present TSW-110-07-T-D headers must not be included in an assumed
lead-free SMT reflow process.** Samtec's TSW/HTSW catalog identifies TSW as
PBT and lists it as not lead-free solderable, with lead-wave-only processing;
it separately lists HTSW as lead-free solderable [1]. The combined SSW/TSW/SMH
specification's reflow section explicitly discusses *surface-mount* parts and
labels its temperature tables SMT [5]. Its generic reflow-pass paragraph is not
an exact-orderable exception to the through-hole TSW catalog restriction.
Tin plating or RoHS status alone is not process compatibility.

Select a staged assembly architecture: SMT components first, headers excluded
from that operation. **The subsequent header attachment process is on hold**
until the exact TSW process is accepted in writing or a high-temperature header
alternative is reviewed and migrated consistently. This is not permission to
hand-solder TSW with an unverified lead-free profile, use a leaded process, or
silently replace it with HTSW. All other stencil/land/reflow decisions stay open.

**Next bounded task:** evaluate the same-function high-temperature header route
and a polarized actual mate/strain-relief arrangement. Resolve the connector
process choice before a coordinated BOM/schematic/PCB-field/test change and
final carrier drawing. This is one connector/process decision, not a new layout
or an open-ended catalog search. Keep capacitor #48 and remaining #45 inputs open.

## What the authored board actually provides

The single Edge.Cuts rectangle runs from **(10,10) to (88,68) mm**: nominal
**78 x 58 mm**. KiCad's 78.05 x 58.05-mm graphic bounding box includes the
0.05-mm outline stroke; it is not the board's specified physical size. Finished
outline and thickness tolerances need the factory drawing. Nominal thickness
is 1.6 mm, with the previously selected but unconfirmed stackup target.

All 68 footprints are front-side; eight diode bodies are DNP. There are 205 SMD
pads and 40 plated through-hole header pads, **no NPTH mounting pads and no
separate mounting-hole footprint or internal Edge.Cuts cutout**. The 122 signal/
power vias are not mounting holes. The ground plane and buried copper remain
under some mechanically empty surface regions.

Coordinates below are top-view native board coordinates, not a mating-face
view. Both header footprint rotations are zero. Each row advances +2.54 mm
in y; odd pins are the lower-x column and even pins the higher-x column.

| Header | Function | Pad 1 (x,y) mm | Pin-grid centre mm | Pin-grid x / y range mm |
|---|---|---|---|---|
| AFE J1 | Digital/power | (80,27) | (81.27,38.43) | 80..82.54 / 27..49.86 |
| AFE J2 | Dummy analog input | (15,32) | (16.27,43.43) | 15..17.54 / 32..54.86 |

The same unkeyed 2x10 form serves electrically incompatible functions. Reversed,
one-position-offset and wrong-header mating must be prevented by the final
mechanical arrangement and verified unpowered before any later allowed test.
Labels alone are not a mechanical interlock. Do not remove an arbitrary pin:
J1's full map is assigned and J2's unused positions are still part of the
current contract. Preserve AFE/DEVKIT prefixes and the existing wiring map.
`REV_A_BENCH_HARNESS.md` now describes the actual layout rather than saying no
layout exists. No cable, keyed connector or live interface was qualified here.

## Mating allocation, not an arbitrary plug guarantee

M1 reserves **8 mm across the rows by 28 mm along them**, centred on each pin
field. These are chosen planning dimensions, not measured or manufacturer
maximum plug dimensions. They exclude fingers/tools, cable bend radius,
connector sway, tails, adapter boards and strain relief, which need their own
external volumes. No closed enclosure is selected.

| Allocation | (xmin,ymin,xmax,ymax), mm | Nearest other courtyard AABB gap | Board-edge margin |
|---|---|---:|---:|
| J1 | (77.27,24.43,85.27,52.43) | C33: 0.726 mm | 2.730 mm |
| J2 | (12.27,29.43,20.27,57.43) | D1/D3/D5/D7: 1.300 mm | 2.270 mm |

Courtyard-centreline bounding boxes conservatively screen the footprint
neighborhood, including DNP diode courtyards. They are not guaranteed assembly
or tool-clearance envelopes. The tightest neighbor is the C33 corner; changing
the plug, candidate body or placement tolerance requires rechecking it.

**Geometry reference only:** Samtec SSW-110-01-T-D is a same-pitch socket with
about 25.91-mm body length, 4.95-mm reference width and 8.51-mm height [3,4].
It has PCB tails, not a finished cable/strain-relief assembly, and is not being
added to the BOM. The drawing's +/-0.25-mm length tolerance, cut flash and sway
must be included in an actual assembly fit review; the width is marked REF.
This is a nominal fit screen, not a worst-case mate certification.

TSW style07 has a 5.84-mm nominal mating post and 2.54-mm reference body
height: nominal unmated height **8.38 mm**. The SSW insertion-depth interval is
3.68..6.35 mm [1,3]. The nominal post lies in that interval, but actual seating
and tolerances remain to be checked. Adding 2.54 and 8.51 gives **11.05 mm**
as a nominal fully seated shell-top estimate, not a guaranteed board-to-board
spacing. Carrier clamps must not obstruct withdrawal or cause board bending.

## Heights and board support

| Item | Reference maximum L x W x H, mm | Centred body-to-own-courtyard AABB margin |
|---|---|---:|
| Proposed 10-uF bulk, C30-C33 | 2.10 x 1.35 x 1.35 | 0.305 mm |
| Proposed 1-uF/100-nF, C8-C29 | 1.70 x 0.90 x 0.90 | 0.280 mm |
| Existing T491D C6 | 7.60 x 4.60 x 3.10 | 0.250 mm |
| Existing T491B C7 | 3.70 x 3.00 x 2.10 | 0.250 mm |

The candidate bulk is 0.40 mm taller than the old part but does not exceed
C6's reference height. Murata bounds come from the previously retained exact
reference records, not an 0805-name assumption; the candidates remain unadopted.
KEMET's current captured dimensions match the existing July2026 land source
[7]. Centred-body containment excludes placement error, solder, termination
fit and process tolerances, so it does not approve the land or component change.
U1's PAG drawing separately specifies 1.20-mm maximum overall height [6].

Choose **4 mm free height over the SMT field**, **15 mm open vertical space over
each header mating allocation**, at least **6 mm further unobstructed withdrawal
travel above the actual mated shell**, and **5 mm board-underside-to-base space**
as carrier design starting points. No lid/tool/fixture is qualified by those
numbers. Cable and adapter protrusions can exceed them and must be accommodated.
For scale, the nominal 2.54-mm TSW tail minus a nominal 1.6-mm board is 0.94 mm;
using the earlier overall minimum thickness1.44 gives1.10 mm before terminal
variation and solder. Neither calculation bounds the actual finished protrusion.
Inspect actual solder/tails, board warp and fixture tolerances before assembly
acceptance. Do not rely on soldermask as the fixture's insulation system.

Four selected **1.5 x 6 mm surface-contact strips** are below; dimensions are
planning allocations, not a supplied or fabricated clamp. Support and removable
retention stay within them; the base fastens outside the PCB. Add strain relief
on the carrier, not on sensitive leads or component bodies. This is not a tested
load/deflection model or permission for a suspended mating daughterboard.

| Region | (xmin,ymin,xmax,ymax), mm | Outer pad/track/via AABB gap | Courtyard gap | Mate-allocation gap |
|---|---|---:|---:|---:|
| Left upper | (10,32,11.5,38) | 1.300 | 1.730 | 0.770 |
| Left lower | (10,48,11.5,54) | 1.300 | 1.730 | 0.770 |
| Right upper | (86.5,27,88,33) | 3.110 | 2.180 | 1.230 |
| Right lower | (86.5,43,88,49) | 3.110 | 2.180 | 1.230 |

These distances are conservative AABB lower bounds on current outside copper,
not actual minimum trace-to-contact distances in three dimensions. The screen
explicitly rejects unsupported outer pours/copper graphics; there are none in
this source. It includes through vias and both outer pad/track layers. Buried
copper, mask damage, edge registration, friction, material leakage, cleanliness
and insertion forces are NOT qualified. Surface clearance is **not permission
to drill into these locations** or automatically reserve a copper keepout.

Samtec recommends independent support for board-to-board mating [5]. M1 applies
that principle through an external carrier because the present PCB has no
mount holes. Actual insertion/extraction force and permissible board strain
must be determined with the chosen mate and carrier, not guessed from pin count.

The existing 1.00-mm header drills also differ from the manufacturer's 1.02-mm
nominal callout [2]. A nominal0.635-mm square post has a0.898-mm diagonal, but
that arithmetic does not include terminal, hole/plating or positioning tolerances.
Keep hole/annulus and process review open; no automatic drill or pad resize.

## Reproduce the source screen

Run this read-only block from the repository root using the system Python
which supplies the pinned KiCad9.0.2 `pcbnew` module. It does not refill/save the
board or create a production dependency. It derives the counts, header grids,
rectangles, gaps and centred-capacitor projections, then checks the retained
record. The record's parameters are chosen allowances; the code does not
revalidate vendor drawings, mechanical force or a real fixture. AABB distance
is deliberately conservative, not a generic exact collision solver.

```python
import hashlib
import json
import math
from pathlib import Path
import pcbnew as k

record = json.loads(Path("docs/checkpoints/20260930_mechanical_envelope.json").read_text())
path = Path("hardware/rev_a/layout/rev_a.kicad_pcb")
assert hashlib.sha256(path.read_bytes()).hexdigest() == record["board_sha256"]
assert k.Version() == "9.0.2"
b = k.LoadBoard(str(path))


def point(p):
    return [p.x / 1e6, p.y / 1e6]


def box(p):
    return [p.GetX() / 1e6, p.GetY() / 1e6, p.GetRight() / 1e6, p.GetBottom() / 1e6]


def span(points):
    return [
        min(p[0] for p in points),
        min(p[1] for p in points),
        max(p[0] for p in points),
        max(p[1] for p in points),
    ]


def separation(a, z):
    return math.hypot(max(a[0] - z[2], z[0] - a[2], 0), max(a[1] - z[3], z[1] - a[3], 0))


def margin(inner, outer):
    return min(inner[0] - outer[0], inner[1] - outer[1], outer[2] - inner[2], outer[3] - inner[3])


fps = {f.GetReference(): f for f in b.GetFootprints()}
pads = [p for f in fps.values() for p in f.Pads()]
tracks = list(b.GetTracks())
edges = [g for g in b.GetDrawings() if g.GetLayer() == k.Edge_Cuts]
assert len(edges) == 1 and edges[0].GetShape() == k.SHAPE_T_RECT
outline = span([point(edges[0].GetStart()), point(edges[0].GetEnd())])
counts = [
    len(fps),
    len(pads),
    len(tracks),
    sum(p.GetAttribute() == k.PAD_ATTRIB_NPTH for p in pads),
    sum(p.GetAttribute() == k.PAD_ATTRIB_PTH for p in pads),
    sum(f.GetLayer() == k.F_Cu for f in fps.values()),
]
assert counts == record["counts_footprints_pads_copper_NPTH_PTH_front"]
assert outline == record["outline_centerline_bbox_mm"]
courts = {}
for ref, f in fps.items():
    gs = [g for g in f.GraphicalItems() if isinstance(g, k.PCB_SHAPE) and g.GetLayer() == k.F_CrtYd]
    assert gs and all(g.GetShape() in (k.SHAPE_T_SEGMENT, k.SHAPE_T_RECT) for g in gs)
    courts[ref] = span([point(p) for g in gs for p in (g.GetStart(), g.GetEnd())])
# This board has no outer-layer zones or copper graphics; don't silently ignore new ones.
assert all(z.GetLayer() == k.In1_Cu for z in b.Zones())
assert not any(g.GetLayer() in (k.F_Cu, k.B_Cu) for g in b.GetDrawings())
assert not any(g.GetLayer() in (k.F_Cu, k.B_Cu) for f in fps.values() for g in f.GraphicalItems())
outer = [
    box(x.GetBoundingBox()) for x in pads + tracks if x.IsOnLayer(k.F_Cu) or x.IsOnLayer(k.B_Cu)
]
allocations, header_rows = {}, []
for ref in ("J1", "J2"):
    f = fps[ref]
    ps = {p.GetNumber(): p for p in f.Pads()}
    origin = point(ps["1"].GetPosition())
    assert len(ps) == 20 and f.GetOrientationDegrees() == 0
    for n in range(1, 21):
        expected = [origin[0] + ((n - 1) % 2) * 2.54, origin[1] + ((n - 1) // 2) * 2.54]
        assert all(abs(a - z) < 1e-6 for a, z in zip(point(ps[str(n)].GetPosition()), expected))
        assert point(ps[str(n)].GetDrillSize()) == [1.0, 1.0]
    grid = span([point(p.GetPosition()) for p in ps.values()])
    cx, cy = (grid[0] + grid[2]) / 2, (grid[1] + grid[3]) / 2
    width, length = record["mate_allocation_width_length_mm"]
    a = [cx - width / 2, cy - length / 2, cx + width / 2, cy + length / 2]
    near, neighbor = min((separation(a, c), r) for r, c in courts.items() if r != ref)
    assert margin(a, outline) >= 2 and near >= 0.5
    allocations[ref] = a
    header_rows.append([ref, origin, a, margin(a, outline), neighbor, near])
support_rows = []
for label, a in record["support_contact_rectangles_mm"].items():
    assert margin(a, outline) >= 0 and a[0] < a[2] and a[1] < a[3]
    distances = [
        min(separation(a, c) for c in outer),
        min(separation(a, c) for c in courts.values()),
        min(separation(a, c) for c in allocations.values()),
    ]
    # Selected screening allowances, not manufacturer tolerances or force qualification.
    assert distances[0] >= 1 and distances[1] >= 0.5 and distances[2] >= 0.5
    support_rows.append([label, *distances])
body_rows = []
for group in record["body_reference_groups"]:
    lx, ly, h = group["maximum_L_W_H_mm"]
    margins = []
    for ref in group["references"]:
        f = fps[ref]
        cx, cy = point(f.GetPosition())
        angle = -math.radians(f.GetOrientationDegrees())
        pts = [
            [
                cx + x * math.cos(angle) - y * math.sin(angle),
                cy + x * math.sin(angle) + y * math.cos(angle),
            ]
            for x in (-lx / 2, lx / 2)
            for y in (-ly / 2, ly / 2)
        ]
        margins.append(margin(span(pts), courts[ref]))
    assert min(margins) > 0
    body_rows.append([group["name"], h, min(margins)])
result = {"headers": header_rows, "supports": support_rows, "body_groups": body_rows}


def compare(actual, saved):
    if isinstance(actual, (int, float)):
        assert isinstance(saved, (int, float)) and math.isclose(actual, saved, abs_tol=1e-6)
    elif isinstance(actual, list):
        assert isinstance(saved, list) and len(actual) == len(saved)
        for a, z in zip(actual, saved):
            compare(a, z)
    else:
        assert actual == saved


for key, value in result.items():
    compare(value, record["observed"][key])
print(json.dumps(result, indent=2))
```

## Evidence and remaining exit conditions

Source-capture36754120103 checked out exactmain8c3440 from GitHub and preserved
its original history. Primary capture36755627629 retained eight PDFs and their
hashes; the checkpoint lists exact URLs/byte identities/revisions. Relevant
pages were inspected as rendered images, not inferred from an unrelated part.
The generic spec's web screenshot failed; its independently downloaded native
PDF page was rendered and inspected instead. Full PDFs are not required project
dependencies and are not incorporated into this product source.

Native/source comparison independently checked all704 track/via forms and245
pad positions, all68 footprint origins and the actual outline. The exact
reproduction above passed. Three changed-record probes were executed and rejected: a support moved into
copper, a mating allocation widened into a neighbor, and an altered retained
clearance result. Original data was restored and the exact block passed again.
These are documentary/data controls, not physical or new project tests. Final PR execution/review must be
read at its actual head; previous CI successes do not validate this source.

M1 closes the initial envelope selection, not the assembly/fixture release.
Next resolve the TSW process/high-temperature alternative plus a physically
polarized mate and cable support, then finalize carrier dimensions/tolerances.
Keep #45/#48, capacitor qualification, factory stack, real powered-off console
behavior, measurement fixture/floor and delivered budget open. No procurement,
fabrication, powered connection, body use or approved insulation is claimed.

## Primary references, checked 2026-09-30

[1] Samtec TSW/HTSW through-hole catalog F-226, pp1-2:
https://suddendocs.samtec.com/catalog_english/tsw_th.pdf
[2] Samtec TSW market drawing revDS, sheets2,6 and footprint revA:
https://suddendocs.samtec.com/prints/tsw-xxx-xx-xxx-x-xx-xxx-mkt.pdf
https://suddendocs.samtec.com/prints/tsw-xxx-xx-x-x-xx-xxx-footprint.pdf
[3] Samtec SSW/SSQ through-hole catalog F-226:
https://suddendocs.samtec.com/catalog_english/ssw_th.pdf
[4] Samtec SSW drawing revCL, sheet1:
https://suddendocs.samtec.com/prints/ssw-1xx-xx-xxx-x-xx-xxx-xx-mkt.pdf
[5] Samtec combined SSW/TSW and SMH/TSW product specification revC,
2023-02-08, pp5-6 (SMT processing versus independent supports):
https://suddendocs.samtec.com/productspecs/tsw-sxx.pdf
[6] TI ADS1299 SBAS499C, PDFp81, PAG drawing4040282/C:
https://www.ti.com/lit/ds/symlink/ads1299.pdf
[7] KEMET T2005_T491, captured2026-07-08 edition, p4:
https://content.kemet.com/datasheets/KEM_T2005_T491.pdf
Murata candidate dimensions: existing `bulk_orderable_addendum.json` and
`20260930_capacitor_e1.json`, retaining their exact suffixes and dated-reference
limits. Do not rewrite those historical records as new approval specifications.
