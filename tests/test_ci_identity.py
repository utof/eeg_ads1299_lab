"""Text contracts for the four pinned, repository-owned gate checkout steps."""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEAD_REF = "          ref: ${{ github.event.pull_request.head.sha || github.sha }}"


class WorkflowIdentityTests(unittest.TestCase):
    def test_every_gate_checkout_selects_the_requested_commit(self) -> None:
        for name, expected_count in (("quality", 2), ("schematic", 1), ("firmware", 1)):
            text = (ROOT / f".github/workflows/{name}.yml").read_text(encoding="utf-8")
            steps = re.split(r"(?m)^      - ", text)[1:]
            checkouts = [step for step in steps if step.startswith("uses: actions/checkout@")]
            with self.subTest(workflow=name):
                self.assertEqual(len(checkouts), expected_count)
            for index, checkout in enumerate(checkouts):
                with self.subTest(workflow=name, checkout=index):
                    self.assertIn(HEAD_REF, checkout.splitlines())
                    self.assertIn("          persist-credentials: false", checkout.splitlines())
                    self.assertIn("          fetch-depth: 0", checkout.splitlines())
