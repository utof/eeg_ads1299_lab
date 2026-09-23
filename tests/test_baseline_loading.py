"""Untrusted JSON must be checked before receiving structured Python types."""

import json
import shutil
from pathlib import Path

import pytest

from hardware.rev_a import load_documents

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "field,value", [("afe", []), ("gates", {"board_profile_reviewed": "false"})]
)
def test_loading_rejects_wrong_nested_shape(tmp_path: Path, field: str, value: object) -> None:
    for name in ("board_profile.json", "bom.json", "sources.json"):
        shutil.copyfile(ROOT / "hardware/rev_a" / name, tmp_path / name)
    path = tmp_path / "board_profile.json"
    document: dict[str, object] = json.loads(path.read_text())
    document[field] = value
    path.write_text(json.dumps(document))
    with pytest.raises(ValueError, match="board_profile"):
        load_documents(tmp_path)
