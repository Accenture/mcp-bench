"""Length conversion functions."""

from typing import Literal

LENGTH_UNIT = Literal[
    "angstrom",
    "astronomical unit",
    "cable",
    "centimeter",
    "chain (surveyors)",
    "decimeter",
    "em (pica)",
    "fathom",
    "foot",
    "foot (US survey)",
    "furlong",
    "hand",
    "hectometer",
    "inch",
    "kilometer",
    "light year",
    "meter",
    "micrometer",
    "mil",
    "mile",
    "nautical mile",
    "nautical mile (UK)",
    "millimeter",
    "nanometer",
    "parsec",
    "picometer",
    "Scandinavian mile",
    "thou",
    "yard",
]


def convert_length_tool(
    value: float,
    from_unit: LENGTH_UNIT,
    to_unit: LENGTH_UNIT,
) -> float:
    """Convert length between units."""

    # Convert to meters first
    to_meters = {
        "angstrom": 1e-10,
        "astronomical unit": 149_598_550_000.0,
        "cable": 182.88,
        "centimeter": 0.01,
        "chain (surveyors)": 20.11684023368,
        "decimeter": 0.1,
        "em (pica)": 0.0042333,
        "fathom": 1.8288,
        "foot": 0.3048,
        "foot (US survey)": 0.304800609601,
        "furlong": 201.168,
        "hand": 0.1016,
        "hectometer": 100.0,
        "inch": 0.0254,
        "kilometer": 1000.0,
        "light year": 9_460_528_405_000_000.0,
        "meter": 1.0,
        "micrometer": 1e-06,
        "mil": 2.54e-05,
        "mile": 1609.344,
        "nautical mile": 1852.0,
        "nautical mile (UK)": 1853.184,
        "millimeter": 0.001,
        "nanometer": 1e-09,
        "parsec": 30_856_776_000_000_000.0,
        "picometer": 1e-12,
        "Scandinavian mile": 10_000.0,
        "thou": 2.54e-05,
        "yard": 0.9144,
    }

    meters = value * to_meters[from_unit]
    return meters / to_meters[to_unit]
