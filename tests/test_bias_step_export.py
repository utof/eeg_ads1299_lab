"""Test-first entry for independent BIAS transient execution."""

from pathlib import Path

from lab.rev_a_bias import export_bias_spice, load_bias_model


def test_step_export_is_an_executable_zero_state_experiment(tmp_path: Path) -> None:
    path = export_bias_spice(tmp_path / "network.cir", load_bias_model(), mode="step")
    assert "wrdata transient.txt" in path.read_text()
    assert "uic" in path.read_text()
