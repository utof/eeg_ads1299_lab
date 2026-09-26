"""TPS7A20 compatibility investigation, NOT a validated Rev A power model.

No vendor library is distributed. A caller may supply the exact TI SBVM961 ZIP.
Rejected probes are retained as failures; completing the investigation is not
proof of model compatibility, physical behavior or hardware safety.
"""

import argparse
import hashlib
import io
import json
import math
import os
import shutil
import stat
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal
from uuid import uuid4

import numpy as np

from .analog import run_ngspice_transient
from .data_types import FloatArray

ARCHIVE_SHA256 = "4db279371817cb0873e103b03ddf26c6a5a1ff2c4672093c0037c940dc8c8fd2"
LIBRARY_SHA256 = "154acfdd2199ac44259908b90b07d15bc7e535a45c8c51d1413894c900718b69"
_Switch = Literal["usual", "inverse", "normalized"]
_OLD = b"_S2 VSWITCH Roff=1e-6 Ron=1E6 Voff=0 Von=1m"
_NEW = b"_S2 VSWITCH Roff=1E6 Ron=1e-6 Voff=1m Von=0"


@dataclass(frozen=True)
class _VendorStimulus:
    """One fixed control experiment, not an editable hardware configuration."""

    name: str
    supply_off: bool
    enable_off: bool


_VENDOR_STIMULI = (
    _VendorStimulus("startup_load", supply_off=False, enable_off=False),
    _VendorStimulus("shutdown", supply_off=True, enable_off=True),
    _VendorStimulus("enable_only", supply_off=False, enable_off=True),
    _VendorStimulus("supply_only", supply_off=True, enable_off=False),
)


_ARCHIVE_LIMIT = 4_000_000
_RAW_WINDOW = (
    "let integration_start = time[0]\n"
    "let integration_stop = time[length(time)-1]\n"
    "print integration_start integration_stop > transient-window.txt\n"
)


def _read_archive(path: Path) -> bytes:
    """Inspect and bound one open descriptor, including growth after fstat.

    Nonblocking open lets POSIX FIFOs reach the regular-file rejection without
    waiting for a writer. Symlinks to regular files are permitted; the descriptor
    rather than a prior pathname stat defines the object actually read.
    """
    flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0)
    with os.fdopen(os.open(path, flags), "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("TI archive must be a regular file")
        if info.st_size > _ARCHIVE_LIMIT:
            raise ValueError("unexpected archive size")
        raw = stream.read(_ARCHIVE_LIMIT + 1)
    if len(raw) > _ARCHIVE_LIMIT:
        raise ValueError("unexpected archive size")
    return raw


def prepare_library(archive: Path, *, normalize_switch: bool) -> bytes:
    """Hash-lock the raw artifact before an optional, explicitly experimental edit."""
    if not isinstance(normalize_switch, bool):
        raise ValueError("normalization request must be boolean")
    raw = _read_archive(archive)
    if hashlib.sha256(raw).hexdigest() != ARCHIVE_SHA256:
        raise ValueError("TI archive SHA-256 mismatch")
    with zipfile.ZipFile(io.BytesIO(raw)) as source:
        library = source.read("tps7a20-adj_trans.lib")
    if hashlib.sha256(library).hexdigest() != LIBRARY_SHA256:
        raise ValueError("TI library SHA-256 mismatch")
    if normalize_switch:
        if library.count(_OLD) != 1:
            raise ValueError("inverse switch edit must have exactly one match")
        library = library.replace(_OLD, _NEW)
    return library


def assess_trace(times: FloatArray, volts: FloatArray, *, target_v: float) -> dict[str, object]:
    """Reject incomplete windows and wrong plateaus; this is only a sanity probe.

    The 2% plateau criterion is NOT a datasheet-accuracy qualification or a
    comparison with Cadence PSpice/physical hardware. It catches a disconnected
    pass path even when the internal regulated node is approximately correct.
    """
    if isinstance(target_v, bool) or not math.isfinite(target_v) or target_v <= 0:
        raise ValueError("target must be finite and positive")
    if times.ndim != 1 or len(times) < 2 or volts.ndim != 2 or volts.shape[0] != len(times):
        raise ValueError("invalid trace dimensions")
    if volts.shape[1] < 1 or not np.all(np.isfinite(times)) or not np.all(np.isfinite(volts)):
        raise ValueError("trace must be finite")
    if times[0] < 0 or times[0] > 10e-6 or np.any(np.diff(times) <= 0):
        raise ValueError("invalid time axis")
    if abs(float(times[-1]) - 0.02) > 1e-9:
        raise ValueError("requested time window is incomplete")
    plateaus = []
    for start, stop in ((0.004, 0.007), (0.009, 0.011), (0.017, 0.019)):
        samples: FloatArray = volts[(times >= start) & (times <= stop), -1]
        if samples.size < 2 or np.max(np.abs(samples - target_v)) > 0.02 * target_v:
            raise ValueError(f"output plateau failed at {start:g}..{stop:g} seconds")
        plateaus.append({"start_s": start, "stop_s": stop, "mean_v": float(np.mean(samples))})
    return {"window_complete": True, "plateaus": plateaus, "sanity_tolerance_fraction": 0.02}


def switch_netlist(variant: _Switch, control_v: float) -> str:
    """Handwritten divider reproducer; contains no TI library or model internals."""
    if variant not in ("usual", "inverse", "normalized") or control_v not in (0, 0.001):
        raise ValueError("unknown switch fixture or endpoint")
    specs = {
        "usual": "Roff=1e6 Ron=1e-6 Voff=0 Von=1m",
        "inverse": "Roff=1e-6 Ron=1e6 Voff=0 Von=1m",
        "normalized": "Roff=1e6 Ron=1e-6 Voff=1m Von=0",
    }
    return (
        f"Independent {variant} VSWITCH endpoint compatibility probe\n"
        f"Vin in 0 3.3\nVctrl ctrl 0 {control_v:g}\n"
        f"Sprobe in out ctrl 0 DUT\nRload out 0 1100\n.model DUT VSWITCH({specs[variant]})\n"
        ".control\nset wr_singlescale\nset wr_vecnames\nset numdgt=15\n"
        "tran 1u 10u\n" + _RAW_WINDOW + "wrdata transient.txt v(out)\nquit\n.endc\n.end\n"
    )


def _run(
    path: Path, text: str, columns: int, *, expected_stop_s: float
) -> tuple[FloatArray, FloatArray]:
    path.mkdir()
    (path / "network.cir").write_text(text, encoding="utf-8")
    init = path / ".spiceinit"
    init.write_text("set ngbehavior=psa\n", encoding="utf-8")
    try:
        return run_ngspice_transient(
            path / "network.cir", path, columns=columns, expected_stop_s=expected_stop_s
        )
    finally:
        # Preserve the exact initialization bytes under a visible artifact name.
        # Reproduction restores this file to .spiceinit before invoking ngspice.
        init.rename(path / "spiceinit.txt")


def _switch_probe(root: Path, variant: _Switch, control: float) -> dict[str, object]:
    low_resistance = (control == 0.001) if variant == "usual" else (control == 0)
    resistance = 1e-6 if low_resistance else 1e6
    expected = 3.3 * 1100 / (1100 + resistance)
    result: dict[str, object] = {
        "variant": variant,
        "control_v": control,
        "expected_endpoint_v": expected,
        "observed_endpoint_v": None,
        "tolerance_v": 1e-5,
        "window_complete": False,
        "compatible_endpoint": None,
        "outcome": "rejected",
    }
    try:
        times, volts = _run(root, switch_netlist(variant, control), 1, expected_stop_s=10e-6)
        actual = float(volts[-1, 0])
        result.update({"observed_endpoint_v": actual, "last_time_s": float(times[-1])})
        if abs(float(times[-1]) - 10e-6) >= 1e-12:
            raise ValueError("requested switch time window is incomplete")
        result.update(
            {
                "window_complete": True,
                "outcome": "probe_completed_not_validated",
                "compatible_endpoint": abs(actual - expected) <= 1e-5,
                "reason": None,
            }
        )
    except (RuntimeError, ValueError) as exc:
        result["reason"] = str(exc)
    return result


def _input_waveform(falling: bool) -> str:
    """Keep rise, fall and observation times identical across the four controls."""
    return (
        "PWL(0 0 1m 0 1.01m 5 15m 5 15.01m 0 20m 0)"
        if falling
        else "PWL(0 0 1m 0 1.01m 5 20m 5)"
    )


def _vendor_netlist(library: Path, stimulus: _VendorStimulus, normalized: bool) -> str:
    if any(c in str(library) for c in ('"', "\n", "\r")):
        raise ValueError("unsupported library path characters")
    return (
        f"TPS7A20 {stimulus.name} compatibility ONLY; switch normalization={normalized}\n"
        f'.param V_out=3.3\n.include "{library}"\n'
        f"Vin in 0 {_input_waveform(stimulus.supply_off)}\n"
        f"Venable en 0 {_input_waveform(stimulus.enable_off)}\n"
        "Xreg in 0 en nc out TPS7A20_ADJ_TRANS\nCin in 0 1u\nCout out 0 1u\nRnc nc 0 1e12\n"
        "Rbase out 0 1100\nVload ctl 0 PWL(0 0 8m 0 8.01m 1 12m 1 12.01m 0 20m 0)\n"
        "Bload out 0 I={v(out)*v(ctl)*(0.010-0.003)/3.3}\n"
        ".options reltol=1e-5 abstol=1e-10 vntol=1e-7 method=gear\n"
        ".control\nset wr_singlescale\nset wr_vecnames\nset numdgt=15\n"
        "tran 1u 20m 0 1u\n"
        + _RAW_WINDOW
        + "wrdata transient.txt v(in) v(en) v(out)\nquit\n.endc\n.end\n"
    )


def _vendor_probe(
    root: Path, library: Path, stimulus: _VendorStimulus, normalized: bool
) -> dict[str, object]:
    shutdown = stimulus.supply_off or stimulus.enable_off
    result: dict[str, object] = {
        "case": stimulus.name,
        "supply_collapse_requested": stimulus.supply_off,
        "enable_deassertion_requested": stimulus.enable_off,
        "shutdown_requested": shutdown,
        "voltage_columns": ["vin_v", "enable_v", "vout_v"],
        "library_edited": normalized,
        "window_complete": False,
    }
    try:
        times, volts = _run(
            root, _vendor_netlist(library, stimulus, normalized), 3, expected_stop_s=0.02
        )
        result.update(
            {
                "rows": len(times),
                "last_time_s": float(times[-1]),
                "final_output_v": float(volts[-1, -1]),
            }
        )
        if abs(float(times[-1]) - 0.02) > 1e-9:
            raise ValueError("vendor trajectory did not finish the requested window")
        result["window_complete"] = True
        # No shutdown accuracy/decay behavior is established by reaching tstop.
        if not shutdown:
            result.update(assess_trace(times, volts, target_v=3.3))
        result["outcome"] = "probe_completed_not_validated"
    except (RuntimeError, ValueError) as exc:
        result.update({"outcome": "rejected", "reason": str(exc)})
    return result


def _version_output(value: str | bytes | None) -> str:
    return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value or ""


def _version(executable: str, root: Path) -> str:
    """Retain setup diagnostics without pretending the investigation completed."""
    log = root / "ngspice-version.log"
    try:
        result = subprocess.run(
            [executable, "--version"], text=True, capture_output=True, timeout=5, check=False
        )
    except subprocess.TimeoutExpired as exc:
        log.write_text(_version_output(exc.stdout) + "\n" + _version_output(exc.stderr))
        raise RuntimeError(f"ngspice version probe timed out: see {log}") from exc
    except OSError as exc:
        log.write_text(str(exc) + "\n")
        raise RuntimeError(f"ngspice version probe could not start: see {log}") from exc
    log.write_text(result.stdout + "\n" + result.stderr)
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError(f"ngspice version probe failed: see {log}")
    return result.stdout


def _vendor_results(
    root: Path, library: bytes | None, normalize_switch: bool
) -> list[dict[str, object]]:
    """Own the private vendor library lifetime; never leave it in retained reports."""
    if library is None:
        return []
    with TemporaryDirectory(prefix="private-ti-model-") as temporary:
        path = Path(temporary) / "vendor.lib"
        path.write_bytes(library)
        return [
            _vendor_probe(root / stimulus.name, path, stimulus, normalize_switch)
            for stimulus in _VENDOR_STIMULI
        ]


def _publish_investigation(root: Path, report: dict[str, object]) -> None:
    """Bind all retained diagnostics before applying an optional execution gate."""
    (root / "pilot.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    files = {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in root.rglob("*")
        if p.is_file()
    }
    (root / "manifest.json").write_text(
        json.dumps({"run_id": root.name, "files": files}, indent=2) + "\n"
    )


def run_pilot(
    out: Path,
    *,
    vendor_archive: Path | None = None,
    normalize_switch: bool = False,
    require_complete_switches: bool = False,
) -> Path:
    """Retain an investigation, including rejected probes; not a successful power study."""
    if not isinstance(normalize_switch, bool):
        raise ValueError("normalization request must be boolean")
    if not isinstance(require_complete_switches, bool):
        raise ValueError("switch completion requirement must be boolean")
    if normalize_switch and vendor_archive is None:
        raise ValueError("normalization requires the caller-supplied vendor archive")
    library = (
        prepare_library(vendor_archive, normalize_switch=normalize_switch)
        if vendor_archive
        else None
    )
    executable = shutil.which("ngspice")
    if executable is None:
        raise RuntimeError("ngspice is required for the compatibility pilot")
    root = out / uuid4().hex
    root.mkdir(parents=True)
    version = _version(executable, root)
    switches = [
        _switch_probe(root / f"switch_{variant}_{control:g}", variant, control)
        for variant in ("usual", "inverse", "normalized")
        for control in (0.0, 0.001)
    ]
    vendor = _vendor_results(root, library, normalize_switch)
    repository = Path(__file__).resolve().parents[1]
    source = repository / "docs/references/ti/tps7a20/source_record.json"
    (root / "source_record.json").write_bytes(source.read_bytes())
    report: dict[str, object] = {
        "schema_version": 2,
        "purpose": "compatibility_investigation_including_failures",
        "ngspice_version": version,
        "ngbehavior": "psa",
        "uv_lock_sha256": hashlib.sha256((repository / "uv.lock").read_bytes()).hexdigest(),
        "switch_probes": switches,
        "switch_execution_complete": all(probe["window_complete"] is True for probe in switches),
        "vendor_probes": vendor,
        "vendor_archive_sha256": ARCHIVE_SHA256 if library is not None else None,
        "original_library_sha256": LIBRARY_SHA256 if library is not None else None,
        "executed_library_sha256": hashlib.sha256(library).hexdigest()
        if library is not None
        else None,
        "library_edited": normalize_switch,
        "model_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "hardware_validated": False,
        "body_connection_permitted": False,
        "limitations": [
            "Endpoint tests do not establish continuous-switch interpolation equivalence.",
            "No Cadence reference run or physical comparison was performed.",
            "The 1uF capacitors and conductance load are fixtures, not a validated power design.",
            "Completing this investigation does not mean every probe passed.",
            "Shutdown controls isolate stimuli; completion does not qualify output decay.",
            "Vendor archive/library are not included; retrieve the exact hashed source separately.",
        ],
    }
    _publish_investigation(root, report)
    if require_complete_switches and not report["switch_execution_complete"]:
        raise RuntimeError(f"Incomplete switch executions; investigation retained at {root}")
    return root


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("reports/tps7a20_compatibility"))
    parser.add_argument("--vendor-archive", type=Path)
    parser.add_argument("--normalize-switch", action="store_true")
    parser.add_argument("--require-complete-switches", action="store_true")
    args = parser.parse_args()
    try:
        root = run_pilot(
            args.out,
            vendor_archive=args.vendor_archive,
            normalize_switch=args.normalize_switch,
            require_complete_switches=args.require_complete_switches,
        )
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"investigation": str(root), "power_model_validated": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
