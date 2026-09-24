# Model/tool reuse review — 2026-09-24

## Decision: do not recreate an ADS1299 chip

The next work is a set of small studies of the selected board and owned electrodes, not a transistor-level ADS1299 implementation or a new simulation framework. Existing `lab.adc` already provides educational code scaling, headroom and filter behavior; do not replace that with a second overlapping ADC framework.

The [current TI ADS1299 catalogue](https://www.ti.com/product/ADS1299) lists an **ADS129x IBIS model, SBAM163A**, not a full analog SPICE macromodel. Its CAD links supply symbols, footprints and 3D models, which are different artifacts from an electrical simulation. A schematic symbol names pins; a footprint locates copper pads; IBIS describes I/O-buffer behavior. None is evidence that the EEG input amplifier, noise, BIAS loop and converter are modeled together. The catalogue search did not find a ready-to-use full ADS1299 analog model. Do not turn that limited finding into a claim that no private or third-party model exists anywhere.

## Highest-value reusable engineering material

### BIAS: reuse TI's RLD analysis and topology

TI lists [SBAA188, Improving Common-Mode Rejection Using the Right-Leg Drive Amplifier](https://www.ti.com/lit/pdf/sbaa188), in the ADS1299 technical documentation. In an [ADS1299 support response](https://e2e.ti.com/support/data-converters-group/data-converters/f/data-converters-forum/539346/ads1299-bias-amplifier-open-loop-gain), TI engineer Brian Pisani states that the ADS1298 RLD circuit is identical to the ADS1299 BIAS circuit and directs designers to the application's cable-load compensation discussion. This is useful manufacturer guidance, not a newly supplied ADS1299 SPICE binary or proof that all ADS1298/1299 circuitry is interchangeable.

Reuse the published feedback topology, equations and test approach. Build only the bounded amplifier/load behavior needed for stability and settling questions, in ordinary ngspice netlists driven by the existing Python workflow. Keep uncertain amplifier/contact/cable parameters explicit. Do not copy the note's illustrative electrode values as MCScap measurements or change the locked Rev A feedback parts without a reviewed hardware decision. A simulation of this block must stay labelled a bounded BIAS study, not a full validated ADS1299.

### Power: a vendor model exists for the already selected regulator

The [TPS7A20 catalogue](https://www.ti.com/product/TPS7A20) supplies **TPS7A20 PSpice Transient Model, SBVM961.ZIP**. The baseline source catalogue had already identified it; the remaining task is retrieval, license/provenance review, exact 3.3-V configuration and an actual ngspice compatibility smoke test before trusting results. That test has not been performed in this review. Do not confuse TPS7A20 with TPS7A20L or claim every PSpice macro is automatically compatible with ngspice.

Use it for startup/load-transient studies of ADS DVDD where supported. The selected regulator does not supply the ESP32-S3. A transient model is not automatically a noise/PSRR model; check its documented scope before making those predictions.

### Schematic: reuse reviewed source drawings, not guessed wiring

Use the [ADS1299-x datasheet](https://www.ti.com/lit/ds/symlink/ads1299.pdf), the [TI ADS1299EEG-FE user guide](https://www.ti.com/lit/ug/slau443b/slau443b.pdf), and TI-linked CAD assets as starting references. Verify every ADS1299-4-specific pin and unused-channel rule, package pad, capacitor polarity and connection. A symbol existing in a library does not complete schematic review. The four-channel board remains the selected design; no alternative AFE/MCU is introduced here.

## Tools: add only at a demonstrated boundary

| Tool/material | Existing project fit | Decision |
|---|---|---|
| ngspice | Existing subprocess/netlist boundary and independent Python numerical comparison | Keep it. No second wrapper is necessary for the current studies. |
| KiCad and its CLI | Authoritative editable schematic/layout; future ERC/DRC in CI | Use when the schematic stage begins. Its integrated simulator is ngspice, not an independent third solver. |
| Hypothesis | Already a pinned Python/pytest development dependency | Use generated inputs and operation sequences now; no extra state-machine framework needed. |
| mutmut | Python mutation testing of small pure/domain boundaries | Worth a scoped opt-in pilot, not a mandatory whole-repo gate yet. Not installed by this review. |
| PySpice / general modeling frameworks | Would add another wrapper over an already working solver boundary | Defer: no missing ADS1299 model is supplied by adding the wrapper. Reconsider only for a concrete unsupported need. |
| Generic DDD/state/electrode plugin frameworks | No demonstrated need with one selected board and one owned electrode family | Do not add. Keep values, validation and I/O ownership explicit in ordinary Python. |

### Health and compatibility observations

The [ngspice news page](https://ngspice.sourceforge.io/news.html) records release 47 on 2026-08-11; the project's observed CI uses distro ngspice 42. Active upstream development is not a reason to silently change the tested engine version.

[KiCad 10.0.0 was released on 2026-03-20](https://www.kicad.org/blog/2026/03/Version-10.0.0-Released/). Its [simulation documentation](https://www.kicad.org/discover/spice/) explains the ngspice integration. This established toolchain is preferable to adding a poorly verified chip-specific repository merely because its name includes ADS1299.

[mutmut on PyPI](https://pypi.org/project/mutmut/) lists version 3.8.0, released 2026-09-12, Python >=3.10 and a BSD-3-Clause license. Recent releases and [maintained documentation](https://mutmut.readthedocs.io/en/latest/) support considering a pilot; they do not establish compatibility with this repository until it runs. It requires POSIX fork support (Windows requires WSL), fitting the current Linux CI and user's Linux environment. The documented configuration uses `source_paths`; a `pyrefly` filter is supported, but can hide some runtime-test gaps. Start a pilot without that filter and classify survivors instead of chasing a blind score.

Pilot acceptance: pin the tool in an optional locked environment, target one small validation/ADC/protocol boundary and focused tests, record elapsed runtime and reproducible survivors, then add tests for meaningful survivors. Keep mutation artifacts separate and ignored. Do not apply mutants to the working source accidentally, add a universal 100% threshold, or count equivalent mutations as confirmed bugs. This review added no runtime or development dependency.

## Owned hardware first

The [MCScap source record](references/mcscap/README.md) now records the user's real electrode family and insulated DIN 1.5 mm connector report. The family manual's impedance/noise/length bounds are not a fitted electrode-skin-cable circuit. Obtain the exact catalogue suffix and actual lead information before calling a numerical profile a model of the owned hardware. Keep normal, asymmetric and disconnected conditions for that same hardware; they are not speculative generalization.

## Ordered next engineering work

1. Finish the small completion-state correction separately from electronics work; retain its failure evidence and API boundary documentation.
2. Resolve MCScap catalogue/lead/test-condition unknowns and define a source-traceable electrode/input study. Preserve the old generic examples as numerical fixtures, not manufacturer measurements.
3. Reuse SBAA188 for a bounded BIAS-loop study, and smoke-test the vendor TPS7A20 model for a separate power study. Neither requires a full chip simulator.
4. Reconcile those studies with an exact KiCad schematic, then target-compile the S3 bench-only profile and perform reviewed dummy-bench measurements before any later body-interface revision.

No circuit safety gate, purchase gate, hardware component or firmware behavior is changed by this research. Model agreement is evidence about the modeled circuit, not permission to attach the board to a person.
