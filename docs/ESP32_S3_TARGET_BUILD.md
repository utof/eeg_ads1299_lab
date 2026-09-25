# Explicit ESP32-S3 compile target — not bench validation

This is an opt-in target build for the selected Rev A four-channel arrangement.
It does not release the schematic, validate wiring or permit hardware operation.
`BOARD_PROFILE_REVIEWED` stays **false** and the sketch halts before configuring
ADS control GPIOs. Internal test/short mux paths are the only acquisition modes;
BIAS, lead-off, SRB1 and Wi-Fi defaults remain disabled as before. No upload or
flashing command is part of the workflow.

## Profile contract

The new `board_config_rev_a_s3.h` contains the proposed GPIOs from the existing
validated hardware JSON: SCLK 12, MISO 13, MOSI 11, CS 10, DRDY 4, RESET 5,
START 6 and PWDN 7. Tests compare every pin with the hardware source of truth.
The header also requires the selected four-channel ADS1299 variant at runtime.
That check is reachable only after the separate wiring-review gate is approved;
this change does not approve it.

Selection requires the explicit compiler definition `EEGLAB_REV_A_S3`. Merely
choosing an S3 MCU does not silently select a wiring profile. The original
ESP32 default pin map and its target restriction are retained in `board_config.h`.
The S3 header rejects any target other than `CONFIG_IDF_TARGET_ESP32S3`.
Native compiler fixtures exercise accepted and rejected combinations. They are
header/guard tests, not a substitute for the real Xtensa/Arduino target build.

The baseline JSON's original `existing_firmware_modified: false` records the
scope of the historical hardware-baseline commit. This later, explicitly scoped
firmware PR supplies the planned S3 profile without changing that baseline or
setting `firmware_port_validated`, `board_profile_reviewed`, or any other gate.

## Reproducible toolchain

`firmware/toolchain.json` is the version/FQBN source for CI and `tools.check`.
The build uses Arduino CLI **1.3.1**, pinned to the official Linux amd64 package
SHA-256, and Arduino-ESP32 **3.3.12**, not a moving latest or release candidate.
The requested target has 8 MB flash and OPI PSRAM enabled in the build options;
the capture buffer still uses internal RAM. This is a compiler configuration,
not evidence that a particular physical module or PCB revision was inspected.

Primary provenance:
- https://github.com/arduino/arduino-cli/releases/tag/v1.3.1
- https://github.com/espressif/arduino-esp32/releases/tag/3.3.12
- https://espressif.github.io/arduino-esp32/package_esp32_index.json

The official core installer verifies its package checksums. The exact installed
CLI version, core list and board properties are retained with the build log.
The CLI binary is hash-checked before execution; project dependencies remain
managed by the unchanged Python lockfile.

After installing the versions in that file:

```bash
uv sync --locked --all-extras
uv run --locked python -m tools.check --firmware
```

The new `Firmware` workflow installs that toolchain and runs the same command.
The ordinary software and native/simulation jobs remain separate. Firmware mode
fails when the compiler or required versions are absent. Each target compile
uses a fresh output directory; a zero exit without new binary artifacts fails.
The CI checkout explicitly selects the PR head (or the push commit); it does not
call a synthetic merge checkout exact-head evidence.
`FIRMWARE_BUILD.json` records the source commit, source-file hashes, toolchain,
directory and binary SHA-256s with
all physical/review/body-use flags false. It is written only after success.
A new firmware request invalidates the old marker before even the ordinary
quality checks; an earlier failure cannot leave an old build looking current.

## Evidence and limits

The test-only commit precedes implementation and preserves the missing-profile
and missing-command failures. Consult the PR's **exact-head** `ESP32-S3 target
compile` job and retained artifact for whole-sketch evidence. No document alone
establishes that a new source revision compiled. The current environment cannot
cross-compile offline until the pinned Arduino toolchain is installed; the actual
cross-compile runs in the dedicated CI job.

Target compilation does not validate SPI timing, ISR latency, serial throughput,
reference/power wiring, regulator behavior, signal quality or body-interface
safety. A physical port remains unvalidated. The next step remains schematic/
pin review and person-disconnected bench testing, not connecting electrodes.
