"""Tests for batch conversion functions."""

from unit_converter_mcp.tools.batch import convert_batch_tool


class TestBatchConversion:
    """Test batch conversion functions."""

    def test_single_successful_conversion(self):
        """Test batch with a single successful conversion."""
        requests = [
            {
                "value": 100,
                "from_unit": "celsius",
                "to_unit": "fahrenheit",
                "conversion_type": "temperature",
                "request_id": "temp_1",
            }
        ]

        results = convert_batch_tool(requests)

        assert len(results) == 1
        result = results[0]
        assert result["success"] is True
        assert result["request_id"] == "temp_1"
        assert result["original_value"] == 100
        assert result["original_unit"] == "celsius"
        assert result["converted_value"] == 212.0
        assert result["converted_unit"] == "fahrenheit"
        assert result["conversion_type"] == "temperature"

    def test_multiple_successful_conversions(self):
        """Test batch with multiple successful conversions of different types."""
        requests = [
            {
                "value": 0,
                "from_unit": "celsius",
                "to_unit": "kelvin",
                "conversion_type": "temperature",
                "request_id": "temp_1",
            },
            {
                "value": 1000,
                "from_unit": "meter",
                "to_unit": "kilometer",
                "conversion_type": "length",
                "request_id": "length_1",
            },
            {
                "value": 1000,
                "from_unit": "gram",
                "to_unit": "kilogram",
                "conversion_type": "mass",
                "request_id": "mass_1",
            },
        ]

        results = convert_batch_tool(requests)

        assert len(results) == 3

        # Check temperature conversion
        temp_result = next(r for r in results if r["request_id"] == "temp_1")
        assert temp_result["success"] is True
        assert temp_result["converted_value"] == 273.15

        # Check length conversion
        length_result = next(r for r in results if r["request_id"] == "length_1")
        assert length_result["success"] is True
        assert length_result["converted_value"] == 1.0

        # Check mass conversion
        mass_result = next(r for r in results if r["request_id"] == "mass_1")
        assert mass_result["success"] is True
        assert mass_result["converted_value"] == 1.0

    def test_conversion_with_auto_generated_request_id(self):
        """Test conversion without providing request_id."""
        requests = [
            {
                "value": 32,
                "from_unit": "fahrenheit",
                "to_unit": "celsius",
                "conversion_type": "temperature",
            }
        ]

        results = convert_batch_tool(requests)

        assert len(results) == 1
        result = results[0]
        assert result["success"] is True
        assert "request_id" in result
        assert result["request_id"] is not None
        assert result["converted_value"] == 0.0

    def test_missing_required_fields(self):
        """Test batch conversion with missing required fields."""
        # Missing value
        requests = [
            {
                "from_unit": "celsius",
                "to_unit": "fahrenheit",
                "conversion_type": "temperature",
                "request_id": "temp_1",
            }
        ]

        results = convert_batch_tool(requests)

        assert len(results) == 1
        result = results[0]
        assert result["success"] is False
        assert "Missing required field: value" in result["error"]

        # Missing from_unit
        requests = [
            {
                "value": 100,
                "to_unit": "fahrenheit",
                "conversion_type": "temperature",
                "request_id": "temp_2",
            }
        ]

        results = convert_batch_tool(requests)

        assert len(results) == 1
        result = results[0]
        assert result["success"] is False
        assert "Missing required field: from_unit" in result["error"]

    def test_invalid_conversion_type(self):
        """Test batch conversion with invalid conversion type."""
        requests = [
            {
                "value": 100,
                "from_unit": "celsius",
                "to_unit": "fahrenheit",
                "conversion_type": "invalid_type",
                "request_id": "invalid_1",
            }
        ]

        results = convert_batch_tool(requests)

        assert len(results) == 1
        result = results[0]
        assert result["success"] is False
        assert "Unsupported conversion type: invalid_type" in result["error"]

    def test_invalid_units(self):
        """Test batch conversion with invalid units."""
        requests = [
            {
                "value": 100,
                "from_unit": "invalid_unit",
                "to_unit": "fahrenheit",
                "conversion_type": "temperature",
                "request_id": "invalid_unit_1",
            }
        ]

        results = convert_batch_tool(requests)

        assert len(results) == 1
        result = results[0]
        assert result["success"] is False
        assert "error" in result

    def test_mixed_success_and_failure(self):
        """Test batch with both successful and failed conversions."""
        requests = [
            {
                "value": 100,
                "from_unit": "celsius",
                "to_unit": "fahrenheit",
                "conversion_type": "temperature",
                "request_id": "success_1",
            },
            {
                "value": 100,
                "from_unit": "invalid_unit",
                "to_unit": "fahrenheit",
                "conversion_type": "temperature",
                "request_id": "failure_1",
            },
            {
                "value": 1000,
                "from_unit": "meter",
                "to_unit": "kilometer",
                "conversion_type": "length",
                "request_id": "success_2",
            },
        ]

        results = convert_batch_tool(requests)

        assert len(results) == 3

        success_count = sum(1 for r in results if r["success"])
        failure_count = sum(1 for r in results if not r["success"])

        assert success_count == 2
        assert failure_count == 1

        # Check successful conversions have expected structure
        successful_results = [r for r in results if r["success"]]
        for result in successful_results:
            assert "original_value" in result
            assert "converted_value" in result
            assert "conversion_type" in result

        # Check failed conversions have error messages
        failed_results = [r for r in results if not r["success"]]
        for result in failed_results:
            assert "error" in result
            assert "original_value" not in result

    def test_empty_batch(self):
        """Test batch conversion with empty request list."""
        requests = []

        results = convert_batch_tool(requests)

        assert len(results) == 0
        assert isinstance(results, list)

    def test_all_conversion_types_supported(self):
        """Test that all conversion types are supported in batch processing."""
        requests = [
            {
                "value": 90,
                "from_unit": "degrees",
                "to_unit": "radians",
                "conversion_type": "angle",
            },
            {
                "value": 100,
                "from_unit": "square meter",
                "to_unit": "square foot",
                "conversion_type": "area",
            },
            {
                "value": 1024,
                "from_unit": "bytes",
                "to_unit": "kilobytes",
                "conversion_type": "computer_data",
            },
            {
                "value": 1000,
                "from_unit": "kilograms per cubic meter",
                "to_unit": "grams per cubic centimeter",
                "conversion_type": "density",
            },
            {
                "value": 1000,
                "from_unit": "joule",
                "to_unit": "calorie",
                "conversion_type": "energy",
            },
            {
                "value": 10,
                "from_unit": "newtons",
                "to_unit": "pounds force",
                "conversion_type": "force",
            },
            {
                "value": 1000,
                "from_unit": "meter",
                "to_unit": "kilometer",
                "conversion_type": "length",
            },
            {
                "value": 1000,
                "from_unit": "gram",
                "to_unit": "kilogram",
                "conversion_type": "mass",
            },
            {
                "value": 1000,
                "from_unit": "watt",
                "to_unit": "kilowatt",
                "conversion_type": "power",
            },
            {
                "value": 101325,
                "from_unit": "pascal",
                "to_unit": "atmosphere",
                "conversion_type": "pressure",
            },
            {
                "value": 100,
                "from_unit": "kilometers per hour",
                "to_unit": "meters per second",
                "conversion_type": "speed",
            },
            {
                "value": 0,
                "from_unit": "celsius",
                "to_unit": "kelvin",
                "conversion_type": "temperature",
            },
            {
                "value": 3600,
                "from_unit": "seconds",
                "to_unit": "hours",
                "conversion_type": "time",
            },
            {
                "value": 1000,
                "from_unit": "milliliter",
                "to_unit": "liter",
                "conversion_type": "volume",
            },
        ]

        results = convert_batch_tool(requests)

        assert len(results) == 14
        # All conversions should succeed (though values may vary)
        for result in results:
            assert result["success"] is True, f"Failed conversion: {result}"

    def test_large_batch_performance(self):
        """Test performance with a larger batch of conversions."""
        # Create 100 temperature conversions
        requests = []
        for i in range(100):
            requests.append(
                {
                    "value": i,
                    "from_unit": "celsius",
                    "to_unit": "fahrenheit",
                    "conversion_type": "temperature",
                    "request_id": f"temp_{i}",
                }
            )

        results = convert_batch_tool(requests)

        assert len(results) == 100
        assert all(r["success"] for r in results)

        # Verify a few random conversions
        assert results[0]["converted_value"] == 32.0  # 0°C = 32°F
        assert results[100 - 1]["converted_value"] == 210.2  # 99°C = 210.2°F

    def test_request_id_preservation(self):
        """Test that request IDs are preserved in results."""
        requests = [
            {
                "value": 100,
                "from_unit": "celsius",
                "to_unit": "fahrenheit",
                "conversion_type": "temperature",
                "request_id": "custom_id_123",
            },
            {
                "value": 1000,
                "from_unit": "meter",
                "to_unit": "kilometer",
                "conversion_type": "length",
                "request_id": "another_custom_id",
            },
        ]

        results = convert_batch_tool(requests)

        request_ids = [r["request_id"] for r in results]
        assert "custom_id_123" in request_ids
        assert "another_custom_id" in request_ids
