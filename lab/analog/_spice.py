"""Netlist serialization and the bounded external-simulator process boundary."""

import math
import shutil
import subprocess
from pathlib import Path

import numpy as np

from ..data_types import ComplexArray, FloatArray
from ._model import Drive, InputNetwork

_DEFAULT_CONFIG = InputNetwork()


def export_spice(
    path: str | Path, network: InputNetwork = _DEFAULT_CONFIG, drive: Drive = "differential"
) -> Path:
    """Write a self-contained AC netlist; only passive parts and sources."""
    if drive not in ("differential", "common"):
        raise ValueError("Unknown drive")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    p = network
    # Negative amplitude expressed as 180-degree phase, portable AC syntax.
    sources = ("AC 0.5", "AC 0.5 180") if drive == "differential" else ("AC 1", "AC 1")
    text = f"""Illustrative EEG passive input network -- NOT A HUMAN-USE SCHEMATIC
* 0 denotes local analog midpoint for small-signal AC, NOT protective earth.
* No ADS1299 silicon, input clamps, body-bias loop, or safety analysis included.
Vp skinp 0 {sources[0]}
Vn skinn 0 {sources[1]}
Rep skinp ep {p.r_electrode_p:.12g}
Cep skinp ep {p.c_electrode_p:.12g}
Ren skinn en {p.r_electrode_n:.12g}
Cen skinn en {p.c_electrode_n:.12g}
Rsp ep inp {p.r_series_p:.12g}
Rsn en inn {p.r_series_n:.12g}
Rip inp 0 {p.r_input_p:.12g}
Rin inn 0 {p.r_input_n:.12g}
Ccp inp 0 {p.c_common_p:.12g}
Ccn inn 0 {p.c_common_n:.12g}
Cd inp inn {p.c_differential:.12g}
.control
set wr_singlescale
set wr_vecnames
set numdgt=15
ac dec 40 0.1 100000
let h = v(inp)-v(inn)
let hr = real(h)
let hi = imag(h)
wrdata ac.txt hr hi
quit
.endc
.end
"""
    path.write_text(text)
    return path


def _log_text(value: str | bytes | None) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value or ""


def _execute_ngspice(
    netlist: str | Path, output_dir: str | Path, filename: str, *, window_required: bool = False
) -> Path:
    """Shared bounded process boundary; callers select a fixed output filename."""
    exe = shutil.which("ngspice")
    if not exe:
        raise RuntimeError("ngspice executable is absent; install it, then rerun --require-ngspice")
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    netlist = Path(netlist).resolve()
    output = output_dir / filename
    log = output_dir / "ngspice.log"
    # A successful exit without NEW output must not validate a previous run.
    output.unlink(missing_ok=True)
    if window_required:
        (output_dir / "transient-window.txt").unlink(missing_ok=True)
    try:
        result = subprocess.run(
            [exe, "-b", str(netlist)],
            cwd=output_dir,
            capture_output=True,
            text=True,
            timeout=45,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        log.write_text(_log_text(exc.stdout) + "\n" + _log_text(exc.stderr), encoding="utf-8")
        raise RuntimeError(f"ngspice timed out: see {log}") from exc
    except OSError as exc:
        log.write_text(f"ngspice could not start: {exc}\n", encoding="utf-8")
        raise RuntimeError(f"ngspice could not start: see {log}") from exc
    log.write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")
    if result.returncode != 0 or not output.exists():
        raise RuntimeError(f"ngspice failed: see {log}")
    return output


def run_ngspice(netlist: str | Path, output_dir: str | Path) -> tuple[FloatArray, ComplexArray]:
    """Run an AC netlist with a deadline and read its real/imaginary output."""
    output = _execute_ngspice(netlist, output_dir, "ac.txt")
    data: FloatArray = np.loadtxt(output, skiprows=1, dtype=np.float64)
    if data.ndim != 2 or data.shape[1] != 3 or not np.all(np.isfinite(data)):
        raise RuntimeError("Unexpected ngspice wrdata format (expected f, real, imag)")
    response: ComplexArray = data[:, 1] + 1j * data[:, 2]
    return data[:, 0], response


def run_ngspice_transient(
    netlist: str | Path,
    output_dir: str | Path,
    *,
    columns: int,
    expected_stop_s: float | None = None,
) -> tuple[FloatArray, FloatArray]:
    """Read a fresh transient.txt: increasing nonnegative seconds, then real columns.

    Exporters must use wr_singlescale/wr_vecnames. Adaptive timesteps need not
    include t=0. Without expected_stop_s this verifies format/execution only.
    With it, require a fresh transient-window.txt recorded from the active time
    vector BEFORE linearize. An interpolated endpoint cannot prove completion.
    The window is integrity evidence from our exporter, not authenticated proof.
    """
    if isinstance(columns, bool) or not isinstance(columns, int) or columns < 1:
        raise ValueError("transient columns must be a positive integer")
    if expected_stop_s is not None:
        _validate_stop(expected_stop_s)
    output = _execute_ngspice(
        netlist, output_dir, "transient.txt", window_required=expected_stop_s is not None
    )
    if expected_stop_s is not None:
        _verify_native_window(output.parent / "transient-window.txt", expected_stop_s)
    try:
        data: FloatArray = np.loadtxt(output, skiprows=1, dtype=np.float64, ndmin=2)
    except (ValueError, UserWarning) as exc:
        raise RuntimeError("Invalid ngspice transient table") from exc
    if data.shape[0] < 2 or data.shape[1] != columns + 1 or not np.all(np.isfinite(data)):
        raise RuntimeError("Invalid ngspice transient table shape or values")
    times = data[:, 0]
    if np.any(times < 0) or np.any(np.diff(times) <= 0):
        raise RuntimeError("Invalid ngspice transient time axis")
    return times, data[:, 1:]


def _validate_stop(stop: float) -> None:
    if isinstance(stop, bool) or not isinstance(stop, (int, float)):
        raise ValueError("expected transient stop must be a positive finite real number")
    if not math.isfinite(stop) or stop <= 0:
        raise ValueError("expected transient stop must be a positive finite real number")


def _verify_native_window(path: Path, expected_stop: float) -> None:
    """Read the raw time-vector endpoints, not linearize's requested output grid."""
    try:
        rows = [line.split() for line in path.read_text(encoding="utf-8").splitlines()]
        if len(rows) != 2 or any(len(row) != 3 or row[1] != "=" for row in rows):
            raise ValueError("two named scalar endpoints required")
        if [row[0] for row in rows] != ["integration_start", "integration_stop"]:
            raise ValueError("unexpected endpoint names")
        start, stop = (float(row[2]) for row in rows)
    except (OSError, UnicodeError, ValueError) as exc:
        raise RuntimeError("Missing or invalid native integration window") from exc
    if not math.isfinite(start) or not math.isfinite(stop) or not 0 <= start < stop:
        raise RuntimeError("Invalid native integration window values")
    if not math.isclose(stop, expected_stop, rel_tol=0, abs_tol=1e-12):
        raise RuntimeError(
            f"Incomplete native integration window: stopped at {stop:g}s; "
            f"requested {expected_stop:g}s"
        )
