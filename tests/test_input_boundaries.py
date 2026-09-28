"""Bad external data must be rejected before it becomes a typed recording."""

import json
from pathlib import Path

import numpy as np
import pytest

from lab.pipeline import load_data
from lab.signals import SyntheticConfig, generate


@pytest.mark.parametrize("bad_field", ["fs_hz", "codes", "invalid"])
def test_loader_rejects_invalid_structure(tmp_path: Path, bad_field: str) -> None:
    data = generate(SyntheticConfig(sessions=3, blocks_per_session=4))
    metadata: dict[str, object] = dict(data["metadata"])
    if bad_field == "fs_hz":
        metadata["fs_hz"] = True
    path = tmp_path / "malformed.npz"
    np.savez_compressed(
        path,
        codes=data["codes"].astype(float) if bad_field == "codes" else data["codes"],
        session=data["session"],
        block=data["block"],
        condition=data["condition"],
        time_s=data["time_s"],
        invalid=data["invalid"][:-1] if bad_field == "invalid" else data["invalid"],
        artifact_truth=data["artifact_truth"],
        metadata_json=np.array(json.dumps(metadata)),
    )
    with pytest.raises(ValueError, match=bad_field):
        load_data(path)
