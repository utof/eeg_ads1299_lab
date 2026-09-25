"""The bounded study never overwrites prior runs or certifies failed comparisons."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from lab.data_types import ComplexArray, FloatArray
from lab.rev_a_bias import main, run_bias_study
from lab.validation import read_object


def test_bias_artifacts_are_identified_hashed_and_explicitly_analytic(tmp_path: Path) -> None:
    root = run_bias_study(tmp_path, run_id="1" * 32)
    report = read_object(json.loads((root / "study.json").read_text()), "report")
    manifest = read_object(json.loads((root / "manifest.json").read_text()), "manifest")
    files = read_object(manifest["files"], "files")
    cases = read_object(report["cases"], "cases")
    assert report["native_status"] == "not_requested"
    assert report["body_connection_permitted"] is False
    assert report["hardware_validated"] is False
    assert len(cases) == 5
    dynamics = read_object(report["amplifier_dynamics_cases"], "dynamics")
    assert set(dynamics) == {"extra_pole_100hz", "extra_pole_1000hz", "extra_pole_100000hz"}
    assert len(list(root.glob("dynamics/*/*/network.cir"))) == 9
    stress = read_object(cases["high_impedance_stress"], "stress")
    assert stress["linear_model_stable"] is False
    assert stress["frequency_response_interpretation"] == "formal_transfer_only_unstable_model"
    assert not (root / "high_impedance_stress" / "linear_step.csv").exists()
    assert len(list(root.glob("*/linear_step.csv"))) == 4
    assert len(list(root.glob("*/*/network.cir"))) == 14
    for name, digest in files.items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
    with pytest.raises(FileExistsError):
        run_bias_study(tmp_path, run_id="1" * 32)
    assert not (tmp_path / "current.json").exists()


def _disagree(_netlist: str | Path, _output: str | Path) -> tuple[FloatArray, ComplexArray]:
    return np.array([10.0, 50.0]), np.zeros(2, dtype=np.complex128)


def _failure_fixture_metadata(_required: bool) -> dict[str, object]:
    # Only for an injected failing run; never published as native evidence.
    return {"failure_injection_fixture": True}


def test_disagreement_retains_partial_evidence_without_completion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("lab.rev_a_bias.run_ngspice", _disagree)
    monkeypatch.setattr("lab.rev_a_bias._execution_identity", _failure_fixture_metadata)
    with pytest.raises(RuntimeError, match="disagreement"):
        run_bias_study(tmp_path, run_id="2" * 32, require_ngspice=True)
    root = tmp_path / ("2" * 32)
    assert list(root.glob("*/*/network.cir"))
    assert not (root / "manifest.json").exists()
    assert not (root / "study.json").exists()


def test_cli_reports_failure_and_rejects_unsafe_run_identity(tmp_path: Path) -> None:
    assert main(["--out", str(tmp_path), "--run-id", "../other"]) == 1
    assert not list(tmp_path.iterdir())
    assert main(["--out", str(tmp_path), "--run-id", "3" * 32]) == 0


def _reference_ac_for_failed_transient(
    netlist: str | Path, _output: str | Path
) -> tuple[FloatArray, ComplexArray]:
    # Deliberate software-only fixture, never evidence that a simulator ran.
    from lab.rev_a_bias import load_bias_model, response

    frequencies = np.array([1.0, 50.0, 60.0])
    result = response(frequencies, load_bias_model())
    values = (
        result.loop_gain if Path(netlist).parent.name == "loop" else result.common_impedance_ohm
    )
    return frequencies, values


@pytest.mark.parametrize("fault", ["disagreement", "late_start", "early_stop"])
def test_failed_transient_cannot_publish_completion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    def invalid_transient(
        _netlist: str | Path, _output: str | Path, *, columns: int
    ) -> tuple[FloatArray, FloatArray]:
        assert columns == 2
        times = np.array([0.0, 0.1])
        if fault == "late_start":
            times[0] = 1e-3
        if fault == "early_stop":
            times[1] = 0.05
        return times, np.zeros((2, 2), dtype=np.float64)

    monkeypatch.setattr("lab.rev_a_bias.run_ngspice", _reference_ac_for_failed_transient)
    monkeypatch.setattr("lab.rev_a_bias.run_ngspice_transient", invalid_transient)
    monkeypatch.setattr("lab.rev_a_bias._execution_identity", _failure_fixture_metadata)
    with pytest.raises(RuntimeError, match="transient"):
        run_bias_study(tmp_path, run_id="4" * 32, require_ngspice=True)
    root = tmp_path / ("4" * 32)
    assert (root / "balanced" / "step" / "network.cir").exists()
    assert not (root / "manifest.json").exists()
    assert not (root / "study.json").exists()
