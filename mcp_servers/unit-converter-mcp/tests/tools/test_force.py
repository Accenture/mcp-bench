"""Tests for force conversion functions."""

from unit_converter_mcp.tools.force import convert_force_tool


class TestForceConversion:
    """Test force conversion functions."""

    def test_newton_to_kilonewton(self):
        """Test newton to kilonewton conversion."""
        result = convert_force_tool(1000, "newtons", "kilonewtons")
        assert result == 1.0

    def test_pound_force_to_newton(self):
        """Test pound force to newton conversion."""
        result = convert_force_tool(1, "pounds force", "newtons")
        assert abs(result - 4.44822161526) < 0.001

    def test_kilogram_force_to_newton(self):
        """Test kilogram force to newton conversion."""
        result = convert_force_tool(1, "kilograms force", "newtons")
        assert abs(result - 9.80665) < 0.001

    def test_dyne_to_newton(self):
        """Test dyne to newton conversion."""
        result = convert_force_tool(100000, "dynes", "newtons")
        assert result == 1.0

    def test_kip_to_newton(self):
        """Test kip to newton conversion."""
        result = convert_force_tool(1, "kips", "newtons")
        assert abs(result - 4448.222) < 0.001

    def test_newton_to_newton(self):
        """Test newton to newton conversion (identity)."""
        result = convert_force_tool(10, "newtons", "newtons")
        assert result == 10.0

    def test_meganewton_to_newton(self):
        """Test meganewton to newton conversion."""
        result = convert_force_tool(1, "meganewtons", "newtons")
        assert result == 1_000_000.0
