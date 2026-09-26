"""Native exports are fixtures here; only fresh CLI runs are CAD execution evidence."""

import hardware.rev_a as rev_a


def test_schematic_checker_public_api_exists() -> None:
    assert callable(getattr(rev_a, "parse_schematic_xml", None)), "no native netlist parser"
    assert callable(getattr(rev_a, "validate_schematic", None)), "no pin-level checker"
