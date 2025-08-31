"""Pressure conversion functions."""

from typing import Literal

PRESSURE_UNIT = Literal[
    "pascal",
    "hectopascal",
    "kilopascal",
    "megapascal",
    "bar",
    "atmosphere",
    "centimeters of water",
    "inches of water",
    "feet of water",
    "meters of water",
    "millimeters of mercury",
    "inches of mercury",
    "kilogram force per square centimeter",
    "newtons per square centimeter",
    "newtons per square millimeter",
    "psi",
    "psf",
]


def convert_pressure_tool(
    value: float,
    from_unit: PRESSURE_UNIT,
    to_unit: PRESSURE_UNIT,
) -> float:
    """Convert pressure between units."""

    # Convert to pascals first
    to_pascals = {
        # SI units and simple multiples
        "pascal": 1.0,
        "hectopascal": 100.0,
        "kilopascal": 1_000.0,
        "megapascal": 1_000_000.0,
        # Reference pressures
        "bar": 100_000.0,  # common in industry & diving
        "atmosphere": 101_325.0,
        # Water‑column units
        "centimeters of water": 98.0665,
        "inches of water": 249.08891,
        "feet of water": 2_989.06692,
        "meters of water": 9_806.65,
        # Mercury‑column units
        "millimeters of mercury": 133.322,
        "inches of mercury": 3_386.388,
        # Force per area
        "kilogram force per square centimeter": 98_066.5,
        "newtons per square centimeter": 10_000.0,
        "newtons per square millimeter": 1_000_000.0,
        # Widely‑recognised US customary symbols
        "psi": 6_894.757293168362,
        "psf": 47.880258980336,
    }

    pascals = value * to_pascals[from_unit]
    return pascals / to_pascals[to_unit]
