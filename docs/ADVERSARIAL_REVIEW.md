# Adversarial architecture review

Review baseline: `e52200d6a3a3334f220ac28f1a1b8e52b80359bf`, after merge-commit merges of PRs #1 and #2. Tracking: issues #3–#8 and PR #9.

## Verdict

Keep the small modular monorepo. The analog model / solver / SPICE boundary / report split is justified. Separate hardware contracts from numerical simulation; a hardware document must not import scientific software to check its static declarations. Do not add a plugin framework, service layer, repository layer, or blanket facade package for every tiny file.

The problems were ownership and runtime invariants, not a lack of layers. Persistence belonged to plotting/orchestration; two verification commands disagreed about the gate; a streaming-looking decoder accumulated its entire input; and editable hardware limits could validate themselves. Types and a complexity ceiling did not catch these.

## Reproduced failures

Before implementation, [run 35933236114](https://github.com/utof/eeg_ads1299_lab/actions/runs/35933236114) executed the added behavioral tests: **22 failed, 2 passed**. Failures covered recording counts/time/labels, mutable hardware limits and guard promises, nonfinite input reaching I/O, the alternate verifier, stale reports/spectra, and capture memory. The 20,000-packet decode retained **13,928,811 bytes** for a 740,000-byte raw file.

## Structural corrections

- `lab.recording` owns synthetic persistence and validation. The pipeline keeps compatibility re-exports, not pass-through functions. DSP validates the same contract before filtering.
- `tools.check` is the only verification orchestrator. `run_lab.py verify` delegates to it; the competing historical writer is removed. Live defaults use ignored `reports/`.
- Capture decoding stores bounded parser/tracker state and stages output. A SHA-256 binds new CSV/JSON generations; inspection verifies and reads the same file descriptor. Two renames are **not** claimed to be one atomic transaction.
- Hardware validation pins reviewed rail limits and integration promises, and rejects nonfinite numbers. Hardware JSON, firmware, selected parts and all false gates are unchanged.
- A new circuit/inspection attempt invalidates old success artifacts. Old spectra cannot survive a new short capture and masquerade as new measurements.

## Growth limits and deliberately rejected churn

Offline analysis and CSV inspection are still batch operations; this change does not claim constant-memory analysis of arbitrarily long recordings. A future real-data importer needs explicit events/montage/session semantics rather than weakening the synthetic contract. Keep models pure and introduce board-specific simulations by composition over the analog API, not board-name branches inside its solver.

The hardware checker is below the 1,000-line review threshold; scattering its schema across arbitrary files would move complexity rather than remove it. The self-contained teaching HTML is preserved as an educational artifact, not a destination for new simulation logic. Existing numerical, transport and native regression tests remain necessary; the audit does not prove absence of all defects.

No result here is an ESP32-S3 target build, physical measurement, completed schematic review, purchasing approval or permission for body connection.
