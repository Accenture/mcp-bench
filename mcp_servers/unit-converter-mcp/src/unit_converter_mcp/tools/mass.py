"""Mass conversion functions."""

from typing import Literal

MASS_UNIT = Literal[
    "carat",
    "decagram",
    "hectogram",
    "gram",
    "milligram",
    "microgram",
    "nanogram",
    "picogram",
    "femtogram",
    "grain",
    "ounce",
    "troy ounce",
    "pound",
    "stone",
    "short ton (US)",
    "long ton (UK)",
    "tonne",
    "kilotonne",
    "megatonne",
    "kilogram",
]


def convert_mass_tool(
    value: float,
    from_unit: MASS_UNIT,
    to_unit: MASS_UNIT,
) -> float:
    """Convert mass between units."""

    # Convert to kilograms first
    to_kilograms = {
        "carat": 0.0002,
        "decagram": 0.01,
        "hectogram": 0.1,
        "gram": 0.001,
        "milligram": 1e-6,
        "microgram": 1e-9,
        "nanogram": 1e-12,
        "picogram": 1e-15,
        "femtogram": 1e-18,
        "grain": 6.479891e-05,
        "ounce": 0.028349523125,
        "troy ounce": 0.0311034768,
        "pound": 0.45359237,
        "stone": 6.35029318,
        "short ton (US)": 907.18474,
        "long ton (UK)": 1_016.0469088,
        "tonne": 1_000.0,
        "kilotonne": 1_000_000.0,
        "megatonne": 1_000_000_000.0,
        "kilogram": 1.0,
    }

    kg = value * to_kilograms[from_unit]
    return kg / to_kilograms[to_unit]
