"""Module for filtering variant data based on paths."""

from typing import Any


def _get_nested_value(data: dict[str, Any], path: str) -> Any:
    """Get a nested value from a dictionary using dot notation path."""
    keys = path.split(".")
    current = data
    for key in keys[:-1]:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def _delete_nested_path(data: dict[str, Any], path: str) -> None:
    """Delete a nested path from a dictionary using dot notation."""
    keys = path.split(".")
    current = data
    for key in keys[:-1]:
        if not isinstance(current, dict) or key not in current:
            return
        current = current[key]

    if isinstance(current, dict) and keys[-1] in current:
        del current[keys[-1]]


def _deep_copy_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Create a deep copy of a dictionary, handling nested dicts and lists."""
    result: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, dict):
            result[key] = _deep_copy_dict(value)
        elif isinstance(value, list):
            result[key] = [
                _deep_copy_dict(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value
    return result


def filter_variants(variants: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Filter out specified paths from variant data.

    Args:
        variants: List of variant dictionaries from MyVariant.info API

    Returns:
        List of variant dictionaries with specified paths removed
    """
    # Create a deep copy to avoid modifying the input
    filtered_variants = []
    for variant in variants:
        # Create a deep copy of the variant
        filtered_variant = _deep_copy_dict(variant)

        # Remove specified paths
        for path in PATH_FILTERS:
            _delete_nested_path(filtered_variant, path)

        filtered_variants.append(filtered_variant)

    return filtered_variants


PATH_FILTERS = [
    "civic.contributors",
    "civic.molecularProfiles",
    "dbsnp.gene.rnas",
    "dbnsfp.clinvar",  # duplicate of root-level clinvar
    "civic.lastAcceptedRevisionEvent",
    "civic.lastSubmittedRevisionEvent",
    "civic.creationActivity",
]
