"""Tests for pressure conversion functions."""

from unit_converter_mcp.tools.pressure import convert_pressure_tool


class TestPressureConversion:
    """Test pressure conversion functions."""

    def test_pascal_to_kilopascal(self):
        """Test pascal to kilopascal conversion."""
        result = convert_pressure_tool(1000, "pascal", "kilopascal")
        assert result == 1.0

    def test_bar_to_pascal(self):
        """Test bar to pascal conversion."""
        result = convert_pressure_tool(1, "bar", "pascal")
        assert result == 100_000.0

    def test_psi_to_pascal(self):
        """Test psi to pascal conversion."""
        result = convert_pressure_tool(1, "psi", "pascal")
        assert abs(result - 6_894.757293168362) < 0.001

    def test_atmosphere_to_bar(self):
        """Test atmosphere to bar conversion."""
        result = convert_pressure_tool(1, "atmosphere", "bar")
        assert abs(result - 1.01325) < 0.001

    def test_same_unit_conversion(self):
        """Test conversion of same unit returns same value."""
        result = convert_pressure_tool(100, "pascal", "pascal")
        assert result == 100.0

    def test_millimeters_of_mercury_to_pascal(self):
        """Test mmHg to pascal conversion."""
        result = convert_pressure_tool(1, "millimeters of mercury", "pascal")
        assert abs(result - 133.322) < 0.001
