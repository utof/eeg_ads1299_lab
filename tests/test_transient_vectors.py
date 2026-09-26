"""Named-output regressions; process doubles are not new simulator evidence."""

import hashlib
import io
import json
import subprocess
from pathlib import Path
from typing import cast

import numpy as np
import pytest

from lab.analog import run_ngspice_transient
from lab.rev_a_power import run_pilot
from lab.validation import read_object


def _process(monkeypatch: pytest.MonkeyPatch, root: Path, table: str) -> None:
    def available(_name: str) -> str:
        return "/fake/ngspice"

    def run(args: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        (root / "transient.txt").write_text(table, encoding="utf-8")
        return subprocess.CompletedProcess(args, 0, "software fixture, not native evidence", "")

    monkeypatch.setattr("shutil.which", available)
    monkeypatch.setattr(subprocess, "run", run)


@pytest.mark.parametrize("header", ["frequency a b", "time a", "time a b extra", "0 1 2"])
def test_transient_rejects_wrong_scale_or_header_shape_without_opt_in(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, header: str
) -> None:
    _process(monkeypatch, tmp_path, header + "\n0 1 2\n0.1 3 4\n")
    with pytest.raises(RuntimeError, match="transient vectors"):
        run_ngspice_transient(tmp_path / "network.cir", tmp_path, columns=2)
    assert "software fixture" in (tmp_path / "ngspice.log").read_text()


def test_named_transient_preserves_numbers_and_accepts_header_spacing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _process(monkeypatch, tmp_path, "  time\t v(common)   v(out)  \n0 1 2\n0.1 3 4\n")
    times, volts = run_ngspice_transient(
        tmp_path / "network.cir", tmp_path, columns=2, expected_vectors=("v(common)", "v(out)")
    )
    np.testing.assert_array_equal(times, [0.0, 0.1])
    np.testing.assert_array_equal(volts, [[1.0, 2.0], [3.0, 4.0]])


@pytest.mark.parametrize("names", ["v(out) v(common)", "v(common) v(common)", "v(common) v(wrong)"])
def test_named_transient_rejects_reordered_duplicate_or_unexpected_vectors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, names: str
) -> None:
    _process(monkeypatch, tmp_path, f"time {names}\n0 1 2\n0.1 3 4\n")
    with pytest.raises(RuntimeError, match="transient vectors"):
        run_ngspice_transient(
            tmp_path / "network.cir", tmp_path, columns=2, expected_vectors=("v(common)", "v(out)")
        )
    assert (tmp_path / "transient.txt").read_text().startswith(f"time {names}")


@pytest.mark.parametrize(
    "vectors",
    [(), ("v(out)",), ("", "v(out)"), ("v(common) v(out)", "v(out)"),
     ("v(out)", "v(out)"), ("v(common)", 42), ["v(common)", "v(out)"]],
)
def test_vector_contract_is_validated_before_filesystem_or_process_work(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, vectors: object
) -> None:
    def forbidden(_name: str) -> str:
        pytest.fail("invalid vector request reached executable discovery")

    monkeypatch.setattr("shutil.which", forbidden)
    with pytest.raises(ValueError, match="expected_vectors"):
        run_ngspice_transient(
            tmp_path / "network.cir", tmp_path, columns=2,
            expected_vectors=cast(tuple[str, ...], vectors),
        )
    assert not list(tmp_path.iterdir())


def _power_process(monkeypatch: pytest.MonkeyPatch, faulty_header: str) -> None:
    def available(_name: str) -> str:
        return "/fake/ngspice"

    def library(_path: Path, *, normalize_switch: bool) -> bytes:
        assert not normalize_switch
        return b"* synthetic private fixture, not a TI model\n"

    def run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if args[-1] == "--version":
            return subprocess.CompletedProcess(args, 0, "software fixture", "")
        root = kwargs["cwd"]
        assert isinstance(root, Path)
        switch = root.name.startswith("switch_")
        stop = 10e-6 if switch else 0.02
        times = np.linspace(0.0, stop, 201)
        columns = 1 if switch else 3
        header = "time v(out)" if switch else "time v(in) v(en) v(out)"
        if root.name == "supply_only":
            header = faulty_header
        data = np.column_stack((times, np.full((201, columns), 3.3)))
        stream = io.StringIO()
        np.savetxt(stream, data, header=header, comments="")
        (root / "transient.txt").write_text(stream.getvalue(), encoding="utf-8")
        (root / "transient-window.txt").write_text(
            f"integration_start = 0\nintegration_stop = {stop:.15g}\n", encoding="utf-8"
        )
        return subprocess.CompletedProcess(args, 0, "software fixture, not native evidence", "")

    monkeypatch.setattr("shutil.which", available)
    monkeypatch.setattr(subprocess, "run", run)
    monkeypatch.setattr("lab.rev_a_power.prepare_library", library)


@pytest.mark.parametrize(
    "header",
    ["time v(en) v(in) v(out)", "time v(out) v(en) v(in)",
     "time v(in) v(en) v(en)", "time v(in) v(en) v(other)",
     "frequency v(in) v(en) v(out)", "time v(in) v(en)"],
)
def test_power_report_rejects_mislabeled_trace_and_retains_its_peers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, header: str
) -> None:
    _power_process(monkeypatch, header)
    root = run_pilot(tmp_path, vendor_archive=Path("synthetic.zip"))
    report = read_object(json.loads((root / "pilot.json").read_text()), "pilot")
    raw = report["vendor_probes"]
    assert isinstance(raw, list)
    values: list[object] = raw
    probes = [read_object(value, "probe") for value in values]
    assert len(probes) == 4
    for probe in probes:
        if probe["case"] == "supply_only":
            assert probe["outcome"] == "rejected"
            assert "transient vectors" in str(probe["reason"])
            assert "final_output_v" not in probe
        else:
            assert probe["outcome"] == "probe_completed_not_validated"
    assert (root / "supply_only/transient.txt").read_text().startswith(header)
    assert (root / "supply_only/ngspice.log").is_file()
    assert report["hardware_validated"] is False
    manifest = read_object(json.loads((root / "manifest.json").read_text()), "manifest")
    files = read_object(manifest["files"], "files")
    for name, digest in files.items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
    assert not list(root.rglob("*.lib"))


@pytest.mark.native
@pytest.mark.parametrize("swapped", [False, True])
def test_native_vector_identity_catches_reordered_outputs(tmp_path: Path, swapped: bool) -> None:
    outputs = "v(b) v(a)" if swapped else "v(a) v(b)"
    path = tmp_path / "network.cir"
    path.write_text(
        "Independent vector identity fixture, not a hardware circuit\n"
        "Va a 0 1\nVb b 0 2\n"
        ".control\nset wr_singlescale\nset wr_vecnames\nset numdgt=15\n"
        f"tran 1u 10u\nwrdata transient.txt {outputs}\nquit\n.endc\n.end\n"
    )
    if swapped:
        with pytest.raises(RuntimeError, match="transient vectors"):
            run_ngspice_transient(path, tmp_path, columns=2, expected_vectors=("v(a)", "v(b)"))
    else:
        _, volts = run_ngspice_transient(
            path, tmp_path, columns=2, expected_vectors=("v(a)", "v(b)")
        )
        np.testing.assert_allclose(volts, np.tile([1.0, 2.0], (len(volts), 1)), rtol=0, atol=1e-12)
