# Rev A component baseline

Read [the hardware decision](../../docs/HARDWARE_BASELINE_REV_A.md) first.

**Selected:** ADS1299-4PAGR, ESP32-S3-DevKitC-1-N8R8, internal ADC reference/clock,
5 V unipolar bench power, and ADC-only TPS7A2033PDBVR regulation.

**Not authorized:** fabrication, purchasing, external-input operation or body connection.
The review flags are deliberately false. These JSON files are a design contract,
not a firmware implementation or a validated KiCad schematic.

```bash
python hardware/rev_a/check_baseline.py
python -m unittest discover -s hardware/rev_a -p 'test_*.py' -v
```

Run those commands from the repository root. Python 3.10+ and no third-party
packages are required. The checker also works when invoked by absolute path.

- `board_profile.json`: selected operating point, proposed GPIO/header assignments and review gates.
- `bom.json`: exact selected MPNs, reference counts, FIT/DNP population and planning costs.
- `sources.json`: primary sources, original-report SHA-256 hashes and access limitations.

This baseline was integrated after inspecting live `main` at
`31205de841c577c373532fbc9d065fa81d0a6ac8`. The existing firmware remains
unchanged and its board/target review guard stays fail-closed. The repository's
entry-point docs link here so future work does not reopen the component decision
by accident. Run the existing project tests and ngspice baseline on this branch
before changing the analog model or porting firmware to the S3.
