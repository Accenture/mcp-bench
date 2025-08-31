"""Tests for mass conversion functions."""

from unit_converter_mcp.tools.mass import convert_mass_tool


class TestMassConversion:
    """Test mass conversion functions."""

    def test_kilogram_to_gram(self):
        """Test kilogram to gram conversion."""
        result = convert_mass_tool(1, "kilogram", "gram")
        assert result == 1000.0

    def test_pound_to_kilogram(self):
        """Test pound to kilogram conversion."""
        result = convert_mass_tool(1, "pound", "kilogram")
        assert abs(result - 0.45359237) < 0.001

    def test_ounce_to_gram(self):
        """Test ounce to gram conversion."""
        result = convert_mass_tool(1, "ounce", "gram")
        assert abs(result - 28.349523125) < 0.001

    def test_carat_to_gram(self):
        """Test carat to gram conversion."""
        result = convert_mass_tool(1, "carat", "gram")
        assert abs(result - 0.2) < 0.001

    def test_stone_to_kilogram(self):
        """Test stone to kilogram conversion."""
        result = convert_mass_tool(1, "stone", "kilogram")
        assert abs(result - 6.35029318) < 0.001

    def test_tonne_to_kilogram(self):
        """Test tonne to kilogram conversion."""
        result = convert_mass_tool(1, "tonne", "kilogram")
        assert result == 1000.0

    def test_milligram_to_gram(self):
        """Test milligram to gram conversion."""
        result = convert_mass_tool(1000, "milligram", "gram")
        assert result == 1.0

    def test_troy_ounce_to_gram(self):
        """Test troy ounce to gram conversion."""
        result = convert_mass_tool(1, "troy ounce", "gram")
        assert abs(result - 31.1034768) < 0.001
