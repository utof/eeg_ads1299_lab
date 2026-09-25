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
import shutil
import subprocess
import sys
import zipfile
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


def prepare_library(archive: Path, *, normalize_switch: bool) -> bytes:
    """Hash-lock the raw artifact before an optional, explicitly experimental edit."""
    if not isinstance(normalize_switch, bool):
        raise ValueError("normalization request must be boolean")
    if archive.stat().st_size > 4_000_000:
        raise ValueError("unexpected archive size")
    raw = archive.read_bytes()
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
        "tran 1u 10u\nwrdata transient.txt v(out)\nquit\n.endc\n.end\n"
    )


def _run(path: Path, text: str, columns: int) -> tuple[FloatArray, FloatArray]:
    path.mkdir()
    (path / "network.cir").write_text(text, encoding="utf-8")
    init = path / ".spiceinit"
    init.write_text("set ngbehavior=psa\n", encoding="utf-8")
    try:
        return run_ngspice_transient(path / "network.cir", path, columns=columns)
    finally:
        # Preserve the exact initialization bytes under a visible artifact name.
        # Reproduction restores this file to .spiceinit before invoking ngspice.
        init.rename(path / "spiceinit.txt")


def _switch_probe(root: Path, variant: _Switch, control: float) -> dict[str, object]:
    times, volts = _run(root, switch_netlist(variant, control), 1)
    low_resistance = (control == 0.001) if variant == "usual" else (control == 0)
    resistance = 1e-6 if low_resistance else 1e6
    expected = 3.3 * 1100 / (1100 + resistance)
    actual = float(volts[-1, 0])
    complete = abs(float(times[-1]) - 10e-6) < 1e-12
    return {
        "variant": variant,
        "control_v": control,
        "expected_endpoint_v": expected,
        "observed_endpoint_v": actual,
        "tolerance_v": 1e-5,
        "compatible_endpoint": complete and abs(actual - expected) <= 1e-5,
    }


def _vendor_netlist(library: Path, shutdown: bool, normalized: bool) -> str:
    if any(c in str(library) for c in ('"', "\n", "\r")):
        raise ValueError("unsupported library path characters")
    vin = (
        "PWL(0 0 1m 0 1.01m 5 15m 5 15.01m 0 20m 0)" if shutdown else "PWL(0 0 1m 0 1.01m 5 20m 5)"
    )
    return (
        f"TPS7A20 compatibility ONLY; experimental switch normalization={normalized}\n"
        f'.param V_out=3.3\n.include "{library}"\nVin in 0 {vin}\n'
        "Xreg in 0 in nc out TPS7A20_ADJ_TRANS\nCin in 0 1u\nCout out 0 1u\nRnc nc 0 1e12\n"
        "Rbase out 0 1100\nVload ctl 0 PWL(0 0 8m 0 8.01m 1 12m 1 12.01m 0 20m 0)\n"
        "Bload out 0 I={v(out)*v(ctl)*(0.010-0.003)/3.3}\n"
        ".options reltol=1e-5 abstol=1e-10 vntol=1e-7 method=gear\n"
        ".control\nset wr_singlescale\nset wr_vecnames\nset numdgt=15\n"
        "tran 1u 20m 0 1u\nwrdata transient.txt v(in) v(out)\nquit\n.endc\n.end\n"
    )


def _vendor_probe(root: Path, library: Path, shutdown: bool, normalized: bool) -> dict[str, object]:
    result: dict[str, object] = {"shutdown_requested": shutdown, "library_edited": normalized}
    try:
        times, volts = _run(root, _vendor_netlist(library, shutdown, normalized), 2)
        result.update(
            {
                "rows": len(times),
                "last_time_s": float(times[-1]),
                "final_output_v": float(volts[-1, -1]),
            }
        )
        if shutdown:
            if abs(float(times[-1]) - 0.02) > 1e-9:
                raise ValueError("shutdown trajectory did not finish the requested window")
            # No shutdown accuracy/decay behavior is established by reaching tstop.
            result["window_complete"] = True
        else:
            result.update(assess_trace(times, volts, target_v=3.3))
        result["outcome"] = "probe_completed_not_validated"
    except (RuntimeError, ValueError) as exc:
        result.update({"outcome": "rejected", "reason": str(exc)})
    return result


def run_pilot(
    out: Path, *, vendor_archive: Path | None = None, normalize_switch: bool = False
) -> Path:
    """Retain an investigation, including rejected probes; not a successful power study."""
    if not isinstance(normalize_switch, bool):
        raise ValueError("normalization request must be boolean")
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
    version = subprocess.run(
        [executable, "--version"], text=True, capture_output=True, timeout=5, check=True
    ).stdout
    root = out / uuid4().hex
    root.mkdir(parents=True)
    switches = [
        _switch_probe(root / f"switch_{variant}_{control:g}", variant, control)
        for variant in ("usual", "inverse", "normalized")
        for control in (0.0, 0.001)
    ]
    vendor: list[dict[str, object]] = []
    if library is not None:
        with TemporaryDirectory(prefix="private-ti-model-") as temporary:
            path = Path(temporary) / "vendor.lib"
            path.write_bytes(library)
            vendor = [
                _vendor_probe(root / name, path, shutdown, normalize_switch)
                for name, shutdown in (("startup_load", False), ("shutdown", True))
            ]
    repository = Path(__file__).resolve().parents[1]
    source = repository / "docs/references/ti/tps7a20/source_record.json"
    (root / "source_record.json").write_bytes(source.read_bytes())
    report = {
        "schema_version": 1,
        "purpose": "compatibility_investigation_including_failures",
        "ngspice_version": version,
        "ngbehavior": "psa",
        "uv_lock_sha256": hashlib.sha256((repository / "uv.lock").read_bytes()).hexdigest(),
        "switch_probes": switches,
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
            "Vendor archive/library are not included; retrieve the exact hashed source separately.",
        ],
    }
    (root / "pilot.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    files = {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in root.rglob("*")
        if p.is_file()
    }
    (root / "manifest.json").write_text(
        json.dumps({"run_id": root.name, "files": files}, indent=2) + "\n"
    )
    return root


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("reports/tps7a20_compatibility"))
    parser.add_argument("--vendor-archive", type=Path)
    parser.add_argument("--normalize-switch", action="store_true")
    args = parser.parse_args()
    try:
        root = run_pilot(
            args.out, vendor_archive=args.vendor_archive, normalize_switch=args.normalize_switch
        )
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"investigation": str(root), "power_model_validated": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
