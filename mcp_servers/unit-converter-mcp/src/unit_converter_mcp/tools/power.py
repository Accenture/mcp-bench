"""Power conversion functions."""

from typing import Literal

POWER_UNIT = Literal[
    "Btu per hour",
    "foot pound‑force per second",
    "ton of refrigeration",
    "calorie per hour",
    "kilocalorie per hour",
    "horsepower",
    "horsepower (metric)",
    "kilogram‑force meter per second",
    "watt",
    "kilowatt",
    "megawatt",
    "gigawatt",
    "terawatt",
    "petawatt",
]


def convert_power_tool(
    value: float,
    from_unit: POWER_UNIT,
    to_unit: POWER_UNIT,
) -> float:
    """Convert power between units."""

    # Convert to watts first
    to_watts = {
        # Anglo‑American & HVAC
        "Btu per hour": 0.2930711,
        "foot pound‑force per second": 1.35582,
        "ton of refrigeration": 3_516.853,
        # Nutrition / chemistry
        "calorie per hour": 0.001162222222,
        "kilocalorie per hour": 1.162222222222,
        # Mechanical power
        "horsepower": 745.69987158227,  # international / mechanical
        "horsepower (metric)": 735.4988,
        "kilogram‑force meter per second": 9.80665,
        # SI and metric multiples
        "watt": 1.0,
        "kilowatt": 1_000.0,
        "megawatt": 1_000_000.0,
        "gigawatt": 1_000_000_000.0,
        "terawatt": 1_000_000_000_000.0,
        "petawatt": 1_000_000_000_000_000.0,
    }

    watts = value * to_watts[from_unit]
    return watts / to_watts[to_unit]
