"""The next analog increment must be executable, not a documentation-only plan."""

from importlib.util import find_spec


def test_bounded_bias_study_entry_point_exists() -> None:
    assert find_spec("lab.rev_a_bias") is not None
