"""Tests for the filters module."""

import json
import os
from typing import Any

import pytest

from biomcp.variants.filters import filter_variants


@pytest.fixture
def braf_v600e_variants() -> list[dict[str, Any]]:
    """Load BRAF V600E test data."""
    test_data_path = os.path.join(
        os.path.dirname(__file__),
        "../../data/myvariant/variants_full_braf_v600e.json",
    )
    with open(test_data_path) as f:
        data = json.load(f)
        return data.get("hits", [])


def test_filter_variants_civic_contributors(braf_v600e_variants):
    """Test filtering out civic.contributors path."""
    # Verify that civic.contributors exists in original data
    variant = braf_v600e_variants[0]
    assert "civic" in variant
    assert "contributors" in variant["civic"]
    assert variant["civic"]["contributors"] is not None

    # Filter out civic.contributors
    filtered = filter_variants(braf_v600e_variants)

    # Verify civic.contributors is removed but civic section remains
    filtered_variant = filtered[0]
    assert "civic" in filtered_variant
    assert "contributors" not in filtered_variant["civic"]

    # Verify other civic data is preserved
    assert "id" in filtered_variant["civic"]
    assert filtered_variant["civic"]["id"] == variant["civic"]["id"]
