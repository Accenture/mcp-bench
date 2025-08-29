#!/usr/bin/env python3
"""
Enhanced Bibliomantic MCP Server

A Model Context Protocol server that integrates enhanced I Ching divination with AI responses,
exploring the bibliomantic approach described in Philip K. Dick's "The Man in the High Castle"
with full traditional Chinese I Ching elements.

This is the main entry point for the enhanced server when invoked directly by Claude Desktop.
Maintains backward compatibility with existing configurations.
"""

import sys
import logging

# Configure logging to stderr (MCP uses stdout for protocol)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Try to import enhanced server first, fall back to original
try:
    from enhanced_bibliomantic_server import mcp
    logger.info("Loaded Enhanced Bibliomantic MCP Server with traditional I Ching content")
except ImportError as e:
    logger.warning(f"Enhanced server not available ({e}), falling back to original server")
    try:
        from bibliomantic_fastmcp_ethical import mcp
        logger.info("Loaded original Bibliomantic MCP Server in compatibility mode")
    except ImportError as fallback_error:
        logger.error(f"Failed to load any server: {fallback_error}")
        # Create a minimal error server to prevent import failure
        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP(name="Bibliomantic Oracle - Error State")
        
        @mcp.tool()
        def server_error() -> str:
            return "Server failed to initialize properly. Please check the logs and ensure all dependencies are installed."

def main():
    """Main entry point for the bibliomantic server."""
    try:
        mcp.run()
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
