"""Property tests complement fixed protocol and scientific regression cases."""

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from lab.adc import MAX_CODE, MIN_CODE, quantize, sinc3_magnitude, to_volts
from lab.data_types import FloatArray
from lab.protocol import FLAG_SYNTHETIC, Packet, StreamDecoder, native_frame, parse_native
from lab.validation import boolean, float_array, integer, number, read_object, stored_array, text


@settings(max_examples=80, deadline=None, derandomize=True)
@given(
    channels=st.sampled_from([4, 6, 8]),
    sample=st.integers(MIN_CODE, MAX_CODE),
    sequence=st.integers(0, 2**32 - 1),
    timestamp=st.integers(0, 2**32 - 1),
)
def test_packet_and_native_round_trip(
    channels: int, sample: int, sequence: int, timestamp: int
) -> None:
    codes = (sample,) * channels
    packet = Packet(sequence, timestamp, codes, flags=FLAG_SYNTHETIC)
    encoded = packet.encode()
    assert Packet.decode(encoded) == packet
    assert parse_native(native_frame(codes), channels)[1] == codes
    split = len(encoded) // 2
    decoder = StreamDecoder()
    assert decoder.feed(encoded[:split]) == []
    assert decoder.feed(encoded[split:]) == [packet]


def test_scalar_and_array_return_contracts_are_preserved() -> None:
    scalar, clipped = quantize(0.0)
    assert isinstance(scalar, np.int32)
    assert isinstance(clipped, np.bool_)
    assert isinstance(to_volts(0), np.float64)
    assert isinstance(sinc3_magnitude(10), np.float64)
    array: FloatArray = np.array([0.0, 1e-6], dtype=np.float64)
    codes, flags = quantize(array)
    assert isinstance(codes, np.ndarray) and codes.shape == array.shape
    assert isinstance(flags, np.ndarray) and flags.shape == array.shape


@pytest.mark.parametrize("value", [None, "3", True, [], {}])
def test_numeric_boundary_rejects_non_numbers(value: object) -> None:
    with pytest.raises(ValueError):
        number({"value": value}, "value")
    with pytest.raises(ValueError):
        integer({"value": value}, "value")


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_numeric_boundary_rejects_nonfinite_values(value: float) -> None:
    with pytest.raises(ValueError):
        number({"value": value}, "value")


def test_validated_primitives_and_defaults() -> None:
    assert number({}, "x", 1.5) == 1.5
    assert integer({}, "x", 2) == 2
    assert boolean({}, "x", False) is False
    assert text({"x": "ok"}, "x") == "ok"
    assert read_object({"x": 3}, "test") == {"x": 3}
    for value in (None, "false", 0):
        with pytest.raises(ValueError):
            boolean({"x": value}, "x")
    with pytest.raises(ValueError):
        text({}, "x")
    with pytest.raises(ValueError):
        read_object([], "test")
    with pytest.raises(ValueError):
        read_object({3: "x"}, "test")


def test_array_boundary_rejects_dtype_shape_and_nonfinite_values() -> None:
    array: FloatArray = np.array([1.0, 2.0])
    assert float_array(array) is array
    assert stored_array(array, np.float64, 1, "x") is array
    with pytest.raises(ValueError):
        float_array([1.0])
    with pytest.raises(ValueError):
        float_array(np.array([1], dtype=np.int32))
    with pytest.raises(ValueError):
        stored_array(array, np.float64, 2, "x")
    with pytest.raises(ValueError):
        stored_array(np.array([np.nan]), np.float64, 1, "x")
