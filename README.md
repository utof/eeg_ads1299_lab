# ADS1299 Learning Lab

**Start without buying anything.** This is a runnable Python learning environment for EEG-like signals, an illustrative electrode/input circuit, signed 24-bit conversion, data transport, signal quality, and a small machine-learning experiment.

It is **not a finished EEG recorder, a validated PCB, or permission to attach a circuit to a person**. The firmware is a board-dependent **bench-only starter** using the ADS1299's internal test/short circuits. **Rev A selects an ADS1299-4 daughterboard plus ESP32-S3-DevKitC-1-N8R8 for simulation/schematic work; none of the hardware-review or body-connection gates are approved.**

## Open these first

| File | What it does for you |
|---|---|
| [START_HERE.html](START_HERE.html) | Offline visual walkthrough, provisional digital pin map, interactive gain/offset calculator. Open with the rest of the repository available. |
| [Development guide](docs/DEVELOPMENT.md) | Locked installation, one quality command, test-first changes, strict typing, and enforced public interfaces. |
| [DX validation record](docs/DX_VALIDATION.md) | A dated CI run with software tests, actual ngspice execution, native helper tests, and limitations. |
| [Historical results report](docs/RESULTS.md) | Original measured outputs and evidence; retained rather than overwritten by routine CI. |
| [Learning guide](docs/LEARNING_GUIDE.md) | A beginner explanation of the electronics, simulations, signal processing, and small exercises. |
| [Hardware guide](docs/HARDWARE_GUIDE.md) | Purchasing gate, $100 budget constraint, conditional wiring, bench tests, and the body-connection boundary. |
| [Rev A hardware baseline](docs/HARDWARE_BASELINE_REV_A.md) | Selected ADS1299-4 + ESP32-S3 components, machine-readable BOM/profile, fail-closed gates, and ordered next work. |
| [Experiments guide](docs/EXPERIMENTS.md) | From synthetic alpha to a future controlled meditation experiment, without confusing artifacts with consciousness. |
| [Next-session handoff](docs/LLM_HANDOFF.md) | Give this to a future assistant together with the source and validation records. |

The earlier uploaded reports are background, not software dependencies. This package does not depend on their old ZIP links or on an AD8232/ADS1115.

## First run: Linux, macOS, or Windows

Use Python **3.11 or newer**; Python 3.13 is the development default. CI exercises clean locked installations on Linux with Python 3.11 and 3.13. macOS and Windows are not currently covered by that CI matrix. `pyproject.toml` and `uv.lock` define the current dependencies; `requirements-tested.txt` is a historical validation record.

Clone or extract the repository, then open a terminal **inside `eeg_ads1299_lab`**:

```bash
uv sync --locked --all-extras
uv run --locked python run_lab.py demo
uv run --locked python -m tools.check
```

Install **uv 0.12.18** first using the [official installation instructions](https://docs.astral.sh/uv/getting-started/installation/). The standalone installer supports an explicit version in its URL. All project commands use `uv`; do not use a separately activated environment or bare Python/pip to run or modify this project. The editable installation makes imports work outside the checkout too.

The demo makes `reports/demo/synthetic_recording.npz`, event/quality CSVs, an analysis JSON, and four PNG figures. Live commands default to ignored `reports/`; committed `results/` examples are historical evidence. Use `--out reports/my_demo` for a separate run. The seed is fixed, but numerical outputs can vary slightly across dependency versions.

The quality command checks formatting, Ruff lint, strict Pyrefly typing, cognitive complexity, Tach import boundaries, the hardware baseline, software tests, and measured branch coverage. It includes the hardware-baseline tests that formerly needed a separate discovery command. Logs and reports go under `reports/check/`, not over historical evidence.

**A successful software check is not a native-simulator, firmware-target, or hardware pass.** Run the explicit native command below for native integration. `uv run --locked python run_lab.py verify` is now a compatibility entry point to the **same** `tools.check` gate. Add `--native` for native integration; `--require-ngspice` remains an alias. There is no competing historical-report verifier.

Before making changes, read [AGENTS.md](AGENTS.md) and install both the pre-commit and commit-message hooks:

```bash
uv run --locked pre-commit install
```

## Run a circuit simulation

```bash
uv run --locked python run_lab.py circuits --out reports/circuits
```

This solves the existing illustrative passive circuit using Python's linear algebra, writes response/tolerance CSVs, and exports two `.cir` files. The numerical solver is **not ngspice**. There is no transistor-level ADS1299 model, and the next Rev A-specific input-network model is separate work.

For a real ngspice cross-check and the full native gate on Debian/Ubuntu/Linux Mint:

```bash
sudo apt update
sudo apt install --no-install-recommends ngspice g++ nodejs
uv run --locked python run_lab.py circuits --require-ngspice --out reports/circuits
uv run --locked python -m tools.check --native
```

The strict commands fail when required tools are absent. The DX CI run recorded in [DX_VALIDATION.md](docs/DX_VALIDATION.md) actually executed ngspice and compared both educational circuits with the independent numerical solution. That newer CI evidence does not change what ran in the original historical validation environment. Simulator logs remain under the output folder.

## Three useful changes

```bash
# Negative control: remove the planted condition difference.
uv run --locked python run_lab.py demo --null-effect --out reports/my_null

# Eight physical channels and 60-Hz residual line interference.
uv run --locked python run_lab.py demo --channels 8 --line-hz 60 --out reports/eight_channels

# Edit a copy of this JSON to change gain, offset, or artifact size.
uv run --locked python run_lab.py demo --config configs/demo.json --out reports/custom
```

Changing a JSON changes the **simulation**, not a physical board. The firmware does not read `configs/demo.json` or the board-review worksheet.

## Test the recording path with no electronics

```bash
uv run --locked python -m tools.check --native
```

The native gate includes the real localhost UDP loopback: nine seconds of synthetic packets with samples 1000 and 2000 deliberately omitted, CSV decoding, and a gap-safe quality report. It checks 2,248 accepted packets and two missing samples. Unexpected extra loss causes a failure rather than a reassuring-looking plot. To run only the loopback, use `uv run --locked python -m tools.run_loopback --out reports/loopback`.

For manual control, use two terminals:

```bash
# Terminal A
uv run --locked python run_lab.py receive --seconds 15 --out reports/practice.bin
```

```bash
# Terminal B, while A is listening
uv run --locked python run_lab.py replay --seconds 8 --drop-every 1000
```

Then:

```bash
uv run --locked python run_lab.py decode reports/practice.bin --out reports/practice.csv
uv run --locked python run_lab.py inspect reports/practice.csv --out reports/practice_quality
```

Keep the `.json` metadata beside the decoded CSV. New captures include a SHA-256 binding the pair; inspection rejects a mismatched generation. Legacy captures without a digest remain readable with an explicit caution. The inspector analyzes only uninterrupted four-second windows. It reports DC offset separately and never fills gaps to manufacture a continuous spectrum. The receiver defaults to localhost; actual LAN use requires `--host 0.0.0.0`, private-network firewall permission, and the computer's LAN address in the firmware. UDP is unencrypted; never expose the port to the public internet.

## What is in the source?

```text
lab/adc.py              Ideal code scaling, range/headroom checks, sinc³ model
lab/analog/            Public analog facade; internal solver, SPICE, and report modules
lab/data_types.py      Typed numerical arrays and data/report contracts
lab/validation.py      Runtime validation at external-data boundaries
lab/signals.py          Deterministic, explicitly synthetic recordings
lab/dsp.py              Quality screens, band power, session-held-out classifier
lab/protocol.py         ADS frame decoding, custom packets, CRC and counters
lab/acquisition.py      UDP/optional bench serial logging and CSV decoding
lab/inspect_capture.py  Gap-safe bench spectra and quality reports
lab/recording.py        Synthetic recording validation and atomic NPZ persistence
lab/pipeline.py         Demo outputs and figures; compatibility persistence re-exports
hardware/rev_a/         Hardware-contract facade, checker, data, and tests
firmware/              Original-ESP32 bench starter; NOT target-compiled by the DX gate
configs/               Editable demo settings and hardware-review worksheet
results/               Historical example recordings, figures, logs, and reports
reports/               Ignored outputs from current quality/simulation runs
tests/                 Regression, property, architecture, and workflow tests
tools/check.py         Shared local/CI quality command
tools/commit_messages.py Conventional Commit hook and actual-history validation
tach.toml              Enforced public interfaces and dependency direction
```

The firmware's default `BOARD_PROFILE_REVIEWED = false` intentionally prevents acquisition startup. Changing that setting acknowledges **bench digital wiring only**, not body-use approval. Do not bypass it just to see a waveform.

## Contributing: uv and Conventional Commits

Use `uv sync --locked --all-extras` and `uv run --locked ...` for project work. Child processes launched with `sys.executable` inherit that locked interpreter; they do not create a second environment. CI bootstraps uv itself separately, then uses the same locked commands.

Commit subjects follow [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/):

```text
feat(simulation): add a Rev A input-network sweep
fix(recording): reject discontinuous sample times
refactor(acquisition): stream decoded packets
chore(dx): synchronize issue labels
```

Use lowercase `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, or `revert`; an optional lowercase scope describes the affected component. A breaking change uses `!` after the type/scope and should explain the incompatibility in a `BREAKING CHANGE:` footer. Subjects must have a nonempty description and no trailing whitespace.

The installed `commit-msg` hook checks the subject. CI checks **actual commits introduced by the PR**, not just its title. Old history is grandfathered. Actual merge commits are exempt, but writing “Merge” on a single-parent commit is not a bypass. **Merge PRs with merge commits: no squash and no history rewriting.** Validate a range locally with:

```bash
uv run --locked python -m tools.commit_messages --base origin/main --head HEAD
uv run --locked python -m tools.check --native
```

Issues use one `type/*`, one `priority/*`, and applicable `area/*` labels. Examples: `type/bug` + `priority/high` + `area/acquisition`, or `type/refactor` + `priority/medium` + `area/dx`. [The label manifest](.github/labels.json) owns names, colors, and descriptions; trusted-main housekeeping synchronizes it without deleting unrelated labels. Merged same-repository PR branches are removed only after ancestry and exact-head checks. Active or changed branches are retained.

Read [the adversarial review](docs/ADVERSARIAL_REVIEW.md) for the architecture verdict, reproduced failures, corrections, and remaining limits.

## Troubleshooting

| Symptom | First action |
|---|---|
| `ModuleNotFoundError` | Run `uv sync --locked --all-extras` and use `uv run --locked` with the repository environment. |
| Missing ngspice or native compiler | Install the required tool; do not count numerical Python tests as native execution. |
| Quality gate failed | Read the named log and `reports/check/CHECK_REPORT.json`; do not bypass the check. |
| `All epochs rejected` | Inspect gain, differential DC offset, and quality flags. An overrange input is an expected negative test. |
| No UDP packets | First repeat localhost loopback. Then inspect the private LAN address, firewall, and UDP port. |
| No four-second spectral windows | The capture is too short or fragmented. Fix acquisition before interpreting spectra. |
| Unexpected ESP32 or board pins | Stop; the supplied firmware pin map is not generic to every ESP32/ADS1299 module. |
| Matplotlib cache permission warning | Set `MPLCONFIGDIR` to a writable directory; no special font installation is required. |

Read [SOURCES.md](docs/SOURCES.md) for primary references and [MODEL_SCOPE.md](docs/MODEL_SCOPE.md) for model boundaries.
