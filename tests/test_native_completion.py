"""An interpolated export must not conceal an unfinished native integration."""

from pathlib import Path

import pytest

from lab.rev_a_bias import BiasModel
from lab.rev_a_bias_overload import (
    InterferencePulse,
    OutputLimits,
    export_overload_spice,
    run_overload_study,
)


@pytest.mark.native
def test_truncated_native_window_cannot_publish_a_padded_overload_trace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def truncated(
        path: Path, model: BiasModel, pulse: InterferencePulse, limits: OutputLimits
    ) -> Path:
        netlist = export_overload_spice(path, model, pulse, limits)
        if path.parent.parent.name == "positive_overload":
            original = netlist.read_text()
            shortened = original.replace("tran 1n 0.035 0", "tran 1n 0.025 0")
            assert shortened != original
            netlist.write_text(shortened)
        return netlist

    monkeypatch.setattr("lab.rev_a_bias_overload.export_overload_spice", truncated)
    with pytest.raises(RuntimeError, match=r"native.*window|integration.*window"):
        run_overload_study(tmp_path, require_ngspice=True, run_id="e" * 32)
    root = tmp_path / ("e" * 32)
    assert (root / "positive_overload" / "native" / "ngspice.log").is_file()
    assert not (root / "manifest.json").exists()
