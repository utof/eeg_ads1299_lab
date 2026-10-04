"""S2 mean-load and two-node return arithmetic, not hardware qualification."""

import math
from pathlib import Path

import pytest

from tools import dc_budget

ROOT = Path(__file__).resolve().parents[1]


def test_resistive_and_capacitive_loads_are_separate() -> None:
    # 3V/10kohm * 0.015 = 4.5uA; 100pF*3V*30000 rising edges/s = 9uA.
    pull, charging = dc_budget.switched_load(3.0, 10000.0, 0.015, 100e-12, 30000.0)
    assert (pull, charging) == pytest.approx((4.5e-6, 9e-6))
    # No factor of two: falling edges dissipate already stored charge.
    assert dc_budget.switched_load(3.0, 10000.0, 0.5, 100e-12, 1e6) == pytest.approx(
        (150e-6, 300e-6)
    )


def test_static_high_still_loads_supply_without_clock_activity() -> None:
    assert dc_budget.switched_load(3.3, 33000.0, 1.0, 100e-12, 0.0) == pytest.approx((100e-6, 0.0))
    assert dc_budget.switched_load(3.3, 33000.0, 0.0, 0.0, 0.0) == (0.0, 0.0)


def test_parallel_returns_use_conductance_not_wire_count() -> None:
    # Ten 0.2ohm paths + two 0.1ohm paths => 70S, 14mA/70S = 0.2mV.
    resistances = {**{f"K1-{i}": 0.2 for i in range(10)}, "C4-1": 0.1, "C4-5": 0.1}
    shift, currents = dc_budget.parallel_returns(resistances, 0.014)
    assert shift == pytest.approx(0.0002)
    assert currents["K1-0"] == pytest.approx(0.001)
    assert currents["C4-1"] == pytest.approx(0.002)
    assert sum(currents.values()) == pytest.approx(0.014)
    assert dc_budget.parallel_returns({"combined": 1 / 70}, 0.014)[0] == pytest.approx(shift)
    opposite, reverse = dc_budget.parallel_returns(resistances, -0.014)
    assert opposite == pytest.approx(-shift)
    assert reverse == pytest.approx({k: -v for k, v in currents.items()})


@pytest.mark.parametrize("bad", [math.nan, math.inf, -1.0, True])
def test_nonphysical_switched_load_parameters_rejected(bad: float) -> None:
    for index in range(5):
        args = [3.3, 42200.0, 0.5, 100e-12, 30000.0]
        args[index] = bad
        with pytest.raises(ValueError):
            dc_budget.switched_load(*args)
    with pytest.raises(ValueError):
        dc_budget.parallel_returns({"wire": bad}, 0.001)


def test_impossible_fraction_zero_resistance_empty_paths_and_overflow_rejected() -> None:
    for args in [(3.3, 0.0, 0.5, 0.0, 0.0), (3.3, 1.0, 1.01, 0.0, 0.0)]:
        with pytest.raises(ValueError):
            dc_budget.switched_load(*args)
    for resistances in (dict[str, float](), {"wire": 0.0}):
        with pytest.raises(ValueError):
            dc_budget.parallel_returns(resistances, 0.0)
    for current in (math.nan, math.inf, True):
        with pytest.raises(ValueError):
            dc_budget.parallel_returns({"wire": 1.0}, current)
    with pytest.raises(ValueError):
        dc_budget.switched_load(1e300, 1.0, 1.0, 1e300, 1.0)
    with pytest.raises(ValueError):
        dc_budget.parallel_returns({"wire": 1e300}, 1e300)


def test_documented_s2_calculation_executes() -> None:
    import re

    path = ROOT / "docs/REV_A_CURRENT_RETURN_S2.md"
    assert path.is_file(), "missing executable mode/current/return study"
    assert len(re.findall(r"```python\n(.*?)\n```", path.read_text(), re.DOTALL)) == 1


def _run_study(root: Path, log: Path) -> dict[str, object]:
    import json
    import re
    import subprocess
    import sys

    from lab.validation import read_object

    text = (ROOT / "docs/REV_A_CURRENT_RETURN_S2.md").read_text()
    blocks = re.findall(r"```python\n(.*?)\n```", text, re.DOTALL)
    assert len(blocks) == 1
    run = subprocess.run(
        [sys.executable, "-c", blocks[0]],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    log.write_text(run.stdout + run.stderr)
    assert run.returncode == 0, run.stderr
    return read_object(json.loads(run.stdout), "S2 result")


def test_actual_study_keeps_the_four_channel_frame_and_port_kcl(tmp_path: Path) -> None:
    from lab.validation import read_object

    result = _run_study(ROOT, tmp_path / "study.log")
    assert result["frame_bytes"] == 15  # not the maximum27-byte local C array
    assert result["clock_rises_per_s"] == 30000
    assert result["spi_clock_busy_fraction"] == pytest.approx(0.03)
    assert result["qualification"] is False
    modes = read_object(result["modes"], "modes")
    active = read_object(modes["steady_acquisition"], "acquisition")
    quiet = read_object(modes["armed_quiet"], "quiet")
    # Independent formula:3 static highs plus CS.97 and SCLK.015,3.6V/41.778kohm.
    expected_pull = 3.985 * 3.6 / 41778
    assert active["pull_A"] == pytest.approx(expected_pull)
    assert quiet["pull_A"] == pytest.approx(4 * 3.6 / 41778)
    assert active["external_charging_A"] == pytest.approx(3.6e-10 * (30000 + 250))
    assert active["total_operating_max_A"] is None
    ret = read_object(result["return_example"], "return")
    assert ret["AFE_ground_export_A"] == pytest.approx(0.01205 + expected_pull)
    assert ret["C4_each_ohm"] == pytest.approx(0.07375171341463414)
    branches = read_object(ret["branch_A"], "branches")
    assert len(branches) == 12
    assert branches["C4-0"] == pytest.approx(0.0013219370633298757)
    assert branches["K1-0"] == pytest.approx(0.0009749512344688805)


def test_current_ledger_matches_both_schematic_sides_and_unchanged_firmware() -> None:
    import json

    from hardware.rev_a import load_documents, parse_auxiliary_contract
    from lab.validation import read_object

    m = read_object(json.loads((ROOT / "docs/studies/s2_current_return.json").read_text()), "S2")
    profile, bom, _ = load_documents()
    assert not any(profile["gates"].values())
    assert m["qualification"] is False
    assert m["source_commit"] == "7325d659aeedf2628cf2a4430854e90ef1277785"
    uncertainty = read_object(m["uncertainty"], "uncertainty")
    assert len(uncertainty) == 8 and all(v is None for v in uncertainty.values())
    rows = read_object(m["forward_outputs"], "forward")
    assert set(rows) == {"SCLK", "MOSI", "CS", "RESET", "START", "PWDN", "CLKSEL"}
    pulls = next(row for row in bom["line_items"] if row["id"] == "bus_pulldowns")
    assert pulls["mpn"] == "RC0603FR-0742K2L"
    contract = parse_auxiliary_contract(
        (ROOT / "hardware/rev_a/auxiliary/contract.json").read_text()
    )
    by_ref = {p.reference: p for p in contract.parts.values()}
    for name, raw in rows.items():
        r = read_object(raw, name)
        assert r["afe_pull"] in pulls["references"]
        ref, pad = r["buffer"], r["pad"]
        assert isinstance(ref, str) and isinstance(pad, str)
        assert by_ref[ref].pins[pad].net == "AFE_" + name
        assert by_ref[ref].pins["14"].net == "AFE_DVDD"
    reverse = read_object(m["reverse_outputs"], "reverse")
    assert set(reverse) == {"MISO", "DRDY"}
    for name, raw in reverse.items():
        r = read_object(raw, name)
        ref, pad, pull = r["buffer"], r["pad"], r["pull"]
        assert isinstance(ref, str) and isinstance(pad, str) and isinstance(pull, str)
        assert by_ref[ref].pins[pad].net == "MCU_" + name
        assert by_ref[ref].pins["1"].net == "MCU_3V3"
        assert by_ref[pull].pins["1"].net == "MCU_" + name
    sketch = (ROOT / "firmware/esp32_ads1299_bench/esp32_ads1299_bench.ino").read_text()
    assert "SPISettings settings(1000000,MSBFIRST,SPI_MODE1);" in sketch
    assert "for(uint8_t i=0;i<3+3*channels;++i)frame[i]=busTransfer(0);" in sketch
    assert "command(0x08); // START while physical START stays low" in sketch


def test_remote_load_cancels_but_signal_return_does_not(tmp_path: Path) -> None:
    import json
    import shutil

    from lab.validation import read_object

    # Change the accounting hypothesis, never the physical board or S1 input.
    clone = tmp_path / "copy"
    clone.mkdir()
    (clone / "docs/studies").mkdir(parents=True)
    # A linked Git working directory is unnecessary: read the real source through symlinks.
    for name in ("hardware", "firmware", ".git"):
        (clone / name).symlink_to(ROOT / name, target_is_directory=True)
    shutil.copyfile(
        ROOT / "docs/studies/s1_supply_paths.json", clone / "docs/studies/s1_supply_paths.json"
    )
    model = read_object(
        json.loads((ROOT / "docs/studies/s2_current_return.json").read_text()), "model"
    )
    hypothesis = read_object(model["return_example"], "return hypothesis")
    hypothesis["remote_internal_and_bleed_A_assumed"] = 0.030
    model["return_example"] = hypothesis
    (clone / "docs/studies/s2_current_return.json").write_text(json.dumps(model))
    ret = read_object(
        _run_study(clone, tmp_path / "remote-current.log")["return_example"], "result"
    )
    assert ret["AFE_5V_in_A"] == pytest.approx(0.04240427647134856)
    assert ret["AFE_ground_export_A"] == pytest.approx(0.01239338647134856)
