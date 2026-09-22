# Learning guide: from a fake signal to an understandable EEG system

You do not need to understand the entire circuit before beginning. Start by changing one number, predicting the result, running the program, and comparing your prediction with the output. That loop is the central skill this project is designed to teach.

**The starting experiment costs nothing:** run the synthetic demo and inspect its figures. Hardware is a later, separately reviewed step.

## 1. What we are trying to measure

A recording channel measures a **voltage difference**, not an absolute amount of “brain activity.” In a simplified description:

```text
channel value = voltage at its positive input − voltage at its negative input
```

The computer eventually receives numbers representing that difference. The measured voltage can contain neural activity, eye movements, muscle activity, contact changes, and interference. The fact that a trace changes when you blink does not establish that the trace is predominantly EEG. MNE's artifact guide explains these different contributors [S7].

For practice, imagine a 10-Hz wave with a 10-microvolt peak. “10 Hz” means ten cycles per second. “10 microvolts” means 0.000010 volts. Its peak-to-peak amplitude is 20 microvolts; its RMS amplitude is approximately 7.07 microvolts. Those are three different measurements of the same sine wave. The tests verify its integrated spectral power rather than comparing incompatible amplitude conventions.

Our program **constructs** brain-like waves. It does not simulate neurons, consciousness, a particular person's brain, or a validated head volume conductor. The condition labels describe how the generator changes its output.

## 2. What each physical part would do

| Part | Role in the eventual system | What it does not do |
|---|---|---|
| Electrode and conductive contact | Couple a scalp potential into an input | They do not selectively extract neural activity. |
| Analog front end | Accept small differential signals while handling common mode, input loading, protection and noise | A small IC does not by itself make a safe complete instrument. |
| ADS1299 | Integrates amplifiers, simultaneous ADC channels, reference/clock options and biopotential functions | It does not replace the supporting PCB, power design or safety review. |
| ESP32 | Reads already-digitized values over SPI and forwards packets | Its built-in ADC is not used in this architecture. |
| Computer | Stores raw samples, checks integrity, computes spectra and runs experiments | It cannot recover information that was clipped before digitization. |
| Battery, enclosure and approved input circuitry | Form part of the physical recording system | A battery alone is not a safety certification. |

The ADS1299 device family is documented in TI's datasheet [S1]. With this architecture you do **not** add an ADS1115 after the ADS1299 or feed its output into the Uno's analog input. The ADS1299 output used here is digital.

Keep the Uno for ordinary breadboard lessons and signal-generation experiments **with no person connected**. An extra controller is not needed just because you already own it.

## 3. Three things called “reference” that are easy to mix up

**Electrode reference** is the other potential against which a recording channel is compared. In a common-reference arrangement, several channels share it.

**ADC voltage reference** is the chip's electrical ruler for converting a measured voltage into a digital number. It is not an electrode. The nominal internal reference used by this project is 4.5 V.

**Bias electrode** belongs to a circuit that influences the body's common-mode potential. It is not a second name for the signal reference. A driven-bias output is active circuitry and needs an appropriate current-limited, stable, reviewed implementation [S1, S2].

**Circuit ground** and **household protective earth** are also different concepts. Never connect an electrode, a bias lead, or a cable shield to household earth as a noise remedy.

This package deliberately does not show a jumper from a bare BIASOUT pin to a person. The internal-test firmware leaves the bias driver and lead-off excitation off. Real reference/bias routing depends on the actual board schematic.

## 4. Gain, ADC counts, and why offsets matter

Gain scales the differential voltage before conversion. For a nominal 4.5-V reference and gain 24, our ideal ADS1299 code model has:

```text
input full scale: ±(4.5 / 24) V = approximately ±187.5 mV
one code step: 4.5 / (24 × 2^23) V = approximately 0.02235 µV
```

These are calculated using the datasheet's scaling relationship [S1]. The 24-bit number is signed: negative voltage differences produce negative codes. Zero is a difference near zero, not a statement that no activity exists.

**One code step is not the same as noise-free resolution.** A thermometer can print six decimal places without measuring temperature to six decimal places. The same distinction applies to ADC bits and the noise of the complete electrode/circuit system.

The electrode interface may also introduce a differential DC offset. Suppose a small wave rides on 30 mV of offset. The raw input is not just a few microvolts: it is roughly 30 mV plus that small variation. At the example gain and common mode this can remain within range. At 300 mV, the same gain exceeds the nominal differential range.

A digital high-pass filter can remove an offset from **valid recorded samples**. It cannot undo saturation. Once the amplifier or converter clips, many different real inputs become the same output code. Filtering those codes produces a nicer-looking trace, not the missing measurement.

### Exercise: deliberately break the range

Copy `configs/demo.json` to a new file. Change `differential_offset_mV` to `300`, then run with that `--config`. The analysis should reject the affected data, not announce a successful EEG experiment. Restore the offset afterward.

Changing gain from 24 to 12 increases the nominal differential range. It also changes the input-referred code size and the operating/noise tradeoffs. Do not treat “maximum gain” as a universally optimal setting. The prototype firmware remains fixed at gain 24 for its internal bench tests; changing simulation settings does not change that firmware.

### The second range condition: common mode

Let the two inputs be `Vp` and `Vn`:

```text
differential voltage = Vp − Vn
common-mode voltage = (Vp + Vn) / 2
```

A tiny difference does not guarantee that both input voltages are at acceptable levels. The datasheet specifies additional amplifier headroom constraints. The model checks the datasheet's PGA common-mode relationship as well as differential full scale [S1]. Open `START_HERE.html` and vary gain, offset, and common mode to see the distinction.

That calculator assumes 0-V/5-V analog rails solely to illustrate the equation. It is not instructions for powering an unknown board, and passing its arithmetic is not a protection or safety test.

## 5. What a resistor and capacitor do in our circuit model

A resistor relates voltage and current. A capacitor's impedance depends on frequency. Used together, they can pass slow variations differently from fast ones.

An electrode/contact is much more complicated than one resistor, but an illustrative resistor in parallel with a capacitor is useful for learning. Our two input paths each contain that contact model, a series resistor, a large input resistance, and a small capacitance to the local midpoint. Another capacitor connects the two inputs.

The **local midpoint** in the AC model is the zero of the small-signal calculation. It is not a wire you attach to the building's earth.

The component values in this package are educational parameters. They are **not approved patient-protection values**. Increasing a series resistor can change loading, noise and filtering; it does not constitute a complete fault-current assessment. The model excludes resistor thermal noise, input clamp leakage, board contamination, and many real parasitics.

### Why matched inputs matter

Imagine the same unwanted 50-Hz voltage appearing on both electrodes. Perfectly identical linear input paths produce equal voltages at the amplifier inputs; subtraction removes the equal part. Make the paths unequal, and some of that common-mode voltage becomes a difference before the amplifier sees it.

In the provided illustrative circuit, changing one contact resistance from 10 kΩ to 50 kΩ produces about **63.84 µV differential amplitude for 100 mV common-mode amplitude at 50 Hz**. That is a model result, not a prediction for your future board. Its perfectly balanced case has essentially zero conversion because the equations are symmetric—not because a real circuit has infinite rejection.

### Exercise: change one contact

In a Python session opened in the project folder:

```python
from dataclasses import replace
from lab.analog import InputNetwork, transfer

balanced = InputNetwork()
unbalanced = replace(balanced, r_electrode_n=50_000)
for name, circuit in [("balanced", balanced), ("unbalanced", unbalanced)]:
    leakage = abs(transfer([50], circuit, drive="common")[0])
    print(name, "differential µV for 100 mV common mode:", leakage * 100_000)
```

Repeat with a different contact capacitance. Write down your prediction before running. A software 50-Hz notch might hide one symptom; it does not repair the electrode mismatch.

## 6. What SPICE is, and what actually ran here

A **schematic** is a drawing of electrical connections. A **netlist** is a textual list of connections and components. A **simulator** solves mathematical models of those components. A **PCB layout** describes the physical board. These are related, but they are not interchangeable.

ngspice is a circuit simulator that can consume textual circuit descriptions [S3]. KiCad is useful for design documents and PCB work; a visual circuit on screen still needs correct models, supplies, connectivity and assumptions before its simulation means anything.

This project intentionally has two paths:

```text
Our passive component parameters → Python nodal equations → AC response
Our passive component parameters → ordinary .cir files → ngspice → AC response
```

Only the first path executed in the provided environment. The second is exported and wired into a strict comparison command, but ngspice itself was unavailable. This is not disguised as a skipped “success.”

The Python solver forms a two-by-two complex admittance matrix and solves Kirchhoff's current-law equations. You can inspect it in a small source file. Tests compare limiting cases with independent closed-form results and check symmetry. When ngspice is installed, the program compares both complex responses at the same frequencies.

There is no active body-bias amplifier model, power-supply model, protection circuit, ESD model, or complete ADS1299 silicon macro-model. Those omissions matter when moving toward physical construction.

### Exercise: see the literal circuit description

Run `python run_lab.py circuits`, then open `results/circuits/balanced.cir` in a text editor. Find `Rep`, `Cep`, `Rsp` and `Cd`; relate each one to the explanation above. Do not try to connect the exported network to your body. It is a model exercise.

## 7. Sampling and filters

The initial sample rate is 250 samples per second **per channel**. Every sample is one row of simultaneous channel values; using more physical channels changes frame length, not the meaning of that row.

At 250 samples/s, the Nyquist frequency is 125 Hz. Frequencies above the useful sampled band must be sufficiently attenuated before they alias. A digital filter applied after a signal has already aliased cannot identify the original frequency from the aliased data alone.

The ADS1299 includes a third-order sinc decimation filter. Its response is not a perfectly flat brick wall [S1]. `model_filter_response.png` compares its nominal mathematical shape with our illustrative passive input circuit. The two traces represent different filters, not two competing estimates of one filter.

The time-domain generator uses a lower-rate, three-moving-average approximation to the sinc³ response. It is efficient for low-frequency lessons, but it does not simulate the chip's actual modulator bitstream, exact internal timing, or radio-frequency aliasing. The external passive circuit is a **separate exercise**, not automatically applied to the synthetic data. This separation is recorded in the metadata.

Our offline analysis uses a 1–40-Hz bandpass on individual candidate windows. This first lesson does not preserve slow DC behavior for interpretation, and it is not an ERP or real-time neurofeedback pipeline. Forward/backward filtering uses future samples; a live display needs a causal design and a latency budget.

## 8. What the plots mean

**Trace:** voltage versus time, displayed after removing the DC level. Always inspect raw offset/range information separately because a centered display can hide a serious DC problem.

**Power spectral density (PSD):** estimated signal power per unit frequency. A 10-Hz sine produces a peak near 10 Hz. The PSD is calculated with Welch's method [S5]. Units are explicitly shown; integrating µV²/Hz over Hz gives µV².

**Alpha-band power:** the integral between 8 and 13 Hz in this project. Band boundaries are analysis choices, not magical biological switches. The synthetic generator's main condition effect is deliberately placed at 10 Hz.

**Classifier score:** whether a simple model can recover the synthetic labels from band-power features in held-out sessions. The default case is intentionally easy. Perfect performance here validates only a limited part of the software path.

### Exercise: remove the answer from the generator

```bash
python run_lab.py demo --null-effect --out results/my_null
```

Now both labels have the same alpha-generation rule. In the recorded example, balanced accuracy falls from 100% to about 54%. One near-chance run is a useful negative control, not a proof that every possible source of leakage has been eliminated.

## 9. How we avoid a misleading machine-learning demonstration

The data are divided into synthetic sessions. A held-out session is never used to fit the model or the feature scaler. Windows from one session stay together. That follows the purpose of grouped validation and train-only preprocessing [S6, S8].

Features are only log band powers. Sample time, session ID, block ID and condition are not inputs to the classifier. Candidate windows do not overlap; filtering does not cross from one session into another. The artifact screen uses fixed rules before the condition is used for classification.

The pipeline also shuffles labels by **whole block within each session**, not by individual samples. Its 20 default permutations are only a quick diagnostic: the smallest possible reported permutation p-value is 1/21. That is not a publication-quality significance analysis or a guarantee of generalization to another person.

Our simple quality screen detects large excursions, flat channels, nonfinite samples and known simulated overrange. It can miss subtle muscle activity and other contamination. Artifact detection is a larger problem than one threshold [S7].

## 10. Why packets need more than numbers

A recording should tell you when data went missing. Each custom packet contains the physical channel count, gain, nominal rate, sample sequence, microcontroller time, an overrun counter, the ADS frame, and a checksum.

The checksum detects transport corruption in covered bytes; it does not prove the analog signal is right. It also cannot detect a wrong SPI value that the firmware already read and then checksummed. Sequence numbers expose missing packets. Timestamps allow checks of continuity and counter rollover.

Run the loopback exercise. Then examine `missing_before` in its CSV: it should flag the intentional losses. The spectral inspector refuses to join separated snippets into one apparently continuous waveform. Missing time is missing time, even when a smooth line would look nicer.

The packet format is specific to this lab. It is not an OpenBCI packet and cannot be assumed compatible with an unrelated board's stock firmware. Details are in [PROTOCOL.md](PROTOCOL.md).

## 11. A practical learning sequence

Spend the first session running the unmodified demo and matching each output to its source file. In the second session, change alpha strength, offset, and artifact size one at a time. In the third, change a passive component and compare predicted versus calculated response. Then repeat the packet-loss exercise.

Only after you understand those results should you choose the exact physical board. The next useful achievement is a reliable **internal test-signal recording from a powered board on the bench with no electrodes on anyone**, not a first unexplained line on your head.

The hardware guide gives the review gates. The experiment guide connects these measurement skills to your longer-term interest in perception and meditation without inventing a “consciousness score.”

References marked `[S#]` are linked in [SOURCES.md](SOURCES.md).
