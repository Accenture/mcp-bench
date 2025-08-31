"""Volume conversion functions."""

from typing import Literal

VOLUME_UNIT = Literal[
    "acre foot",
    "barrel (oil)",
    "bushel (UK)",
    "bushel (US)",
    "bushel",
    "centiliter",
    "cubic centimeter",
    "cubic decimeter",
    "cubic foot",
    "cubic inch",
    "cubic kilometer",
    "cubic meter",
    "cubic mile",
    "cubic millimeter",
    "cubic yard",
    "cup",
    "deciliter",
    "fluid ounce (imperial)",
    "fluid ounce (US)",
    "fluid ounce",
    "gallon (imperial)",
    "gallon (US)",
    "gallon",
    "kiloliter",
    "liter",
    "milliliter",
    "microliter",
    "nanoliter",
    "picoliter",
    "pint (imperial)",
    "pint (US)",
    "pint",
    "quart (imperial)",
    "quart (US)",
    "quart",
    "tablespoon",
    "teaspoon",
]


def convert_volume_tool(
    value: float,
    from_unit: VOLUME_UNIT,
    to_unit: VOLUME_UNIT,
) -> float:
    """Convert volume between units."""

    # Convert to liters first
    to_liters = {
        "acre foot": 1233481.83754752,
        "barrel (oil)": 158.987294928,
        "bushel (UK)": 36.36872,
        "bushel (US)": 35.23907016688,
        "bushel": 35.23907016688,  # Default to US bushel
        "centiliter": 0.01,
        "cubic centimeter": 0.001,
        "cubic decimeter": 1.0,
        "cubic foot": 28.316846592,
        "cubic inch": 0.016387064,
        "cubic kilometer": 1_000_000_000_000.0,
        "cubic meter": 1000.0,
        "cubic mile": 4_168_181_825_000.0,
        "cubic millimeter": 1e-06,
        "cubic yard": 764.554857984,
        "cup": 0.2365882365,
        "deciliter": 0.1,
        "fluid ounce (imperial)": 0.0284130625,
        "fluid ounce (US)": 0.029573529562,
        "fluid ounce": 0.029573529562,  # Default to US fluid ounce
        "gallon (imperial)": 4.54609,
        "gallon (US)": 3.785411784,
        "gallon": 3.785411784,  # Default to US gallon
        "kiloliter": 1000.0,
        "liter": 1.0,
        "milliliter": 0.001,
        "microliter": 1e-06,
        "nanoliter": 1e-09,
        "picoliter": 1e-12,
        "pint (imperial)": 0.56826125,
        "pint (US)": 0.473176473,
        "pint": 0.473176473,  # Default to US pint
        "quart (imperial)": 1.1365225,
        "quart (US)": 0.946352946,
        "quart": 0.946352946,  # Default to US quart
        "tablespoon": 0.014786764781,
        "teaspoon": 0.004928921594,
    }

    liters = value * to_liters[from_unit]
    return liters / to_liters[to_unit]
