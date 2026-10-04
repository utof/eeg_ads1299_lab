"""Small DC accounting controls; these do not model transients or authorize hardware."""

import math

import pytest

from tools.dc_budget import remote_voltages, tree_drops


def test_shared_trunk_carries_all_loads_once() -> None:
    # Independent KCL/KVL: trunk carries 30mA, not each branch's own current.
    drops = tree_drops(
        {"trunk": 2.0, "a": 3.0, "b": 4.0},
        {"a": ("trunk", "a"), "b": ("trunk", "b")},
        {"a": 0.01, "b": 0.02},
    )
    assert drops == pytest.approx({"a": 0.09, "b": 0.14})


def test_subdivision_and_zero_load_preserve_voltage() -> None:
    drops = tree_drops(
        {"first": 0.5, "second": 1.5, "a": 3.0, "b": 4.0},
        {"a": ("first", "second", "a"), "b": ("first", "second", "b")},
        {"a": 0.01, "b": 0.0},
    )
    assert drops == pytest.approx({"a": 0.05, "b": 0.02})


def test_return_offset_has_a_sign_and_sense_does_not_see_feed_loss() -> None:
    # G_AFE is 20mV above G_AUX: rail and sense at AUX both rise, not fall.
    assert remote_voltages(3.3, 0.020, 0.050, 0.001) == pytest.approx((3.270, 3.319))
    assert remote_voltages(3.3, -0.020, 0.050, 0.001) == pytest.approx((3.230, 3.279))
    # A large feed failure is NOT necessarily visible on separately sensed source.
    delivered, sensed = remote_voltages(3.3, 0.0, 1.0, 0.001)
    assert delivered == pytest.approx(2.3) and sensed == pytest.approx(3.299)


@pytest.mark.parametrize("bad", [math.nan, math.inf, -1.0, True])
def test_invalid_resistance_or_current_is_not_a_result(bad: float) -> None:
    with pytest.raises(ValueError):
        tree_drops({"e": bad}, {"a": ("e",)}, {"a": 0.01})
    with pytest.raises(ValueError):
        tree_drops({"e": 1.0}, {"a": ("e",)}, {"a": bad})


def test_cycles_reconvergence_and_missing_loads_are_not_trees() -> None:
    with pytest.raises(ValueError):
        tree_drops({"e": 1.0}, {"a": ("e", "e")}, {"a": 0.01})
    with pytest.raises(ValueError):
        tree_drops({"x": 1.0, "e": 1.0}, {"a": ("e",), "b": ("x", "e")}, {"a": 1.0, "b": 1.0})
    with pytest.raises(ValueError):
        tree_drops({"e": 1.0}, {"a": ("e",)}, {})
    with pytest.raises(ValueError):
        tree_drops({"e": 1.0}, {"a": ("unknown",)}, {"a": 1.0})


def test_zero_resistance_is_valid_but_overflow_is_not() -> None:
    assert tree_drops({"e": 0.0}, {"a": ("e",)}, {"a": 1.0}) == {"a": 0.0}
    with pytest.raises(ValueError):
        tree_drops({"e": 1e308}, {"a": ("e",)}, {"a": 1e308})
    with pytest.raises(ValueError):
        remote_voltages(3.3, math.nan, 0.0, 0.0)
    with pytest.raises(ValueError):
        remote_voltages(3.3, 0.0, -1.0, 0.0)


def test_malformed_path_and_unused_edge_are_rejected() -> None:
    from typing import cast

    with pytest.raises(ValueError):
        tree_drops({"e": 1.0}, {"a": cast(tuple[str, ...], "e")}, {"a": 1.0})
    with pytest.raises(ValueError):
        tree_drops({"": 1.0}, {"a": ("",)}, {"a": 1.0})
    with pytest.raises(ValueError):
        tree_drops({"e": 1.0, "unused": 0.0}, {"a": ("e",)}, {"a": 1.0})
