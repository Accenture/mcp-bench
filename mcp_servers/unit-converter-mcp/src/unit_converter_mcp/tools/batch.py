"""Batch conversion functionality for processing multiple unit conversions in one request."""

from collections.abc import Callable
from typing import Any, Literal

from .angle import ANGLE_UNIT, convert_angle_tool
from .area import AREA_UNIT, convert_area_tool
from .computer import COMPUTER_DATA_UNIT, convert_computer_data_tool
from .density import DENSITY_UNIT, convert_density_tool
from .energy import ENERGY_UNIT, convert_energy_tool
from .force import FORCE_UNIT, convert_force_tool
from .length import LENGTH_UNIT, convert_length_tool
from .mass import MASS_UNIT, convert_mass_tool
from .power import POWER_UNIT, convert_power_tool
from .pressure import PRESSURE_UNIT, convert_pressure_tool
from .speed import SPEED_UNIT, convert_speed_tool
from .temperature import TEMPERATURE_UNIT, convert_temperature_tool
from .time import TIME_UNIT, convert_time_tool
from .volume import VOLUME_UNIT, convert_volume_tool

# Type definitions for batch conversion requests
CONVERSION_TYPE = Literal[
    "angle",
    "area",
    "computer_data",
    "density",
    "energy",
    "force",
    "length",
    "mass",
    "power",
    "pressure",
    "speed",
    "temperature",
    "time",
    "volume",
]

# Union type for all possible unit types
UNIT_TYPE = (
    ANGLE_UNIT
    | AREA_UNIT
    | COMPUTER_DATA_UNIT
    | DENSITY_UNIT
    | ENERGY_UNIT
    | FORCE_UNIT
    | LENGTH_UNIT
    | MASS_UNIT
    | POWER_UNIT
    | PRESSURE_UNIT
    | SPEED_UNIT
    | TEMPERATURE_UNIT
    | TIME_UNIT
    | VOLUME_UNIT
)


class BatchConversionRequest:
    """Represents a single conversion request within a batch."""

    def __init__(
        self,
        value: float,
        from_unit: str,
        to_unit: str,
        conversion_type: CONVERSION_TYPE,
        request_id: str | None = None,
    ):
        """Initialize a batch conversion request.

        Args:
            value: The numeric value to convert
            from_unit: Source unit for conversion
            to_unit: Target unit for conversion
            conversion_type: Type of conversion (temperature, length, etc.)
            request_id: Optional identifier for tracking individual requests
        """
        self.value = value
        self.from_unit = from_unit
        self.to_unit = to_unit
        self.conversion_type = conversion_type
        self.request_id = (
            request_id or f"{conversion_type}_{hash((value, from_unit, to_unit))}"
        )


class BatchConversionResult:
    """Represents the result of a single conversion within a batch."""

    def __init__(
        self,
        request_id: str,
        success: bool,
        original_value: float | None = None,
        original_unit: str | None = None,
        converted_value: float | None = None,
        converted_unit: str | None = None,
        conversion_type: str | None = None,
        error_message: str | None = None,
    ):
        """Initialize a batch conversion result.

        Args:
            request_id: Identifier matching the original request
            success: Whether the conversion succeeded
            original_value: Original value that was converted
            original_unit: Original unit
            converted_value: Result of conversion (if successful)
            converted_unit: Target unit (if successful)
            conversion_type: Type of conversion performed
            error_message: Error details (if failed)
        """
        self.request_id = request_id
        self.success = success
        self.original_value = original_value
        self.original_unit = original_unit
        self.converted_value = converted_value
        self.converted_unit = converted_unit
        self.conversion_type = conversion_type
        self.error_message = error_message

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary format matching individual tool responses."""
        result = {
            "request_id": self.request_id,
            "success": self.success,
        }

        if self.success:
            result.update(
                {
                    "original_value": self.original_value,
                    "original_unit": self.original_unit,
                    "converted_value": self.converted_value,
                    "converted_unit": self.converted_unit,
                    "conversion_type": self.conversion_type,
                }
            )
        else:
            result["error"] = self.error_message

        return result


# Mapping of conversion types to their respective conversion functions
CONVERSION_FUNCTIONS: dict[str, Callable[..., float]] = {
    "angle": convert_angle_tool,
    "area": convert_area_tool,
    "computer_data": convert_computer_data_tool,
    "density": convert_density_tool,
    "energy": convert_energy_tool,
    "force": convert_force_tool,
    "length": convert_length_tool,
    "mass": convert_mass_tool,
    "power": convert_power_tool,
    "pressure": convert_pressure_tool,
    "speed": convert_speed_tool,
    "temperature": convert_temperature_tool,
    "time": convert_time_tool,
    "volume": convert_volume_tool,
}


def convert_batch_tool(requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Perform batch unit conversions.

    Args:
        requests: List of conversion request dictionaries, each containing:
            - value: float - The numeric value to convert
            - from_unit: str - Source unit
            - to_unit: str - Target unit
            - conversion_type: str - Type of conversion
            - request_id: str (optional) - Identifier for tracking

    Returns:
        List of conversion result dictionaries with success/failure status
        and either converted values or error messages.
    """
    results: list[dict[str, Any]] = []

    for request_data in requests:
        try:
            # Validate required fields first
            value = request_data.get("value")
            from_unit = request_data.get("from_unit")
            to_unit = request_data.get("to_unit")
            conversion_type = request_data.get("conversion_type")
            request_id = request_data.get("request_id")

            if value is None:
                raise ValueError("Missing required field: value")
            if not from_unit:
                raise ValueError("Missing required field: from_unit")
            if not to_unit:
                raise ValueError("Missing required field: to_unit")
            if not conversion_type:
                raise ValueError("Missing required field: conversion_type")

            # Create request object with validated data
            request = BatchConversionRequest(
                value=float(value),
                from_unit=str(from_unit),
                to_unit=str(to_unit),
                conversion_type=conversion_type,
                request_id=request_id,
            )

            # Validate conversion type
            if request.conversion_type not in CONVERSION_FUNCTIONS:
                raise ValueError(
                    f"Unsupported conversion type: {request.conversion_type}"
                )

            # Perform the conversion
            conversion_func = CONVERSION_FUNCTIONS[request.conversion_type]
            converted_value = conversion_func(
                request.value, request.from_unit, request.to_unit
            )

            # Create successful result
            result = BatchConversionResult(
                request_id=request.request_id,
                success=True,
                original_value=request.value,
                original_unit=request.from_unit,
                converted_value=converted_value,
                converted_unit=request.to_unit,
                conversion_type=request.conversion_type,
            )

        except Exception as e:
            # Create error result
            request_id = request_data.get("request_id", f"error_{len(results)}")
            result = BatchConversionResult(
                request_id=request_id,
                success=False,
                error_message=str(e),
            )

        results.append(result.to_dict())

    return results
