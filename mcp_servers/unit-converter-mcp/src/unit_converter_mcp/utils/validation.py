"""Common validation functions for unit conversion."""

from typing import Any


class Validator:
    """Validator class for unit conversion operations."""

    def __init__(self, name: str):
        """Initialize validator with a name for error messages.

        Args:
            name: The name to use in error messages (e.g., "temperature", "length")
        """
        self.name = name

    def validate_positive_number(self, value: Any) -> None:
        """Validate that a value is a positive number."""
        if not isinstance(value, int | float):
            raise TypeError(f"{self.name} must be a number, got {type(value).__name__}")
        if value < 0:
            raise ValueError(f"{self.name} must be non-negative, got {value}")

    def validate_unit(self, unit: str, valid_units: tuple[str]) -> None:
        """Validate that a unit is in the list of valid units."""
        if unit not in valid_units:
            raise ValueError(
                f"Invalid {self.name} unit '{unit}'. Valid units: {', '.join(valid_units)}"
            )
