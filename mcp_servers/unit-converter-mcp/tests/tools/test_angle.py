"""Tests for angle conversion functions."""

import math

from unit_converter_mcp.tools.angle import convert_angle_tool


class TestAngleConversion:
    """Test angle conversion functions."""

    def test_degrees_to_radians(self):
        """Test degrees to radians conversion."""
        result = convert_angle_tool(180, "degrees", "radians")
        assert abs(result - math.pi) < 1e-10

    def test_radians_to_degrees(self):
        """Test radians to degrees conversion."""
        result = convert_angle_tool(math.pi, "radians", "degrees")
        assert abs(result - 180) < 1e-10

    def test_degrees_to_arcmin(self):
        """Test degrees to arc-minutes conversion."""
        result = convert_angle_tool(1, "degrees", "arcmin")
        assert result == 60.0

    def test_arcmin_to_degrees(self):
        """Test arc-minutes to degrees conversion."""
        result = convert_angle_tool(60, "arcmin", "degrees")
        assert result == 1.0

    def test_degrees_to_arcsec(self):
        """Test degrees to arc-seconds conversion."""
        result = convert_angle_tool(1, "degrees", "arcsec")
        assert result == 3600.0

    def test_arcsec_to_degrees(self):
        """Test arc-seconds to degrees conversion."""
        result = convert_angle_tool(3600, "arcsec", "degrees")
        assert result == 1.0

    def test_degrees_to_turns(self):
        """Test degrees to turns conversion."""
        result = convert_angle_tool(360, "degrees", "turns")
        assert result == 1.0

    def test_turns_to_degrees(self):
        """Test turns to degrees conversion."""
        result = convert_angle_tool(0.25, "turns", "degrees")
        assert result == 90.0

    def test_degrees_to_gons(self):
        """Test degrees to gons conversion."""
        result = convert_angle_tool(90, "degrees", "gons")
        assert result == 100.0

    def test_gons_to_degrees(self):
        """Test gons to degrees conversion."""
        result = convert_angle_tool(100, "gons", "degrees")
        assert result == 90.0

    def test_same_unit_conversion(self):
        """Test that converting to the same unit returns the same value."""
        result = convert_angle_tool(45, "degrees", "degrees")
        assert result == 45.0

    def test_radians_to_turns(self):
        """Test direct conversion between non-degree units."""
        result = convert_angle_tool(2 * math.pi, "radians", "turns")
        assert abs(result - 1.0) < 1e-10

    def test_arcmin_to_arcsec(self):
        """Test conversion from arc-minutes to arc-seconds."""
        result = convert_angle_tool(1, "arcmin", "arcsec")
        assert result == 60.0
