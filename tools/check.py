"""One local/CI quality gate. Native checks are explicit; no hardware approval."""

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
import re
import shutil
import subprocess
import sys
import sysconfig
import time
import tomllib
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path
from tempfile import mkdtemp

from hardware.rev_a import (
    auxiliary_source_snapshot,
    bench_harness,
    load_documents,
    parse_schematic_xml,
    read_schematic_file,
    schematic_source_snapshot,
    validate,
    validate_erc,
    validate_schematic,
    validate_schematic_bom,
)

ROOT = Path(__file__).resolve().parents[1]


def _tool(name: str) -> str:
    executable = shutil.which(name, path=sysconfig.get_path("scripts"))
    if executable is None:
        raise RuntimeError(f"Missing {name} in this Python environment; run uv sync --locked")
    return executable


def command_plan(out: Path) -> list[tuple[str, list[str]]]:
    return [
        ("format", [_tool("ruff"), "format", "--check", "."]),
        ("lint", [_tool("ruff"), "check", "."]),
        (
            "types",
            [
                _tool("pyrefly"),
                "check",
                "--python-interpreter-path",
                sys.executable,
                "--min-severity",
                "warn",
            ],
        ),
        ("complexity", [_tool("complexipy"), "--failed"]),
        ("architecture", [_tool("tach"), "check"]),
        ("baseline", [sys.executable, "hardware/rev_a/check_baseline.py"]),
        (
            "tests",
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "-m",
                "not native and not integration and not schematic",
                "--cov",
                "--cov-branch",
                f"--cov-report=json:{out / 'coverage.json'}",
                "--cov-report=term-missing",
                f"--junitxml={out / 'pytest.xml'}",
            ],
        ),
    ]


def run_step(name: str, command: Sequence[str], out: Path, timeout: float = 300) -> None:
    """Every subprocess is bounded; a timeout or nonzero exit is a failure."""
    out.mkdir(parents=True, exist_ok=True)
    log = out / f"{name}.log"
    print(f"[{name}] {' '.join(command)}", flush=True)
    # A real file retains even partial output if the child times out.
    with log.open("w", encoding="utf-8") as stream:
        try:
            result = subprocess.run(
                command,
                cwd=ROOT,
                stdout=stream,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            stream.write(f"\n{name} timed out after {timeout:g} s\n")
            raise RuntimeError(f"{name} timed out; see {log}") from exc
    print(log.read_text(encoding="utf-8"), end="", flush=True)
    if result.returncode:
        raise RuntimeError(f"{name} failed with exit code {result.returncode}; see {log}")


def _mapping(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{label}: expected an object")
    items: dict[object, object] = value
    result: dict[str, object] = {}
    for key, item in items.items():
        if not isinstance(key, str):
            raise ValueError(f"{label}: expected string keys")
        result[key] = item
    return result


def _finite_number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError(f"{label}: expected a finite number")
    return float(value)


def check_branch_coverage(path: Path, minimum: float) -> float:
    raw: object = json.loads(path.read_text())
    totals = _mapping(_mapping(raw, "coverage").get("totals"), "totals")
    total = _finite_number(totals.get("num_branches"), "num_branches")
    covered = _finite_number(totals.get("covered_branches"), "covered_branches")
    if total <= 0 or not 0 <= covered <= total:
        raise ValueError("No valid measured branch coverage")
    percent = 100.0 * covered / total
    if percent < minimum:
        raise ValueError(f"Branch coverage {percent:.2f}% is below the {minimum:.2f}% floor")
    print(f"Branch coverage: {covered:g}/{total:g} = {percent:.2f}% (floor {minimum:.2f}%)")
    return percent


def require_native_tools() -> None:
    for name in ("ngspice", "node", "openscad"):
        if shutil.which(name) is None:
            raise RuntimeError(f"Native checks require {name}; absence is not a pass")
    if not (shutil.which("g++") or shutil.which("clang++")):
        raise RuntimeError("Native checks require g++ or clang++; absence is not a pass")
    renderer = shutil.which("openscad")
    assert renderer is not None  # Required above; use this resolved executable for the probe.
    try:
        version = subprocess.run(
            [renderer, "--version"], capture_output=True, text=True, timeout=10, check=False
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"OpenSCAD 2021.01 version probe timed out after {exc.timeout} s; "
            f"stdout={exc.stdout!r}; stderr={exc.stderr!r}"
        ) from exc
    except OSError as exc:
        raise RuntimeError(f"OpenSCAD 2021.01 version probe failed: {exc}") from exc
    output = "\n".join(part.strip() for part in (version.stdout, version.stderr) if part.strip())
    if version.returncode != 0 or output != "OpenSCAD version 2021.01":
        raise RuntimeError(
            f"OpenSCAD 2021.01 required; probe exit {version.returncode}, output {output!r}"
        )


def _native(out: Path) -> None:
    require_native_tools()
    # Retain the diagnostic run before pytest can fail on the same native fixture.
    run_step(
        "rev-a-power",
        [
            sys.executable,
            "-m",
            "lab.rev_a_power",
            "--require-complete-switches",
            "--out",
            str(out / "rev_a_power"),
        ],
        out,
    )
    run_step(
        "rev-a-supply",
        [sys.executable, "-m", "lab.rev_a_supply", "--out", str(out / "rev_a_supply")],
        out,
    )
    run_step(
        "native-tests",
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-m",
            "native or integration",
            f"--junitxml={out / 'native-pytest.xml'}",
            f"--basetemp={out / 'native-temp'}",
        ],
        out,
    )
    run_step(
        "ngspice",
        [
            sys.executable,
            "run_lab.py",
            "circuits",
            "--require-ngspice",
            "--out",
            str(out / "circuits"),
        ],
        out,
    )
    run_step(
        "rev-a-input",
        [sys.executable, "-m", "lab.rev_a", "--require-ngspice", "--out", str(out / "rev_a_input")],
        out,
    )
    run_step(
        "rev-a-bias",
        [
            sys.executable,
            "-m",
            "lab.rev_a_bias",
            "--require-ngspice",
            "--out",
            str(out / "rev_a_bias"),
        ],
        out,
    )
    run_step(
        "rev-a-bias-overload",
        [
            sys.executable,
            "-m",
            "lab.rev_a_bias_overload",
            "--require-ngspice",
            "--out",
            str(out / "rev_a_bias_overload"),
        ],
        out,
    )
    run_step(
        "loopback",
        [
            sys.executable,
            "-m",
            "tools.run_loopback",
            "--out",
            str(out / "loopback"),
        ],
        out,
        timeout=40,
    )


def _firmware_config() -> dict[str, str]:
    raw = _mapping(json.loads((ROOT / "firmware/toolchain.json").read_text()), "firmware")
    result: dict[str, str] = {}
    for name in ("cli_version", "core", "core_version", "fqbn", "cpp_flags"):
        value = raw.get(name)
        if not isinstance(value, str) or not value:
            raise ValueError(f"firmware {name} must be a nonempty string")
        result[name] = value
    return result


def _firmware(out: Path) -> None:
    """Compile the complete guarded sketch, never upload or enable its hardware gate."""
    marker = out / "FIRMWARE_BUILD.json"
    cli = shutil.which("arduino-cli")
    if cli is None:
        raise RuntimeError("Firmware checks require arduino-cli; absence is not a pass")
    config = _firmware_config()
    run_step("firmware-source", ["git", "rev-parse", "HEAD"], out)
    source_commit = (out / "firmware-source.log").read_text().strip()
    if re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
        raise RuntimeError("Cannot establish firmware source commit")
    run_step("arduino-version", [cli, "version"], out)
    version = (out / "arduino-version.log").read_text()
    if not re.search(r"Version:\s*" + re.escape(config["cli_version"]) + r"\b", version):
        raise RuntimeError("arduino-cli does not match the pinned version")
    run_step("arduino-core", [cli, "core", "list"], out)
    core = (out / "arduino-core.log").read_text()
    pattern = (
        r"^" + re.escape(config["core"]) + r"\s+" + re.escape(config["core_version"]) + r"(?:\s|$)"
    )
    if re.search(pattern, core, re.MULTILINE) is None:
        raise RuntimeError("Arduino ESP32 core does not match the pinned version")
    run_step(
        "s3-board", [cli, "board", "details", "--fqbn", config["fqbn"], "--format", "json"], out
    )
    build = Path(mkdtemp(prefix="s3-", dir=out))
    run_step(
        "s3-compile",
        [
            cli,
            "compile",
            "--fqbn",
            config["fqbn"],
            "--build-property",
            "compiler.cpp.extra_flags=" + config["cpp_flags"],
            "--output-dir",
            str(build),
            "firmware/esp32_ads1299_bench",
        ],
        out,
        timeout=600,
    )
    binaries = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in build.glob("*.bin")}
    if not binaries:
        raise RuntimeError("S3 compilation returned without fresh binary artifacts")
    marker.write_text(
        json.dumps(
            {
                "scope": "target_compile_only",
                "source_commit": source_commit,
                "source_sha256": {
                    p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in (ROOT / "firmware/esp32_ads1299_bench").iterdir()
                    if p.is_file()
                },
                "toolchain": config,
                "artifact_directory": build.name,
                "sha256": binaries,
                "physical_hardware_tested": False,
                "board_profile_reviewed": False,
                "body_connection_authorized": False,
            },
            indent=2,
        )
        + "\n"
    )


def _schematic_snapshot(cad: Path, footprints: Path) -> dict[str, str]:
    result = schematic_source_snapshot(cad, footprints)
    result.update(auxiliary_source_snapshot(cad.parent / "auxiliary", footprints))
    for name in (
        "board_profile.json",
        "bom.json",
        "sources.json",
        "check_baseline.py",
        "check_schematic.py",
        "schematic_sources.py",
        "schematic_symbols.py",
        "schematic_bom.py",
        "footprint_geometry.py",
        "pcb_seed.py",
        "layout/rev_a.kicad_pcb",
        "harness.py",
        "auxiliary.py",
        "__init__.py",
    ):
        path = cad.parent / name
        result["contract/" + name] = hashlib.sha256(read_schematic_file(path).encode()).hexdigest()
    result["tools/check.py"] = hashlib.sha256(
        read_schematic_file(ROOT / "tools/check.py").encode()
    ).hexdigest()
    # Bind the route-defining source AND the host oracle used by this gate.
    # This list describes the existing focused test inputs, not a new pin map.
    for name in (
        "firmware/toolchain.json",
        "pyproject.toml",
        "tests/test_firmware_sketch_startup.py",
        "tests/test_bench_harness.py",
        "tests/test_pcb_placement.py",
        "tests/test_service_access.py",
        "hardware/rev_a/service_c4.json",
        "tests/test_pcb_power.py",
        "tests/test_auxiliary_contract.py",
        "tests/test_auxiliary_native.py",
        "tests/test_auxiliary_placement.py",
        "tests/auxiliary_placement_probe.py",
        "tests/test_auxiliary_ground.py",
        "tests/auxiliary_ground_probe.py",
        "tests/test_auxiliary_routing.py",
        "tests/auxiliary_routing_probe.py",
        "tests/test_reference_performance.py",
        "tests/test_auxiliary_clock.py",
        "tests/test_supply_inventory.py",
        "tests/supply_inventory_probe.py",
        "docs/studies/s1_supply_paths.json",
        "tools/dc_budget.py",
        "docs/REV_A_CURRENT_RETURN_S2.md",
        "docs/studies/s2_current_return.json",
        "tests/test_current_return_s2.py",
        "tests/fixtures/auxiliary_clock_before_review.json",
        "tests/fixtures/auxiliary_p2_preservation.json",
        "tests/fixtures/auxiliary_p3_pending_edges.json",
        "tests/native_sketch_startup_test.cpp",
        "tests/native_c2_session_test.cpp",
        "tests/test_firmware_interlock.py",
        *(
            "firmware/esp32_ads1299_bench/" + name
            for name in (
                "bench_console.h",
                "board_config.h",
                "board_config_rev_a_s3.h",
                "esp32_ads1299_bench.ino",
                "portable_core.h",
                "rev_a_startup.h",
                "c2_interlock.h",
            )
        ),
        *(
            "tests/firmware_stubs/" + name
            for name in ("Arduino.h", "SPI.h", "WiFi.h", "WiFiUdp.h", "driver/gpio.h")
        ),
    ):
        result[name] = hashlib.sha256(read_schematic_file(ROOT / name).encode()).hexdigest()
    for name in (
        "tests/fixtures/auxiliary_c3_netlist.xml.gz",
        "tests/fixtures/rev_a_netlist.xml.gz",
    ):
        path = ROOT / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 2_000_000:
            raise ValueError("invalid native graph fixture")
        result[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def _schematic(out: Path) -> None:
    """Fresh native ERC/export plus project contracts; never release hardware."""
    cli = shutil.which("kicad-cli")
    if cli is None:
        raise RuntimeError("Schematic checks require kicad-cli; absence is not a pass")
    cad = ROOT / "hardware/rev_a/kicad"
    footprints = Path(
        os.environ.get("KICAD9_FOOTPRINT_DIR", "/usr/share/kicad/footprints")
    ).resolve()
    before = _schematic_snapshot(cad, footprints)
    profile, bom, sources = load_documents(cad.parent)
    errors = validate(profile, bom, sources)
    if errors:
        raise ValueError("Invalid schematic baseline: " + "; ".join(errors))
    build = Path(mkdtemp(prefix="schematic-", dir=out))
    # A fresh native configuration prevents local GUI preferences hiding ERC findings.
    prefix = [
        "env",
        "LC_ALL=C",
        "LANG=C",
        f"KICAD_CONFIG_HOME={build / 'config'}",
        f"KICAD9_FOOTPRINT_DIR={footprints}",
        cli,
    ]
    run_step("kicad-version", [*prefix, "version"], out)
    if (out / "kicad-version.log").read_text().strip() != "9.0.2":
        raise ValueError("KiCad must match the pinned 9.0.2 version")
    run_step("schematic-source", ["git", "rev-parse", "HEAD"], out)
    source_commit = (out / "schematic-source.log").read_text().strip()
    if re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
        raise ValueError("Cannot establish schematic source commit")
    run_step("schematic-dirty", ["git", "status", "--porcelain", "--untracked-files=normal"], out)
    root = str(cad / "rev_a.kicad_sch")
    run_step(
        "schematic-erc",
        [
            *prefix,
            "sch",
            "erc",
            "--format",
            "json",
            "--severity-all",
            "--exit-code-violations",
            "-o",
            str(build / "erc.json"),
            root,
        ],
        out,
    )
    validate_erc(read_schematic_file(build / "erc.json"))
    run_step(
        "schematic-netlist",
        [
            *prefix,
            "sch",
            "export",
            "netlist",
            "--format",
            "kicadxml",
            "-o",
            str(build / "netlist.xml"),
            root,
        ],
        out,
    )
    netlist = parse_schematic_xml(read_schematic_file(build / "netlist.xml"))
    errors = validate_schematic(netlist, profile, bom)
    if errors:
        raise ValueError("Schematic connectivity: " + "; ".join(errors))
    run_step(
        "schematic-pdf",
        [
            *prefix,
            "sch",
            "export",
            "pdf",
            "--black-and-white",
            "-o",
            str(build / "schematic.pdf"),
            root,
        ],
        out,
    )
    run_step(
        "schematic-bom",
        [
            *prefix,
            "sch",
            "export",
            "bom",
            "--fields",
            "Reference,ContractRef,Value,MPN,Footprint,Population,${DNP},${EXCLUDE_FROM_BOARD}",
            "--labels",
            "Reference,ContractRef,Value,MPN,Footprint,Population,DNP,OffBoard",
            "-o",
            str(build / "bom.csv"),
            root,
        ],
        out,
    )
    validate_schematic_bom(read_schematic_file(build / "bom.csv"), netlist)
    _harness_console_proof(out)
    harness = bench_harness(
        netlist,
        profile,
        bom,
        sources,
        read_schematic_file(ROOT / "firmware/esp32_ads1299_bench/bench_console.h"),
    )
    (build / "harness.json").write_text(
        json.dumps(
            {
                "scope": "document_derived_terminal_groups_not_physical_validation",
                "devkit_revision": "v1.1",
                "physical_wiring_approved": False,
                "console_interface_qualified": False,
                "body_connection_authorized": False,
                "groups": [asdict(group) for group in harness],
            },
            indent=2,
        )
        + "\n"
    )
    run_step(
        "schematic-tests",
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-m",
            "schematic",
            f"--junitxml={out / 'schematic-pytest.xml'}",
            f"--basetemp={out / 'schematic-tests'}",
        ],
        out,
        # Aggregate budget for the growing real-CAD suite, not a per-command limit.
        # The growing suite exceeded 300 s on CI; individual native bounds stay fixed.
        timeout=450,
    )
    if _schematic_snapshot(cad, footprints) != before:
        raise RuntimeError("A schematic source/dependency changed during native checks")
    _schematic_marker(out, build, source_commit, before, len(netlist.parts), len(netlist.nets))


def _harness_console_proof(out: Path) -> None:
    """The standalone CAD gate must execute its claimed firmware route too.

    Reuse existing real-sketch host tests. This is not target/peripheral evidence;
    it does not require ngspice or run unrelated native studies a second time.
    """
    compiler = shutil.which("g++") or shutil.which("clang++")
    if compiler is None:
        raise RuntimeError("Harness route checks require g++ or clang++; absence is not a pass")
    run_step("harness-console-compiler", [compiler, "--version"], out)
    run_step(
        "harness-console-tests",
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/test_firmware_sketch_startup.py",
            "tests/test_bench_harness.py",
            "tests/test_firmware_interlock.py",
            "-m",
            "native",
            f"--junitxml={out / 'harness-console-pytest.xml'}",
            f"--basetemp={out / 'harness-console-tests'}",
        ],
        out,
    )


def _schematic_marker(
    out: Path, build: Path, commit: str, inputs: dict[str, str], parts: int, pins: int
) -> None:
    artifacts: dict[str, str] = {}
    for name in ("erc.json", "netlist.xml", "schematic.pdf", "bom.csv", "harness.json"):
        path = build / name
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError("Native CAD command did not produce every fresh artifact")
        artifacts[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    report = {
        "scope": "native_erc_and_project_connectivity_only",
        "source_commit": commit,
        "source_dirty": bool((out / "schematic-dirty.log").read_text().strip()),
        "kicad_version": "9.0.2",
        "source_sha256": inputs,
        "artifact_directory": build.name,
        "artifact_sha256": artifacts,
        "component_count": parts,
        "terminal_count": pins,
        "schematic_released": False,
        "physical_hardware_tested": False,
        "body_connection_authorized": False,
    }
    (out / "SCHEMATIC_CHECK.json").write_text(json.dumps(report, indent=2) + "\n")


def _branch_floor() -> float:
    config = _mapping(tomllib.loads((ROOT / "pyproject.toml").read_text()), "pyproject")
    tool = _mapping(config.get("tool"), "tool")
    settings = _mapping(tool.get("lab-check"), "lab-check")
    floor = _finite_number(settings.get("minimum-branch-coverage"), "minimum-branch-coverage")
    if not 0 < floor <= 100:
        raise ValueError("Branch floor must be in (0, 100]")
    return floor


def _installed_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "not installed"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--native", action="store_true", help="Require native tools and run integration checks"
    )
    parser.add_argument(
        "--firmware", action="store_true", help="Require the pinned S3 target compiler"
    )
    parser.add_argument(
        "--schematic",
        action="store_true",
        help="Require pinned native KiCad ERC/export and connectivity checks",
    )
    parser.add_argument("--out", type=Path, default=ROOT / "reports/check")
    args = parser.parse_args(argv)
    out: Path = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    report_path = out / "CHECK_REPORT.json"
    report_path.unlink(missing_ok=True)  # Never retain a stale successful status.
    if args.firmware:
        (out / "FIRMWARE_BUILD.json").unlink(missing_ok=True)
    if args.schematic:
        (out / "SCHEMATIC_CHECK.json").unlink(missing_ok=True)
    completed: list[str] = []
    started = time.monotonic()
    failure: str | None = None
    branch_percent: float | None = None
    try:
        for name, command in command_plan(out):
            run_step(name, command, out)
            completed.append(name)
        branch_percent = check_branch_coverage(out / "coverage.json", _branch_floor())
        if args.native:
            _native(out)
            completed.append("native")
        if args.firmware:
            _firmware(out)
            completed.append("firmware")
        if args.schematic:
            _schematic(out)
            completed.append("schematic")
    except (RuntimeError, ValueError, OSError) as exc:
        failure = str(exc)
        print(f"ERROR: {failure}", file=sys.stderr)
    versions = {
        name: _installed_version(name)
        for name in ("ruff", "pyrefly", "complexipy", "tach", "pytest", "numpy", "scipy")
    }
    report = {
        "passed": failure is None,
        "completed": completed,
        "error": failure,
        "branch_coverage_percent": branch_percent,
        "python": sys.version,
        "versions": versions,
        "elapsed_seconds": time.monotonic() - started,
        "native_requested": bool(args.native),
        "firmware_requested": bool(args.firmware),
        "schematic_requested": bool(args.schematic),
        "physical_hardware_tested": False,
        "body_connection_authorized": False,
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 1 if failure else 0


if __name__ == "__main__":
    raise SystemExit(main())
