"""Analog-feed hypothesis, separate from regulator compatibility and physical validation."""

from dataclasses import dataclass
from pathlib import Path

from .data_types import FloatArray


@dataclass(frozen=True, slots=True)
class SupplyCase:
    source_v: float = 4.95
    feed_r_ohm: float = 10.0
    shared_r_ohm: float = 0.1
    capacitance_f: float = 10e-6
    analog_g_s: float = 0.002
    idle_g_s: float = 0.02
    burst_g_s: float = 0.08


def steady_state(case: SupplyCase, *, burst: bool = False) -> tuple[float, float]:
    """Return the rail equilibrium (V) and time constant (s)."""
    raise NotImplementedError("test-first analog-feed specification")


def rail_response(case: SupplyCase, times_s: FloatArray) -> FloatArray:
    """Uncharged startup at 1 ms; conductance burst from 8 to 12 ms."""
    raise NotImplementedError("test-first analog-feed specification")


def supply_netlist(case: SupplyCase) -> str:
    raise NotImplementedError("test-first analog-feed specification")


def run_supply_study(out: Path) -> Path:
    raise NotImplementedError("test-first analog-feed specification")


def main() -> int:
    raise NotImplementedError("test-first analog-feed specification")


if __name__ == "__main__":
    raise SystemExit(main())
