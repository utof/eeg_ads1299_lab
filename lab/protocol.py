"""Self-describing lab transport around a native ADS1299 frame.

This is our protocol, NOT OpenBCI's format and NOT an ADS1299 on-wire command.
All integer metadata is little endian; native ADS channel words stay big endian.
"""

from __future__ import annotations

import binascii
import struct
from collections.abc import Iterable
from dataclasses import dataclass
from typing import SupportsInt

import numpy as np

from .adc import GAINS, MAX_CODE, MIN_CODE, RATES
from .data_types import TrackerInfo, TrackerSummary

MAGIC = b"E9"
VERSION = 1
HEADER = struct.Struct("<2sBBBBHIII")
FLAG_TEST = 1
FLAG_SHORT = 2
FLAG_SYNTHETIC = 4
FLAG_OVERRUN = 8
CHANNELS = (4, 6, 8)


def signed24(data: bytes | bytearray) -> int:
    if len(data) != 3:
        raise ValueError("A channel word must have exactly three bytes")
    value = int.from_bytes(data, "big")
    return value - (1 << 24) if value & (1 << 23) else value


def native_frame(codes: Iterable[SupportsInt], status: int = 0xC00000) -> bytes:
    values = list(codes)
    if len(values) not in CHANNELS or (status & 0xF00000) != 0xC00000:
        raise ValueError("Invalid ADS frame shape/status")
    if not 0 <= status <= 0xFFFFFF:
        raise ValueError("Invalid status")
    buf = bytearray(status.to_bytes(3, "big"))
    for x in values:
        if not isinstance(x, (int, np.integer)) or not MIN_CODE <= x <= MAX_CODE:
            raise ValueError("Signed 24-bit integer code required")
        buf.extend((int(x) & 0xFFFFFF).to_bytes(3, "big"))
    return bytes(buf)


def parse_native(frame: bytes | bytearray, channels: int) -> tuple[int, tuple[int, ...]]:
    if channels not in CHANNELS or len(frame) != 3 + 3 * channels:
        raise ValueError("Wrong native frame length")
    if frame[0] & 0xF0 != 0xC0:
        raise ValueError("Invalid ADS1299 status prefix")
    return (
        int.from_bytes(frame[:3], "big"),
        tuple(signed24(frame[i : i + 3]) for i in range(3, len(frame), 3)),
    )


@dataclass(frozen=True)
class Packet:
    sequence: int
    time_us: int
    codes: tuple[int, ...]
    gain: int = 24
    fs_hz: int = 250
    flags: int = FLAG_SYNTHETIC
    overruns: int = 0
    status: int = 0xC00000

    def encode(self) -> bytes:
        for x in (self.sequence, self.time_us, self.overruns):
            if not isinstance(x, int) or not 0 <= x <= 0xFFFFFFFF:
                raise ValueError("Metadata counter outside uint32")
        if self.gain not in GAINS or self.fs_hz not in RATES:
            raise ValueError("Unsupported gain/rate")
        if not isinstance(self.flags, int) or not 0 <= self.flags <= 15:
            raise ValueError("Unknown flag bits")
        header = HEADER.pack(
            MAGIC,
            VERSION,
            len(self.codes),
            self.flags,
            self.gain,
            self.fs_hz,
            self.sequence,
            self.time_us,
            self.overruns,
        )
        data = header + native_frame(self.codes, self.status)
        return data + struct.pack("<H", binascii.crc_hqx(data, 0xFFFF))

    @staticmethod
    def decode(data: bytes | bytearray) -> Packet:
        if len(data) < HEADER.size + 3 + 12 + 2:
            raise ValueError("Packet too short")
        header: tuple[bytes, int, int, int, int, int, int, int, int] = HEADER.unpack_from(data)
        magic, ver, n, flags, gain, fs, seq, t, over = header
        if magic != MAGIC or ver != VERSION or n not in CHANNELS:
            raise ValueError("Bad packet header")
        if gain not in GAINS or fs not in RATES or flags & ~15:
            raise ValueError("Invalid packet configuration")
        if len(data) != HEADER.size + 3 + 3 * n + 2:
            raise ValueError("Wrong packet length")
        if binascii.crc_hqx(data[:-2], 0xFFFF) != struct.unpack("<H", data[-2:])[0]:
            raise ValueError("CRC mismatch")
        status, codes = parse_native(data[HEADER.size : -2], n)
        return Packet(seq, t, codes, gain, fs, flags, over, status)


class StreamDecoder:
    """Recover concatenated packets from serial chunks; count damaged bytes."""

    def __init__(self) -> None:
        self.buffer = bytearray()
        self.discarded_bytes = 0
        self.invalid_candidates = 0

    def feed(self, chunk: bytes | bytearray) -> list[Packet]:
        self.buffer.extend(chunk)
        packets = []
        while len(self.buffer) >= HEADER.size:
            if self.buffer[:2] != MAGIC:
                del self.buffer[0]
                self.discarded_bytes += 1
                continue
            ver, n = self.buffer[2:4]
            if ver != VERSION or n not in CHANNELS:
                del self.buffer[0]
                self.discarded_bytes += 1
                self.invalid_candidates += 1
                continue
            size = HEADER.size + 3 + 3 * n + 2
            if len(self.buffer) < size:
                break
            try:
                p = Packet.decode(bytes(self.buffer[:size]))
            except ValueError:
                del self.buffer[0]
                self.discarded_bytes += 1
                self.invalid_candidates += 1
                continue
            del self.buffer[:size]
            packets.append(p)
        return packets


class Tracker:
    """Track one device boot. Reject duplicates/backward packets, never sort.

    A restart is intentionally not repaired here. Start a new capture instead.
    32-bit timestamp wrap is accepted only for forward deltas under 2**31 us.
    """

    def __init__(self) -> None:
        self.last: Packet | None = None
        self.elapsed_us = 0
        self.accepted = 0
        self.missing = 0
        self.duplicates = 0
        self.stale = 0
        self.timing_anomalies = 0
        self.configuration: tuple[int, int, int, int] | None = None

    def observe(self, p: Packet) -> TrackerInfo | None:
        conf = (len(p.codes), p.gain, p.fs_hz, p.flags & 7)
        if self.configuration is None:
            self.configuration = conf
        if conf != self.configuration:
            raise ValueError("Configuration changed: start a new recording")
        gap = 0
        if self.last is not None:
            ds = (p.sequence - self.last.sequence) & 0xFFFFFFFF
            dt = (p.time_us - self.last.time_us) & 0xFFFFFFFF
            if ds == 0:
                self.duplicates += 1
                return None
            if ds >= 1 << 31 or dt >= 1 << 31:
                self.stale += 1
                return None
            gap = ds - 1
            self.missing += gap
            expected = ds * 1e6 / p.fs_hz
            if abs(dt - expected) > max(500, expected * 0.1):
                self.timing_anomalies += 1
            self.elapsed_us += dt
        self.last = p
        self.accepted += 1
        return {"elapsed_us": self.elapsed_us, "missing_before": gap}

    def summary(self) -> TrackerSummary:
        return {
            "accepted": self.accepted,
            "missing": self.missing,
            "duplicates": self.duplicates,
            "stale": self.stale,
            "timing_anomalies": self.timing_anomalies,
        }
