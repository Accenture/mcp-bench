"""Force conversion functions."""

from typing import Literal

FORCE_UNIT = Literal[
    "dynes",
    "kilograms force",
    "kilonewtons",
    "kips",
    "meganewtons",
    "newtons",
    "pounds force",
    "tonnes force",
    "long tons force",
    "short tons force",
]


def convert_force_tool(
    value: float,
    from_unit: FORCE_UNIT,
    to_unit: FORCE_UNIT,
) -> float:
    """Convert force between units."""

    # Convert to newtons first
    to_newtons = {
        "dynes": 1e-05,
        "kilograms force": 9.80665,
        "kilonewtons": 1_000.0,
        "kips": 4_448.222,
        "meganewtons": 1_000_000.0,
        "newtons": 1.0,
        "pounds force": 4.44822161526,
        "tonnes force": 9_806.65,
        "long tons force": 9_964.01641818352,
        "short tons force": 8_896.443230521,
    }

    newtons = value * to_newtons[from_unit]
    return newtons / to_newtons[to_unit]
