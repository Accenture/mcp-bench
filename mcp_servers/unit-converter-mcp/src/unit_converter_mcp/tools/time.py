"""Time conversion functions."""

from typing import Literal

TIME_UNIT = Literal[
    "picoseconds",
    "femtoseconds",
    "nanoseconds",
    "microseconds",
    "milliseconds",
    "seconds",
    "minutes",
    "hours",
    "days",
    "weeks",
    "fortnights",
    "months",
    "quarters",
    "synodic months",
    "years",
    "decades",
    "centuries",
    "millennia",
]


def convert_time_tool(
    value: float,
    from_unit: TIME_UNIT,
    to_unit: TIME_UNIT,
) -> float:
    """Convert time between units."""

    # Convert to seconds first
    to_seconds = {
        # sub‑second
        "picoseconds": 1e-12,
        "femtoseconds": 1e-15,
        "nanoseconds": 1e-09,
        "microseconds": 1e-06,
        "milliseconds": 0.001,
        # second and above
        "seconds": 1.0,
        "minutes": 60.0,
        "hours": 3_600.0,
        "days": 86_400.0,
        "weeks": 604_800.0,
        "fortnights": 1_209_600.0,
        # calendar averages
        "months": 2_628_000.0,  # 1/12 of avg Gregorian year
        "quarters": 7_884_000.0,  # 3 × avg month
        # optional lunar unit (keep or drop as you wish)
        "synodic months": 2_551_442.8896,  # mean lunation
        # years & multiples — now ONE canonical value
        "years": 31_556_952.0,  # average Gregorian (365.2425 d)
        "decades": 315_569_520.0,  # 10 × year
        "centuries": 3_155_695_200.0,  # 100 × year
        "millennia": 31_556_952_000.0,  # 1 000 × year
    }

    seconds = value * to_seconds[from_unit]
    return seconds / to_seconds[to_unit]
