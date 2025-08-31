"""Tests for speed conversion functions."""

from unit_converter_mcp.tools.speed import convert_speed_tool


class TestSpeedConversion:
    """Test speed conversion functions."""

    def test_meters_per_second_to_kilometers_per_hour(self):
        """Test meters per second to kilometers per hour conversion."""
        result = convert_speed_tool(1, "meters per second", "kilometers per hour")
        assert abs(result - 3.6) < 0.001

    def test_miles_per_hour_to_meters_per_second(self):
        """Test miles per hour to meters per second conversion."""
        result = convert_speed_tool(1, "miles per hour", "meters per second")
        assert abs(result - 0.44704) < 0.001

    def test_knots_to_meters_per_second(self):
        """Test knots to meters per second conversion."""
        result = convert_speed_tool(1, "knots", "meters per second")
        assert abs(result - 0.514444444444) < 0.001

    def test_feet_per_second_to_meters_per_second(self):
        """Test feet per second to meters per second conversion."""
        result = convert_speed_tool(1, "feet per second", "meters per second")
        assert abs(result - 0.3048) < 0.001

    def test_same_unit_conversion(self):
        """Test conversion between same units."""
        result = convert_speed_tool(100, "meters per second", "meters per second")
        assert result == 100.0

    def test_speed_of_light_conversion(self):
        """Test speed of light conversion."""
        result = convert_speed_tool(1, "speed of light", "meters per second")
        assert result == 299_792_458.0
