# Power pilot recovery and independent review

This is a correction to the compatibility investigation in
`TPS7A20_COMPATIBILITY.md`, not a claim that the regulator model or board is
validated. No vendor-library bytes, model parameters, voltage tolerances,
hardware JSON, dependencies or firmware settings changed.

## Failure-first evidence

The recovered PR #26 initially conflated an incomplete switch trajectory with
a completed incompatible endpoint. That first review correction was preserved
when the branch was reconciled with main. A further focused Codex review
identified an unbounded caller-supplied archive read and missing diagnostics
when the simulator version probe fails.

Test-only commit `65a20db96cf6a0dd3377e25ad961ea3e82489919` reached runtime
checks in run `36194322084`: eight intended failures, 468 passing software tests
and five passing subtests. The preceding test commit had stopped at a typing
diagnostic in a recovered fixture; that was corrected separately, without
changing any behavioral assertion.

Intermediate source `7e74fa5dc0f0cc972622990126687f668aaf8fe9` passed both
Python quality jobs and the actual S3 compile, but failed one real native test
in run `36194892452`: a switch integration shortened from 10 us to 5 us was
accepted after `linearize` padded its exported table back to 10 us. The other
43 native/integration tests passed. This was an executed false positive, not
just a source-review suspicion.

## Corrected boundaries

Both switch and optional vendor exporters now record raw integration endpoints
before output interpolation. The existing shared transient runner requires a
fresh `transient-window.txt` and verifies the requested stop time. A padded
output table alone cannot establish completion. The six handwritten native
fixtures must all complete, including the inverse-switch cases whose completed
voltage mismatch is an investigation result rather than a simulator pass.

Process errors and incomplete switch runs retain `outcome: rejected`,
`window_complete: false`, and `compatible_endpoint: null`. Completed vendor
windows with incorrect plateaus remain distinguishable from incomplete runs.
Only the declared sampled plateau sanity check is performed; this is not a
continuous-time regulation or datasheet accuracy guarantee.

Archive input uses one open descriptor, rejects non-regular files and reads at
most 4,000,001 bytes before enforcing the 4,000,000-byte limit. Nonblocking open
avoids waiting for a POSIX FIFO writer. Hash checks still precede ZIP parsing
and the optional exact one-line edit. Synthetic ZIP fixtures test the adapter;
they are explicitly not TI-model execution. No archive member is extracted to
a caller-chosen path, and neither original nor adapted vendor library is
included in report artifacts.

Version-probe timeout, nonzero exit, launch failure and empty output retain
`ngspice-version.log` in a unique attempt directory. They fail without publishing
`pilot.json` or a completion manifest. Subprocess and archive limits do not
promise availability against a malicious filesystem, OS or external writer.

## Verification scope

The recovered e820ffc simulation baseline was rerun locally: 443 software tests
plus five subtests, 36 native/integration tests, all shared quality checks and
600/758 branches (79.16%, unchanged 71% floor). The recovered local ngspice
binary lacks its XSPICE compiled-model installation, so the new VSWITCH native
fixtures require the complete CI installation. Do not turn that environment
limitation into a vendor-model or physical-device failure.

Final candidate CI, not this document, establishes the integrated result.
Require Python 3.11/3.13, Native integration and ESP32-S3 target compile on the
final PR head. Normal quality jobs exercise GitHub's merge checkout; Firmware
explicitly builds the head SHA. No optional vendor startup/shutdown rerun was
performed during this recovery correction; the original observed failures
remain dated evidence and are not silently promoted to success.
