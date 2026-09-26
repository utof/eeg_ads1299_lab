# Host doubles for the actual sketch startup boundary

These minimal headers let `native_sketch_startup_test.cpp` compile and execute the
real `.ino` up to its first `SPI.begin`. They record software calls; they do not
emulate the ESP32, model electrical rails or validate peripheral behavior. The
Wi-Fi/UDP bodies exist only because the full sketch must compile; those paths
are not exercised or represented as transport tests.

The default reviewed-false header runs unchanged in the review-stop scenario.
Other scenarios change only a temporary copied header. There is no production
bypass macro and the real header must remain byte-identical after every test.
Fake time bounds infinite confirmation/halt loops. Each scenario has a separate
process, preventing state or serial replies from leaking between runs.

Seven scenarios cover the unchanged guard, no reply, prequeued replies, only a
fresh R, an early/queued V, both fresh replies and an injected GPIO latch failure.
Five deliberate source mutations must compile and then fail behavioral checks:
remove the review stop, accept queued replies, skip the sequence, request the
wrong VCAP key, or ignore GPIO failure. They supplement—not replace—the timing
and pin-operation mutants in `test_firmware_startup.py`.

Run `uv run --locked python -m pytest tests/test_firmware_sketch_startup.py -q`
with g++ or clang++; missing compilers produce native skips, not execution
passes. The native CI job executes this through the existing `tools.check`
entry point; no new orchestrator or dependency is introduced. Real target
compilation remains the separate pinned Arduino/S3 workflow.
