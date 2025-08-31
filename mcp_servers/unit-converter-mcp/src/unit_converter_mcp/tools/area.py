"""Area conversion functions."""

from typing import Literal

AREA_UNIT = Literal[
    "acre",
    "are",
    "hectare",
    "square centimeter",
    "square foot",
    "square inch",
    "square kilometer",
    "square meter",
    "square mile",
    "square millimeter",
    "square yard",
]


def convert_area_tool(
    value: float,
    from_unit: AREA_UNIT,
    to_unit: AREA_UNIT,
) -> float:
    """Convert area between units."""

    # Convert to square meters first
    to_square_meters = {
        "acre": 4046.8564224,
        "are": 100.0,
        "hectare": 10_000.0,
        "square centimeter": 0.0001,
        "square foot": 0.09290304,
        "square inch": 0.00064516,
        "square kilometer": 1_000_000.0,
        "square meter": 1.0,
        "square mile": 2_589_988.110336,
        "square millimeter": 1e-6,
        "square yard": 0.83612736,
    }

    square_meters = value * to_square_meters[from_unit]
    return square_meters / to_square_meters[to_unit]
