"""The CLI must publish a generation identity rather than a reusable marker."""

from pathlib import Path

from lab.rev_a import main


def test_cli_publishes_an_identifiable_generation(tmp_path: Path) -> None:
    assert main(["--out", str(tmp_path)]) == 0
    assert (tmp_path / "current.json").is_file()
    assert not (tmp_path / "study.json").exists()
