# S4: named serial setup and conditions for using vendor limits

**Result:** the existing worksheet can use a conditional ADC-regulator interval
of **3.2505–3.3495 V**, but the installed conditions needed to justify that interval
are unverified. It is NOT written into the default physical-input template.
Controller and exported-rail operating-current ceilings, source regulation,
common-pair resistance and ground offsets remain unknown. This is a concrete
component-evidence result and an identified setup blocker, not completed power
qualification. No board, circuit, firmware, cable, part or permission changed.

Use [the existing S3 worksheet](REV_A_SUPPLY_ACCEPTANCE_S3.md), not a new solver.
The evidence record is `studies/s4_serial_evidence.json`. Seven input hashes bind
it to the actual firmware/build selection, component records and unchanged S3
worksheet. The source snapshot also includes this note, record and their tests.
The mandatory [GitHub runbook](REPOSITORY_PUBLICATION.md) remains in force.

## One named setup, not every possible operating mode

`rev_a_f1_serial_internal_250` means the selected four-channel ADS1299-4, gain24,
internal test mux, internal reference and clock, nominal250SPS, mode1/1MHz SPI,
F1 handshake and serial output through the C1 header-UART path. The selected
build has8MB flash and OPI PSRAM. `USE_WIFI_UDP=false` means the sketch does not
enter its Wi-Fi initialization branch. It does NOT establish a measured radio,
CPU, memory or peripheral power state or make their current zero. No CPU-clock
measurement exists. The distributed `BOARD_PROFILE_REVIEWED=false` build still
halts before acquisition: this is a conditional future steady state, not a
recording that has been performed or an instruction to enable it.

The controller is externally powered at its5V header; neither DevKit USB is
connected under the existing C1/F1 constraints. The ADC digital regulator is
separate from the controller regulator. The reviewed C4 feed/sense distinction
and shared source/return identities from S2/S3 remain unchanged. Startup,
reference charging, network mode, stalled I/O, partial rails and faults are
outside the steady-state current question and still need separate bounds.

## What primary evidence establishes

### ADC regulator: use the correct row, not the dropout headline

For TPS7A2033PDBVR (DBV), TI specifies ±1.5% accuracy for input **3.6 V to6 V**,
output current **1 mA to300mA**, and junction temperature−40..125°C. The table's
defaults include1V enable and1µF input/output capacitors. Stability, effective
capacitance/ESR, enable, input/load range and thermal conditions must be checked
for the actual assembly. The **145mV** DBV dropout limit is tested at300mA with
output at95% of nominal; it is not the accuracy row's headroom requirement. [1]

Arithmetic:3.3×(1±0.015)=[3.2505,3.3495]V. This leaves **250.5 mV** to either
edge of the existing3.0–3.6V C3 ANALYSIS window at the regulator pins. Remote
feed loss and signed ground differences still apply; this is not spare allowance
already granted to the cable. Do not add typical line/load regulation on top of
a limit already covering the stated line/load range as though independent.

The minimum load is a real applicability question. An ADS typical current plus
S2's external-only mean is not a proven minimum or maximum total U2 output current.
A small mean cannot establish instantaneous compliance with the load range either.
Do not add a bleeder, raise the source or change a component to satisfy this row
without a separate reviewed design decision. Effective capacitance under bias,
stability and junction temperature remain subject to the existing #48/stackup
work, not inferred from nominal capacitor labels or ambient temperature.

### Controller: capacity and typical benchmarks are not bounds

The module datasheet lists0.5A as minimum external supply capability, **not a maximum**
load current. Its modem-sleep table has two TYPICAL columns (peripheral clocks
disabled/enabled), and warns that embedded PSRAM and flash activity can increase
consumption. Neither a typical row nor500mA can fill total operating/peak fields. [2]

The official v1.1 board drawing identifies an **SGM2212-3.3XKC3G/TR**, not a generic
AMS1117. It also shows CP2102N VDD, the power indicator and RGB device connected
to the3.3V supply. Removing USB does not physically disconnect these loads. This
identifies terms to account for; it does not claim their operating currents or
that the user's uninspected board necessarily matches the drawing. [3]

The controller branch must include the module/memory, real DevKit overhead,
regulator ground current and the exported MCU-side auxiliary loads (including
the reverse data outputs and C1 target side). Do not add the host-side isolated
supply to the target source, or power the controller from ADC DVDD. Confirm the
actual DevKit revision/component population before applying vendor-part limits.

### Exported DVDD: no-load current does not cover loaded switching

The TXU0304 combined6µA limit is for static rail-level inputs with zero output
load over−40..125°C. It is not a bound for this clocked, cable-loaded setup. [4]
S2's calculated output-resistor and external charging contributions remain useful
partial terms, but cannot replace internal dynamic current, input leakage,
bleeds, receiver current, real capacitance and branch-return accounting. No
complete active or peak current ceiling has been established from these tables.

## How the conditional interval is exercised without granting a pass

The tests create a TEMPORARY copy of S3's template and fill only its `regulator`
term with the conditional interval. They execute the ORIGINAL S3 calculation in
normal Python, `-O`, and `PYTHONOPTIMIZE=1`; they do not implement another voltage
solver. All eight results remain indeterminate: remote supply still needs feed
and ground terms, and analog/MCU/source quantities remain unknown. The committed
21-term S3 template stays entirelynull, its qualification flag staysfalse, and
no measurement record is inserted. Any later evidence-backed population needs
its own conditions, assembly identity, uncertainty and review.

Run from the repository root in the pinned environment:

```sh
uv run --locked python -m pytest tests/test_steady_source_s4.py -q
```

These are source/data and process regressions, not physical experiments. The
JSON is a reviewed evidence note, not an instrument-input or approval API.
Source hashes establish which files were inspected, not accuracy of a measurement.

## The next missing input is identifiable

No actual regulated bench source model, lead set or current-measurement instrument
is identified in the project. The nominal5V/1A target is not a bought or measured
source. To replace `source_error`, identify the source and its specified settings,
load/temperature domain, accuracy and regulation; to replace `common_pair`, also
identify the outgoing AND return leads/interfaces and defensible current range.
A source model alone cannot close the whole worksheet, but without it there is
no applicable source accuracy/load-regulation specification to import.

**Next: obtain the user's actual bench-source model (or confirmation it is not
chosen), then map its stated accuracy/load-regulation conditions into the EXISTING
S3 record.** Do not launch another generic accounting framework or repeat this
manufacturer search. Prepare unsent vendor questions only as needed. For the
unbounded controller/exported currents, obtain condition-matched manufacturer
limits or a separately reviewed empirical envelope; never relabel a capacity,
current-limit setting or typical measurement as the operating maximum.

No procurement or powered measurements are authorized. Proposed four-wire work
still applies only to detached passive harnesses after current/compliance/fixture
review; meters inject current. All #45/#48, reference-gap, mechanical, budget,
purchasing, fabrication, powered-connection and body-use restrictions remain.

## Primary references

Page images were inspected on2026-10-07. References are to the exact described
revisions/rows; datasheet PDFs are not redistributed or required at test runtime.

[1] TI TPS7A20 SBVS338H (July2024), pp5–6, especially DBV accuracy vs dropout rows:
https://www.ti.com/lit/ds/symlink/tps7a20.pdf

[2] Espressif ESP32-S3-WROOM-1/1U v1.8, pp27/29, tables6-2/6-6 and footnotes:
https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf

[3] Espressif ESP32-S3-DevKitC-1 v1.1 schematic,20221130, sheet2:
https://dl.espressif.com/dl/schematics/SCH_ESP32-S3-DevKitC-1_V1.1_20221130.pdf

[4] TI TXU0304 SCES935A (November2021), p8, combined supply-current conditions:
https://www.ti.com/lit/ds/symlink/txu0304.pdf
