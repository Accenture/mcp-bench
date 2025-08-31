"""Speed conversion functions."""

from typing import Literal

SPEED_UNIT = Literal[
    "centimeters per minute",
    "centimeters per second",
    "feet per hour",
    "feet per minute",
    "feet per second",
    "inches per minute",
    "inches per second",
    "kilometers per hour",
    "kilometers per second",
    "knots",
    "Mach (ISA sea level)",
    "speed of sound",
    "meters per hour",
    "meters per minute",
    "meters per second",
    "miles per hour",
    "miles per minute",
    "miles per second",
    "yards per hour",
    "yards per minute",
    "yards per second",
    "speed of light",
]


def convert_speed_tool(
    value: float,
    from_unit: SPEED_UNIT,
    to_unit: SPEED_UNIT,
) -> float:
    """Convert speed between units."""

    # Convert to meters per second first
    to_meters_per_second = {
        "centimeters per minute": 0.000166666667,
        "centimeters per second": 0.01,
        "feet per hour": 8.4666836e-05,
        "feet per minute": 0.00508,
        "feet per second": 0.3048,
        "inches per minute": 0.00042333418,
        "inches per second": 0.0254,
        "kilometers per hour": 0.277777777778,
        "kilometers per second": 1000.0,
        "knots": 0.514444444444,
        "Mach (ISA sea level)": 340.2933,  # 15 °C, 101.3 kPa
        "speed of sound": 343.0,  # dry air, ~1 atm, room temp
        "meters per hour": 0.000277777778,
        "meters per minute": 0.016666666667,
        "meters per second": 1.0,
        "miles per hour": 0.44704,
        "miles per minute": 26.8224,
        "miles per second": 1609.344,
        "yards per hour": 0.000254000508,
        "yards per minute": 0.01524,
        "yards per second": 0.9144,
        "speed of light": 299_792_458.0,  # exact physical constant
    }

    meters_per_second = value * to_meters_per_second[from_unit]
    return meters_per_second / to_meters_per_second[to_unit]
