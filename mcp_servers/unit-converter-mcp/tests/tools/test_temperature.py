"""Tests for temperature conversion functions."""

from unit_converter_mcp.tools.temperature import convert_temperature_tool


class TestTemperatureConversion:
    """Test temperature conversion functions."""

    def test_celsius_to_fahrenheit(self):
        """Test Celsius to Fahrenheit conversion."""
        result = convert_temperature_tool(0, "celsius", "fahrenheit")
        assert result == 32.0

    def test_fahrenheit_to_celsius(self):
        """Test Fahrenheit to Celsius conversion."""
        result = convert_temperature_tool(32, "fahrenheit", "celsius")
        assert result == 0.0

    def test_celsius_to_kelvin(self):
        """Test Celsius to Kelvin conversion."""
        result = convert_temperature_tool(0, "celsius", "kelvin")
        assert result == 273.15

    def test_kelvin_to_celsius(self):
        """Test Kelvin to Celsius conversion."""
        result = convert_temperature_tool(273.15, "kelvin", "celsius")
        assert result == 0.0
