"""Tests for length conversion functions."""

from unit_converter_mcp.tools.length import convert_length_tool


class TestLengthConversion:
    """Test length conversion functions."""

    def test_meter_to_kilometer(self):
        """Test meter to kilometer conversion."""
        result = convert_length_tool(1000, "meter", "kilometer")
        assert result == 1.0

    def test_inch_to_centimeter(self):
        """Test inch to centimeter conversion."""
        result = convert_length_tool(1, "inch", "centimeter")
        assert abs(result - 2.54) < 0.001

    def test_foot_to_meter(self):
        """Test foot to meter conversion."""
        result = convert_length_tool(1, "foot", "meter")
        assert abs(result - 0.3048) < 0.001
