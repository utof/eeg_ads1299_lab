"""Exercise numerical boundaries and report paths without pretending to run SPICE."""

import json
from pathlib import Path

import numpy as np
import pytest

from lab.acquisition import capture_udp, decode_capture, replay_packets
from lab.adc import behavioral_decimate, sinc3_magnitude, to_volts
from lab.analog import circuit_report
from lab.dsp import bandpower, psd, quality_flags
from lab.pipeline import run_demo
from lab.signals import SyntheticConfig, parse_metadata


def test_educational_report_and_missing_native_tool_are_explicit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PATH", "")
    report = circuit_report(tmp_path / "ordinary")
    assert report["ngspice"]["status"] == "not_run"
    assert report["safety_validation"] is False
    assert report["monte_carlo_trials"] == 200
    assert (tmp_path / "ordinary/balanced.cir").exists()
    with pytest.raises(RuntimeError, match="unavailable"):
        circuit_report(tmp_path / "required", require_ngspice=True)


def test_demo_writes_all_outputs_and_real_plots(tmp_path: Path) -> None:
    report = run_demo(tmp_path, SyntheticConfig(sessions=3, blocks_per_session=4), permutations=0)
    assert report["kind"] == "synthetic_pipeline_test_not_neuroscience_evidence"
    assert len(list(tmp_path.glob("*.png"))) == 4
    for image in tmp_path.glob("*.png"):
        assert image.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert json.loads((tmp_path / "analysis_report.json").read_text()) == report
    assert (tmp_path / "epoch_quality.csv").exists()
    assert (tmp_path / "events.csv").exists()


@pytest.mark.parametrize("value", [{"fs_hz": True}, {"sessions": "3"}, {"extra": 1}, []])
def test_configuration_parser_rejects_invalid_input(value: object) -> None:
    with pytest.raises(ValueError):
        SyntheticConfig.from_mapping(value)


def test_configuration_defaults_and_metadata_checks() -> None:
    assert SyntheticConfig.from_mapping({}) == SyntheticConfig()
    with pytest.raises(ValueError, match="synthetic demos"):
        parse_metadata({"kind": "live"})
    with pytest.raises(ValueError, match="missing fields"):
        parse_metadata({"kind": "synthetic_only"})


@pytest.mark.parametrize("values", [[], [np.nan], [[np.inf]], [[[0.0]]]])
def test_decimator_rejects_invalid_shapes_and_values(values: object) -> None:
    # The stored-array adapter owns dtype; malformed dimensions are checked by the model.
    raw = np.array(values, dtype=np.float64)
    with pytest.raises(ValueError):
        behavioral_decimate(raw)


def test_numeric_guards_are_exercised() -> None:
    with pytest.raises(ValueError, match="ratio"):
        behavioral_decimate([0.0, 1.0], ratio=1)
    with pytest.raises(ValueError, match="sample/modulator"):
        sinc3_magnitude([10], fs_hz=7)
    with pytest.raises(ValueError, match="integral"):
        sinc3_magnitude([10], fmod_hz=1001)
    with pytest.raises(ValueError, match="integers"):
        to_volts([1.5])
    with pytest.raises(ValueError, match="24-bit"):
        to_volts([2**23])
    with pytest.raises(ValueError, match="frequency band"):
        bandpower([0.0], 250, 10, 5)
    with pytest.raises(ValueError, match="PSD"):
        psd([0.0], 250)
    assert quality_flags([[np.nan]])["nonfinite_or_shape"]


def test_transport_option_guards_and_empty_capture(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="duration"):
        capture_udp(tmp_path / "x.bin", seconds=0)
    with pytest.raises(ValueError, match="replay"):
        replay_packets(channels=3)
    raw = tmp_path / "empty.bin"
    raw.write_bytes(b"garbage")
    with pytest.raises(ValueError, match="No valid"):
        decode_capture(raw, tmp_path / "empty.csv")
