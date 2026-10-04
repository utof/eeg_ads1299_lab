"""Steady resistive accounting only; supplied paths and loads are explicit hypotheses.

No plane extraction, regulators, switching-current model or physical pass criterion.
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
