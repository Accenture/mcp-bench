"""
Main entry point for Reddit MCP server
"""

from mcp_reddit.reddit_fetcher import mcp

if __name__ == "__main__":
    # Run the FastMCP server
    mcp.run()