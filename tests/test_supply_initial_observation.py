"""An early source edge must not disappear inside the historical near-zero allowance."""

import json
import shutil
from dataclasses import replace
from itertools import pairwise
from pathlib import Path
from typing import cast

import numpy as np
import pytest

from lab.data_types import FloatArray
from lab.rev_a_supply import SupplyCase, SupplyTiming, rail_response, run_supply_study
from lab.validation import read_object


@pytest.mark.parametrize(
    ("source_on", "first_sample", "rejected"),
    [
        (2e-9, 9e-9, True),
        (0.0, 0.5e-9, True),
        (2e-9, 1e-9, False),
        (2e-9, 2e-9, False),
        (0.0, 0.0, False),
        (0.001, 9e-9, False),
        (0.001, 11e-9, True),
    ],
)
def test_initial_observation_is_bounded_by_source_on_not_only_absolute_tolerance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    source_on: float,
    first_sample: float,
    rejected: bool,
) -> None:
    timing = SupplyTiming(source_on_s=source_on)

    def process_double(
        _netlist: Path,
        out: Path,
        *,
        columns: int,
        expected_stop_s: float,
        expected_vectors: tuple[str, ...],
    ) -> tuple[FloatArray, FloatArray]:
        assert columns == 1 and expected_stop_s == timing.stop_s
        assert expected_vectors == ("v(avdd)",)
        resistances = {
            "stiff_source": 0.0,
            "shared_0p1_ohm": 0.1,
            "shared_0p5_ohm": 0.5,
            "shared_1_ohm": 1.0,
            "bulk_100uf": 1.0,
        }
        case = replace(
            SupplyCase(),
            shared_r_ohm=resistances[out.name],
            capacitance_f=100e-6 if out.name == "bulk_100uf" else 10e-6,
        )
        times = np.array(
            [first_sample, 0.002, 0.004, 0.008, 0.009, 0.010, 0.012, 0.014, 0.016, 0.02]
        )
        # Exact analytical values isolate observation completeness; this double
        # neither runs ngspice nor independently verifies the physics.
        return times, rail_response(case, times, timing=timing)[:, None]

    monkeypatch.setattr("lab.rev_a_supply.run_ngspice_transient", process_double)
    if rejected:
        with pytest.raises(RuntimeError, match="retained"):
            run_supply_study(tmp_path, timing=timing)
    else:
        run_supply_study(tmp_path, timing=timing)
    report = read_object(json.loads(next(tmp_path.glob("*/study.json")).read_text()), "report")
    assert report["native_comparison_passed"] is (not rejected)
    rows = cast(list[dict[str, object]], report["cases"])
    assert len(rows) == 5
    if rejected:
        for row in rows:
            assert row["native_execution_complete"] is False
            assert row["native_comparison_passed"] is False
            assert row["error"] == "incomplete observed supply window"


@pytest.mark.native
@pytest.mark.parametrize("source_on", [0.0, 2e-9])
def test_native_zero_and_early_source_edges_keep_the_initial_sample(
    tmp_path: Path, source_on: float
) -> None:
    assert shutil.which("ngspice"), "actual early-source test requires ngspice"
    try:
        root = run_supply_study(tmp_path, timing=SupplyTiming(source_on_s=source_on))
    except RuntimeError:
        # The CI upload does not include pytest's temporary directory. Surface
        # each retained case failure before that directory disappears.
        for report_path in tmp_path.glob("*/study.json"):
            print(report_path.read_text())
        for log_path in tmp_path.glob("*/*/ngspice.log"):
            print(str(log_path), log_path.read_text()[-4000:])
        raise
    report = read_object(json.loads((root / "study.json").read_text()), "report")
    assert report["native_comparison_passed"] is True
    assert read_object(report["timing"], "timing")["source_on_s"] == source_on
    files = list(root.glob("*/comparison.csv"))
    assert len(files) == 5
    for path in files:
        first = float(path.read_text().splitlines()[1].split(",")[0])
        assert 0 <= first <= min(1e-8, source_on)


@pytest.mark.parametrize("source_on", [0.0, 2e-9, 0.001])
def test_source_pwl_has_strictly_increasing_time_points(source_on: float) -> None:
    from lab.rev_a_supply import supply_netlist

    line = next(
        line
        for line in supply_netlist(
            SupplyCase(), timing=SupplyTiming(source_on_s=source_on)
        ).splitlines()
        if line.startswith("Vsource ")
    )
    values = [float(value) for value in line.split("PWL(", 1)[1].removesuffix(")").split()]
    times, volts = values[::2], values[1::2]
    assert times[0] == 0 and volts[0] == 0
    assert all(later > earlier for earlier, later in pairwise(times))
    assert times[-2:] == [source_on + 1e-9, 0.02]
    assert volts[-2:] == [4.95, 4.95]
