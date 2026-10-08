# L3: choose an internal-test-only pilot, not an external-input qualification

2026-10-08. Source: main `ea853b338ebe6b79f01d283244eec77faebc64f4`,
tree `df5b2668f8aca78754d71c1207e97634317ae0c0` (merged L2/PR95).

**Decision: retain the six upstream net-pair geometries in the proposed first
internal-test pilot instead of making a combined analog reroute now.** This is
an explicit, restricted design proposal for the later release decision. It is
NOT a fabrication release, an accepted external-input design, or authority to
change a hardware/firmware gate. The finished pilot may require another PCB
revision before it can meet E1. No money, order or future performance is committed.

This closes the choice between immediate analog rerouting and a bounded pilot
proposal for this group; do not reopen that same choice each turn. The later
manufacturing decision must explicitly accept this restricted purpose and its
possible rework/revision cost. Until then the proposal is not applied authority.
#45/#48, the actual stack/process and L2's digital-channel disposition remain open.

## 1. Exact scope: six electrical pairs at nine locations

A fresh read-only centreline check of the current authored AFE reproduces the
existing positions. Repeated authored segments produce 18 raw pair hits but
only the nine distinct coordinates below. This is not a new native refill,
field extraction, capacitance calculation or measurement.

| B.Cu net | In2.Cu net | Distinct crossing coordinates, mm | Pilot disposition |
|---|---|---|---|
| CH3P_DUMMY | CH2N_DUMMY | (19.70,40.80) | Retain only within the restricted scope below |
| CH3N_DUMMY | CH2N_DUMMY | (19.70,37.10) | Same |
| CH4N_DUMMY | CH2N_DUMMY | (19.70,39.60) | Same |
| CH3P_DUMMY | AVDD | (20.50,40.80), (24.90,38.45) | Same; supply coupling is not disabled by the mux |
| CH3N_DUMMY | AVDD | (20.50,36.95), (24.90,33.15) | Same |
| CH4N_DUMMY | AVDD | (20.50,39.60), (24.90,35.50) | Same |

These are before R1-R8, not the already-repaired filtered DNP branches.
The implicated connector identities are J2.4/CH2N, .5/CH3P, .6/CH3N and .8/CH4N;
all eight J2 input paths still have their own 4.99k series resistor to the ADC.
In1 ground is above both B and In2, not between them. Nominal centreline crossings
are not shorts and cannot establish actual coupling magnitude or its absence.
The earlier native projected areas and hypothetical injection models remain in
`REV_A_UPSTREAM_COUPLING_DISPOSITION.md` with their original source/limitations.
Do not assign a guessed pF per crossing or repeat those simulations to claim a pass.

AFE PCB SHA256 remains
`60097ff4acf8408d5a172930de74bcd36aa50a379dd30a831e4bc64d3841c8a6`.
No route, footprint, component, rule, pending-reference outline or threshold changes.
The previous blind B-to-F layer-swap experiment already failed DRC; it rules out
that shortcut, not the feasibility of a carefully redesigned combined route.

## 2. Why this pilot can answer a useful question without answering E1

TI's mux drawing and register table separate the normal external input from
internal test and input-short selections [1, pp20-21,50]. The existing sketch
has these paths already; this proposal adds no new firmware mode.

| Existing source selection | Register consequence | What it exercises / does not establish |
|---|---|---|
| `USE_INTERNAL_TEST=true` | CONFIG2=0xD0; CH1-4SET=0x65: powered channel, gain24, SRB2 open, MUX=101 | Generated internal test through PGA/ADC/readout; not the J2/R-C external transfer |
| Existing alternative `USE_INTERNAL_TEST=false` | CONFIG2=0xC0; CH1-4SET=0x61, MUX=001 | Internal input-short diagnostic, not external acquisition and not a substitute for E1 |
| Distributed `BOARD_PROFILE_REVIEWED=false` | Setup stops before reviewed controls/acquisition | No physical test has run; this flag is not changed here |

CONFIG3=0xE0 retains the internal reference with BIAS disabled; lead-off settings,
bias/sense masks and MISC1/SRB1 remain zero as in the current sketch. Register
writes use its existing readback checks before RDATAC/START. Readback expresses
an intended configuration; it does not independently prove fault-free silicon,
continuous register integrity or a safe real assembly.

The selected internal test is downstream of the external selection switches,
so it does not traverse the six external trace pairs. B1 separately terminates
J2.1-8 and .10 at its inspected, enclosed common point; .9 BIAS and .11-20 remain
individually isolated. There is no independently driven external aggressor in
this proposed setup. This is a topology/scope rationale, NOT a quantified noise
reduction. The finite wire/return impedance, input protection, off-switch parasitics,
pads, package, shared rails and reference can still couple disturbances. AVDD
is still an active supply. Its startup/ripple/ground behavior must remain within
the applicable B2/S3 and release conditions; no deliberate supply injection here.

**Internal test is not an electrical isolation barrier.** It does not protect
external pins from overvoltage, permit an unpowered input source, make BIAS safe,
replace the B1 low-input precondition, or make SPI edges and partial-rail faults
irrelevant. Keep B1 fitted through reviewed shutdown/discharge. No special credit
for low B1 impedance is taken from the old hypothetical 5k/50k source examples.

## 3. Explicit boundary of the proposed pilot

The intended result is a person-disconnected demonstration of reviewed startup,
reference/conversion operation, configuration, four-channel framing and transport
using the generated internal test. Use the existing B2 run card and fault handling.
Do not introduce another capture schema or a parallel commissioning checklist.

| Required restriction | Consequence if absent or changed |
|---|---|
| Inspected J2-only B1, intact return/joints, BIAS/spares isolated; no external source, electrode or person | HOLD; restore the accepted fixture and assess the fault, not a live replacement |
| Existing internal test selection, gain24/250SPS nominal, internal reference/clock, BIAS/lead-off/SRB off and serial-only mode | Changed mux, source or excitation withdraws this disposition; a new review is needed |
| Actual stack, assembly, component, power and digital-channel decisions accepted at their existing stages | This analog scope choice cannot substitute for any of those decisions |
| Receiver/rail observations and existing startup/STOP/full-run invalidation requirements retained | Bad/missing evidence remains a fault or HOLD, not an acceptable pilot artifact |
| First build described as internal-test-only, with external performance unqualified and possible later PCB revision | Do not describe it as a usable EEG front end or promise E1 results from it |

A good square wave does not verify external channel order (B1 commoning and the
shared test generator hide permutations), J2-to-ADC gain/CMRR, the 4.7nF filter,
external input noise, all digital bits, or this board's fault response. Preserve
raw failed/invalid runs; do not normalize or filter away evidence to produce a
success story. This note selects no new amplitude/noise acceptance number.

## 4. What remains required for any external dummy-input claim

E1's existing requirements remain intact in `REV_A_STACKUP_BENCH_REQUIREMENTS.md`:
1-10k per-leg calibrated sources; 1-40Hz performance band; 0.50uV RMS total-noise
limit; 0.50uV-peak coherent total with its separate class allocations and uncertainty.
The input-channel and AVDD allocations are respectively 0.20 and 0.10uV peak;
they are not allowances per crossing. This is not a newly weakened E1 target.

Before changing to any normal external-input acquisition, require its own reviewed
source/startup protection and declared stack/geometry. Then either qualify the
unchanged board under the complete E1 conditions, or perform a combined repair
and requalify. Include reciprocal CH2N-to-CH3/CH4 tests, AVDD/internal shared paths,
P/N mismatch, simultaneous aggressors and the existing alias/floor controls.
Internal-short or internal-test success cannot be carried across as that evidence.
A new fixture, stack or analog route requires reconciliation; this is not blanket
permission to treat future geometry as equivalent.

Do not make E1 measurements a condition for merely preparing this restricted
pilot, but do not defer an actual component/insulation/rail hazard into a powered
experiment. First-power energy/current/ramp/abort limits and physical instrument
acceptance are still prerequisites, not things to discover without bounds.

## 5. Next concrete build step, not another analog study

Carry this restricted-purpose proposal into the eventual release decision. The
next independent source decision is **L2's SPI damping/rework provision at the
actual drivers**, starting at U102's clock output and the ADC's DOUT source.
Inspect physical access and choose either a credible, supported rework method
or minimal series-footprint provision before fabrication. A resistor before a
re-driving buffer does not damp the new edge it creates; no universal value is
selected by L3. Assess the other L2 paths with the same driver-based distinction.

Use the existing L2 timing conditions and B2 observation requirements. Do not
repeat timing arithmetic, L1's tiny edge inventory, B1-B3, capacitor-family
selection, RFQ drafting or price searches. Any actual BOM/CAD/contract change
needs one consistent reviewed revision and targeted failure-first regressions;
this paper scope decision needs no production refactor or new test framework.

## Evidence and approval status

Local source inspection matched all 251 AFE net-labelled pads to the frozen
native netlist and checked all eight J2-to-resistor-to-U1 paths. Exact rational
segment intersections reproduce the six-pair/nine-location inventory above.
The selected source register values and unchanged Q1 input/schedule hashes were
checked. These are authoring controls, not new project tests, native CAD runs,
extracted parasitics or physical experiments. Current-head CI/review, if completed,
are recorded in the PR, not inferred from these checks or earlier green results.

[1] TI ADS1299-x, SBAS499C (January2017), input mux Figure18 pp20-21,
CONFIG2 Table14 p47, CHnSET Table17 p50. Page images20,47,50 inspected on
2026-10-08: https://www.ti.com/lit/ds/symlink/ads1299.pdf

Moscow planning/no detailed price research retained. No supplier contact, purchase,
fabrication, fixture construction/mating, powering, external acquisition or body
use authorized. All software/hardware gates stay unchanged; #45/#48 stay open.
