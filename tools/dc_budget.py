"""Steady accounting with explicit path, current and ideal-output hypotheses.

No plane extraction, regulator/transient model or physical pass criterion.
Mean external charging is separate from internal switching and peak current.
Do not use the tree method for meshes, active sources or signed per-load currents.
"""

import math
from collections import defaultdict
from collections.abc import Mapping


def _number(value: float, *, signed: bool = False) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("budget values must be finite real numbers")
    if not math.isfinite(value) or (not signed and value < 0):
        raise ValueError("budget values must be finite and nonnegative unless signed")


def _route_ids(route: tuple[str, ...]) -> None:
    if not isinstance(route, tuple) or not route:
        raise ValueError("path must be a nonempty tuple of edge IDs")
    if not all(isinstance(edge, str) and edge for edge in route):
        raise ValueError("edge IDs must be nonempty strings")
    if len(set(route)) != len(route):
        raise ValueError("paths must be cycle-free")


def _edge_currents(
    resistances: Mapping[str, float],
    paths: Mapping[str, tuple[str, ...]],
    loads: Mapping[str, float],
) -> dict[str, float]:
    if not paths or paths.keys() != loads.keys():
        raise ValueError("one explicit nonnegative current is required for every path")
    prefixes: dict[str, tuple[str, ...]] = {}
    currents: dict[str, float] = defaultdict(float)
    for sink, route in paths.items():
        _number(loads[sink])
        _route_ids(route)
        for index, edge in enumerate(route):
            if edge not in resistances:
                raise ValueError("path references an unknown edge")
            prefix = route[: index + 1]
            if prefixes.setdefault(edge, prefix) != prefix:
                raise ValueError("paths must form one rooted tree, without reconvergence")
            currents[edge] += loads[sink]
    return dict(currents)


def tree_drops(
    resistances: Mapping[str, float],
    paths: Mapping[str, tuple[str, ...]],
    loads: Mapping[str, float],
) -> dict[str, float]:
    """KCL then KVL: each shared edge carries the sum of downstream load currents.

    Edge IDs denote oriented root-to-load elements, not whole nets or arbitrary
    shortest paths through copper. Unused resistances are rejected. A finite
    answer is not a guarantee that the physical loads/geometry fit this model.
    """
    for resistance in resistances.values():
        _number(resistance)
    currents = _edge_currents(resistances, paths, loads)
    if currents.keys() != resistances.keys():
        raise ValueError("unused resistance hides an unmodeled branch")
    result = {
        sink: sum(currents[edge] * resistances[edge] for edge in route)
        for sink, route in paths.items()
    }
    for value in (*currents.values(), *result.values()):
        _number(value)
    return result


def remote_voltages(
    local_v: float, ground_shift_v: float, feed_drop_v: float, sense_drop_v: float
) -> tuple[float, float]:
    """Return (delivered rail, sensed source), both measured against remote ground.

    ground_shift_v = G_source - G_remote; it is signed. A separate sense wire
    measures upstream of feed loss. Negative results are possible: they expose
    an invalid operating hypothesis, not a clamped voltage or an approval.
    """
    for value in (local_v, feed_drop_v, sense_drop_v):
        _number(value)
    _number(ground_shift_v, signed=True)
    delivered = local_v + ground_shift_v - feed_drop_v
    sensed = local_v + ground_shift_v - sense_drop_v
    _number(delivered, signed=True)
    _number(sensed, signed=True)
    return delivered, sensed


def switched_load(
    rail_v: float,
    resistance_ohm: float,
    high_fraction: float,
    capacitance_f: float,
    rising_hz: float,
) -> tuple[float, float]:
    """Return (pull, capacitive charging) mean amperes for an ideal rail/zero output.

    Frequency counts LOW-to-HIGH transitions, not both edges. Resistance and
    capacitance are external loads only. This excludes internal switching power,
    leakage, ground offset, finite output levels and peak/short-circuit current.
    Inputs are hypotheses, not component or physical qualification limits.
    """
    for value in (rail_v, resistance_ohm, high_fraction, capacitance_f, rising_hz):
        _number(value)
    if resistance_ohm == 0 or high_fraction > 1:
        raise ValueError("positive resistance and a duty fraction in [0, 1] are required")
    pull = rail_v / resistance_ohm * high_fraction
    charging = capacitance_f * rail_v * rising_hz
    for result in (pull, charging):
        _number(result)
    return pull, charging


def parallel_returns(
    resistances: Mapping[str, float], export_a: float
) -> tuple[float, dict[str, float]]:
    """Return (G_source - G_remote, signed branch currents) for two lumped nodes.

    All paths connect exactly the same two equipotential nodes. This is not a
    distributed ground-plane or shared-source solver. Positive export flows
    from source ground to remote ground; a signed export reverses every path.
    Zero-ohm/unknown paths are not silently accepted as ideal measured wires.
    """
    _number(export_a, signed=True)
    if not resistances:
        raise ValueError("at least one explicit return path is required")
    conductance: dict[str, float] = {}
    for name, resistance in resistances.items():
        _number(resistance)
        if not isinstance(name, str) or not name or resistance == 0:
            raise ValueError("return paths need nonempty IDs and positive resistances")
        conductance[name] = 1 / resistance
        _number(conductance[name])
    total = sum(conductance.values())
    _number(total)
    if total == 0:
        raise ValueError("return conductance underflow")
    shift = export_a / total
    _number(shift, signed=True)
    currents = {name: shift * value for name, value in conductance.items()}
    for current in currents.values():
        _number(current, signed=True)
    return shift, currents


def _interval(value: tuple[float, float] | None) -> None:
    if value is None:
        return
    if not isinstance(value, tuple) or len(value) != 2:
        raise ValueError("interval must be a lower/upper tuple or unknown")
    for endpoint in value:
        _number(endpoint, signed=True)
    if value[0] > value[1]:
        raise ValueError("interval endpoints must be ordered")


def voltage_bounds(
    source_v: tuple[float, float] | None,
    signed_terms_v: Mapping[str, tuple[float, float] | None],
) -> tuple[float, float] | None:
    """Conservative endpoint sums, or unknown if ANY required term is unknown.

    Every term is ADDED: represent a positive loss [a,b] as [-b,-a]. Ground
    reference shifts retain their algebraic sign. No independence assumption,
    statistical cancellation, implicit zero, circuit solving or approval occurs.
    Correlated quantities may make the interval wider than physically reachable.
    The caller must partition paths to avoid double-counting shared losses.
    """
    _interval(source_v)
    for name, interval in signed_terms_v.items():
        if not isinstance(name, str) or not name:
            raise ValueError("voltage terms need nonempty IDs")
        _interval(interval)
    if source_v is None or any(v is None for v in signed_terms_v.values()):
        return None
    low, high = source_v
    for value in signed_terms_v.values():
        if value is not None:
            low += value[0]
            high += value[1]
    _number(low, signed=True)
    _number(high, signed=True)
    return low, high
