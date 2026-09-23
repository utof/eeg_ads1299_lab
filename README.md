# ADS1299 Learning Lab

**Start without buying anything.** This is a runnable Python learning environment for EEG-like signals, an illustrative electrode/input circuit, signed 24-bit conversion, data transport, signal quality, and a small machine-learning experiment.

It is **not a finished EEG recorder, a validated PCB, or permission to attach a circuit to a person**. The firmware is a board-dependent **bench-only starter** using the ADS1299's internal test/short circuits. **Rev A now selects an ADS1299-4 daughterboard plus ESP32-S3-DevKitC-1-N8R8 for simulation/schematic work; none of the hardware-review or body-connection gates are approved.**

## Open these first

| File | What it does for you |
|---|---|
| [START_HERE.html](START_HERE.html) | Offline visual walkthrough, provisional digital pin map, interactive gain/offset calculator. Open after extracting the entire ZIP. |
| [Results report](docs/RESULTS.md) | What actually ran, measured outputs, test evidence, and what remains unverified. |
| [Learning guide](docs/LEARNING_GUIDE.md) | A beginner explanation of the electronics, simulations, signal processing, and small exercises. |
| [Hardware guide](docs/HARDWARE_GUIDE.md) | Purchasing gate, $100 budget constraint, conditional wiring, bench tests, and the body-connection boundary. |\n| [Rev A hardware baseline](docs/HARDWARE_BASELINE_REV_A.md) | Selected ADS1299-4 + ESP32-S3 components, machine-readable BOM/profile, fail-closed gates, and ordered next work. |
| [Experiments guide](docs/EXPERIMENTS.md) | From synthetic alpha to a future controlled meditation experiment, without confusing artifacts with consciousness. |
| [Next-session handoff](docs/LLM_HANDOFF.md) | Give this to a future assistant together with the source and validation records. |

The earlier uploaded reports are background, not software dependencies. This package does not depend on their old ZIP links or on an AD8232/ADS1115.

## First run: Linux, macOS, or Windows

Use Python **3.11 or newer**. The tested environment was Python 3.13.5 on Linux; exact package versions are in `requirements-tested.txt`. The runtime here already had the dependencies: a clean internet installation on your own operating system was not exercised.

Extract the ZIP, then open a terminal **inside `eeg_ads1299_lab`**:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python run_lab.py demo
python run_lab.py verify
```

Windows PowerShell: create the environment with `py -3 -m venv .venv`. You can avoid activation-policy changes by running `.venv\Scripts\python.exe -m pip install -r requirements.txt` and `.venv\Scripts\python.exe run_lab.py demo`. Use that Python path for the other commands too.

The demo makes `results/demo/synthetic_recording.npz`, event/quality CSVs, an analysis JSON, and four PNG figures. The included example results were already generated. Regenerating uses the same seed, but numerical outputs can vary slightly across dependency versions.

`verify` runs the tests and writes `VALIDATION.json`. **A successful default verification means the available software checks passed, not that ngspice or hardware was verified.** Read the individual status fields. A native C++ compiler is needed to repeat the portable firmware-core test; absence is reported as a skipped test.

## Run a circuit simulation

```bash
python run_lab.py circuits
```

This solves an illustrative passive circuit using Python's linear algebra, writes response/tolerance CSVs, and exports two `.cir` files. It is an independent nodal solver, **not ngspice**. There is no transistor-level ADS1299 model.

For a real ngspice cross-check on Debian/Ubuntu/Linux Mint:

```bash
sudo apt update
sudo apt install ngspice g++
python run_lab.py circuits --require-ngspice
python run_lab.py verify --require-ngspice
```

The strict commands fail when ngspice is absent. Here ngspice could not be installed, so those external-simulator runs remain unverified. When installed, the circuit command executes ngspice and compares its complex AC response with the independent numerical solution. Logs remain under the output folder.

## Three useful changes

```bash
# Negative control: remove the planted condition difference.
python run_lab.py demo --null-effect --out results/my_null

# Eight physical channels and 60-Hz residual line interference.
python run_lab.py demo --channels 8 --line-hz 60 --out results/eight_channels

# Edit a copy of this JSON to change gain, offset, or artifact size.
python run_lab.py demo --config configs/demo.json --out results/custom
```

Changing a JSON changes the **simulation**, not a physical board. The firmware does not read `configs/demo.json` or the board-review worksheet.

## Test the recording path with no electronics

```bash
python tools/run_loopback.py
```

This takes about ten seconds. It starts a real localhost UDP receiver, sends nine seconds of synthetic packets, deliberately omits samples 1000 and 2000, decodes to CSV, and creates a gap-safe quality report. It asserts 2,248 accepted packets and two missing samples. Unexpected extra loss causes a failure rather than a reassuring-looking plot.

For manual control, use two terminals:

```bash
# Terminal A
python run_lab.py receive --seconds 15 --out results/practice.bin
```

```bash
# Terminal B, while A is listening
python run_lab.py replay --seconds 8 --drop-every 1000
```

Then:

```bash
python run_lab.py decode results/practice.bin --out results/practice.csv
python run_lab.py inspect results/practice.csv --out results/practice_quality
```

Keep the `.json` metadata beside the decoded CSV. The inspector analyzes only uninterrupted four-second windows. It reports DC offset separately and never fills gaps to manufacture a continuous spectrum. The receiver defaults to localhost; actual LAN use requires `--host 0.0.0.0`, private-network firewall permission, and the computer's LAN address in the firmware. UDP is unencrypted; never expose the port to the public internet.

## What is in the source?

```text
lab/adc.py              Ideal code scaling, range/headroom checks, sinc³ model
lab/analog.py           Two-node passive circuit solver + ngspice export/check
lab/signals.py          Deterministic, explicitly synthetic recordings
lab/dsp.py              Quality screens, band power, session-held-out classifier
lab/protocol.py         ADS frame decoding, custom packets, CRC and counters
lab/acquisition.py      UDP/optional bench serial logging and CSV decoding
lab/inspect_capture.py  Gap-safe bench spectra and quality reports
lab/pipeline.py         Demo outputs and figures
firmware/              Original-ESP32 bench starter; NOT target-compiled here
configs/               Editable demo settings and hardware-review worksheet
results/               Example recordings, figures, actual logs and reports
tests/                 Regression tests, including native portable C++ code
tools/                 Validation, localhost integration test
```

The firmware's default `BOARD_PROFILE_REVIEWED = false` intentionally prevents acquisition startup. Changing that setting acknowledges **bench digital wiring only**, not body-use approval. Do not bypass it just to see a waveform.

## Troubleshooting

| Symptom | First action |
|---|---|
| `ModuleNotFoundError` | Use the same virtual-environment Python for installation and execution. |
| `ngspice executable is absent` | Install ngspice; do not count Python circuit tests as ngspice execution. |
| `All epochs rejected` | Inspect gain, differential DC offset, and quality flags. An overrange input is an expected negative test. |
| No UDP packets | First repeat localhost loopback. Then inspect the private LAN address, firewall, and UDP port. |
| No four-second spectral windows | The capture is too short or fragmented. Fix acquisition before interpreting spectra. |
| Unexpected ESP32 or board pins | Stop; the supplied pin map is not generic to every ESP32/ADS1299 module. |
| Matplotlib cache permission warning | Set `MPLCONFIGDIR` to a writable directory; no special font installation is required. |

Read [SOURCES.md](docs/SOURCES.md) for primary references and [MODEL_SCOPE.md](docs/MODEL_SCOPE.md) for model boundaries.
