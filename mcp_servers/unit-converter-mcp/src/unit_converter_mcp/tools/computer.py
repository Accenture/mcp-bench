"""Computer storage conversion functions."""

from typing import Literal

COMPUTER_DATA_UNIT = Literal[
    "bits",
    "bytes",
    "kilobytes",
    "megabytes",
    "gigabytes",
    "terabytes",
    "petabytes",
    "exabytes",
]


def convert_computer_data_tool(
    value: float,
    from_unit: COMPUTER_DATA_UNIT,
    to_unit: COMPUTER_DATA_UNIT,
) -> float:
    """Convert computer storage between units."""

    # Convert to megabytes first
    to_megabytes = {
        "bits": 1.19209e-07,
        "bytes": 9.53674e-07,
        "kilobytes": 0.0009765625,
        "megabytes": 1.0,
        "gigabytes": 1024.0,
        "terabytes": 1048576.0,
        "petabytes": 1073741824.0,
        "exabytes": 1099511627776.0,
    }

    megabytes = value * to_megabytes[from_unit]
    return megabytes / to_megabytes[to_unit]
