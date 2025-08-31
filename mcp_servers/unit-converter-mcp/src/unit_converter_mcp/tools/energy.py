"""Energy conversion functions."""

from typing import Literal

ENERGY_UNIT = Literal[
    "joule",
    "kilojoule",
    "megajoule",
    "gigajoule",
    "terajoule",
    "petajoule",
    "exajoule",
    "watt hour",
    "kilowatt hour",
    "megawatt hour",
    "gigawatt hour",
    "terawatt hour",
    "Btu",
    "calorie",
    "kilocalorie",
    "therm",
    "foot‑pound force",
    "inch‑pound force",
    "erg",
    "electron volt",
]


def convert_energy_tool(
    value: float,
    from_unit: ENERGY_UNIT,
    to_unit: ENERGY_UNIT,
) -> float:
    """Convert energy between units."""

    # Convert to joules first
    to_joules = {
        # SI and metric prefixes
        "joule": 1.0,
        "kilojoule": 1_000.0,
        "megajoule": 1_000_000.0,
        "gigajoule": 1_000_000_000.0,
        "terajoule": 1_000_000_000_000.0,
        "petajoule": 1_000_000_000_000_000.0,
        "exajoule": 1_000_000_000_000_000_000.0,
        # Electrical‑energy units
        "watt hour": 3_600.0,
        "kilowatt hour": 3_600_000.0,
        "megawatt hour": 3_600_000_000.0,
        "gigawatt hour": 3_600_000_000_000.0,
        "terawatt hour": 3_600_000_000_000_000.0,
        # Heat / nutrition
        "Btu": 1_054.35,
        "calorie": 4.184,
        "kilocalorie": 4_184.0,
        "therm": 105_505_585.257348,
        # Mechanical & particle‑physics units
        "foot‑pound force": 1.355_817_948_331,
        "inch‑pound force": 0.112_984_829_028,
        "erg": 1e-7,
        "electron volt": 1.602_176_634e-19,
    }

    joules = value * to_joules[from_unit]
    return joules / to_joules[to_unit]
