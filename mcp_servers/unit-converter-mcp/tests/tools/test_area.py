"""Tests for area conversion functions."""

from unit_converter_mcp.tools.area import convert_area_tool


class TestAreaConversion:
    """Test area conversion functions."""

    def test_square_meter_to_hectare(self):
        """Test square meter to hectare conversion."""
        result = convert_area_tool(10000, "square meter", "hectare")
        assert result == 1.0

    def test_acre_to_square_meter(self):
        """Test acre to square meter conversion."""
        result = convert_area_tool(1, "acre", "square meter")
        assert abs(result - 4046.8564224) < 0.001

    def test_square_foot_to_square_meter(self):
        """Test square foot to square meter conversion."""
        result = convert_area_tool(1, "square foot", "square meter")
        assert abs(result - 0.09290304) < 0.001

    def test_square_kilometer_to_square_mile(self):
        """Test square kilometer to square mile conversion."""
        result = convert_area_tool(2.589988110336, "square kilometer", "square mile")
        assert abs(result - 1.0) < 0.001
