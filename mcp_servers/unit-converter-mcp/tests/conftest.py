"""Test configuration for unit converter MCP."""

import sys
from pathlib import Path

# Add the src directory to the Python path for testing
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))
