"""One-shot, reviewed source edits; removed before the quality gate and commit."""
from pathlib import Path


def edit(name: str, before: str, after: str) -> None:
    path = Path(name)
    text = path.read_text(encoding="utf-8")
    if text.count(before) != 1:
        raise RuntimeError(f"Expected exactly one reviewed fragment in {name}: {before[:100]!r}")
    path.write_text(text.replace(before, after), encoding="utf-8")


Path("lab/recording.py").write_text(r'''"""Synthetic recording persistence and its runtime data contract.

This is deliberately not a live-EEG importer. Arrays have one owner for dtype,
units, label consistency and continuity checks; filtering must not repair them.
"""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from .adc import MAX_CODE, MIN_CODE
from .data_types import Recording
from .signals import parse_metadata
from .validation import read_object, stored_array


def validate_recording(value: object) -> Recording:
    """Return a checked typed view, without copying the numerical buffers."""
    values = read_object(value, "recording")
    try:
        data: Recording = {
            "codes": stored_array(values["codes"], np.int32, 2, "codes"),
            "session": stored_array(values["session"], np.int16, 1, "session"),
            "block": stored_array(values["block"], np.int16, 1, "block"),
            "condition": stored_array(values["condition"], np.int8, 1, "condition"),
            "time_s": stored_array(values["time_s"], np.float64, 1, "time_s"),
            "invalid": stored_array(values["invalid"], np.bool_, 2, "invalid"),
            "artifact_truth": stored_array(values["artifact_truth"], np.bool_, 1, "artifact_truth"),
            "metadata": parse_metadata(values["metadata"]),
        }
    except KeyError as exc:
        raise ValueError(f"Recording missing field: {exc}") from exc
    _validate_alignment(data)
    _validate_blocks(data)
    _validate_sessions(data)
    return data


def _validate_alignment(data: Recording) -> None:
    samples = len(data["codes"])
    cfg = data["metadata"]
    expected = (samples, cfg["channels"])
    if samples == 0 or data["codes"].shape != expected or data["invalid"].shape != expected:
        raise ValueError("codes/invalid: empty recording or channel/sample count mismatch")
    lengths = {
        "session": len(data["session"]),
        "block": len(data["block"]),
        "condition": len(data["condition"]),
        "time_s": len(data["time_s"]),
        "artifact_truth": len(data["artifact_truth"]),
    }
    for name, length in lengths.items():
        if length != samples:
            raise ValueError(f"{name}: sample count mismatch")
    if np.any(data["codes"] < MIN_CODE) or np.any(data["codes"] > MAX_CODE):
        raise ValueError("counts must be signed 24-bit ADC values")
    if not np.all(np.isin(data["condition"], [0, 1])):
        raise ValueError("condition must be 0 or 1")
    if np.any(data["session"] < 0) or np.any(data["session"] >= cfg["sessions"]):
        raise ValueError("session identifier outside metadata range")
    if np.any(data["block"] < 0) or np.any(data["block"] >= cfg["sessions"] * cfg["blocks_per_session"]):
        raise ValueError("block identifier outside metadata range")
    if np.any(data["time_s"] < 0):
        raise ValueError("time_s must be nonnegative")


def _validate_blocks(data: Recording) -> None:
    for block in np.unique(data["block"]):
        indices = np.flatnonzero(data["block"] == block)
        if not np.all(np.diff(indices) == 1):
            raise ValueError("Noncontiguous block: identifiers must not be reused")
        if len(np.unique(data["session"][indices])) != 1:
            raise ValueError("A block must belong to exactly one session")
        if len(np.unique(data["condition"][indices])) != 1:
            raise ValueError("A block must contain exactly one condition")


def _validate_sessions(data: Recording) -> None:
    period = 1.0 / data["metadata"]["fs_hz"]
    for session in np.unique(data["session"]):
        indices = np.flatnonzero(data["session"] == session)
        if not np.all(np.diff(indices) == 1):
            raise ValueError("Noncontiguous session: identifiers must not be reused")
        steps = np.diff(data["time_s"][indices])
        if not np.allclose(steps, period, rtol=1e-9, atol=1e-9):
            raise ValueError("time_s discontinuity: synthetic samples must be uniformly spaced")


def load_data(path: str | Path) -> Recording:
    try:
        with np.load(path, allow_pickle=False) as archive:
            names = ("codes", "session", "block", "condition", "time_s", "invalid", "artifact_truth")
            values: dict[str, object] = {name: archive[name] for name in names}
            raw: object = archive["metadata_json"]
            if not isinstance(raw, np.ndarray) or raw.ndim != 0 or raw.dtype.kind != "U":
                raise ValueError("metadata_json must be a scalar Unicode string")
            values["metadata"] = json.loads(str(raw))
    except KeyError as exc:
        raise ValueError(f"Recording archive missing field: {exc}") from exc
    return validate_recording(values)


def save_data(data: Recording, path: str | Path) -> None:
    data = validate_recording(data)
    path = Path(path)
    if not str(path).endswith(".npz"):
        path = Path(str(path) + ".npz")
    path.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".recording-", dir=path.parent) as directory:
        staged = Path(directory) / "recording.npz"
        np.savez_compressed(
            staged,
            codes=data["codes"],
            session=data["session"],
            block=data["block"],
            condition=data["condition"],
            time_s=data["time_s"],
            invalid=data["invalid"],
            artifact_truth=data["artifact_truth"],
            metadata_json=np.array(json.dumps(data["metadata"], allow_nan=False)),
        )
        staged.replace(path)
''', encoding="utf-8")

Path("lab/acquisition.py").write_text(r'''"""Bounded bench capture/replay and streaming, gap-preserving decoding.

UDP is local-network, unencrypted. Never use public Wi-Fi for recordings.
Transport CRC cannot detect a wrong SPI word checksummed by the firmware.
"""

import csv
import hashlib
import json
import math
import socket
import time
from collections.abc import Generator
from contextlib import closing
from itertools import chain
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from .adc import ADCConfig, to_volts
from .data_types import CaptureSummary, FloatArray, TrackerInfo
from .protocol import CHANNELS, FLAG_SYNTHETIC, Packet, StreamDecoder, Tracker


def _duration(seconds: float) -> None:
    if isinstance(seconds, bool) or not math.isfinite(seconds) or seconds <= 0:
        raise ValueError("Capture duration must be finite and positive")


def _udp_options(seconds: float, port: int) -> None:
    _duration(seconds)
    if type(port) is not int or not 0 <= port <= 65535:
        raise ValueError("UDP port must be an integer in [0, 65535]")


def capture_udp(
    path: str | Path, seconds: float = 10, host: str = "127.0.0.1", port: int = 9000
) -> dict[str, int]:
    _udp_options(seconds, port)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    counts = {"datagrams": 0, "valid_packets": 0, "invalid_packets": 0}
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((host, port))
        sock.settimeout(0.2)
        print(f"Listening on {host}:{sock.getsockname()[1]} for {seconds:g} s", flush=True)
        with path.open("wb") as stream:
            end = time.monotonic() + seconds
            while time.monotonic() < end:
                try:
                    data, _ = sock.recvfrom(4096)
                except TimeoutError:
                    continue
                counts["datagrams"] += 1
                try:
                    Packet.decode(data)
                except ValueError:
                    counts["invalid_packets"] += 1
                    continue
                stream.write(data)
                counts["valid_packets"] += 1
    path.with_suffix(".capture.json").write_text(json.dumps(counts, indent=2), encoding="utf-8")
    return counts


def capture_serial(
    path: str | Path, port: str, seconds: float = 10, baud: int = 460800
) -> dict[str, int | str]:
    _duration(seconds)
    if type(baud) is not int or baud <= 0 or not port.strip():
        raise ValueError("Serial capture requires a port and positive integer baud rate")
    try:
        import serial
    except ImportError as exc:
        raise RuntimeError("Run uv sync --locked --extra serial to capture USB serial") from exc
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    # Bench only: disconnect EVERY body electrode, not just the signal channel.
    with serial.Serial(port, baudrate=baud, timeout=0.2) as ser, path.open("wb") as stream:
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            data = ser.read(max(1, ser.in_waiting))
            stream.write(data)
            total += len(data)
    return {"bytes": total, "transport": "serial_bench_only"}


def _accepted_packets(
    path: Path, decoder: StreamDecoder, tracker: Tracker
) -> Generator[tuple[Packet, TrackerInfo], None, None]:
    with path.open("rb") as stream:
        while chunk := stream.read(65536):
            for packet in decoder.feed(chunk):
                info = tracker.observe(packet)
                if info is not None:
                    yield packet, info


def _csv_fields(channels: int) -> list[str]:
    return [
        "sequence", "device_time_us", "elapsed_s", "missing_before", "flags", "overruns", "status",
        *(f"ch{i + 1}_count" for i in range(channels)),
        *(f"ch{i + 1}_uV" for i in range(channels)),
    ]


def _csv_row(packet: Packet, info: TrackerInfo, adc: ADCConfig) -> list[str | int | float]:
    uv: FloatArray = np.asarray(to_volts(np.asarray(packet.codes, dtype=np.int32), adc)) * 1e6
    return [
        packet.sequence, packet.time_us, info["elapsed_us"] / 1e6, info["missing_before"],
        packet.flags, packet.overruns, f"{packet.status:06x}", *packet.codes,
        *(float(value) for value in uv),
    ]


def _capture_summary(
    first: Packet, tracker: Tracker, decoder: StreamDecoder, vref_v: float
) -> CaptureSummary:
    last = tracker.last
    assert last is not None, "summary requires an accepted packet"
    tracked = tracker.summary()
    return {
        "accepted": tracked["accepted"],
        "missing": tracked["missing"],
        "duplicates": tracked["duplicates"],
        "stale": tracked["stale"],
        "timing_anomalies": tracked["timing_anomalies"],
        "channels": len(first.codes),
        "gain": first.gain,
        "fs_hz": first.fs_hz,
        "assumed_vref_v": vref_v,
        "discarded_bytes": decoder.discarded_bytes,
        "invalid_candidates": decoder.invalid_candidates,
        "trailing_bytes": len(decoder.buffer),
        "last_device_overruns": last.overruns,
        "flags": first.flags,
        "gap_policy": "retain gaps; do not interpolate or bridge for FFT",
        "recording_mode": (
            "synthetic" if first.flags & 4 else "internal_test" if first.flags & 1
            else "internal_short" if first.flags & 2 else "external_unreviewed"
        ),
    }


def _write_capture(path: Path, out_csv: Path, vref_v: float) -> CaptureSummary:
    decoder, tracker = StreamDecoder(), Tracker()
    with closing(_accepted_packets(path, decoder, tracker)) as packets:
        first_pair = next(packets, None)
        if first_pair is None:
            raise ValueError("No valid forward-moving packets found")
        first, _ = first_pair
        adc = ADCConfig(gain=first.gain, fs_hz=first.fs_hz, vref_v=vref_v)
        with out_csv.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(_csv_fields(len(first.codes)))
            for packet, info in chain((first_pair,), packets):
                writer.writerow(_csv_row(packet, info, adc))
    return _capture_summary(first, tracker, decoder, vref_v)


def decode_capture(path: str | Path, out_csv: str | Path, vref_v: float = 4.5) -> CaptureSummary:
    """Stream into staged outputs; a digest binds each new CSV/metadata pair.

    Two renames are not one atomic transaction. Readers verify the digest, so
    interruption between renames is detected rather than accepted as a valid pair.
    Decode failures before publication leave any prior output pair untouched.
    """
    ADCConfig(vref_v=vref_v)
    path, out_csv = Path(path).resolve(), Path(out_csv).resolve()
    metadata = out_csv.with_suffix(".json")
    if path in (out_csv, metadata) or metadata == out_csv:
        raise ValueError("Capture input, CSV output and metadata must be distinct paths")
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".decode-", dir=out_csv.parent) as directory:
        staged_csv, staged_metadata = Path(directory) / "capture.csv", Path(directory) / "capture.json"
        summary = _write_capture(path, staged_csv, vref_v)
        with staged_csv.open("rb") as stream:
            summary["csv_sha256"] = hashlib.file_digest(stream, "sha256").hexdigest()
        staged_metadata.write_text(json.dumps(summary, indent=2, allow_nan=False), encoding="utf-8")
        staged_csv.replace(out_csv)
        staged_metadata.replace(metadata)
    return summary


def replay_packets(
    host: str = "127.0.0.1",
    port: int = 9000,
    seconds: float = 3,
    channels: int = 4,
    fs_hz: int = 250,
    drop_every: int = 0,
) -> dict[str, int | bool]:
    _udp_options(seconds, port)
    ADCConfig(fs_hz=fs_hz)
    if channels not in CHANNELS or type(drop_every) is not int or drop_every < 0 or port == 0:
        raise ValueError("Invalid replay options")
    end = int(seconds * fs_hz)
    start = time.monotonic()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        for seq in range(end):
            deadline = start + seq / fs_hz
            wait = deadline - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            if drop_every and seq and seq % drop_every == 0:
                continue
            amplitudes: FloatArray = np.asarray(
                [500 * np.sin(2 * np.pi * 10 * seq / fs_hz + 0.1 * c) for c in range(channels)],
                dtype=np.float64,
            )
            codes = tuple(int(value) for value in amplitudes)
            packet = Packet(
                seq, int(seq * 1e6 / fs_hz) & 0xFFFFFFFF, codes, fs_hz=fs_hz, flags=FLAG_SYNTHETIC
            )
            sock.sendto(packet.encode(), (host, port))
    return {"generated_samples": end, "synthetic": True}
''', encoding="utf-8")

# Persistence moves out of plotting/orchestration. Compatibility uses re-exports, not wrappers.
pipeline = Path("lab/pipeline.py")
p = pipeline.read_text(encoding="utf-8")
start, end = p.index("def save_data("), p.index("def make_plots(")
p = p[:start] + p[end:]
p = p[:p.index('\n\nScalar = TypeVar("Scalar", bound=np.generic)')] + "\n"
p = p.replace("from typing import TypeVar\n", "").replace("from numpy.lib.npyio import NpzFile\n", "").replace("from numpy.typing import NDArray\n", "")
p = p.replace("from .signals import SyntheticConfig, generate, parse_metadata", "from .signals import SyntheticConfig, generate")
p = p.replace("from .validation import stored_array", "from .recording import load_data as load_data\nfrom .recording import save_data as save_data")
pipeline.write_text(p, encoding="utf-8")
edit("lab/dsp.py", "from .validation import float_array", "from .recording import validate_recording\nfrom .validation import float_array")
edit("lab/dsp.py", '    cfg = data["metadata"]\n', '    data = validate_recording(data)\n    cfg = data["metadata"]\n')
edit("lab/dsp.py", '        # Dataset uses contiguous blocks; refusing otherwise prevents bridging.\n        if not np.all(np.diff(indices) == 1):\n            raise ValueError("Noncontiguous block")\n', '        # The recording boundary has already verified continuity and labels.\n')
edit("lab/signals.py", "from dataclasses import dataclass, fields", "from dataclasses import dataclass, fields\nfrom math import isclose")
edit("lab/signals.py", '    return _metadata(\n        cfg,\n        number(values, "adc_lsb_v"),\n        number(values, "surrogate_filter_delay_s"),', '    scale = number(values, "adc_lsb_v")\n    delay = number(values, "surrogate_filter_delay_s")\n    expected_scale = ADCConfig(gain=cfg.gain, fs_hz=cfg.fs_hz).lsb_v\n    if not isclose(scale, expected_scale, rel_tol=1e-12, abs_tol=0.0):\n        raise ValueError("adc_lsb_v scale disagrees with the synthetic ADC configuration")\n    if delay < 0:\n        raise ValueError("surrogate_filter_delay_s must be nonnegative")\n    return _metadata(\n        cfg,\n        scale,\n        delay,')
edit("lab/data_types.py", '    recording_mode: str\n\n\nclass InspectionReport', '    recording_mode: str\n    csv_sha256: NotRequired[str]\n\n\nclass InspectionReport')

# A digest check and parsing share the same file descriptor, avoiding a rename race.
edit("lab/inspect_capture.py", "import csv\n", "import csv\nimport hashlib\nimport io\n")
edit("lab/inspect_capture.py", '    metadata_path = csv_path.with_suffix(".json")\n', '    metadata_path = csv_path.with_suffix(".json")\n    outputs = (out_dir / "spectrum.csv", out_dir / "quality_report.json")\n    if any(p.resolve() in (csv_path.resolve(), metadata_path.resolve()) for p in outputs):\n        raise ValueError("Inspection output must not overwrite its input")\n    out_dir.mkdir(parents=True, exist_ok=True)\n    for output in outputs:\n        output.unlink(missing_ok=True)\n')
edit("lab/inspect_capture.py", '    x, counts, times, sequence = _read_capture(csv_path, n)\n', '    digest = text(metadata, "csv_sha256") if "csv_sha256" in metadata else None\n    x, counts, times, sequence = _read_capture(csv_path, n, digest)\n')
edit("lab/inspect_capture.py", '    out_dir.mkdir(parents=True, exist_ok=True)\n    if spectra', '    if digest is None:\n        result["cautions"].append("Legacy capture: no digest binds this CSV to its metadata.")\n    if spectra')
edit("lab/inspect_capture.py", '    csv_path: Path, n: int\n', '    csv_path: Path, n: int, expected_digest: str | None\n')
edit("lab/inspect_capture.py", '    with csv_path.open(newline="") as stream:\n        rows = list(csv.DictReader(stream))\n', '    with csv_path.open("rb") as binary:\n        actual_digest = hashlib.file_digest(binary, "sha256").hexdigest()\n        if expected_digest is not None and actual_digest != expected_digest:\n            raise ValueError("Capture CSV/metadata digest mismatch")\n        binary.seek(0)\n        with io.TextIOWrapper(binary, encoding="utf-8", newline="") as stream:\n            rows = list(csv.DictReader(stream))\n')

# The checked electrical envelope cannot be redefined by the input being checked.
edit("hardware/rev_a/check_baseline.py", '        if type(value) not in (int, float):\n            raise ValueError(f"{path}: expected a number, not {type(value).__name__}")', '        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):\n            raise ValueError(f"{path}: expected a finite number")')
edit("hardware/rev_a/check_baseline.py", '    try:\n        for document in (profile, bom, sources):', '    try:\n        _check_shape(profile, BoardProfile, "profile")\n        _check_shape(bom, BillOfMaterials, "bom")\n        _check_shape(sources, SourcesDocument, "sources")\n        for document in (profile, bom, sources):')
edit("hardware/rev_a/check_baseline.py", '        _validate_afe(profile, parts, bom, require)\n        _validate_network(profile, parts, bom, require)\n        _validate_power(profile, parts, bom, require)', '        _validate_afe(profile, parts, require)\n        _validate_network(profile, parts, require)\n        _validate_power(profile, parts, bom, require)\n        _validate_integration(profile, require)')
for name in ("_validate_afe", "_validate_network"):
    edit("hardware/rev_a/check_baseline.py", f'def {name}(\n    profile: BoardProfile,\n    parts: dict[str, BomItem],\n    bom: BillOfMaterials,', f'def {name}(\n    profile: BoardProfile,\n    parts: dict[str, BomItem],')
edit("hardware/rev_a/check_baseline.py", '    power = profile["power"]\n', '    power = profile["power"]\n    require(\n        power["avdd_operating_min_v"] == 4.75 and power["avdd_operating_max_v"] == 5.25,\n        "reviewed ADS operating rail limits must not be redefined",\n    )\n    require(\n        power["external_source_nominal_v"] == power["avdd_design_v"] == 5.0,\n        "reviewed 5 V bench source drift",\n    )\n    require(\n        0 <= power["external_source_tolerance_fraction"] <= 0.01\n        and power["analog_branch_design_current_budget_a"] == 0.01,\n        "reviewed source tolerance/current budget drift",\n    )\n    require(\n        power["common_ground"] is True\n        and power["battery_selected"] is False\n        and power["charger_fitted"] is False,\n        "bench power integration drift",\n    )\n')
edit("hardware/rev_a/check_baseline.py", '    require(\n        profile["integration"]["this_json_is_not_loaded_by_existing_firmware"] is True,\n        "this commit does not implement firmware integration",\n    )\n    require(\n        profile["integration"]["preserve_simulated_channel_counts"] == [4, 6, 8],\n        "retain multi-variant simulation support",\n    )\n', '')
edit("hardware/rev_a/check_baseline.py", '\ndef main() -> int:\n', '\ndef _validate_integration(profile: BoardProfile, require: Callable[[bool, str], None]) -> None:\n    integration = profile["integration"]\n    require(\n        integration["requires_explicit_s3_firmware_profile"] is True\n        and integration["do_not_remove_existing_target_guard"] is True\n        and integration["this_json_is_not_loaded_by_existing_firmware"] is True,\n        "explicit S3 port and existing target guards must remain required",\n    )\n    require(\n        integration["existing_firmware_modified"] is False\n        and integration["existing_model_defaults_modified"] is False,\n        "baseline must not claim firmware or educational-model modifications",\n    )\n    require(\n        integration["preserve_simulated_channel_counts"] == [4, 6, 8],\n        "retain multi-variant simulation support",\n    )\n\n\ndef main() -> int:\n')

# One verification owner. Historical evidence is not a live output directory.
Path("tools/validate.py").unlink()
edit("run_lab.py", '"""Entry point: python run_lab.py --help.', '"""Entry point: uv run --locked python run_lab.py --help.')
run_lab = Path("run_lab.py")
run_lab.write_text(run_lab.read_text(encoding="utf-8").replace('default=ROOT / "results/', 'default=ROOT / "reports/'), encoding="utf-8")
edit("run_lab.py", '    verify.add_argument("--require-ngspice", action="store_true")', '    verify.add_argument("--native", "--require-ngspice", dest="native", action="store_true")\n    verify.add_argument("--out", type=Path, default=ROOT / "reports/check")')
edit("run_lab.py", '        from tools.validate import validate\n\n        return validate(ROOT, args.require_ngspice)', '        from tools.check import main as check\n\n        options = ["--out", str(args.out)]\n        if args.native:\n            options.append("--native")\n        return check(options)')
edit("lab/analog/_report.py", '    out.mkdir(parents=True, exist_ok=True)\n', '    out.mkdir(parents=True, exist_ok=True)\n    report_path = out / "circuit_report.json"\n    report_path.unlink(missing_ok=True)\n    if require_ngspice and not shutil.which("ngspice"):\n        raise RuntimeError("Native SPICE validation required but ngspice unavailable; no SPICE pass claimed.")\n')
edit("lab/analog/_report.py", '    (out / "circuit_report.json").write_text(json.dumps(report, indent=2))\n    if require_ngspice and not shutil.which("ngspice"):\n        raise RuntimeError(\n            "Native SPICE validation required but ngspice unavailable; no SPICE pass claimed."\n        )', '    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")')

# Update the enforced dependency graph, not just Python imports.
edit("tach.toml", '[[modules]]\npath = "tools.validate"\ndepends_on = ["lab.analog"]\n\n', '')
edit("tach.toml", '[[interfaces]]\nfrom = ["tools.validate"]\nexpose = ["validate"]\n\n', '')
edit("tach.toml", '"tools.validate"', '"tools.check"')
edit("tach.toml", 'path = "lab.dsp"\ndepends_on = ["lab.adc", "lab.data_types", "lab.validation"]', 'path = "lab.dsp"\ndepends_on = ["lab.adc", "lab.data_types", "lab.recording", "lab.validation"]')
edit("tach.toml", 'path = "lab.pipeline"\ndepends_on = ["lab.adc", "lab.analog", "lab.data_types", "lab.dsp", "lab.signals", "lab.validation"]', 'path = "lab.pipeline"\ndepends_on = ["lab.adc", "lab.analog", "lab.data_types", "lab.dsp", "lab.recording", "lab.signals"]')
edit("tach.toml", 'expose = ["Scalar", "load_data", "make_plots", "run_demo", "save_data"]', 'expose = ["load_data", "make_plots", "run_demo", "save_data"]')
with Path("tach.toml").open("a", encoding="utf-8") as stream:
    stream.write('\n[[modules]]\npath = "lab.recording"\ndepends_on = ["lab.adc", "lab.data_types", "lab.signals", "lab.validation"]\n\n[[interfaces]]\nfrom = ["lab.recording"]\nexpose = ["load_data", "save_data", "validate_recording"]\n')

Path("tests/test_review_artifacts.py").write_text(r'''"""Publication failures must not corrupt raw input or masquerade as old evidence."""

import hashlib
import json
from pathlib import Path

import pytest

from lab.acquisition import decode_capture
from lab.inspect_capture import inspect_capture
from lab.protocol import Packet


def _raw(path: Path) -> Path:
    path.write_bytes(b"".join(Packet(i, i * 4000, (i, i, i, i)).encode() for i in range(8)))
    return path


def test_new_capture_pair_is_bound_by_digest(tmp_path: Path) -> None:
    csv_path = tmp_path / "capture.csv"
    result = decode_capture(_raw(tmp_path / "input.bin"), csv_path)
    assert result["csv_sha256"] == hashlib.sha256(csv_path.read_bytes()).hexdigest()
    metadata: object = json.loads(csv_path.with_suffix(".json").read_text())
    assert metadata == result


def test_inspection_rejects_mixed_generations(tmp_path: Path) -> None:
    csv_path = tmp_path / "capture.csv"
    decode_capture(_raw(tmp_path / "input.bin"), csv_path)
    with csv_path.open("a", encoding="utf-8") as stream:
        stream.write("\n")
    with pytest.raises(ValueError, match="digest mismatch"):
        inspect_capture(csv_path, tmp_path / "quality")
    assert not (tmp_path / "quality/quality_report.json").exists()


def test_failed_decode_preserves_previous_pair(tmp_path: Path) -> None:
    raw = _raw(tmp_path / "input.bin")
    csv_path = tmp_path / "capture.csv"
    decode_capture(raw, csv_path)
    csv_before = csv_path.read_bytes()
    metadata_before = csv_path.with_suffix(".json").read_bytes()
    raw.write_bytes(Packet(0, 0, (0, 0, 0, 0)).encode() + Packet(1, 4000, (0, 0, 0, 0), gain=12).encode())
    with pytest.raises(ValueError, match="Configuration changed"):
        decode_capture(raw, csv_path)
    assert csv_path.read_bytes() == csv_before
    assert csv_path.with_suffix(".json").read_bytes() == metadata_before
    assert not list(tmp_path.glob(".decode-*"))


@pytest.mark.parametrize("output_name", ["input.bin", "input.json"])
def test_decode_never_overwrites_input(tmp_path: Path, output_name: str) -> None:
    raw = _raw(tmp_path / output_name)
    before = raw.read_bytes()
    with pytest.raises(ValueError, match="distinct paths"):
        decode_capture(raw, raw)
    assert raw.read_bytes() == before


def test_empty_decode_does_not_publish(tmp_path: Path) -> None:
    raw, output = tmp_path / "empty.bin", tmp_path / "empty.csv"
    raw.write_bytes(b"broken")
    with pytest.raises(ValueError, match="No valid"):
        decode_capture(raw, output)
    assert not output.exists()
    assert not output.with_suffix(".json").exists()
''', encoding="utf-8")

Path("docs/ADVERSARIAL_REVIEW.md").write_text('''# Adversarial architecture review

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
''', encoding="utf-8")
