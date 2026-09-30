# K1: high-temperature header revision and coded cable-cartridge design

Base main `a55ce97a6029a4759d23f1f528feda3c5a0dc6b8`, 2026-09-30.
**Adopt HTSW-110-07-T-D for both board headers.** This is an explicit component
revision, not a silent substitution or manufacturing approval. Select the
IDSD-10-S-04.00-T-G-ST4 single-ended cable configuration as the external harness
design target and a carrier-supported, differently coded cartridge at each
header. The cable/carrier are not yet BOM-qualified or physically validated.

The current BOM/profile, both native schematic symbols, PCB Value/MPN fields,
current baseline table and actual native-export fixtures are migrated together.
No pin is omitted; circuit values, all routing/zone fill, pads, drills, local
footprints, firmware, models, dependencies and approval gates are unchanged.
Historical TSW/mechanical/capacitor records remain dated evidence, not rewritten.

## 1. Header and attachment decision

The exact HTSW product page identifies a tin, 20-position, two-row 2.54-mm
through-hole part [1]. The shared catalog distinguishes HTSW's LCP, lead-free
compatible construction from TSW's PBT/lead-wave-only restriction [2]. The
linked HTSW BQ drawing and revision-B land drawing establish the selected
straight -07 geometry [3,4]: no locking-lead, locking-clip, washer or omitted
position suffix is adopted.

| Property | HTSW selection / compatibility consequence |
|---|---|
| Posts and grid | 0.025-inch square reference; 2.54-mm row/column pitch; all 20 pins |
| Mating post | 0.230 +/-0.008 inch = 5.842 +/-0.2032 mm, per drawing |
| Body | 25.4 mm nominal length, -0.381/+0.127 mm; 5.03-mm width and 2.54-mm height are REF |
| Tail | 2.54 mm nominal catalog tail; not a guaranteed finished protrusion |
| Existing land | Same generic 2x10 footprint and 1.00-mm source drills retained |
| Manufacturer land | 0.040-inch / 1.02-mm nominal hole callout; actual finished-hole/registration/pin-fit DFM still open |

The slightly narrower reference body does not justify moving pins, enlarging
holes or treating a generic KiCad STEP model as an exact HTSW model. Pin sway,
cut flash, terminal variation, finished plating and board thickness still need
process/fit evaluation. This revision removes the known **family material**
obstacle; it does not certify the unchanged hole process.

**Chosen assembly architecture:** populate/reflow SMT first, then attach the
unmated HTSW headers by an assembler-accepted selective lead-free through-hole
process. Exact alloy, temperature, dwell, preheat, fixtures, cleaning and
inspection criteria must be accepted before use. None was supplied by a vendor
or validated here. Do not infer a soldering temperature from the connector's
operating-temperature range or apply a generic SMT-family test to this job.
Cable sockets and printed cartridges stay out of board reflow. No permission
for an improvised TSW or HTSW hand-soldering profile follows from this record.

The header allowance changes from $0.90 to **$2.00 each**. The new fitted and
planning subtotals are **$76.34 / $94.34**. This is a deliberately rounded
planning allowance, not a supplier quote. The historical $3 harness reserve is
not proven sufficient for two IDC assemblies or the coded carrier; quote the
complete basket before claiming the $100 objective is met. No purchase occurred.

## 2. A real cable configuration, not the old PCB-tail socket

Select **IDSD-10-S-04.00-T-G-ST4** as the harness design target: ten positions per
row, single IDC end, four-inch nominal length, tin contacts, gray ribbon and
stripped/tinned free ends. This configuration follows the manufacturer catalog
and Rev AE assembly drawing [5,6]; the exact configured product page was not
retrieved. Do not equate construction-code validity with current stock, a
factory-accepted order, price or electrical qualification.

The drawing/catalog describe 28-AWG stranded tinned-copper ribbon. Four inches
is **101.6 +/-3.175 mm**; ST4 is nominal **6.35-mm stripped/tinned free end**,
not an insulated plug on the controller side. The nominal body length is
26.90 mm, drawing upper length 27.28 mm; width is **5.08 mm REF**, and upper
body height 9.52 mm. Cable bow, bend allowance and real tool/strain-relief space
are additional to this rectangle. Tin mating contacts avoid deliberately
specifying dissimilar contact finishes; they do not prove microvolt stability.

Samtec recommends -07 posts for IDXX mating [2]. IDSD insertion is
0.220..0.245 inch [5]. At the -07 post's stated extremes, the **fully seated,
zero-added-gap** arithmetic margins are only **0.0508 mm** above minimum and
**0.1778 mm** below maximum insertion. That is NOT guaranteed engagement.
A cartridge must not hold the socket above its proper seating plane; actual
post length, socket seating, tilt, retention and withdrawal need a measured
stack-up. Do not hide this small lower margin behind nominal 5.84-mm fit.

Keep the existing electrical harness map. Identify every cable conductor by
unpowered continuity to the actual mating contact; a top-view pin map is not
a mating-face view, and stripe color alone is not a complete pinout proof.
J1's ten return positions stay represented. On J2, unused 11..20 and initially
disabled BIAS9 are individually insulated at their free ends, not tied together
or left exposed. The free ends require a reviewed controller/fixture termination,
not bare wires to an unqualified live adapter. No power-up or external-input
mode is enabled. Cable capacitance, imbalance and activity coupling must still
meet E1; 101.6-mm length is not proof of E1's fixture loading limits.

## 3. K1 coding geometry: preserve every electrical contact

Bare HTSW/IDSD is **not keyed**. Do not use HTSW omitted-position or IDSD -Pxx
blocked-hole options: that would change the existing twenty-position contract.
A shrouded-header redesign is not assumed to fit the unchanged neighboring
copper. Instead specify a **captive cable cartridge and receiver guide fixed
to the external carrier**, with an inward guide rib and matching cartridge
groove. J1 and J2 use different groove positions. Neither guides nor cable loads
are supported by solder joints or the ADC board alone.

Top-view coordinates below are relative to the header's pin-grid center; +x
is toward the higher-x/even-pin column, +y toward pins19/20, NOT a mirrored
mating-face drawing. Selected dimensions are design allocations, not supplier
part tolerances or a released print:

| Feature | K1 allocation |
|---|---|
| Captive cartridge cross-section | 8.0 x 28.6 mm, centered on the 2x10 grid |
| Receiver bore | 8.4 x 29.0 mm |
| Cartridge side groove | x=3.2..4.0 mm; y=center +/-1.2 mm; full guided height |
| Inward receiver rib | x=3.4..4.2 mm; y=center +/-1.0 mm |
| Code centers | J1 y=+7.0 mm; J2 y=-7.0 mm, both on +x side |
| Cartridge height / guide z | 12 mm / 9.5..14.5 mm above PCB top |
| Raised guide outer rectangle | 10.4 x 31.0 mm; supports reach the carrier, not SMT components |
| Working / withdrawal space | 17 mm header height plus 8 mm withdrawal allocation, revising M1's initial allowance |

The receiver's solid rib rejects a cartridge without its groove, the wrong
code and a 180-degree reversal in the parallel model below. Its closed bore
rejects pitch-offset and quarter-turn poses. The cartridge must be mechanically
captured in the correct orientation to its socket; markings, adhesive alone,
or a removable sleeve that can be swapped between cables are not a qualified
interlock. Retain a separate strain-relief saddle on the carrier, outside the
socket and first bend. Bare sockets, missing guide ribs, damaged cartridges,
forced/tilted approaches and incorrect sleeve installation are NOT protected
by the numerical cross-section check.

The 12-mm cartridge permits a 5-mm guide overlap even near the nominal seated
position. Inspect the actual highest male tip against the selected <=9.0-mm
allocation so that guide entry at14.5mm nominally precedes electrical approach.
This is an axial planning check, **not a proof of first-contact protection for
arbitrary tilt**. Finish a dimensioned CAD carrier with chamfers, socket capture,
bend/strain relief, tolerances and force/deflection limits, then validate unpowered
wrong-port/reverse/offset/tilted approaches before any allowed powered test.

A new native AABB screen gives cartridge-to-other-courtyard lower bounds of
**0.5894 mm at J1/C33 and 1.30 mm at J2/D1**, versus M1's smaller planning box.
The wider receiver projection actually **overlaps C33's courtyard in XY**.
It MUST be raised as specified and supported from the carrier; do not turn this
into a positive 2D clearance or place its wall on the PCB. Receiver-to-J2 D1
projection gap is only0.10mm. These are planning projections, not full3D fit
or body/placement uncertainty approval. The IDSD width is REF, so no maximum
width/assembly tolerance was inferred. Coordinates are retained in the JSON.

## 4. Reproduce the bounded coding and source checks

Run from a locked repository checkout. Integers below are hundredths of a
millimeter; rectangle intersection/subtraction is exact for the stated parallel
cross-sections. The 912 enumerated poses include two ports, two cartridges,
four quarter-turns, three row offsets and nineteen column offsets. These are
not 912 physical tests or a continuous 3D/tolerance proof. The separate +/-0.1mm
translation probes are chosen design checks, not manufactured tolerance bounds.

```python
import hashlib
import itertools
import json
from pathlib import Path
from hardware.rev_a import load_documents, totals, validate

record = json.loads(Path("docs/checkpoints/20260930_connector_k1.json").read_text())
profile, bom, sources = load_documents()
assert not validate(profile, bom, sources)
header = next(row for row in bom["line_items"] if row["id"] == "headers")
assert header["mpn"] == "HTSW-110-07-T-D" and header["quantity"] == 2
assert totals(bom)["planning_total"].as_tuple() == (0, (9, 4, 3, 4), -2)
board = Path("hardware/rev_a/layout/rev_a.kicad_pcb").read_bytes()
assert board.count(b'"HTSW-110-07-T-D"') == 4
assert hashlib.sha256(board).hexdigest() == record["board_sha256"]
assert (
    hashlib.sha256(board.replace(b'"HTSW-110-07-T-D"', b'"TSW-110-07-T-D"')).hexdigest()
    == record["base_board_sha256"]
)
p = record["key_profile"]


def intersection(a, b):
    return [max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])]


def area(a):
    return max(0, a[2] - a[0]) * max(0, a[3] - a[1])


def pose(a, turns, dx, dy):
    points = list(itertools.product((a[0], a[2]), (a[1], a[3])))
    for _ in range(turns):
        points = [(-y, x) for x, y in points]
    return [
        min(x for x, y in points) + dx,
        min(y for x, y in points) + dy,
        max(x for x, y in points) + dx,
        max(y for x, y in points) + dy,
    ]


def accepts(port, plug, turns=0, dx=0, dy=0, groove_present=True):
    body = pose(p["plug_body"], turns, dx, dy)
    cy = p["codes_y"][plug]
    half = p["groove_half_length"]
    groove = pose([p["groove_x"][0], cy - half, p["groove_x"][1], cy + half], turns, dx, dy)
    cy = p["codes_y"][port]
    half = p["rib_half_length"]
    rib = [p["rib_x"][0], cy - half, p["rib_x"][1], cy + half]
    if area(intersection(body, p["bore"])) != area(body):
        return False
    overlap = intersection(body, rib)
    relief = area(intersection(overlap, groove)) if groove_present and area(overlap) else 0
    return area(overlap) == relief


poses = accepted = 0
for port, plug, turn, col, row in itertools.product(
    p["codes_y"], p["codes_y"], range(4), range(-1, 2), range(-9, 10)
):
    result = accepts(port, plug, turn, col * p["pitch"], row * p["pitch"])
    expected = port == plug and turn == col == row == 0
    assert result == expected, (port, plug, turn, col, row)
    poses += 1
    accepted += result
assert (poses, accepted) == (912, 2)
for port in p["codes_y"]:
    assert not accepts(port, port, groove_present=False)
    for dx, dy in itertools.product((-p["translation_probe"], 0, p["translation_probe"]), repeat=2):
        assert accepts(port, port, dx=dx, dy=dy)
# Inch-dimension arithmetic is not a guaranteed physical engagement result.
low = (0.230 - 0.008 - 0.220) * 25.4
high = (0.245 - (0.230 + 0.008)) * 25.4
assert abs(low - record["reference_limits"]["full_seating_min_insertion_margin_mm"]) < 1e-12
assert abs(high - record["reference_limits"]["full_seating_max_insertion_margin_mm"]) < 1e-12
assert not any(record["approvals"].values())
print(
    json.dumps(
        {
            "parallel_poses": poses,
            "accepted_correct_poses": accepted,
            "translation_probes": 18,
            "insertion_arithmetic_mm": [low, high],
        },
        indent=2,
    )
)
```

The additional native9.0.2 read-only screen below reproduces the six XY
projection rows. It neither refills the board nor proves z-clearance, socket
capture or assembly tolerances. The receiver's zero J1 projection gap is
intentionally retained as an overlap requiring the raised design.

```python
from pathlib import Path
import json, math
import pcbnew as k

b = k.LoadBoard("hardware/rev_a/layout/rev_a.kicad_pcb")
fps = {f.GetReference(): f for f in b.GetFootprints()}


def span(ps):
    return [
        min(p[0] for p in ps),
        min(p[1] for p in ps),
        max(p[0] for p in ps),
        max(p[1] for p in ps),
    ]


def xy(p):
    return [p.x / 1e6, p.y / 1e6]


def sep(a, z):
    return math.hypot(max(a[0] - z[2], z[0] - a[2], 0), max(a[1] - z[3], z[1] - a[3], 0))


courts = {}
for ref, f in fps.items():
    gs = [g for g in f.GraphicalItems() if isinstance(g, k.PCB_SHAPE) and g.GetLayer() == k.F_CrtYd]
    assert all(g.GetShape() in (k.SHAPE_T_SEGMENT, k.SHAPE_T_RECT) for g in gs)
    courts[ref] = span([xy(p) for g in gs for p in (g.GetStart(), g.GetEnd())])
rows = []
for ref in ("J1", "J2"):
    grid = span([xy(p.GetPosition()) for p in fps[ref].Pads()])
    cx, cy = (grid[0] + grid[2]) / 2, (grid[1] + grid[3]) / 2
    for label, w, l in [
        ("IDSD_reference", 5.08, 27.28),
        ("cartridge", 8, 28.6),
        ("raised_guide", 10.4, 31),
    ]:
        rect = [cx - w / 2, cy - l / 2, cx + w / 2, cy + l / 2]
        near, neighbor = min((sep(rect, c), r) for r, c in courts.items() if r != ref)
        rows.append(
            dict(
                header=ref,
                item=label,
                bbox_mm=rect,
                nearest_other_courtyard=neighbor,
                lower_bound_gap_mm=near,
            )
        )
assert sum(len(f.Pads()) for f in fps.values()) == 245
record = json.loads(Path("docs/checkpoints/20260930_connector_k1.json").read_text())
assert k.Version() == "9.0.2"
assert len(rows) == len(record["native_xy_screen"]) == 6
for actual, retained in zip(rows, record["native_xy_screen"]):
    for key in ("header", "item", "nearest_other_courtyard"):
        assert actual[key] == retained[key]
    assert all(
        math.isclose(a, b, abs_tol=1e-6)
        for a, b in zip(actual["bbox_mm"], retained["bbox_mm"], strict=True)
    )
    assert math.isclose(actual["lower_bound_gap_mm"], retained["lower_bound_gap_mm"], abs_tol=1e-6)
print(json.dumps(rows, indent=2))
```

## 5. Evidence and exit

Test-only `382173ca55047bf5fd430aa7f60fd3b432293571` produced two actual ordinary
failures before migration: old header selection and old planning totals. The
focused baseline/graph/CSV selection then passed127tests+7subtests after the
change. New frozen XML/CSV were exported with actual KiCad9.0.2; comparing their
parsed graph to the old fixture shows only the two header Value/MPN fields
changed. Nets, pin functions/types and every other part record are identical.
The PCB is exactly the preceding bytes after reversing those four field edits:
no copper, fill, pad or geometry change is hidden in the new board hash.

The coding model and intentionally wrong coding/oversize-bore records are
analysis controls, not new project tests or built interlocks. Local/native and
hosted final-head gate results are recorded separately on the PR; a source-load
or fixture export is not a fresh DRC run. Reference PDFs are not dependencies;
their URLs, revisions, capture dates and hashes are retained. Two initially
guessed HTSW filenames and configured product HTTP requests failed; the actual
manufacturer-linked drawing/footprint URLs were then captured. Web PDF screenshots
failed for those two drawings; captured bytes were rendered locally and read.

**Next: dimensioned keyed carrier/cartridge CAD**, including the raised C33
clearance, actual socket capture/engagement and cable strain relief; then the
remaining powered-off console/interface decision. The HTSW source migration
is already done and must not be repeated. Factory process/hole acceptance,
cable configuration/termination quote, fit/force tests, capacitor#48, stackup,
E1 fixture/noise and upstream coupling remain explicit release conditions.
No purchase, fabrication, powered connection or body use is authorized.

## Primary references inspected 2026-09-30

[1] Exact HTSW identity: https://www.samtec.com/products/htsw-110-07-t-d
[2] HTSW/TSW catalog: https://suddendocs.samtec.com/catalog_english/htsw_th.pdf
[3] HTSW series print BQ, sheets1,2,3,6: https://suddendocs.samtec.com/prints/htsw-xxx-xx-xxx-x-xx-xx-xx-mkt.pdf
[4] HTSW recommended land B, sheet1: https://suddendocs.samtec.com/prints/htsw-xxx-xx-xxx-x-xx-xx-xx-footprint.pdf
[5] IDSD catalog: https://suddendocs.samtec.com/catalog_english/idsd.pdf
[6] IDSX assembly AE, sheets1,2: https://suddendocs.samtec.com/prints/idsx-xx-x-xx.xx-xxx-xxx-mkt.pdf

Manufacturer nominal/REF dimensions and family processing statements do not
constitute job-specific dimensional, force or solder-process approval. The
carrier geometry and budgets above are engineering selections made here.
