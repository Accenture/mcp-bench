"""Angle conversion functions."""

import math
from collections.abc import Callable
from typing import Literal

from ..utils import Validator

ANGLE_UNIT = Literal["degrees", "radians", "arcmin", "arcsec", "turns", "gons"]

validator = Validator("angle")


def _radians_to_degrees(value: float) -> float:
    """Convert radians to degrees."""
    return value * 180.0 / math.pi


def _degrees_to_radians(value: float) -> float:
    """Convert degrees to radians."""
    return value * math.pi / 180.0


def _arcmin_to_degrees(value: float) -> float:
    """Convert arc-minutes to degrees."""
    return value / 60.0


def _degrees_to_arcmin(value: float) -> float:
    """Convert degrees to arc-minutes."""
    return value * 60.0


def _arcsec_to_degrees(value: float) -> float:
    """Convert arc-seconds to degrees."""
    return value / 3_600.0


def _degrees_to_arcsec(value: float) -> float:
    """Convert degrees to arc-seconds."""
    return value * 3_600.0


def _turns_to_degrees(value: float) -> float:
    """Convert turns to degrees."""
    return value * 360.0


def _degrees_to_turns(value: float) -> float:
    """Convert degrees to turns."""
    return value / 360.0


def _gons_to_degrees(value: float) -> float:
    """Convert gons to degrees."""
    return value * (9.0 / 10.0)


def _degrees_to_gons(value: float) -> float:
    """Convert degrees to gons."""
    return value * (10.0 / 9.0)


def convert_angle_tool(
    value: float,
    from_unit: ANGLE_UNIT,
    to_unit: ANGLE_UNIT,
) -> float:
    """Convert angle between units."""

    # Dictionary mapping units to their conversion functions to degrees
    to_degrees: dict[ANGLE_UNIT, Callable[[float], float]] = {
        "radians": _radians_to_degrees,
        "arcmin": _arcmin_to_degrees,
        "arcsec": _arcsec_to_degrees,
        "turns": _turns_to_degrees,
        "gons": _gons_to_degrees,
        "degrees": lambda x: x,
    }

    # Dictionary mapping units to their conversion functions from degrees
    from_degrees: dict[ANGLE_UNIT, Callable[[float], float]] = {
        "radians": _degrees_to_radians,
        "arcmin": _degrees_to_arcmin,
        "arcsec": _degrees_to_arcsec,
        "turns": _degrees_to_turns,
        "gons": _degrees_to_gons,
        "degrees": lambda x: x,
    }

    # Convert to degrees first
    degrees = to_degrees[from_unit](value)

    # Convert from degrees to target unit
    return from_degrees[to_unit](degrees)
