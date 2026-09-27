# Rev A footprint review: pin geometry checked, assembly decisions still open

**Review date: 2026-09-27.** This is the footprint subset of issue #45 after
merged PR #46. The nine distinct footprint definitions cover 68 daughterboard
instances (60 fitted, eight DNP); MOD1 remains off-board. Their unique pad sets
contain 102 pads. Those are not the 256 terminals of the full schematic graph.
No footprint, component, BOM, schematic connection, firmware or rail is changed
by this slice. All review, fabrication/purchase and body-use gates remain false.

## Decision and evidence classes

The old native gate only hashed installed footprint files. A familiar filename
could therefore conceal renumbered pads, reversed polarity, wrong copper side,
an undersized hole or collapsed land while the schematic graph stayed correct.
The gate now validates the installed pad definitions before accepting their
hashes. It reuses the existing bounded read-only token reader and package IDs.

Keep three different statements separate:

1. **Manufacturer package evidence:** numbered terminals, pitch, body/lead
   dimensions and marking from the specific drawings listed below.
2. **Inspected library geometry:** exact pad coordinates, sizes, layers, holes
   and round-rectangle shape in Debian `kicad-footprints 9.0.2-1`. These are the
   values frozen by the regression checker, not manufacturer tolerance limits.
3. **Assembly qualification:** land-pattern choice, tolerances, finished plated
   holes, mask/stencil, solder process and mechanical mating. This is NOT done.

A green check establishes statement 2, supported by the pin/package comparison
in statement 1 where evidence is available. It does not establish statement 3.
In particular, the two KEMET, two SOT and connector examples below differ from
the installed choices. They are explicit pre-fabrication decisions, not errors
silently waived and not proof that every alternative IPC land pattern is wrong.

## Installed geometry (millimetres, local front/top-view coordinates)

X increases right and Y down. The coordinate frame is the footprint's local
frame, not final board placement. Root orientation is front copper. All SMD
pads use front copper/mask/paste and round rectangles. The through-hole header
uses all copper/mask layers, pad 1 rectangular and the remaining pads circular.

| Existing library ID | Inspected pad geometry |
|---|---|
| `Package_QFP:TQFP-64_10x10mm_P0.5mm` | 64 pads, 0.50 pitch; side centres at ±5.6625; along-side centres −3.75 through +3.75; lands 1.475 radial × 0.300 tangential. No exposed pad 65. |
| `Package_TO_SOT_SMD:SOT-23-5` | Pads 1/2/3 at X=−1.1375, Y=−0.95/0/+0.95; 4/5 at X=+1.1375, Y=+0.95/−0.95; lands 1.325 × 0.600. |
| `Package_TO_SOT_SMD:SOT-23` | Pads 1/2 at (−0.9375, −0.95/+0.95); pad 3 at (+0.9375, 0); lands 1.475 × 0.600. |
| `Capacitor_Tantalum_SMD:CP_EIA-3528-21_Kemet-B` | Pad 1 at (−1.54, 0), pad 2 at (+1.54, 0); lands 1.340 × 2.390; inner gap 1.740. |
| `Capacitor_Tantalum_SMD:CP_EIA-7343-31_Kemet-D` | Pad 1 at (−3.12, 0), pad 2 at (+3.12, 0); lands 2.070 × 2.590; inner gap 4.170. |
| `Connector_PinHeader_2.54mm:PinHeader_2x10_P2.54mm_Vertical` | Odd/even columns at X=0/2.54; ten rows at Y=0 through 22.86 in 2.54 steps; copper 1.700 × 1.700; drill 1.000. |
| `Resistor_SMD:R_0603_1608Metric` | Centres at (±0.825, 0); lands 0.800 × 0.950; inner gap 0.850. |
| `Capacitor_SMD:C_0603_1608Metric` | Centres at (±0.775, 0); lands 0.900 × 0.950; inner gap 0.650. |
| `Capacitor_SMD:C_0805_2012Metric` | Centres at (±0.950, 0); lands 1.000 × 1.450; inner gap 0.900. |

Round-rectangle ratios are 0.25 except KEMET B=0.186567 and D=0.120773.
The comparison's 0.000001 mm tolerance accommodates numeric representation;
it is **not a manufacturing allowance**. Graphics, 3D models and courtyard
clearance are not inferred from this copper check.

## Manufacturer comparison and remaining decisions

### ADS1299-4PAGR / PAG-64

TI's PAG drawing [1, PDF page 81, drawing 4040282/C] gives 64 leads at 0.50 mm
pitch, 7.50 mm span between the first/last centres of a side, 9.80–10.20 mm
body sides and 11.80–12.20 mm overall lead span. Lead width is 0.17–0.27 mm;
lead-foot length is 0.45–0.75 mm. The installed 16-per-side pitch and numbering
match after rotating the manufacturer's top view into the library frame.

In that library frame, pins 1–16 run down the left, 17–32 across the bottom,
33–48 up the right and 49–64 across the top from right to left. The pin-one
triangle/chamfer is at the upper-left. The existing schematic checker separately
binds each pad number to its ADS function. There is no exposed thermal pad.

The installed radial lands extend from 4.925 to 6.400 mm from the centre.
This arithmetic describes copper, not a solder-fillet tolerance study. The TI
outline inspected here does not prescribe that exact 1.475 × 0.300 land.
Keep solder-mask web, stencil and placement tolerances open for the assembler.

### TPS7A2033PDBVR / DBV-5

TI [2, PDF pages 56–57, DBV0005A 4214839/K] gives 0.95 mm adjacent pitch,
1.90 mm outer-pin span and numbered top-view leads. The installed 1/2/3 and
4/5 arrangement agrees with the DBV pad roles already checked in the graph:
IN=1, GND=2, EN=3, NC=4, OUT=5. It must not be substituted with another SOT-23
regulator's pin order merely because the body looks similar.

TI's example lands are **1.100 × 0.600 mm**, with **2.600 mm opposing-row
centre spacing**. KiCad uses **1.325 × 0.600** and **2.275** respectively.
These are different patterns. TI's drawing notes that IPC alternatives may
exist; this review neither changes to its example nor approves the installed
alternative. Choose and document the actual assembly land/process together.

### BAV199,215 / SOT23

Nexperia Rev. 4 [3, pages 1 and 5–6] identifies terminals 1=A1, 2=K2 and
3=K1/A2. Rotating its top view into the library frame preserves those identities;
a mirror does not. The package's paired-terminal pitch is 1.90 mm. Body length
is 2.8–3.0 mm, width 1.2–1.4 mm and overall transverse span 2.1–2.5 mm.

The reflow example uses copper lands **0.700 × 0.600 mm**, with 2.000 mm
opposing-row centre separation, whereas this generic KiCad footprint uses
**1.475 × 0.600** and 1.875 mm. Do not confuse the example's smaller paste
aperture with its copper land. This is another explicit process/land decision.
Eight packages remain DNP, which does not excuse an incorrect future pin map
and does not qualify the optional diodes as protection.

### T491B226K016AT / T491D107K016AT

KEMET's T491 drawing [4, printed page 4] gives B-body dimensions
3.5±0.2 × 2.8±0.2 × 1.9±0.2 mm and D-body dimensions
7.3±0.3 × 4.3±0.3 × 2.8±0.3 mm. The body stripe identifies the positive
terminal [4, page 15]. In the installed library this is pad 1 on the left;
the schematic requires pad 1 at VREFP or VCAP1 and pad 2 at its return. That
positive marking must remain clear after board rotation and assembly printing.

For a direct comparison with **density level B, nominal** in KEMET Table 2,
L is each land's length along the two-pad axis, W is transverse width, and S
is the inner gap (not centre spacing):

| Case | KEMET nominal L × W; S | Installed KiCad L × W; S | Installed minus nominal |
|---|---|---|---|
| B / 3528–21 | 1.800 × 2.230; 1.120 | 1.340 × 2.390; 1.740 | L −0.460; W +0.160; gap +0.620 |
| D / 7343–31 | 2.370 × 2.430; 3.870 | 2.070 × 2.590; 4.170 | L −0.300; W +0.160; gap +0.300 |

The installed patterns are not identical to any of that table's A/B/C rows.
Do not call them KEMET's nominal recommendations just because their names say
Kemet-B/D. Nor does this comparison alone prove they cannot be soldered.
**Before fabrication, choose a documented land strategy with assembly input:**
use the selected manufacturer's applicable pattern or justify a different one
with component/placement/process tolerances. A later reviewed change must update
the actual footprint, geometry regression and source evidence together. Do not
change the 100 µF/22 µF components or circuit to hide a footprint decision.

### Samtec TSW-110-07-T-D / 2×10 header

Samtec's exact-family print and footprint [5] give 2.54 mm pitch in both axes,
0.025 inch (0.635 mm) square posts and a **0.040 inch / 1.02 mm** recommended
board-hole callout. KiCad's nominal drill is **1.00 mm** and its chosen copper
pad is 1.70 mm. The 0.02 mm difference is visible; finished-hole/plating and
fabricator tolerances have not been qualified by comparing those nominal values.

This is an unkeyed strip. Its package drawing does not establish our electrical
pin-one assignment or a mating cable's cavity numbering. The square KiCad pad 1
and existing board-qualified harness establish the intended numbering. Board
rotation, mating-face mirroring, connector length/clearance and a qualified mate
remain open. Never infer cable pin order from a solder-side view.

### Yageo RC0603 and Murata GRM chip components

The Yageo RC-group drawing [6, page 4] gives RC0603 a 1.60±0.10 × 0.80±0.10 mm
body, 0.45±0.10 mm height, and terminal lengths 0.25±0.15 mm. That covers the
selected resistor family. An exact manufacturer land recommendation was not
established from that sheet; the installed 0.800 × 0.950 lands remain an
inspected generic-library choice. Swapping the two equivalent resistor pads
is harmless; collapsing or moving their copper is not.

Murata's exact reference sheets for GRM1885C1H472JA01 and GRM188R61E105KA12
[7] were retrieved as text: each gives 1.6±0.1 × 0.8±0.1 mm body dimensions.
The PDF images/land tables could not be reliably retrieved in this session.
Exact mechanical sheets for GRM1885C1H152JA01, GRM188R71H104KA93 and
GRM219R61A106KE44 were not successfully obtained. **Do not extrapolate those
missing thickness, terminal or land details from a package prefix or a
partially parsed table.** The 0603/0805 library copper is regression-checked,
but this is not a completed exact-MPN MLCC assembly review. Obtain the missing
manufacturer drawings before resolving that portion of #45. No procurement or
lifecycle conclusion is inferred from a distributor listing.

## Executable checks and measured blind spots

`uv run --locked python -m tools.check --native --schematic` uses the existing
orchestrator. The footprint reader runs on the actual installed files inside
`schematic_source_snapshot`, before they are hashed. Its implementation joins
the before/after source snapshot (44 inputs for this revision). The inherited
firmware route proof, ERC, complete graph, BOM and symbol-cache checks remain.
No new registry, runtime download, CAD generator or dependency is introduced.

The fixture sources are unmodified KiCad files, individually gzip-compressed
with zero timestamps. The collection retains KiCad's attribution/license.
They are ordinary-test fixtures, never a substitute for the installed library.
Nine actual CLI tests load and export the installed footprints to SVG and compare
their parsed pads with the frozen fixture. The native exports were inspected;
no physical package or board was measured.

Two additional native controls shrink a VCAP land and a header drill in copied
installed libraries. Each still produces a zero-violation schematic ERC report
and a valid XML graph, then fails the new geometry snapshot. They demonstrate
why schematic connectivity alone is insufficient for this particular fault.
Canonical files still pass. Wrong numbered pads, layers, sizes, drills,
polarized reversals, missing/duplicate fields and unsupported copper overrides
are rejected. A sweep renumbers all 102 pads one at a time; none is optional.
Benign nonpolar swaps, whitespace/numeric spelling and equivalent rectangle
quarter-turns remain accepted. This is finite fault testing, not exhaustive
code mutation coverage or manufacturing certification.

The read-only parser deliberately fixes the inspected local frame and pad
shape vocabulary. Whole-definition rotations or additional pad features need
explicit review, even if a human believes them equivalent. Silkscreen contents,
3D-model accuracy, courtyard adequacy, final-board orientation and assembly
process are not automatically checked. Future placement/DRC must independently
preserve the schematic and include the actual package and mating review.

## Primary source register

[1] TI ADS1299 SBAS499C, package appendix: PAG S-PQFP-G64, 4040282/C 11/96;
PDF page 81 (one-based). Drawing visually checked.
https://www.ti.com/lit/ds/symlink/ads1299.pdf

[2] TI TPS7A20, DBV0005A 4214839/K 08/2024: package and example board layout,
PDF pages 56–57 (one-based). Both drawings visually checked.
https://www.ti.com/lit/ds/symlink/tps7a20.pdf

[3] Nexperia BAV199 Rev. 4, 1 April 2023, pinning and package/reflow drawings,
pages 1 and 5–6. Drawings visually checked; not physical measurement.
https://assets.nexperia.com/documents/data-sheet/BAV199.pdf

[4] KEMET/Yageo T2005_T491, printed page 4 dimensions and page 15 Table 2/marking.
Retrieved version has mixed page footers: the dimension page says 4/28/2025;
the land table says 2026-07-08. Both tables and polarity text visually checked.
https://content.kemet.com/datasheets/KEM_T2005_T491.pdf

[5] Samtec TSW-110-07-T-D exact product page and its linked family drawings:
marketing print sheet 1 and recommended footprint sheet 1, visually checked.
https://www.samtec.com/products/tsw-110-07-t-d
https://suddendocs.samtec.com/prints/tsw-xxx-xx-xxx-x-xx-xxx-mkt.pdf
https://suddendocs.samtec.com/prints/tsw-xxx-xx-x-x-xx-xxx-footprint.pdf

[6] Yageo RC-group datasheet, Nov. 14, 2025, V14, page 4 dimensions, visually
checked. This source supplies component dimensions, not an approved PCB land.
https://yageogroup.com/content/datasheet/asset/file/PYU-RC_GROUP_51_ROHS_L

[7] Murata exact reference specifications, page 1 dimensions, text extraction
only (2016 reference sheets); image/land-table verification remains incomplete.
https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM1885C1H472JA01-01.pdf
https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM188R61E105KA12-01.pdf

Primary drawings govern the comparison above. Older research's VREFP-to-DVDD,
BIAS and generic capacitor recommendations are not used to redesign this circuit.
Issue #45 also retains actual interface/board identification and powered-off
qualification. None of this authorizes connecting a person or purchasing a PCB.
