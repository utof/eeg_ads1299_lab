"""Bounded bench capture/replay and streaming, gap-preserving decoding.

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
        "sequence",
        "device_time_us",
        "elapsed_s",
        "missing_before",
        "flags",
        "overruns",
        "status",
        *(f"ch{i + 1}_count" for i in range(channels)),
        *(f"ch{i + 1}_uV" for i in range(channels)),
    ]


def _csv_row(packet: Packet, info: TrackerInfo, adc: ADCConfig) -> list[str | int | float]:
    uv: FloatArray = np.asarray(to_volts(np.asarray(packet.codes, dtype=np.int32), adc)) * 1e6
    return [
        packet.sequence,
        packet.time_us,
        info["elapsed_us"] / 1e6,
        info["missing_before"],
        packet.flags,
        packet.overruns,
        f"{packet.status:06x}",
        *packet.codes,
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
            "synthetic"
            if first.flags & 4
            else "internal_test"
            if first.flags & 1
            else "internal_short"
            if first.flags & 2
            else "external_unreviewed"
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
        staged_csv, staged_metadata = (
            Path(directory) / "capture.csv",
            Path(directory) / "capture.json",
        )
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
