"""An omitted amplifier pole must be an explicit assumption, not a hidden constant."""

from dataclasses import fields

from lab.rev_a_bias import load_bias_model


def test_optional_extra_pole_is_an_explicit_model_parameter() -> None:
    assert "extra_pole_hz" in {field.name for field in fields(load_bias_model())}
