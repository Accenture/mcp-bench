"""Main MCP server using FastMCP."""

from typing import Annotated, Literal, get_args

from fastmcp import FastMCP
from pydantic import Field

from .tools import (
    ANGLE_UNIT,
    AREA_UNIT,
    COMPUTER_DATA_UNIT,
    DENSITY_UNIT,
    ENERGY_UNIT,
    FORCE_UNIT,
    LENGTH_UNIT,
    MASS_UNIT,
    POWER_UNIT,
    PRESSURE_UNIT,
    SPEED_UNIT,
    TEMPERATURE_UNIT,
    TIME_UNIT,
    VOLUME_UNIT,
    convert_angle_tool,
    convert_area_tool,
    convert_batch_tool,
    convert_computer_data_tool,
    convert_density_tool,
    convert_energy_tool,
    convert_force_tool,
    convert_length_tool,
    convert_mass_tool,
    convert_power_tool,
    convert_pressure_tool,
    convert_speed_tool,
    convert_temperature_tool,
    convert_time_tool,
    convert_volume_tool,
)

# Unit type literal for list_supported_units function
UNIT_TYPE = Literal[
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

# Create the FastMCP server instance
app: FastMCP = FastMCP("Unit Converter MCP Server")


@app.tool()
def convert_temperature(
    value: Annotated[float, Field(description="Temperature value to convert")],
    from_unit: Annotated[TEMPERATURE_UNIT, Field(description="Source unit")],
    to_unit: Annotated[TEMPERATURE_UNIT, Field(description="Target unit")],
) -> dict:
    """Convert temperature between units."""
    converted_value = convert_temperature_tool(value, from_unit, to_unit)
    return {
        "original_value": value,
        "original_unit": from_unit,
        "converted_value": converted_value,
        "converted_unit": to_unit,
        "conversion_type": "temperature",
    }


@app.tool()
def convert_angle(
    value: Annotated[float, Field(description="Angle value to convert")],
    from_unit: Annotated[ANGLE_UNIT, Field(description="Source unit")],
    to_unit: Annotated[ANGLE_UNIT, Field(description="Target unit")],
) -> dict:
    """Convert angle between units."""
    converted_value = convert_angle_tool(value, from_unit, to_unit)
    return {
        "original_value": value,
        "original_unit": from_unit,
        "converted_value": converted_value,
        "converted_unit": to_unit,
        "conversion_type": "angle",
    }


@app.tool()
def convert_length(
    value: Annotated[float, Field(description="Length value to convert")],
    from_unit: Annotated[LENGTH_UNIT, Field(description="Source unit")],
    to_unit: Annotated[LENGTH_UNIT, Field(description="Target unit")],
) -> dict:
    """Convert length between units."""
    converted_value = convert_length_tool(value, from_unit, to_unit)
    return {
        "original_value": value,
        "original_unit": from_unit,
        "converted_value": converted_value,
        "converted_unit": to_unit,
        "conversion_type": "length",
    }


@app.tool()
def convert_energy(
    value: Annotated[float, Field(description="Energy value to convert")],
    from_unit: Annotated[ENERGY_UNIT, Field(description="Source unit")],
    to_unit: Annotated[ENERGY_UNIT, Field(description="Target unit")],
) -> dict:
    """Convert energy between units."""
    converted_value = convert_energy_tool(value, from_unit, to_unit)
    return {
        "original_value": value,
        "original_unit": from_unit,
        "converted_value": converted_value,
        "converted_unit": to_unit,
        "conversion_type": "energy",
    }


@app.tool()
def convert_force(
    value: Annotated[float, Field(description="Force value to convert")],
    from_unit: Annotated[FORCE_UNIT, Field(description="Source unit")],
    to_unit: Annotated[FORCE_UNIT, Field(description="Target unit")],
) -> dict:
    """Convert force between units."""
    converted_value = convert_force_tool(value, from_unit, to_unit)
    return {
        "original_value": value,
        "original_unit": from_unit,
        "converted_value": converted_value,
        "converted_unit": to_unit,
        "conversion_type": "force",
    }


@app.tool()
def convert_pressure(
    value: Annotated[float, Field(description="Pressure value to convert")],
    from_unit: Annotated[PRESSURE_UNIT, Field(description="Source unit")],
    to_unit: Annotated[PRESSURE_UNIT, Field(description="Target unit")],
) -> dict:
    """Convert pressure between units."""
    converted_value = convert_pressure_tool(value, from_unit, to_unit)
    return {
        "original_value": value,
        "original_unit": from_unit,
        "converted_value": converted_value,
        "converted_unit": to_unit,
        "conversion_type": "pressure",
    }


@app.tool()
def convert_power(
    value: Annotated[float, Field(description="Power value to convert")],
    from_unit: Annotated[POWER_UNIT, Field(description="Source unit")],
    to_unit: Annotated[POWER_UNIT, Field(description="Target unit")],
) -> dict:
    """Convert power between units."""
    converted_value = convert_power_tool(value, from_unit, to_unit)
    return {
        "original_value": value,
        "original_unit": from_unit,
        "converted_value": converted_value,
        "converted_unit": to_unit,
        "conversion_type": "power",
    }


@app.tool()
def convert_speed(
    value: Annotated[float, Field(description="Speed value to convert")],
    from_unit: Annotated[SPEED_UNIT, Field(description="Source unit")],
    to_unit: Annotated[SPEED_UNIT, Field(description="Target unit")],
) -> dict:
    """Convert speed between units."""
    converted_value = convert_speed_tool(value, from_unit, to_unit)
    return {
        "original_value": value,
        "original_unit": from_unit,
        "converted_value": converted_value,
        "converted_unit": to_unit,
        "conversion_type": "speed",
    }


@app.tool()
def convert_area(
    value: Annotated[float, Field(description="Area value to convert")],
    from_unit: Annotated[AREA_UNIT, Field(description="Source unit")],
    to_unit: Annotated[AREA_UNIT, Field(description="Target unit")],
) -> dict:
    """Convert area between units."""
    converted_value = convert_area_tool(value, from_unit, to_unit)
    return {
        "original_value": value,
        "original_unit": from_unit,
        "converted_value": converted_value,
        "converted_unit": to_unit,
        "conversion_type": "area",
    }


@app.tool()
def convert_mass(
    value: Annotated[float, Field(description="Weight value to convert")],
    from_unit: Annotated[MASS_UNIT, Field(description="Source unit")],
    to_unit: Annotated[MASS_UNIT, Field(description="Target unit")],
) -> dict:
    """Convert weight between units."""
    converted_value = convert_mass_tool(value, from_unit, to_unit)
    return {
        "original_value": value,
        "original_unit": from_unit,
        "converted_value": converted_value,
        "converted_unit": to_unit,
        "conversion_type": "mass",
    }


@app.tool()
def convert_volume(
    value: Annotated[float, Field(description="Volume value to convert")],
    from_unit: Annotated[VOLUME_UNIT, Field(description="Source unit")],
    to_unit: Annotated[VOLUME_UNIT, Field(description="Target unit")],
) -> dict:
    """Convert volume between units."""
    converted_value = convert_volume_tool(value, from_unit, to_unit)
    return {
        "original_value": value,
        "original_unit": from_unit,
        "converted_value": converted_value,
        "converted_unit": to_unit,
        "conversion_type": "volume",
    }


@app.tool()
def convert_computer_data(
    value: Annotated[float, Field(description="Computer storage value to convert")],
    from_unit: Annotated[COMPUTER_DATA_UNIT, Field(description="Source unit")],
    to_unit: Annotated[COMPUTER_DATA_UNIT, Field(description="Target unit")],
) -> dict:
    """Convert computer storage between units."""
    converted_value = convert_computer_data_tool(value, from_unit, to_unit)
    return {
        "original_value": value,
        "original_unit": from_unit,
        "converted_value": converted_value,
        "converted_unit": to_unit,
        "conversion_type": "computer_data",
    }


@app.tool()
def convert_density(
    value: Annotated[float, Field(description="Density value to convert")],
    from_unit: Annotated[DENSITY_UNIT, Field(description="Source unit")],
    to_unit: Annotated[DENSITY_UNIT, Field(description="Target unit")],
) -> dict:
    """Convert density between units."""
    converted_value = convert_density_tool(value, from_unit, to_unit)
    return {
        "original_value": value,
        "original_unit": from_unit,
        "converted_value": converted_value,
        "converted_unit": to_unit,
        "conversion_type": "density",
    }


@app.tool()
def convert_time(
    value: Annotated[float, Field(description="Time value to convert")],
    from_unit: Annotated[TIME_UNIT, Field(description="Source unit")],
    to_unit: Annotated[TIME_UNIT, Field(description="Target unit")],
) -> dict:
    """Convert time between units."""
    converted_value = convert_time_tool(value, from_unit, to_unit)
    return {
        "original_value": value,
        "original_unit": from_unit,
        "converted_value": converted_value,
        "converted_unit": to_unit,
        "conversion_type": "time",
    }


@app.tool()
def convert_batch(
    requests: Annotated[
        list[dict],
        Field(
            description="List of conversion requests. Each request should contain: value (float), from_unit (str), to_unit (str), conversion_type (str), and optionally request_id (str)"
        ),
    ],
) -> dict:
    """Perform multiple unit conversions in a single batch request.

    Each request in the batch should contain:
    - value: The numeric value to convert
    - from_unit: Source unit for conversion
    - to_unit: Target unit for conversion
    - conversion_type: Type of conversion (temperature, length, mass, etc.)
    - request_id: Optional identifier for tracking individual requests

    Returns a structured response with individual results for each conversion,
    including success/failure status and either converted values or error messages.
    """
    results = convert_batch_tool(requests)

    # Count successful and failed conversions
    successful = sum(1 for result in results if result["success"])
    failed = len(results) - successful

    return {
        "batch_results": results,
        "summary": {
            "total_requests": len(requests),
            "successful_conversions": successful,
            "failed_conversions": failed,
        },
    }


@app.tool()
def list_supported_units(
    unit_type: Annotated[
        UNIT_TYPE | None,
        Field(
            description="Specific unit type to get supported units for. If not specified, returns all supported units.",
            default=None,
        ),
    ],
) -> dict:
    """List all supported units for each conversion type or for a specific type."""
    all_units = {
        "angle": get_args(ANGLE_UNIT),
        "area": get_args(AREA_UNIT),
        "computer_data": get_args(COMPUTER_DATA_UNIT),
        "density": get_args(DENSITY_UNIT),
        "energy": get_args(ENERGY_UNIT),
        "force": get_args(FORCE_UNIT),
        "temperature": get_args(TEMPERATURE_UNIT),
        "length": get_args(LENGTH_UNIT),
        "mass": get_args(MASS_UNIT),
        "power": get_args(POWER_UNIT),
        "pressure": get_args(PRESSURE_UNIT),
        "speed": get_args(SPEED_UNIT),
        "time": get_args(TIME_UNIT),
        "volume": get_args(VOLUME_UNIT),
    }

    if unit_type is not None:
        return {unit_type: all_units[unit_type]}

    return all_units


def main() -> None:
    """Main entry point for the MCP server."""
    app.run()


if __name__ == "__main__":
    main()
