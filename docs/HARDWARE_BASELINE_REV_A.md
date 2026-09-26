# Rev A hardware baseline: ADS1299-4 + ESP32-S3 bench daughterboard

**Decision date:** 2026-09-23  
**Base repository commit:** `31205de841c577c373532fbc9d065fa81d0a6ac8`  
**Status:** component and interface baseline for simulation/schematic work; **not** fabrication, purchasing, external-input, or human-connection approval.

## Decision

Use a four-channel `ADS1299-4PAGR` daughterboard connected to an official `ESP32-S3-DevKitC-1-N8R8`. Start at 250 SPS, gain 24, SPI mode 1 at 1 MHz, with the ADS1299 internal 4.5 V reference and internal clock. Use an externally regulated 5 V unipolar analog bench rail and a `TPS7A2033PDBVR` for **ADS DVDD only**; the ESP32-S3 remains on the devkit regulator.

Each differential channel starts with two 4.99 kΩ series resistors and one 4.7 nF C0G capacitor **across INP/INN**. No input-to-ground common-mode capacitors are fitted in Rev A. BIAS starts disabled; reserve 1 MΩ || 1.5 nF feedback plus a separate 1 MΩ output resistor for later dummy-load loop testing. Optional BAV199 steering-diode footprints are DNP initially.

This deliberately resolves the component ambiguity without pretending the hardware is validated. The existing original-ESP32 firmware guard and `BOARD_PROFILE_REVIEWED=false` behavior remain unchanged.

## Exact component baseline

The machine-readable source of truth is [`hardware/rev_a/bom.json`](../hardware/rev_a/bom.json). Planning costs are allowances, not live supplier quotes.

| MPN | Qty | Population | Planning line cost |
|---|---:|---|---:|
| `ADS1299-4PAGR` | 1 | FIT | $45.00 |
| `ESP32-S3-DevKitC-1-N8R8` | 1 | FIT | $15.00 |
| `TPS7A2033PDBVR` | 1 | FIT | $1.20 |
| `RC0603FR-074K99L` | 8 | FIT | $0.64 |
| `GRM1885C1H472JA01D` | 4 | FIT | $1.60 |
| `RC0603FR-071ML` | 2 | FIT | $0.20 |
| `GRM1885C1H152JA01D` | 1 | FIT | $0.35 |
| `T491D107K016AT` | 1 | FIT | $2.00 |
| `T491B226K016AT` | 1 | FIT | $1.20 |
| `GRM188R61E105KA12D` | 15 | FIT | $2.25 |
| `GRM188R71H104KA93D` | 7 | FIT | $0.70 |
| `GRM219R61A106KE44D` | 4 | FIT | $1.40 |
| `RC0603FR-0710RL` | 1 | FIT | $0.08 |
| `RC0603FR-0710KL` | 12 | FIT | $0.72 |
| `TSW-110-07-T-D` | 2 | FIT | $1.80 |
| `BAV199,215` | 8 | DNP | $2.40 |

Fitted components: **$74.14**. Bare-PCB reserve: **$15.00**. Harness/mating reserve: **$3.00**. **Planning subtotal: $92.14**. Optional BAV199 population adds $2.40. Shipping, tax/VAT/import charges, assembly/stencil/setup, tools, bench instrumentation, battery/charger, enclosure, and any patient-safety hardware are excluded. Obtain one delivered basket/assembly quote before purchasing.

## Electrical contract

### Input network

```text
source P -- 4.99k --+---- ADS INxP
                     |
                   4.7 nF C0G
                     |
source N -- 4.99k --+---- ADS INxN
```

For an ideal zero-impedance differential source, the analytical pole is:

`1 / (2*pi*(4.99k + 4.99k)*4.7nF) = 3393.06 Hz`.

That is an RFI-network reference calculation, not an EEG passband specification and not a SPICE result. Electrode/source impedance and mismatch must be swept explicitly.

### Power

```text
regulated 5.0 V bench source
  +-- 10 ohm RC feed --> quiet analog rail --> ADS AVDD / AVDD1
  +-- TPS7A2033PDBVR --> 3.3 V --> ADS DVDD only
  +-- devkit 5 V input --> onboard regulator --> ESP32-S3
```

Do not power the ESP32-S3 from the ADS DVDD regulator. Do not simultaneously power the devkit from USB and its external 5 V header. The analog feed resistor is a filter element, not a regulator; the design envelope in `board_profile.json` must remain within the ADS operating rail range.

### Reference / VCAP baseline

Use the ADS1299 internal reference and clock. The selected baseline includes 100 µF solid tantalum at VCAP1, 22 µF solid tantalum across VREFP/VREFN, local 1 µF supply/VCAP capacitors, 100 nF high-frequency bypass, and 10 µF local rail bulk capacitors. Final schematic review must verify every pin, polarity, effective capacitance under bias, and datasheet-required connection.

### Proposed S3 signal map

| Signal | ESP32-S3 GPIO | ADS1299 pin |
|---|---:|---:|
| SCLK | 12 | 40 |
| MOSI/DIN | 11 | 34 |
| MISO/DOUT | 13 | 43 |
| CS | 10 | 39 |
| DRDY | 4 | 47 |
| RESET | 5 | 36 |
| START | 6 | 38 |
| PWDN | 7 | 35 |
| CLKSEL | 8 | 52 |

This map is **proposed, not bench-verified**. GPIO8 is exposed on the official
DevKitC-1 v1.1 header and is reserved here for CLKSEL so the ADS input can stay
low during rail startup and be asserted only after supplies stabilize. J_DIG pin
19 carries CLKSEL; the former passive DVDD sense assignment is removed.

The ADS1299 power-up sequence requires its digital and analog inputs low until
the supplies stabilize. Therefore SCLK, DIN/MOSI, CS, RESET, START, PWDN and
CLKSEL all have a declared power-up level of 0 in `board_profile.json`. CS and
CLKSEL use 10 kΩ pulldowns, not pullups. The intended operational CLKSEL level
remains 1 for the internal oscillator; firmware must make that transition only
after the supply-stable boundary. This contract does not claim that rail timing
has been measured.

The current firmware does not load `hardware/rev_a/board_profile.json`; an explicit S3 firmware profile is a later commit. Do not remove the existing target/review guard just to make the build pass.

## Fail-closed gates

Rev A keeps all of these false:

```json
{
  "board_profile_reviewed": false,
  "firmware_port_validated": false,
  "schematic_released": false,
  "purchase_approved": false,
  "human_connection_allowed": false
}
```

No person or animal should be connected to this Rev A design. Battery operation, Wi-Fi, a USB isolator, low-leakage clamps, or a high-value BIAS resistor do not by themselves establish system safety.

## Validation

From the repository root:

```bash
uv run --locked python hardware/rev_a/check_baseline.py
uv run --locked python -m unittest discover -s hardware/rev_a -p 'test_*.py' -v
```

These checks verify the declarative BOM/profile contract, quantities, pin conflicts, cost arithmetic, frame length, provenance references, and fail-closed gates. They do **not** run SPICE, compile firmware, perform KiCad ERC/DRC, measure hardware, or certify safety.

## Next work, in order

1. **Implement the Rev A input network in ngspice.**
   a. Preserve the existing educational circuit as a regression fixture.  
   b. Add the selected 4.99 kΩ / 4.7 nF differential network and explicit source/electrode impedance.  
   c. Sweep impedance imbalance, R/C tolerance, cable capacitance, 50/60 Hz common mode, and bounded clamp leakage.  
   d. Compare the ideal case to 3393.06 Hz and commit numerical regression tests.

2. **Model BIAS and power behavior.**
   a. Add a bounded behavioral BIAS amplifier, the 1 MΩ / 1.5 nF network, dummy electrode/cable loads, and saturation.  
   b. Sweep uncertain loop parameters and check stability/recovery.  
   c. Model analog-rail startup and burst-like MCU/radio current coupling.

3. **Create the KiCad schematic and explicit ESP32-S3 firmware profile.**
   a. Use the exact BOM and four-channel pin rules.  
   b. Preserve all firmware guards and keep external-input acquisition disabled.  
   c. Compile supported targets and test ID/register readback plus 4/6/8-channel frame handling.

4. **Layout, quote, and bench bring-up.**
   a. Four-layer layout, ERC/DRC, reference/VCAP locality, controlled return paths, radio separation.  
   b. Obtain a delivered parts/fabrication/assembly quote before ordering.  
   c. Bring up rails -> ID/registers -> internal test -> input-short noise -> reviewed dummy source -> radio on/off comparison.

5. **Treat any body-connected design as a later revision.**
   a. Resolve battery/charging separation, enclosure, electrode connector/protection, BIAS fault paths, and qualified safety review.  
   b. Revalidate analog/noise behavior after those changes; bench success is not patient-safety evidence.

## Provenance

Detailed primary-source URLs, the two research-report hashes, verification notes, and the inspected upstream SHA are in [`hardware/rev_a/sources.json`](../hardware/rev_a/sources.json). Dynamic stock/pricing should be rechecked at purchasing time.
