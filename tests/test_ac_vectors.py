"""AC table semantics: independent complex values and adversarial exporter mutations."""

import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from lab.analog import run_ngspice


def _process(monkeypatch: pytest.MonkeyPatch, root: Path, table: bytes) -> None:
    def available(_name: str) -> str:
        return "/fake/ngspice"

    def run(args: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        (root / "ac.txt").write_bytes(table)
        return subprocess.CompletedProcess(args, 0, "software fixture, not native evidence", "")

    monkeypatch.setattr("shutil.which", available)
    monkeypatch.setattr(subprocess, "run", run)


@pytest.mark.parametrize(
    "header",
    [
        "time hr hi",
        "frequency hi hr",
        "frequency hr hr",
        "frequency real imag",
        "frequency hr",
        "frequency hr hi extra",
        "1 2 3",
    ],
)
def test_ac_rejects_wrong_scale_or_vector_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, header: str
) -> None:
    _process(monkeypatch, tmp_path, (header + "\n1 2 -3\n10 4 -5\n").encode())
    with pytest.raises(RuntimeError, match="AC vectors"):
        run_ngspice(tmp_path / "network.cir", tmp_path)
    assert (tmp_path / "ac.txt").read_text().startswith(header)
    assert "software fixture" in (tmp_path / "ngspice.log").read_text()


@pytest.mark.parametrize("axis", [(0.0, 1.0), (-1.0, 1.0), (1.0, 1.0), (10.0, 1.0)])
def test_ac_rejects_nonpositive_repeated_or_decreasing_frequency(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, axis: tuple[float, float]
) -> None:
    _process(monkeypatch, tmp_path, f"frequency hr hi\n{axis[0]} 2 -3\n{axis[1]} 4 -5\n".encode())
    with pytest.raises(RuntimeError, match="AC frequency axis"):
        run_ngspice(tmp_path / "network.cir", tmp_path)


@pytest.mark.parametrize(
    "table",
    [
        b"frequency hr hi\n",
        b"frequency hr hi\n1 2 -3\n",
        b"frequency hr hi\n1 2 -3\n2 bad 4\n",
        b"frequency hr hi\n1 2 -3\n2 4\n",
        b"frequency hr hi\n1 2 nan\n2 3 4\n",
        b"frequency hr hi\n1 2 3\n2 inf 4\n",
        b"frequency hr hi\n1 2 3\n2 4 \xff\n",
    ],
)
def test_ac_invalid_tables_use_the_shared_rejection_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, table: bytes
) -> None:
    _process(monkeypatch, tmp_path, table)
    with pytest.raises(RuntimeError):
        run_ngspice(tmp_path / "network.cir", tmp_path)
    assert (tmp_path / "ac.txt").read_bytes() == table


@settings(max_examples=40, derandomize=True, deadline=None)
@given(
    st.lists(
        st.tuples(
            st.floats(-1e3, 1e3, allow_nan=False, allow_infinity=False),
            st.floats(-1e3, 1e3, allow_nan=False, allow_infinity=False),
        ),
        min_size=2,
        max_size=8,
    )
)
def test_ac_preserves_asymmetric_complex_values(values: list[tuple[float, float]]) -> None:
    rows = "".join(f"{index} {real!r} {imag!r}\n" for index, (real, imag) in enumerate(values, 1))
    with TemporaryDirectory() as temporary, pytest.MonkeyPatch.context() as patch:
        root = Path(temporary)
        _process(patch, root, ("  frequency\t hr   hi  \n" + rows).encode())
        frequency, actual = run_ngspice(root / "network.cir", root)
        np.testing.assert_array_equal(frequency, np.arange(1, len(values) + 1))
        np.testing.assert_array_equal(actual.real, [value[0] for value in values])
        np.testing.assert_array_equal(actual.imag, [value[1] for value in values])


@pytest.mark.native
@pytest.mark.parametrize("swapped", [False, True])
def test_native_ac_rejects_export_order_mutation(tmp_path: Path, swapped: bool) -> None:
    outputs = "hi hr" if swapped else "hr hi"
    path = tmp_path / "network.cir"
    path.write_text(
        "Independent passive RC identity fixture, not a board model\n"
        "Vin in 0 AC 1\nRfeed in out 1000\nCload out 0 1u\n"
        ".control\nset wr_singlescale\nset wr_vecnames\nset numdgt=15\n"
        "ac lin 3 100 300\nlet hr = real(v(out))\nlet hi = imag(v(out))\n"
        f"wrdata ac.txt {outputs}\nquit\n.endc\n.end\n"
    )
    if swapped:
        with pytest.raises(RuntimeError, match="AC vectors"):
            run_ngspice(path, tmp_path)
    else:
        frequency, response = run_ngspice(path, tmp_path)
        np.testing.assert_allclose(frequency, [100.0, 200.0, 300.0], rtol=0, atol=1e-9)
        expected = 1.0 / (1.0 + 2j * np.pi * frequency * 1e-3)
        np.testing.assert_allclose(response, expected, rtol=1e-12, atol=1e-12)
