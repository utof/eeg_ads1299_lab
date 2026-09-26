"""Independent circuit equations; supply hypotheses never establish hardware approval."""

import hashlib
import json
import shutil
import sys
from collections.abc import Sequence
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from typing import cast

import numpy as np
import pytest

from lab.data_types import FloatArray
from lab.rev_a_supply import (
    SupplyCase,
    main,
    rail_response,
    run_supply_study,
    steady_state,
    supply_netlist,
)
from lab.validation import read_object
from tools.check import main as check_main


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_v", 0.0),
        ("source_v", float("nan")),
        ("source_v", True),
        ("feed_r_ohm", 0.0),
        ("shared_r_ohm", -1.0),
        ("shared_r_ohm", float("inf")),
        ("capacitance_f", 0.0),
        ("capacitance_f", -1e-6),
        ("analog_g_s", -0.1),
        ("idle_g_s", -0.1),
        ("burst_g_s", -0.1),
        ("burst_g_s", False),
    ],
)
def test_case_rejects_invalid_physical_parameters(field: str, value: float) -> None:
    with pytest.raises(ValueError):
        replace(SupplyCase(), **{field: value})


@pytest.mark.parametrize("shared_r", [0.05, 0.5, 1.0])
@pytest.mark.parametrize("burst", [False, True])
def test_dc_equilibrium_matches_independent_two_node_kcl(shared_r: float, burst: bool) -> None:
    case = replace(SupplyCase(), shared_r_ohm=shared_r)
    g_mcu = case.idle_g_s + (case.burst_g_s if burst else 0.0)
    # KCL at the shared bus and analog rail; not the reduced Thevenin formula.
    matrix = np.array(
        [
            [1 / shared_r + g_mcu + 1 / case.feed_r_ohm, -1 / case.feed_r_ohm],
            [-1 / case.feed_r_ohm, 1 / case.feed_r_ohm + case.analog_g_s],
        ]
    )
    expected: FloatArray = np.linalg.solve(matrix, np.array([case.source_v / shared_r, 0.0]))
    voltage, tau = steady_state(case, burst=burst)
    assert voltage == pytest.approx(float(expected[1]), abs=1e-12)
    assert tau > 0
    slower = replace(case, capacitance_f=10 * case.capacitance_f)
    slow_voltage, slow_tau = steady_state(slower, burst=burst)
    assert slow_voltage == voltage
    assert slow_tau == pytest.approx(10 * tau, rel=1e-14)


def test_stiff_source_isolates_mcu_bursts_and_matches_loaded_rc_step() -> None:
    case = replace(SupplyCase(), shared_r_ohm=0.0)
    times = np.linspace(0.0, 0.02, 2001)
    resistance = 1 / (1 / case.feed_r_ohm + case.analog_g_s)
    final = case.source_v * resistance / case.feed_r_ohm
    expected = final * (
        1 - np.exp(-np.maximum(times - 0.001, 0) / (resistance * case.capacitance_f))
    )
    actual = rail_response(case, times)
    np.testing.assert_allclose(actual, expected, atol=1e-12, rtol=0)
    np.testing.assert_allclose(
        actual, rail_response(replace(case, burst_g_s=10.0), times), atol=1e-12, rtol=0
    )


def test_state_remains_continuous_and_recovery_has_the_correct_direction() -> None:
    case = replace(SupplyCase(), shared_r_ohm=1.0)
    times = np.array([0.0, 0.001, 0.007, 0.008, 0.008000000001, 0.012, 0.012000000001, 0.02])
    volts = rail_response(case, times)
    assert volts[0] == 0 and volts[1] == 0
    assert abs(float(volts[4]) - float(volts[3])) < 1e-7
    assert abs(float(volts[6]) - float(volts[5])) < 1e-7
    assert volts[3] > volts[5] and volts[-1] > volts[6]
    assert 0 <= np.min(volts) <= np.max(volts) <= case.source_v


@pytest.mark.parametrize(
    "times",
    [[], [-0.01], [0.03], [0.0, 0.0], [0.02, 0.01], [0.0, float("nan")], [[0.0, 0.01]]],
)
def test_time_axis_is_validated(times: list[float] | list[list[float]]) -> None:
    with pytest.raises(ValueError):
        rail_response(SupplyCase(), np.asarray(times, dtype=np.float64))


def test_case_is_frozen_and_non_boolean_phase_is_rejected() -> None:
    case = SupplyCase()
    with pytest.raises(FrozenInstanceError):
        field = "source_v"
        setattr(case, field, 99.0)
    with pytest.raises(ValueError):
        steady_state(case, burst=cast(bool, 1))  # Deliberately invalid runtime boundary input.


def test_netlist_keeps_mcu_load_upstream_of_the_selected_feed() -> None:
    netlist = supply_netlist(SupplyCase())
    assert "Rshared source bus " in netlist
    assert "Rfeed bus avdd 10" in netlist
    assert "Bmcu bus 0 I=" in netlist
    assert "Banalog avdd 0 I=" in netlist
    assert "Cbulk avdd 0 " in netlist
    assert netlist.index("integration_stop") < netlist.index("wrdata")
    assert ".include" not in netlist and "TPS7A20" not in netlist


def test_invalid_baseline_is_rejected_before_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def rejected(*_args: object) -> list[str]:
        return ["injected invalid hardware contract"]

    monkeypatch.setattr("lab.rev_a_supply.validate", rejected)
    with pytest.raises(ValueError, match="hardware contract"):
        run_supply_study(tmp_path / "attempt")
    assert not (tmp_path / "attempt").exists()


def test_rejected_native_runs_keep_all_diagnostics_and_no_success_claim(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[Path] = []

    def rejected(
        _netlist: Path, out: Path, *, columns: int, expected_stop_s: float
    ) -> tuple[FloatArray, FloatArray]:
        assert columns == 1 and expected_stop_s == 0.02
        calls.append(out)
        (out / "ngspice.log").write_text("injected native failure; not a simulation")
        raise RuntimeError("injected incomplete native integration")

    monkeypatch.setattr("lab.rev_a_supply.run_ngspice_transient", rejected)
    with pytest.raises(RuntimeError, match="retained"):
        run_supply_study(tmp_path)
    assert len(calls) == 5
    roots = list(tmp_path.glob("*/study.json"))
    assert len(roots) == 1
    report = read_object(json.loads(roots[0].read_text()), "study")
    assert report["native_comparison_passed"] is False
    assert report["hardware_validated"] is False
    manifest = read_object(json.loads((roots[0].parent / "manifest.json").read_text()), "manifest")
    files = read_object(manifest["files"], "files")
    for name, expected in files.items():
        assert hashlib.sha256((roots[0].parent / name).read_bytes()).hexdigest() == expected
    for path in calls:
        assert "injected" in (path / "ngspice.log").read_text()


@pytest.mark.parametrize("fail", [False, True])
def test_shared_native_gate_retains_supply_evidence_before_native_tests(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fail: bool
) -> None:
    commands: dict[str, list[str]] = {}

    def plan(_out: Path) -> list[tuple[str, list[str]]]:
        return []

    def coverage(_path: Path, _floor: float) -> float:
        return 80.0

    def available() -> None:
        pass

    def step(name: str, command: Sequence[str], _out: Path, timeout: float = 300) -> None:
        commands[name] = list(command)
        if name == "rev-a-supply" and fail:
            raise RuntimeError("injected failed supply study with retained evidence")

    monkeypatch.setattr("tools.check.command_plan", plan)
    monkeypatch.setattr("tools.check.check_branch_coverage", coverage)
    monkeypatch.setattr("tools.check.require_native_tools", available)
    monkeypatch.setattr("tools.check.run_step", step)
    assert check_main(["--native", "--out", str(tmp_path)]) == int(fail)
    command = commands["rev-a-supply"]
    assert command[:3] == [sys.executable, "-m", "lab.rev_a_supply"]
    assert command[command.index("--out") + 1] == str(tmp_path / "rev_a_supply")
    if fail:
        assert "native-tests" not in commands
    else:
        assert list(commands).index("rev-a-supply") < list(commands).index("native-tests")


def test_cli_reports_missing_simulator(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PATH", "")
    monkeypatch.setattr(sys, "argv", ["supply-study", "--out", str(tmp_path)])
    assert main() == 1


@pytest.mark.native
def test_actual_ngspice_comparison_does_not_promote_margin_breaches_to_hardware_failure(
    tmp_path: Path,
) -> None:
    if shutil.which("ngspice") is None:
        pytest.skip("ngspice unavailable; tools.check --native rejects missing native tools")
    root = run_supply_study(tmp_path)
    report = read_object(json.loads((root / "study.json").read_text()), "study")
    assert report["native_comparison_passed"] is True
    assert report["hardware_validated"] is False
    assert report["body_connection_permitted"] is False
    cases = report["cases"]
    assert isinstance(cases, list)
    values: list[object] = cases
    assert len(values) == 5
    margins = {
        read_object(case, "case")["name"]: read_object(case, "case")["model_margin_ok"]
        for case in values
    }
    assert margins == {
        "stiff_source": True,
        "shared_0p1_ohm": True,
        "shared_0p5_ohm": False,
        "shared_1_ohm": False,
        "bulk_100uf": False,
    }
