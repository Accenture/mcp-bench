"""
Basic tests for the Wikipedia MCP package.
"""
import pytest
from wikipedia_mcp import __version__

def test_version():
    """Test that version is a string."""
    assert isinstance(__version__, str)

def test_import():
    """Test that the package can be imported."""
    import wikipedia_mcp
    assert wikipedia_mcp is not None 