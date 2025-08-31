"""Tests for time conversion functions."""

from unit_converter_mcp.tools.time import convert_time_tool


class TestTimeConversion:
    """Test time conversion functions."""

    def test_seconds_to_minutes(self):
        """Test seconds to minutes conversion."""
        result = convert_time_tool(60, "seconds", "minutes")
        assert result == 1.0

    def test_minutes_to_hours(self):
        """Test minutes to hours conversion."""
        result = convert_time_tool(60, "minutes", "hours")
        assert result == 1.0

    def test_hours_to_days(self):
        """Test hours to days conversion."""
        result = convert_time_tool(24, "hours", "days")
        assert result == 1.0

    def test_days_to_weeks(self):
        """Test days to weeks conversion."""
        result = convert_time_tool(7, "days", "weeks")
        assert result == 1.0

    def test_milliseconds_to_seconds(self):
        """Test milliseconds to seconds conversion."""
        result = convert_time_tool(1000, "milliseconds", "seconds")
        assert result == 1.0

    def test_years_to_days(self):
        """Test years to days conversion."""
        result = convert_time_tool(1, "years", "days")
        # Using average Gregorian year: 365.2425 days
        assert abs(result - 365.2425) < 0.001

    def test_fortnights_to_days(self):
        """Test fortnights to days conversion."""
        result = convert_time_tool(1, "fortnights", "days")
        assert result == 14.0

    def test_decades_to_years(self):
        """Test decades to years conversion."""
        result = convert_time_tool(1, "decades", "years")
        assert result == 10.0

    def test_centuries_to_years(self):
        """Test centuries to years conversion."""
        result = convert_time_tool(1, "centuries", "years")
        assert result == 100.0

    def test_nanoseconds_to_microseconds(self):
        """Test nanoseconds to microseconds conversion."""
        result = convert_time_tool(1000, "nanoseconds", "microseconds")
        assert abs(result - 1.0) < 0.001
