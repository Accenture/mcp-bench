"""Tests for energy conversion functions."""

from unit_converter_mcp.tools.energy import convert_energy_tool


class TestEnergyConversion:
    """Test energy conversion functions."""

    def test_joule_to_kilojoule(self):
        """Test joule to kilojoule conversion."""
        result = convert_energy_tool(1000, "joule", "kilojoule")
        assert result == 1.0

    def test_kilowatt_hour_to_joule(self):
        """Test kilowatt hour to joule conversion."""
        result = convert_energy_tool(1, "kilowatt hour", "joule")
        assert result == 3_600_000.0

    def test_calorie_to_joule(self):
        """Test calorie to joule conversion."""
        result = convert_energy_tool(1, "calorie", "joule")
        assert abs(result - 4.184) < 0.001

    def test_btu_to_joule(self):
        """Test BTU to joule conversion."""
        result = convert_energy_tool(1, "Btu", "joule")
        assert abs(result - 1054.35) < 0.001

    def test_foot_pound_force_to_joule(self):
        """Test foot-pound force to joule conversion."""
        result = convert_energy_tool(1, "foot‑pound force", "joule")
        assert abs(result - 1.355_817_948_331) < 0.001

    def test_electron_volt_to_joule(self):
        """Test electron volt to joule conversion."""
        result = convert_energy_tool(1, "electron volt", "joule")
        assert abs(result - 1.602_176_634e-19) < 1e-25

    def test_same_unit_conversion(self):
        """Test conversion between same units."""
        result = convert_energy_tool(100, "joule", "joule")
        assert result == 100.0
