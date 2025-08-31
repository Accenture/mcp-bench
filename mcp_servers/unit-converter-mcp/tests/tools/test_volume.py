"""Tests for volume conversion functions."""

from unit_converter_mcp.tools.volume import convert_volume_tool


class TestVolumeConversion:
    """Test volume conversion functions."""

    def test_liter_to_milliliter(self):
        """Test liter to milliliter conversion."""
        result = convert_volume_tool(1, "liter", "milliliter")
        assert result == 1000.0

    def test_gallon_to_liter(self):
        """Test gallon to liter conversion."""
        result = convert_volume_tool(1, "gallon", "liter")
        assert abs(result - 3.78541) < 0.001

    def test_cup_to_milliliter(self):
        """Test cup to milliliter conversion."""
        result = convert_volume_tool(1, "cup", "milliliter")
        assert abs(result - 236.588) < 0.1
