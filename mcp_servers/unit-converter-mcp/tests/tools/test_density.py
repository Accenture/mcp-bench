"""Tests for density conversion functions."""

from unit_converter_mcp.tools.density import convert_density_tool


class TestDensityConversion:
    """Test density conversion functions."""

    def test_kilograms_per_liter_to_grams_per_cubic_centimeter(self):
        """Test kilograms per liter to grams per cubic centimeter conversion."""
        result = convert_density_tool(
            1, "kilograms per liter", "grams per cubic centimeter"
        )
        assert result == 1.0

    def test_grams_per_liter_to_kilograms_per_liter(self):
        """Test grams per liter to kilograms per liter conversion."""
        result = convert_density_tool(1000, "grams per liter", "kilograms per liter")
        assert result == 1.0

    def test_pounds_per_gallon_to_kilograms_per_liter(self):
        """Test pounds per gallon (US) to kilograms per liter conversion."""
        result = convert_density_tool(
            1, "pounds per gallon (US)", "kilograms per liter"
        )
        assert abs(result - 0.119826427) < 0.001

    def test_tonnes_per_cubic_meter_to_kilograms_per_liter(self):
        """Test tonnes per cubic meter to kilograms per liter conversion."""
        result = convert_density_tool(
            1, "tonnes per cubic meter", "kilograms per liter"
        )
        assert result == 1.0

    def test_pounds_per_cubic_foot_to_grams_per_cubic_centimeter(self):
        """Test pounds per cubic foot to grams per cubic centimeter conversion."""
        result = convert_density_tool(
            1, "pounds per cubic foot", "grams per cubic centimeter"
        )
        assert abs(result - 0.016018463) < 0.001

    def test_grains_per_gallon_us_to_milligrams_per_liter(self):
        """Test grains per gallon (US) to milligrams per liter conversion."""
        result = convert_density_tool(
            1, "grains per gallon (US)", "milligrams per liter"
        )
        assert abs(result - 17.118012) < 0.001

    def test_same_unit_conversion(self):
        """Test conversion between same units."""
        result = convert_density_tool(100, "kilograms per liter", "kilograms per liter")
        assert result == 100.0

    def test_default_units(self):
        """Test that default units work correctly."""
        # Test that "grains per gallon" defaults to US
        result1 = convert_density_tool(1, "grains per gallon", "kilograms per liter")
        result2 = convert_density_tool(
            1, "grains per gallon (US)", "kilograms per liter"
        )
        assert result1 == result2

        # Test that "pounds per gallon" defaults to US
        result3 = convert_density_tool(1, "pounds per gallon", "kilograms per liter")
        result4 = convert_density_tool(
            1, "pounds per gallon (US)", "kilograms per liter"
        )
        assert result3 == result4
