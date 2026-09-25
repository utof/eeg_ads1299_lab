"""The overload study must be an executable feature, not an edited plot."""

import subprocess
import sys
from pathlib import Path


def test_overload_study_cli_exists(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "lab.rev_a_bias_overload", "--help"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stderr
