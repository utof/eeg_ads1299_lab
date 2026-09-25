"""One local/CI quality gate. Native checks are explicit; no hardware approval."""

import argparse
import hashlib
import importlib.metadata
import json
import math
import re
import shutil
import subprocess
import sys
import sysconfig
import time
import tomllib
from collections.abc import Sequence
from pathlib import Path
from tempfile import mkdtemp

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
                "not native and not integration",
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
    for name in ("ngspice", "node"):
        if shutil.which(name) is None:
            raise RuntimeError(f"Native checks require {name}; absence is not a pass")
    if not (shutil.which("g++") or shutil.which("clang++")):
        raise RuntimeError("Native checks require g++ or clang++; absence is not a pass")


def _native(out: Path) -> None:
    require_native_tools()
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
    parser.add_argument("--out", type=Path, default=ROOT / "reports/check")
    args = parser.parse_args(argv)
    out: Path = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    report_path = out / "CHECK_REPORT.json"
    report_path.unlink(missing_ok=True)  # Never retain a stale successful status.
    if args.firmware:
        (out / "FIRMWARE_BUILD.json").unlink(missing_ok=True)
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
        "physical_hardware_tested": False,
        "body_connection_authorized": False,
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 1 if failure else 0


if __name__ == "__main__":
    raise SystemExit(main())
