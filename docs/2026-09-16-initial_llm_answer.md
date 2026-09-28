I built an **ADS1299-focused learning lab you can use before buying anything**: simulation scripts, tests, generated example data, an offline visual guide, and the Markdown explanations.

**[Download the complete project ZIP](sandbox:/mnt/data/eeg_ads1299_lab.zip)** — approximately 3 MB.

The key boundary: **the Python simulations and analysis were exercised here; this is not yet a validated, body-connected EEG recorder.** The hardware-dependent steps are documented separately.

## Start with these files

Everything is included in the ZIP. These links also open the main guides individually:

| File                                                                                      | What it gives you                                                                                                                                                                                                      |
| ----------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **[Visual “Start Here” guide](sandbox:/mnt/data/eeg_ads1299_lab/START_HERE.html)**        | A signal-flow explanation, interactive gain/offset calculator, and provisional digital wiring table. Its calculator and example figure work offline; extract the ZIP to keep its links to the other documents working. |
| **[Results report](sandbox:/mnt/data/eeg_ads1299_lab/docs/RESULTS.md)**                   | What actually ran, numerical results, verification evidence, and explicit limitations.                                                                                                                                 |
| **[Beginner learning guide](sandbox:/mnt/data/eeg_ads1299_lab/docs/LEARNING_GUIDE.md)**   | What electrodes, reference, bias, gain, ADC counts, SPICE, filtering, spectra, and classifiers do—with exercises.                                                                                                      |
| **[Hardware and wiring guide](sandbox:/mnt/data/eeg_ads1299_lab/docs/HARDWARE_GUIDE.md)** | The purchasing decision, $100 constraint, conditional ESP32 connections, and progression through bench tests.                                                                                                          |
| **[Experiment guide](sandbox:/mnt/data/eeg_ads1299_lab/docs/EXPERIMENTS.md)**             | A progression from synthetic signals toward future alpha and controlled meditation experiments.                                                                                                                        |

There is also an **`LLM_HANDOFF.md`** inside the project. It preserves your goals, the code’s assumptions, what has been tested, and what a future assistant must not casually assume.

## What I verified

I ran the test suite, extended it, corrected a test issue, exercised the complete synthetic pipeline, and tested actual localhost data transmission. Finally, I extracted the finished ZIP into a fresh directory, checked its file hashes, and reran the tests.

**Final result: 65 tests passed, with no failures or skips.**

That count applies to the included software tests—not to unavailable external tools or physical hardware.

| Component                                                          | Verification status                                                                |
| ------------------------------------------------------------------ | ---------------------------------------------------------------------------------- |
| Python signal generation, ADC model, analysis, and packet handling | **Tested**                                                                         |
| Passive circuit model and component-tolerance calculations         | **Executed** using an independent numerical solver                                 |
| Real localhost UDP capture → binary file → CSV → spectrum          | **Executed**                                                                       |
| Portable C++ packet/checksum helpers                               | **Compiled and compared byte-for-byte with Python**                                |
| Interactive guide’s calculator arithmetic                          | **Tested under Node**; browser rendering was not verified                          |
| Actual ngspice execution                                           | **Not run:** ngspice was unavailable and installation attempts failed              |
| Complete ESP32 firmware                                            | **Not target-compiled or hardware-tested:** the required toolchain was unavailable |
| Physical board, electrode protection, or human EEG                 | **Not tested**                                                                     |

The detailed record is in **[VALIDATION.json](sandbox:/mnt/data/eeg_ads1299_lab/VALIDATION.json)**.

### The simulation produces a result—and has a negative control

The default generator deliberately creates stronger 10-Hz activity for its “eyes closed” label. It also adds other frequency components, noise, offsets, line interference, and artifacts.

The analysis accepted **78** four-second windows and rejected **18**. It recovered an **11.14× closed/open alpha-power ratio**, and the simple classifier achieved **100% balanced accuracy on held-out synthetic sessions**.

That is a deliberately easy, planted effect—not demonstrated brain decoding.

When I removed that condition-dependent effect and reran the pipeline, the alpha-power ratio became **1.03×**, and classification fell to **54.17%**, against a **50% baseline**. That negative control is important: the project does not merely show you an impressive classifier score without testing what happens when its intended signal disappears.

The recording-path test also worked: it received **2,248 packets**, identified **both deliberately omitted samples**, and recovered the synthetic **10-Hz** signal without joining across missing data.

## How the project is structured

I retained the useful separation in your earlier report between analog-circuit modeling and Python converter/analysis modeling, rather than treating one enormous simulation as proof that everything works. 

There are three practical layers:

**Circuit learning.** A small, inspectable model lets you change electrode resistance, capacitance, input loading, and mismatch. It demonstrates how equal interference on two inputs can become a differential error when their paths differ. The same circuit is exported as ordinary `.cir` files for a future ngspice cross-check.

**Recording and analysis.** Python generates synthetic recordings, models conversion and clipping, checks data quality, computes spectra and band powers, and runs a simple classifier. Training and testing are separated by complete sessions, with preprocessing fitted only on training data—the kind of separation needed to avoid common leakage mistakes. ([Scikit-learn][1])

**Bench acquisition starter.** The ESP32 code is restricted to the ADS1299’s **internal test signal or internally shorted inputs**. It has packet counters, timestamps, checksums, register readback, and a default-disabled board-review gate. It does **not** provide an external-electrode recording mode.

The intended eventual architecture is:

```text
Reviewed electrode interface
            ↓
Assembled ADS1299 front-end board
            ↓ SPI digital data
          ESP32
            ↓ wireless
Computer: raw recording → quality checks → analysis
```

The ADS1299 already integrates amplification and simultaneous analog-to-digital conversion. You do not need an ADS1115 after it, and this architecture does not use the Uno’s analog inputs to digitize the EEG. ([Texas Instruments][2])

## Two important things to understand before buying

### 1. “ADS1299 chip” is not the same purchase as “usable EEG board”

At the price check, DigiKey listed the eight-channel **bare chip** at **$88.58**, and the four-channel ADS1299-4 at **$44.99**. Neither is a complete assembled recorder. ([DigiKey][3])

So I have **not verified a complete, documented ADS1299 build within your additional $100 budget**. That does not mean it is impossible; it means a complete board-and-accessories quote is needed before treating it as a workable budget.

My recommendation is to **keep the money unspent while running the software and identifying the exact board**. Buying a bare fine-pitch chip now could consume the budget without getting you to a usable front end.

The hardware guide provides a purchasing worksheet and a provisional spending allocation, clearly distinguished from actual supplier quotations.

### 2. A software filter cannot rescue an amplifier that has saturated

For the nominal 4.5-V reference and gain of 24, the ideal differential range is approximately **±187.5 mV**. Small EEG-like variations can ride on a much larger electrode offset, so the offset and common-mode operating limits matter—not only the wave’s microvolt amplitude. The project checks these separately. ([Texas Instruments][4])

The interactive guide lets you explore this directly: increase the offset, change gain, then move common mode toward a supply rail.

One included exercise intentionally exceeds the range. The correct result is rejection—not a reassuring filtered trace.

## Your first hands-on session

After extracting the ZIP, open a terminal in `eeg_ads1299_lab`. On Linux or macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

python run_lab.py demo
python run_lab.py verify
```

Windows instructions are in the README.

Then open `START_HERE.html` and examine the files under `results/demo`.

For the next exercise, remove the planted effect:

```bash
python run_lab.py demo --null-effect --out results/my_null
```

Then test the recording path without electronics:

```bash
python tools/run_loopback.py
```

And explore the passive circuit:

```bash
python run_lab.py circuits
```

That last command runs the included **Python circuit solver**. Once ngspice is installed on your computer, this command requires the actual external simulator and compares its output:

```bash
python run_lab.py circuits --require-ngspice
```

It deliberately fails when ngspice is missing rather than counting that check as successful.

## How this connects to meditation and consciousness

A useful first physiological target, **after the hardware is reviewed**, is a repeatable posterior-alpha comparison between eyes-open and eyes-closed periods. OpenBCI uses this as an accessible introductory EEG observation. ([OpenBCI Documentation][5])

For a later meditation experiment, I would hold the **eye condition constant** between meditation and quiet rest, balance the order, repeat on different days, and record subjective observations separately. Otherwise, you could accidentally study eye closure, drowsiness, posture, or muscle tension while calling the result “meditation.” Eye and muscle artifacts are genuine contributors to EEG recordings, not merely cosmetic noise. ([MNE Tools][6])

The experiment guide develops that progression. It is meant to help you ask increasingly precise questions—not give a classifier an unsupported “consciousness score.”

Finally, **do not attach the current unreviewed circuit to yourself**. Even TI’s own ADS1299 evaluation platform is described as laboratory engineering equipment, not a direct patient interface. Battery and wireless operation are important precautions, but they do not replace review of the input protection, bias circuitry, power arrangement, and construction. ([Texas Instruments][7])

**For the next hardware-specific step, send the exact ADS1299 board listing or schematic and the model printed on your ESP32.** Those are what turn the provisional signal map into an accurate board-specific wiring guide.

[1]: https://scikit-learn.org/stable/common_pitfalls.html "https://scikit-learn.org/stable/common_pitfalls.html"
[2]: https://www.ti.com/product/ADS1299?utm_source=chatgpt.com "ADS1299 data sheet, product information and support"
[3]: https://www.digikey.com/en/products/detail/texas-instruments/ADS1299IPAGR/3536907 "ADS1299IPAGR Texas Instruments | Analog Front End (AFE) | DigiKey"
[4]: https://www.ti.com/lit/ds/symlink/ads1299.pdf "https://www.ti.com/lit/ds/symlink/ads1299.pdf"
[5]: https://docs.openbci.com/GettingStarted/Biosensing-Setups/EEGSetup/ "https://docs.openbci.com/GettingStarted/Biosensing-Setups/EEGSetup/"
[6]: https://mne.tools/stable/auto_tutorials/preprocessing/10_preprocessing_overview.html "Overview of artifact detection — MNE 1.13.2 documentation"
[7]: https://www.ti.com/lit/ug/slau443b/slau443b.pdf "https://www.ti.com/lit/ug/slau443b/slau443b.pdf"

