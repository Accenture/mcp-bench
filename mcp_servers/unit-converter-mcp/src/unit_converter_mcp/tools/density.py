"""Density conversion functions."""

from typing import Literal

DENSITY_UNIT = Literal[
    "grains per gallon (UK)",
    "grains per gallon (US)",
    "grains per gallon",
    "grams per cubic centimeter",
    "grams per liter",
    "kilograms per liter",
    "kilograms per cubic meter",
    "milligrams per liter",
    "ounces per gallon (UK)",
    "ounces per gallon (US)",
    "ounces per gallon",
    "pounds per cubic foot",
    "pounds per gallon (UK)",
    "pounds per gallon (US)",
    "pounds per gallon",
    "tonnes per cubic meter",
    "tons per cubic yard (UK)",
    "tons per cubic yard (US)",
    "tons per cubic yard",
]


def convert_density_tool(
    value: float,
    from_unit: DENSITY_UNIT,
    to_unit: DENSITY_UNIT,
) -> float:
    """Convert density between units."""

    # Convert to kilograms per liter first
    to_kilograms_per_liter = {
        # grain‑based hardness units
        "grains per gallon (UK)": 1.4253948e-05,
        "grains per gallon (US)": 1.7118012e-05,
        "grains per gallon": 1.7118012e-05,  # Default to US grains per gallon
        # metric staples
        "grams per cubic centimeter": 1.0,
        "grams per liter": 0.001,
        "kilograms per liter": 1.0,
        "kilograms per cubic meter": 0.001,
        "milligrams per liter": 1e-06,
        # fluid‑ounce units
        "ounces per gallon (UK)": 0.006236023,
        "ounces per gallon (US)": 0.007489152,
        "ounces per gallon": 0.007489152,  # Default to US ounces per gallon
        # pound‑based units
        "pounds per cubic foot": 0.016018463,
        "pounds per gallon (UK)": 0.099776373,
        "pounds per gallon (US)": 0.119826427,
        "pounds per gallon": 0.119826427,  # Default to US pounds per gallon
        # tonne/ton bulk‑density units
        "tonnes per cubic meter": 1.0,
        "tons per cubic yard (UK)": 1.328939184,
        "tons per cubic yard (US)": 1.186552843,
        "tons per cubic yard": 1.186552843,  # Default to US tons per cubic yard
    }

    kilograms_per_liter = value * to_kilograms_per_liter[from_unit]
    return kilograms_per_liter / to_kilograms_per_liter[to_unit]
