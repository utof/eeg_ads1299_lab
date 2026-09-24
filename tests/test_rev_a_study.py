"""Independent references and failure contracts for the first Rev A study."""

import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from hardware.rev_a import BillOfMaterials, BoardProfile, SourcesDocument, load_documents
from lab.analog import InputNetwork, transfer
from lab.data_types import ComplexArray, FloatArray
from lab.rev_a import load_baseline, main, study


@pytest.fixture(scope="module")
def report_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("rev-a")


def test_loads_selected_values_without_changing_educational_defaults() -> None:
    baseline = load_baseline()
    assert baseline.series_resistance_ohm == 4990
    assert baseline.differential_capacitance_f == 4.7e-9
    assert baseline.resistor_tolerance == 0.01
    assert baseline.capacitor_tolerance == 0.05
    assert baseline.resistor_mpn == "RC0603FR-074K99L"
    assert baseline.capacitor_mpn == "GRM1885C1H472JA01D"
    assert InputNetwork().r_series_p == 10000
    assert InputNetwork().c_differential == 1e-9


def test_report_is_explicit_about_analytic_only_and_safety(report_dir: Path) -> None:
    result = study(report_dir)
    assert result.ngspice_status == "not_requested"
    assert result.ngspice_max_abs_error == {}
    assert len(result.cases) == 3
    assert len(list(report_dir.glob("*/*/network.cir"))) == 6
    assert len(list(report_dir.glob("*/response.csv"))) == 3
    stored: object = json.loads((report_dir / "study.json").read_text(encoding="utf-8"))
    assert isinstance(stored, dict)
    assert stored["hardware_validated"] is False
    assert stored["clamps_fitted"] is False
    assert stored["body_connection_permitted"] is False


def test_ideal_source_limit_matches_independent_rc_reference(report_dir: Path) -> None:
    result = study(report_dir)
    b = result.baseline
    pole = 1 / (2 * np.pi * (2 * b.series_resistance_ohm) * b.differential_capacitance_f)
    assert result.ideal_source_pole_hz == pytest.approx(pole, rel=1e-12)
    model = result.cases["ideal_source_limit"].parameters
    frequencies: FloatArray = np.geomspace(0.1, 100000, 101)
    reference: ComplexArray = np.asarray(1 / (1 + 1j * frequencies / pole), dtype=np.complex128)
    np.testing.assert_allclose(transfer(frequencies, model), reference, rtol=3e-7, atol=1e-9)


def test_loaded_resistive_case_matches_independent_half_circuit(report_dir: Path) -> None:
    model = replace(
        study(report_dir).cases["balanced"].parameters,
        c_electrode_p=0.0,
        c_electrode_n=0.0,
        c_common_p=0.0,
        c_common_n=0.0,
    )
    frequencies: FloatArray = np.array([0.0, 10.0, 50.0, 60.0, 1000.0])
    resistance = model.r_series_p + model.r_electrode_p
    expected: ComplexArray = np.asarray(
        1
        / (
            1
            + resistance / model.r_input_p
            + 2j * np.pi * frequencies * 2 * resistance * model.c_differential
        ),
        dtype=np.complex128,
    )
    np.testing.assert_allclose(transfer(frequencies, model), expected, rtol=1e-12, atol=1e-12)


def test_balanced_common_mode_cancels_and_mismatch_does_not(report_dir: Path) -> None:
    result = study(report_dir)
    balanced = result.cases["balanced"]
    mismatch = result.cases["impedance_mismatch"]
    assert balanced.common_to_differential_50hz < 1e-12
    assert balanced.common_to_differential_60hz < 1e-12
    assert mismatch.common_to_differential_50hz > 1e-6
    assert mismatch.common_to_differential_60hz > 1e-6


def test_all_eight_bom_tolerance_corners_are_preserved(report_dir: Path) -> None:
    result = study(report_dir)
    for name, nominal in result.cases.items():
        corners = result.corners[name]
        assert len(corners) == 8
        values = {
            (item.parameters.r_series_p, item.parameters.r_series_n, item.parameters.c_differential)
            for item in corners
        }
        assert len(values) == 8
        p = nominal.parameters
        assert {row[0] for row in values} == {p.r_series_p * 0.99, p.r_series_p * 1.01}
        assert {row[2] for row in values} == {p.c_differential * 0.95, p.c_differential * 1.05}


def test_dc_leakage_bound_has_correct_units_and_is_linear(report_dir: Path) -> None:
    result = study(report_dir, leakage_bound_a=1e-9)
    for case in result.cases.values():
        p = case.parameters
        rp, rn = p.r_electrode_p + p.r_series_p, p.r_electrode_n + p.r_series_n
        expected = 1e-9 * (1 / (1 / rp + 1 / p.r_input_p) + 1 / (1 / rn + 1 / p.r_input_n))
        assert case.leakage_dc_bound_v == pytest.approx(expected, rel=1e-12)
    doubled = study(report_dir, leakage_bound_a=2e-9)
    assert doubled.cases["balanced"].leakage_dc_bound_v == pytest.approx(
        2 * result.cases["balanced"].leakage_dc_bound_v
    )
    zero = study(report_dir, leakage_bound_a=0.0)
    assert zero.cases["balanced"].leakage_dc_bound_v == 0


@pytest.mark.parametrize("bound", [-1.0, float("nan"), float("inf")])
def test_invalid_leakage_bound_does_not_create_outputs(tmp_path: Path, bound: float) -> None:
    out = tmp_path / "absent"
    with pytest.raises(ValueError, match="leakage"):
        study(out, leakage_bound_a=bound)
    assert not out.exists()


def _absent(_name: str) -> None:
    return None


def test_required_missing_simulator_invalidates_old_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    report = tmp_path / "study.json"
    report.write_text('{"ngspice_status":"executed_and_compared"}', encoding="utf-8")
    monkeypatch.setattr("shutil.which", _absent)
    with pytest.raises(RuntimeError, match="ngspice"):
        study(tmp_path, require_ngspice=True)
    assert not report.exists()


def _wrong_simulation(_netlist: str | Path, _out: str | Path) -> tuple[FloatArray, ComplexArray]:
    return np.array([10.0, 50.0, 60.0]), np.zeros(3, dtype=np.complex128)


def test_simulator_disagreement_cannot_publish_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("lab.rev_a.run_ngspice", _wrong_simulation)
    with pytest.raises(RuntimeError, match="disagree"):
        study(tmp_path, require_ngspice=True)
    assert not (tmp_path / "study.json").exists()


def test_rejects_invalid_hardware_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    profile, bom, sources = load_documents()
    profile["input_network"]["series_resistance_each_ohm"] = 123.0

    def invalid_documents() -> tuple[BoardProfile, BillOfMaterials, SourcesDocument]:
        return profile, bom, sources

    monkeypatch.setattr("lab.rev_a.load_documents", invalid_documents)
    with pytest.raises(ValueError, match="baseline"):
        load_baseline()


def test_cli_uses_requested_output_and_leakage_units(tmp_path: Path) -> None:
    assert main(["--out", str(tmp_path), "--leakage-bound-na", "2"]) == 0
    assert (tmp_path / "study.json").exists()
    assert main(["--out", str(tmp_path), "--leakage-bound-na", "-1"]) == 1


@pytest.mark.native
def test_real_ngspice_compares_all_six_drives(tmp_path: Path) -> None:
    result = study(tmp_path, require_ngspice=True)
    assert result.ngspice_status == "executed_and_compared"
    assert len(result.ngspice_max_abs_error) == 6
    assert max(result.ngspice_max_abs_error.values()) < 1e-5
    assert len(list(tmp_path.glob("*/*/ngspice.log"))) == 6


@pytest.mark.parametrize("bound", [-1.0, float("nan"), float("inf")])
def test_invalid_rerun_removes_old_completion_marker(tmp_path: Path, bound: float) -> None:
    marker = tmp_path / "study.json"
    marker.write_text('{"ngspice_status":"executed_and_compared"}', encoding="utf-8")
    with pytest.raises(ValueError, match="leakage"):
        study(tmp_path, leakage_bound_a=bound)
    assert not marker.exists()


def test_analytic_rerun_removes_previous_simulator_outputs(tmp_path: Path) -> None:
    study(tmp_path)
    for netlist in tmp_path.glob("*/*/network.cir"):
        for name in ("ac.txt", "ngspice.log"):
            (netlist.parent / name).write_text("stale evidence", encoding="utf-8")
    result = study(tmp_path)
    assert result.ngspice_status == "not_requested"
    assert not list(tmp_path.glob("*/*/ac.txt"))
    assert not list(tmp_path.glob("*/*/ngspice.log"))


@pytest.mark.parametrize("tolerance", [-0.01, 1.0, float("nan"), float("inf")])
def test_baseline_rejects_invalid_tolerances(tolerance: float) -> None:
    with pytest.raises(ValueError, match="tolerance"):
        replace(load_baseline(), resistor_tolerance=tolerance)
