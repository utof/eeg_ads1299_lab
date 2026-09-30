# Rev A input geometry and conditional coupling review

**Reviewed source:** main `5197c5b9478391e305c5d41f6c992bbdcd6bfd56`,
tree `eecf9efb62f13d2cbda4d3815bed3de05a231fb6`, after merged output-repair PR #64.
Authored board SHA256:
`232b7c68a63ae13aebcf71f8c0b1f210421c30452a1afc7b7c86dc1c118b23a3`.
This review changes no copper, circuit, component, dependency or approval gate.
The geometry record is `checkpoints/20260930_input_geometry.json`.

## Finding and bounded next action

**Preserve the front-layer resistor/filter-to-ADC fanout. Rework the CH1N_DUMMY
corridor first to remove its three unshielded cross-channel overlaps with the
IN2P/IN3P/IN4P branches to DNP diode pads.** Prefer an F-layer corridor over In1,
subject to native clearance and neighboring-route review. This is a layout
improvement recommendation, not a measured crosstalk failure. Do not add arbitrary
length-matching meanders, delete the DNP connections, change the input network,
or disturb the AVDD1 and MISO/DRDY repairs to meet a simplistic length target.

The planned exit condition is an intact CH1N connection with no such cross-channel
B/In2 overlap, no new unreferenced long corridor, preserved sensitive main paths,
and fresh refill/parity/DRC. First reproduce a focused geometry-policy failure;
then repair and challenge it with a connected-but-wrong-layer copy and benign
edits. Do not create a general field solver or approval framework for this slice.
Other upstream overlaps and the branch imbalance remain explicit follow-through,
not implicitly fixed by repairing CH1N alone.

## Separate the main path from electrically connected branches

The 16 input-related nets contain 134 segments and 22 vias. Eight are upstream
CHnP/N_DUMMY nets; eight are filtered INnP/N nets. All eight **main R-to-C-to-ADC
itineraries are F.Cu, with no intervening vias**. Each R output to differential
capacitor terminal is 2.425 mm of 0.20-mm track. The capacitor-to-U1 fanout uses
0.15-mm tracks. Each C1-C4 bridges P to N; none is a fitted shunt to ground.
The selected circuit remains 4.99 kohm per leg and 4.7 nF differential C0G.

| Channel | Upstream P / N authored sums, mm | Upstream P / N vias | Main R-to-ADC P / N, mm | C-to-ADC P / N, mm |
|---|---:|---:|---:|---:|
| 1 | 36.295 / 23.479 | 0 / 2 | 11.094 / 10.659 | 8.669 / 8.234 |
| 2 | 33.759 / 22.752 | 0 / 1 | 9.851 / 9.416 | 7.426 / 6.991 |
| 3 | 20.547 / 20.067 | 1 / 1 | 9.416 / 9.851 | 6.991 / 7.426 |
| 4 | 26.853 / 17.302 | 0 / 1 | 10.659 / 11.094 | 8.234 / 8.669 |

Upstream values sum all authored net segments, including overlaps/tails; they
are not shortest conductive lengths. Main columns instead follow explicit
ordered terminal-to-terminal itineraries through the capacitor pad. Neither
metric includes pad spreading, vias' barrels, package or external lead lengths.
Main P/N differences have magnitude 0.435 mm, not the much larger upstream
net-sum differences. This alone is neither analog failure nor parasitic balance.
CH1N/CH2N have In2 segments; CH3P/CH3N/CH4N have B segments. Other upstream
legs are F-only. Layer sums and main-path UUIDs are in the record.

D1-D8 are **not fitted**, but their pad3 connections and branch copper still
exist. From each filtered-net tap via to its diode pad3, the P branch has
8.5125 mm on B plus 1.2 mm on F; N has 4.0125 mm on B plus 1.2 mm on F.
Both use two vias. Thus the off-main branches are 9.7125 versus 5.2125 mm,
a 4.5-mm geometric difference. A duplicate 0.825-mm F segment on the main
connection is not counted again in the branch-only itinerary. DNP does not
mean zero board capacitance, and it does not imply a fitted diode junction.
No diode leakage/protection qualification is inferred.

Fresh native full-width projection of each main F itinerary onto In1 has zero
uncovered area **only after exempting its own net's via clearances**. Before
that exemption the local opening contributes approximately 0.219794 mm2 per
itinerary. Native polygon approximation is 5 um; the own-via mask uses the
0.25-mm zone clearance plus 25 um approximation margin, as in the existing
output screen. This does not erase the physical openings or prove low return
impedance, capacitance matching or whole-route shielding. No unrelated void
is exempted. In1 remains one filled region.

## Cross-layer neighborhood: 13 locations, not 22 independent problems

The copper order is F / In1 GND / In2 routed copper / B. A centreline screen of
all B/In2 segment pairs involving any input net found 22 raw intersections.
Overlapping authored AVDD segments duplicate some coordinates; grouping by
both nets and position leaves **13 distinct locations**:

| B net / branch | In2 net | Positions (x,y), mm |
|---|---|---|
| IN2P, IN3P, IN4P DNP branches | CH1N_DUMMY | (30.475,41.775); (29.5,37.775); (27.125,33.775), respectively |
| CH4N_DUMMY, CH3N_DUMMY, CH3P_DUMMY | CH2N_DUMMY | (19.7,39.6); (19.7,37.1); (19.7,40.8), respectively |
| CH3N_DUMMY | CH1N_DUMMY | (27,33.2) |
| CH4N_DUMMY | AVDD | (20.5,39.6); (24.9,35.5) |
| CH3N_DUMMY | AVDD | (20.5,36.95); (24.9,33.15) |
| CH3P_DUMMY | AVDD | (20.5,40.8); (24.9,38.45) |

In1 fill contains all 13 projected points, but **it is above both B and In2,
not between them**. These are not shorts. The three filtered/unfiltered
cross-channel overlaps are the first rework target; the other four upstream
input overlaps and six supply overlaps stay in the review record. Centreline
crossings are a screen, not a crosstalk extractor: nearby parallel routes,
pads, via barrels, shared supplies and cables can also couple. No dielectric
stackup, edge/source spectrum or measured transfer has been established.

## Conditional imbalance calculation, not PCB parasitic extraction

To quantify why length alone is insufficient, four illustrative passive-network
runs reused `lab.analog.InputNetwork`, `transfer`, `export_spice`, `run_ngspice`.
No production solver, model parameter, expectation or dependency was changed.
These runs study **unequal capacitance to ground**, not the cross-channel mutual
capacitances at the 13 crossings. They must not be used to assign pF to the
4.5-mm branch difference or predict this board's CMRR.

Assumptions: matched source resistance Rs of 5k or 50k ohm per leg; selected
4.99k series resistance; source capacitance zero; matched illustrative 1T-ohm
load; Cn=100pF, Cp=100pF+delta; Cd=4.7nF. A 10mV common-mode AC amplitude is
chosen solely to show scaling. Source/load/C values are not measured electrodes,
board parameters or a silicon input model. No body, BIAS, protection, package,
cable, tolerance/aging, mutual coupling or noise source is modeled.

| Rs per leg | Assumed extra P capacitance | Calculated differential amplitude at 50 / 60 Hz for 10mV common, uV |
|---|---:|---:|
| 5k ohm | 1pF | 0.031371 / 0.037637 |
| 5k ohm | 10pF | 0.313706 / 0.376373 |
| 50k ohm | 1pF | 0.170475 / 0.203400 |
| 50k ohm | 10pF | 1.704729 / 2.033959 |

An independent two-node solution, with s=j*2*pi*f, R=Rs+4990 and q=1+R/1e12,
is:

```text
D = q*q + q*s*R*(Cp+Cn+2*Cd) + (s*R)^2*(Cp*Cn+Cd*(Cp+Cn))
(Vp-Vn)/Vcommon = -s*R*(Cp-Cn)/D
```

All four circuits completed actual ngspice runs on the existing 241-point
0.1-Hz to 100-kHz logarithmic sweep. Formula-versus-existing-solver maximum
absolute error was below 6e-16 V/V; versus native ngspice below 5e-16 V/V.
The table is calculated at exact 50/60 Hz, **not represented as native sample
points**. Balanced-C cancellation and P/N sign-swap controls were checked in
the existing solver across the grid. This is numerical consistency for a
hypothetical lumped network, not fitted or validated physical behavior.

Reproduce with the locked environment and installed ngspice, from the repo root:

```python
from pathlib import Path
from lab.analog import InputNetwork, export_spice, run_ngspice, transfer

for rs in (5000.0, 50000.0):
    for delta in (1e-12, 10e-12):
        cfg = InputNetwork(
            r_electrode_p=rs,
            r_electrode_n=rs,
            c_electrode_p=0,
            c_electrode_n=0,
            r_series_p=4990,
            r_series_n=4990,
            r_input_p=1e12,
            r_input_n=1e12,
            c_common_p=100e-12 + delta,
            c_common_n=100e-12,
            c_differential=4.7e-9,
        )
        directory = Path("reports/input-sensitivity") / f"{rs:g}-{delta:g}"
        frequency, native = run_ngspice(
            export_spice(directory / "input.cir", cfg, "common"), directory
        )
        print(rs, delta, abs(transfer([50.0, 60.0], cfg, "common")) * 10000)
```

## Execution, provenance and remaining decisions

Fresh GitHub-only source capture36696579521 checked out exact5197, verified its
tree/board and retained a source bundle. The local baseline ordinary+schematic
gate passed on that clean source:1091ordinary+14subtests,145KiCad cases,22console
cases,86.06%branches with unchanged71%floor. These22 console cases are part of
the existing98native suite, not22 new unique tests. This baseline command did
not request the complete98native suite or an S3 build. Read this review PR's
live final-head CI/review for later evidence; baseline passes are not later passes.

The native geometry was independently checked against raw forms for all706
track/via items and245pads; eight explicit main paths checked terminal endpoints,
continuity/layers/nets/lengths. All22 raw crossings agreed with an independent
determinant intersection screen and reversal controls before deduplication.
Fresh native refill/DRC on the baseline authored board reported0/0/0,exit0;
canonical schematic ERC0. Four native sensitivity circuits and geometry controls
are analysis evidence, **not added project tests or physical experiments**.

An initial outer20s local command timeout was superseded by the completed
baseline run. An initial two-point linear SPICE sweep returned one row and was
correctly rejected by the existing runner; the four successful runs use the
unchanged default logarithmic exporter. Neither failure is counted as a pass.
No check, timeout policy, tolerance or threshold was relaxed.

Primary basis, inspected including page images: TI ADS1299 SBAS499C pp68,72-73,
https://www.ti.com/lit/ds/symlink/ads1299.pdf . TI favors a differential filter
capacitor to reduce sensitivity to component mismatch and shows partitioned
analog/digital layout and compact input filtering. Its figures are not a
universal millimeter limit or a requirement to split this board's ground.

Keep #45/#48 open. The CH1N/DNP-corridor rework, remaining input/supply overlaps,
parasitic extraction or bounded physical testing, stackup, capacitor lifecycle/
effective-C, mechanics/assembly, actual console/rail-loss behavior and delivered
budget remain unresolved. No purchasing, fabrication, powered connection or
body-use authorization. The missing user-facing PR64 report did not erase its
already-merged copper; do not reapply its authoring scripts.
