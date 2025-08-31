"""Tests for power conversion functions."""

from unit_converter_mcp.tools.power import convert_power_tool


class TestPowerConversion:
    """Test power conversion functions."""

    def test_watt_to_kilowatt(self):
        """Test watt to kilowatt conversion."""
        result = convert_power_tool(1000, "watt", "kilowatt")
        assert result == 1.0

    def test_horsepower_to_watt(self):
        """Test horsepower to watt conversion."""
        result = convert_power_tool(1, "horsepower", "watt")
        assert abs(result - 745.69987158227) < 0.001

    def test_kilowatt_to_horsepower(self):
        """Test kilowatt to horsepower conversion."""
        result = convert_power_tool(1, "kilowatt", "horsepower")
        assert abs(result - 1.34102) < 0.001

    def test_btu_per_hour_to_watt(self):
        """Test Btu per hour to watt conversion."""
        result = convert_power_tool(1, "Btu per hour", "watt")
        assert abs(result - 0.2930711) < 0.001

    def test_same_unit_conversion(self):
        """Test conversion between same units."""
        result = convert_power_tool(100, "watt", "watt")
        assert result == 100.0

    def test_metric_horsepower_to_horsepower(self):
        """Test metric horsepower to international horsepower conversion."""
        result = convert_power_tool(1, "horsepower (metric)", "horsepower")
        assert abs(result - 0.98632) < 0.001
