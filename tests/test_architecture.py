"""Exercise the actual checked-in architecture policy, including rejection paths."""

import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest

import hardware.rev_a as baseline
import lab.analog as analog
from lab.validation import read_object

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def policy_copy(tmp_path: Path) -> Path:
    for folder in ("lab", "hardware", "tools", "tests"):
        for path in (ROOT / folder).rglob("*.py"):
            destination = tmp_path / path.relative_to(ROOT)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, destination)
    for name in ("tach.toml", "run_lab.py"):
        shutil.copyfile(ROOT / name, tmp_path / name)
    return tmp_path


def check_policy(root: Path) -> subprocess.CompletedProcess[str]:
    executable = shutil.which("tach")
    assert executable is not None, "Install the locked development environment"
    return subprocess.run(
        [executable, "check"], cwd=root, capture_output=True, text=True, timeout=30, check=False
    )


@pytest.mark.parametrize(
    "relative_path,source,allowed",
    [
        ("tests/probe.py", "from lab.analog import InputNetwork, transfer\n", True),
        ("tests/probe.py", "from lab.analog._solver import transfer\n", False),
        ("tests/probe.py", "import lab.analog._solver as solver\n", False),
        ("tests/probe.py", "from lab.dsp import _cross_validate\n", False),
        ("tests/probe.py", "from hardware.rev_a.check_baseline import validate\n", False),
        ("lab/protocol.py", "from lab.pipeline import run_demo\n", False),
        ("orphan.py", "from lab.analog import transfer\n", False),
    ],
)
def test_policy_accepts_facades_and_rejects_bypasses(
    policy_copy: Path, relative_path: str, source: str, allowed: bool
) -> None:
    path = policy_copy / relative_path
    with path.open("a", encoding="utf-8") as stream:
        stream.write("\n" + source)
    result = check_policy(policy_copy)
    assert (result.returncode == 0) is allowed, result.stdout + result.stderr


@pytest.mark.parametrize(
    "module,exports", [("lab.analog", analog.__all__), ("hardware.rev_a", baseline.__all__)]
)
def test_facade_export_lists_match_policy(module: str, exports: list[str]) -> None:
    config = read_object(tomllib.loads((ROOT / "tach.toml").read_text()), "Tach")
    interfaces = config["interfaces"]
    assert isinstance(interfaces, list)
    entries: list[object] = interfaces
    for entry in entries:
        rule = read_object(entry, "interface")
        if rule["from"] == [module]:
            assert rule["expose"] == sorted(exports)
            return
    pytest.fail(f"No interface for {module}")
