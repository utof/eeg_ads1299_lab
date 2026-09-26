"""Derive document-based external wiring from the checked native schematic.

The DevKit map is manufacturer pin evidence, NOT another ADS GPIO assignment.
This numbered-terminal worksheet is neither a fabricated cable nor permission
for live wiring. The external 3.3 V console interface remains unqualified.
"""

import re
from dataclasses import dataclass

from .check_baseline import BillOfMaterials, BoardProfile, SourcesDocument, validate
from .check_schematic import SchematicNetlist, validate_schematic

# ESP32-S3-DevKitC-1 V1.1 schematic, 2022-11-30, sheet 2, J1; also user guide J1.
# Tuple index + 1 is the physical header pad, NOT the GPIO or module package pad.
_DEVKIT_J1 = (
    "3V3",
    "3V3",
    "EN",
    "GPIO4",
    "GPIO5",
    "GPIO6",
    "GPIO7",
    "GPIO15",
    "GPIO16",
    "GPIO17",
    "GPIO18",
    "GPIO8",
    "GPIO3",
    "GPIO46",
    "GPIO9",
    "GPIO10",
    "GPIO11",
    "GPIO12",
    "GPIO13",
    "GPIO14",
    "5V",
    "GND",
)


@dataclass(frozen=True)
class HarnessNet:
    name: str
    endpoints: tuple[str, ...]


def _devkit(signal: str) -> str:
    if _DEVKIT_J1.count(signal) != 1:
        raise ValueError(f"no unique reviewed DevKit J1 pad for {signal}")
    return f"DEVKIT.J1.{_DEVKIT_J1.index(signal) + 1}"


def _console(content: str) -> dict[str, int]:
    # Closed declarations owned by firmware; actual call/argument behavior is
    # independently executed by the real-sketch host test and target compiler.
    rows = re.findall(r"constexpr (?:int|unsigned) CONSOLE_(RX|TX|BAUD)\s*=\s*(\d+);", content)
    values = {name: int(value) for name, value in rows}
    if len(rows) != 3 or values != {"RX": 17, "TX": 18, "BAUD": 460800}:
        raise ValueError("console must use the reviewed RX17/TX18, 460800 baud declarations")
    return values


def bench_harness(
    netlist: SchematicNetlist,
    profile: BoardProfile,
    bom: BillOfMaterials,
    sources: SourcesDocument,
    console_header: str,
) -> tuple[HarnessNet, ...]:
    """Produce named physical terminal groups only after the source contracts pass.

    Endpoints are board-qualified: AFE.J1 is NOT DEVKIT.J1. Power/ground groups
    describe common nodes, not a serial current path or qualified cable routing.
    Signal group labels retain GPIO numbers but no physical pin is guessed from
    a GPIO number. No connection is made to an adapter's power or reset outputs.
    """
    errors = validate(profile, bom, sources)
    if errors:
        raise ValueError("invalid harness baseline: " + "; ".join(errors))
    errors = validate_schematic(netlist, profile, bom)
    if errors:
        raise ValueError("invalid harness source: " + "; ".join(errors))
    if profile["mcu"]["preferred_pcb_revision"] != "v1.1":
        raise ValueError("physical harness requires the reviewed DevKit v1.1")
    console = _console(console_header)
    header = profile["interface_headers"]["J_DIG"]["pin_map"]
    native = netlist.parts["J_DIG"].native_ref
    pins = {signal: pin for pin, signal in header.items() if signal != "DGND"}
    expected = {row["signal"] for row in profile["spi"]["signals"]} | {"VIN_5V_AFE"}
    if set(pins) != expected or len(header) != 20:
        raise ValueError("harness requires nine signals, one supply and ten ground contacts")
    groups = []
    for row in profile["spi"]["signals"]:
        signal, gpio = row["signal"], row["gpio"]
        afe = f"AFE.{native}.{pins[signal]}"
        devkit = _devkit(f"GPIO{gpio}")
        # Display the transmitter first, avoiding ambiguous TX-to-TX wording.
        ends = (devkit, afe) if row["direction_from_mcu"] == "out" else (afe, devkit)
        groups.append(HarnessNet(f"{signal} / GPIO{gpio}", ends))
    groups.extend(
        [
            HarnessNet(
                "Console receive / GPIO17", ("INTERFACE.TX_3V3", _devkit(f"GPIO{console['RX']}"))
            ),
            HarnessNet(
                "Console transmit / GPIO18", (_devkit(f"GPIO{console['TX']}"), "INTERFACE.RX_3V3")
            ),
            HarnessNet(
                "External regulated 5 V",
                (
                    "SUPPLY.+5V",
                    f"AFE.{native}.{pins['VIN_5V_AFE']}",
                    _devkit("5V"),
                ),
            ),
            HarnessNet(
                "Common return",
                (
                    "SUPPLY.RETURN",
                    _devkit("GND"),
                    "INTERFACE.GND",
                    *(f"AFE.{native}.{pin}" for pin, signal in header.items() if signal == "DGND"),
                ),
            ),
        ]
    )
    return tuple(groups)
