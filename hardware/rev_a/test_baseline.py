"""Regression tests for the declarative baseline, not physical performance."""

from __future__ import annotations

import copy
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from typing_extensions import override

from hardware.rev_a import load_documents, totals, validate

HERE = Path(__file__).resolve().parent


class BaselineTests(unittest.TestCase):
    @override
    def setUp(self) -> None:
        self.profile, self.bom, self.sources = copy.deepcopy(load_documents())

    def assert_rejected(self, substring: str) -> None:
        errors = validate(self.profile, self.bom, self.sources)
        self.assertTrue(any(substring in error for error in errors), errors)

    def test_baseline_consistent(self) -> None:
        self.assertEqual(validate(self.profile, self.bom, self.sources), [])

    def test_markdown_bom_matches_json(self) -> None:
        doc = (HERE.parent.parent / "docs/HARDWARE_BASELINE_REV_A.md").read_text(encoding="utf-8")
        for row in self.bom["line_items"]:
            value = Decimal(row["planning_unit_usd"]) * row["quantity"]
            expected = (
                f"`{row['mpn']}` | {row['quantity']} | {row['population'].upper()} | ${value:.2f} |"
            )
            self.assertIn(expected, doc)
        self.assertIn(f"Planning subtotal: ${totals(self.bom)['planning_total']:.2f}", doc)

    def test_costs_and_optional_exclusion(self) -> None:
        result = totals(self.bom)
        self.assertEqual(result["fitted"], Decimal("74.14"))
        self.assertEqual(result["planning_total"], Decimal("92.14"))
        self.assertEqual(result["dnp_options"], Decimal("2.40"))

    def test_every_gate_is_fail_closed(self) -> None:
        for gate in self.profile["gates"]:
            with self.subTest(gate=gate):
                changed = copy.deepcopy(self.profile)
                changed["gates"][gate] = True
                self.assertTrue(any(gate in e for e in validate(changed, self.bom, self.sources)))

    def test_missing_gate_rejected(self) -> None:
        del self.profile["gates"]["human_connection_allowed"]
        self.assertTrue(validate(self.profile, self.bom, self.sources))

    def test_wrong_channel_count(self) -> None:
        self.profile["afe"]["channels"] = 8
        self.assert_rejected("four physical channels")

    def test_missing_frame_status_bytes(self) -> None:
        self.profile["afe"]["frame_bytes"] = 12
        self.assert_rejected("status")

    def test_wrong_spi_mode(self) -> None:
        self.profile["spi"]["mode"] = 0
        self.assert_rejected("SPI contract")

    def test_usb_gpio_conflict(self) -> None:
        self.profile["spi"]["signals"][0]["gpio"] = 19
        self.assert_rejected("conflicting GPIO")

    def test_duplicate_gpio(self) -> None:
        self.profile["spi"]["signals"][0]["gpio"] = 11
        self.assert_rejected("GPIO conflict")

    def test_count_mismatch(self) -> None:
        self.bom["line_items"][3]["quantity"] = 4
        self.assert_rejected("quantity/reference mismatch")

    def test_duplicate_reference(self) -> None:
        self.bom["line_items"][3]["references"][0] = "U1"
        self.assert_rejected("duplicate component reference")

    def test_unknown_source(self) -> None:
        self.bom["line_items"][0]["source_ids"] = ["INVENTED"]
        self.assert_rejected("unknown source")

    def test_radio_supply_rejected(self) -> None:
        self.profile["power"]["dvdd_regulator_supplies_mcu"] = True
        self.assert_rejected("must not supply the ESP32")

    def test_bad_analog_feed_budget(self) -> None:
        self.profile["power"]["analog_branch_design_current_budget_a"] = 0.03
        self.assert_rejected("outside ADS operating range")

    def test_cm_cap_population_rejected(self) -> None:
        self.profile["input_network"]["common_mode_capacitance_fitted_f"] = 4.7e-9
        self.assert_rejected("ground-shunt")

    def test_clamps_cannot_be_silently_populated(self) -> None:
        self.bom["line_items"][-1]["population"] = "fit"
        self.assert_rejected("DNP")

    def test_reference_capacitance_tolerance_margin(self) -> None:
        next(r for r in self.bom["line_items"] if r["id"] == "vref")["spec"]["capacitance_f"] = (
            10e-6
        )
        self.assert_rejected("below 10 uF")

    def test_price_increase_flags_budget(self) -> None:
        self.bom["line_items"][0]["planning_unit_usd"] = "90.00"
        self.assert_rejected("planning budget exceeded")

    def test_nonfinite_price_rejected(self) -> None:
        self.bom["line_items"][0]["planning_unit_usd"] = "NaN"
        self.assert_rejected("finite and nonnegative")

    def test_header_pin_missing(self) -> None:
        del self.profile["interface_headers"]["J_DIG"]["pin_map"]["20"]
        self.assert_rejected("pins 1 through 20")

    def test_cli_works_from_other_working_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            proc = subprocess.run(
                [sys.executable, str(HERE / "check_baseline.py")],
                cwd=directory,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("NOT hardware or safety validation", proc.stdout)

    def test_cli_bad_json_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "board_profile.json").write_text("{broken", encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(HERE / "check_baseline.py"), "--directory", directory],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("ERROR:", proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)


if __name__ == "__main__":
    unittest.main()
