"""Tests for computer storage conversion functions."""

from unit_converter_mcp.tools.computer import convert_computer_data_tool


class TestComputerConversion:
    """Test computer storage conversion functions."""

    def test_megabytes_to_gigabytes(self):
        """Test megabytes to gigabytes conversion."""
        result = convert_computer_data_tool(1024, "megabytes", "gigabytes")
        assert result == 1.0

    def test_bytes_to_kilobytes(self):
        """Test bytes to kilobytes conversion."""
        result = convert_computer_data_tool(1048576, "bytes", "kilobytes")
        assert abs(result - 1024.0) < 0.001

    def test_gigabytes_to_terabytes(self):
        """Test gigabytes to terabytes conversion."""
        result = convert_computer_data_tool(1024, "gigabytes", "terabytes")
        assert abs(result - 1.0) < 0.001

    def test_bits_to_bytes(self):
        """Test bits to bytes conversion."""
        result = convert_computer_data_tool(8, "bits", "bytes")
        assert abs(result - 1.0) < 0.001

    def test_same_unit_conversion(self):
        """Test conversion between same units."""
        result = convert_computer_data_tool(100, "megabytes", "megabytes")
        assert result == 100.0
