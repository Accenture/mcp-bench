"""Temperature conversion functions."""

from collections.abc import Callable
from typing import Literal

from ..utils import Validator

TEMPERATURE_UNIT = Literal["celsius", "fahrenheit", "kelvin"]

validator = Validator("temperature")


def _fahrenheit_to_celsius(value: float) -> float:
    """Convert Fahrenheit to Celsius."""
    return (value - 32) * 5 / 9


def _celsius_to_fahrenheit(value: float) -> float:
    """Convert Celsius to Fahrenheit."""
    return value * 9 / 5 + 32


def _kelvin_to_celsius(value: float) -> float:
    """Convert Kelvin to Celsius."""
    validator.validate_positive_number(value)
    return value - 273.15


def _celsius_to_kelvin(value: float) -> float:
    """Convert Celsius to Kelvin."""
    return value + 273.15


def convert_temperature_tool(
    value: float,
    from_unit: TEMPERATURE_UNIT,
    to_unit: TEMPERATURE_UNIT,
) -> float:
    """Convert temperature between units."""

    # Dictionary mapping units to their conversion functions to Celsius
    to_celsius: dict[TEMPERATURE_UNIT, Callable[[float], float]] = {
        "fahrenheit": _fahrenheit_to_celsius,
        "kelvin": _kelvin_to_celsius,
        "celsius": lambda x: x,
    }

    # Dictionary mapping units to their conversion functions from Celsius
    from_celsius: dict[TEMPERATURE_UNIT, Callable[[float], float]] = {
        "fahrenheit": _celsius_to_fahrenheit,
        "kelvin": _celsius_to_kelvin,
        "celsius": lambda x: x,
    }

    # Convert to Celsius first
    celsius = to_celsius[from_unit](value)

    # Convert from Celsius to target unit
    return from_celsius[to_unit](celsius)
