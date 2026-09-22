# Wire protocol: EEG Learning Lab version 1

This is a **custom protocol**, not OpenBCI or a seller's stock packet format. The native ADS1299 frame is wrapped with metadata and a CRC.

## Byte layout

| Byte offset | Size | Representation | Field |
|---|---:|---|---|
| 0 | 2 | ASCII | `E9` magic |
| 2 | 1 | unsigned | Version = 1 |
| 3 | 1 | unsigned | Physical channel count: 4, 6 or 8 |
| 4 | 1 | bit flags | Mode and cumulative overrun indicator |
| 5 | 1 | unsigned | Gain: 1, 2, 4, 6, 8, 12 or 24 |
| 6 | 2 | little endian | Nominal samples/second |
| 8 | 4 | little endian | DRDY-derived uint32 sequence |
| 12 | 4 | little endian | uint32 device microseconds at DRDY |
| 16 | 4 | little endian | Cumulative uint32 acquisition overrun count |
| 20 | 3 | big endian | Native status word; high nibble must be `0xC` |
| 23 | 3 × channels | big endian, signed two's complement | Native channel values |
| Final 2 | 2 | little endian | CRC-16/CCITT-FALSE over all preceding bytes |

Total packet length is `25 + 3 × channels`: 37, 43 or 49 bytes. The maximum data packet at 250 SPS is 12,250 payload bytes/s, before transport overhead. This is a sizing calculation, not a measured wireless throughput guarantee.

CRC polynomial `0x1021`, initial value `0xffff`, no reflection, no final XOR. Flags: bit 0 internal test; bit 1 internal short; bit 2 synthetic; bit 3 at least one cumulative overrun. The starter emits internal test **or** short, never external normal-input EEG mode.

The native frame length depends on the physical chip variant. Powering down channels on an eight-channel chip does not turn it into a four-channel frame [S1]. The sketch determines the variant from the ID register. Reference voltage is not carried in the packet: the host uses `--vref` (default 4.5 V), which must match the actual calibrated setup.

## Host behavior

UDP expects exactly one packet per datagram. Serial is a byte stream; its decoder searches for framing and validates length, fields, native prefix and CRC. Startup diagnostic text may be discarded during resynchronization.

The tracker accepts forward sequence numbers, detects gaps, and extends the device time across uint32 rollover. Duplicates and backward/out-of-order packets are not treated as new samples. A reboot or clock/configuration change requires a new capture; do not join it silently to the old recording.

The CSV preserves `missing_before`, raw counts, converted microvolts, status, flags and overrun counters. The quality inspector splits at discontinuities in sequence or device timing. It never interpolates holes into a PSD.

A CRC validates bytes in transit, not the origin or safety of the signal. Native ADS1299 SPI frames do not provide this transport CRC; a faulty SPI word that the MCU then wraps and checksums can still pass host CRC validation. Also, the wire format is unauthenticated and unencrypted. Use a private network and do not expose the receiver publicly.

## Firmware timing limitations

The ISR only records the DRDY count and timestamp. SPI reads happen in the main loop. If another conversion arrives during a read, the candidate is discarded. Missed servicing increments counters; no missing frame is invented. This is a conservative starter, not a proven hard-real-time driver. Blocking serial/radio work can still cost samples.

The portable C++ packet/CRC/sign-conversion helpers were compiled and compared byte-for-byte with Python. The ESP32 interrupt/HAL/radio path still requires a full target build and physical measurement.

References marked `[S#]` are linked in [SOURCES.md](SOURCES.md).
