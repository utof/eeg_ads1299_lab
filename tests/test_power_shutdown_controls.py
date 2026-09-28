"""Independent shutdown stimuli, not a qualification of the vendor regulator."""

import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
import pytest

from lab.analog import run_ngspice_transient
from lab.data_types import FloatArray
from lab.rev_a_power import run_pilot
from lab.validation import read_object

_CASES = ("startup_load", "shutdown", "enable_only", "supply_only")
_SYNTHETIC = b"PRIVATE SYNTHETIC LIBRARY: no vendor implementation"


def _software_pilot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, rejected: str | None = None
) -> Path:
    def available(_name: str) -> str:
        return "/fake/ngspice"

    def version(args: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args, 0, "software fixture, not native evidence", "")

    def library(_archive: Path, *, normalize_switch: bool) -> bytes:
        assert normalize_switch is False
        return _SYNTHETIC

    def trace(
        netlist: Path,
        out: Path,
        *,
        columns: int,
        expected_stop_s: float | None = None,
        expected_vectors: tuple[str, ...] | None = None,
    ) -> tuple[FloatArray, FloatArray]:
        assert expected_stop_s is not None
        expected = ("v(out)",) if columns == 1 else ("v(in)", "v(en)", "v(out)")
        assert expected_vectors == expected
        assert netlist.is_file()
        if out.name == rejected:
            raise RuntimeError("deliberately incomplete shutdown integration")
        times = np.linspace(0.0, expected_stop_s, 201)
        return times, np.full((201, columns), 3.3)

    monkeypatch.setattr("lab.rev_a_power.shutil.which", available)
    monkeypatch.setattr("lab.rev_a_power.subprocess.run", version)
    monkeypatch.setattr("lab.rev_a_power.prepare_library", library)
    monkeypatch.setattr("lab.rev_a_power.run_ngspice_transient", trace)
    return run_pilot(tmp_path / "reports", vendor_archive=tmp_path / "synthetic.zip")


def _vendor_probes(root: Path) -> list[dict[str, object]]:
    report = read_object(json.loads((root / "pilot.json").read_text()), "pilot")
    raw = report["vendor_probes"]
    assert isinstance(raw, list)
    values: list[object] = raw
    return [read_object(value, "vendor probe") for value in values]


def test_vendor_pilot_separates_enable_from_supply_collapse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _software_pilot(tmp_path, monkeypatch)
    probes = _vendor_probes(root)
    assert [probe.get("case") for probe in probes] == list(_CASES)
    for probe in probes:
        assert probe["voltage_columns"] == ["vin_v", "enable_v", "vout_v"]
        assert probe["library_edited"] is False
        assert probe["shutdown_requested"] is (probe["case"] != "startup_load")


def test_each_control_netlist_changes_only_the_intended_input(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _software_pilot(tmp_path, monkeypatch)
    held = "PWL(0 0 1m 0 1.01m 5 20m 5)"
    falling = "PWL(0 0 1m 0 1.01m 5 15m 5 15.01m 0 20m 0)"
    for name, supply, enable in (
        ("startup_load", held, held),
        ("shutdown", falling, falling),
        ("enable_only", held, falling),
        ("supply_only", falling, held),
    ):
        text = (root / name / "network.cir").read_text()
        assert f"Vin in 0 {supply}\n" in text
        assert f"Venable en 0 {enable}\n" in text
        assert "Xreg in 0 en nc out TPS7A20_ADJ_TRANS\n" in text
        assert "wrdata transient.txt v(in) v(en) v(out)" in text
        assert text.index("integration_stop") < text.index("wrdata")
        assert "Cout out 0 1u" in text
        assert "reltol=1e-5 abstol=1e-10 vntol=1e-7 method=gear" in text


@pytest.mark.parametrize("rejected", _CASES)
def test_one_failed_vendor_control_does_not_hide_its_peers_or_publish_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, rejected: str
) -> None:
    root = _software_pilot(tmp_path, monkeypatch, rejected)
    probes = _vendor_probes(root)
    assert [probe.get("case") for probe in probes] == list(_CASES)
    for probe in probes:
        failed = probe["case"] == rejected
        assert probe["window_complete"] is (not failed)
        assert probe["outcome"] == ("rejected" if failed else "probe_completed_not_validated")
        if failed:
            assert "incomplete" in str(probe["reason"])
    report = read_object(json.loads((root / "pilot.json").read_text()), "pilot")
    assert report["schema_version"] == 2
    assert report["hardware_validated"] is False
    assert report["body_connection_permitted"] is False
    manifest = read_object(json.loads((root / "manifest.json").read_text()), "manifest")
    files = read_object(manifest["files"], "files")
    for name, digest in files.items():
        data = (root / name).read_bytes()
        assert hashlib.sha256(data).hexdigest() == digest
        assert _SYNTHETIC not in data
    assert not list(root.rglob("*.lib"))


@pytest.mark.native
@pytest.mark.parametrize("swap_inputs", [False, True])
def test_native_synthetic_model_observes_each_independent_input(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, swap_inputs: bool
) -> None:
    # Continuous algebraic test double. It has no regulator dynamics and is
    # deliberately NOT the TI macro-model or a physically valid device model.
    # Unequal input weights make swapped pin identities observable natively.
    def library(_archive: Path, *, normalize_switch: bool) -> bytes:
        assert normalize_switch is False
        return (
            b"* Synthetic wiring fixture only\n"
            b".SUBCKT TPS7A20_ADJ_TRANS VIN GND EN NC VOUT\n"
            b"Bfixture VOUT GND V={0.2*V(VIN,GND)+0.46*V(EN,GND)}\n"
            b".ENDS TPS7A20_ADJ_TRANS\n"
        )

    def swapped_trace(
        netlist: Path,
        out: Path,
        *,
        columns: int,
        expected_stop_s: float | None = None,
        expected_vectors: tuple[str, ...] | None = None,
    ) -> tuple[FloatArray, FloatArray]:
        text = netlist.read_text().replace("Xreg in 0 en nc out", "Xreg en 0 in nc out")
        netlist.write_text(text)
        return run_ngspice_transient(
            netlist,
            out,
            columns=columns,
            expected_stop_s=expected_stop_s,
            expected_vectors=expected_vectors,
        )

    if swap_inputs:
        monkeypatch.setattr("lab.rev_a_power.run_ngspice_transient", swapped_trace)
    monkeypatch.setattr("lab.rev_a_power.prepare_library", library)
    root = run_pilot(tmp_path / "reports", vendor_archive=tmp_path / "synthetic.zip")
    probes = _vendor_probes(root)
    assert [probe.get("case") for probe in probes] == list(_CASES)
    outputs: list[float] = []
    for name, supply, enable in (
        ("startup_load", 5.0, 5.0),
        ("shutdown", 0.0, 0.0),
        ("enable_only", 5.0, 0.0),
        ("supply_only", 0.0, 5.0),
    ):
        probe = next(probe for probe in probes if probe["case"] == name)
        assert probe["window_complete"] is True
        assert probe["outcome"] == "probe_completed_not_validated"
        data = np.loadtxt(root / name / "transient.txt", skiprows=1, ndmin=2)
        assert data.shape[1] == 4
        assert data[-1, 0] == pytest.approx(0.02, abs=1e-12)
        assert data[-1, 1:3] == pytest.approx([supply, enable])
        outputs.append(float(data[-1, 3]))
    expected = [3.3, 0.0, 1.0, 2.3]
    if swap_inputs:
        assert outputs != pytest.approx(expected), "oracle must detect swapped model inputs"
        assert outputs == pytest.approx([3.3, 0.0, 2.3, 1.0])
    else:
        assert outputs == pytest.approx(expected)
