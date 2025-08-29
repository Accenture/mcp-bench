from mcp.server.fastmcp import FastMCP
from app import get_fruit_info

# Initialize MCP server
mcp = FastMCP("fruityvice-mcp")

@mcp.tool()
async def get_fruit_nutrition(fruit_name: str) -> dict:
    """
    Get nutritional information and details for a given fruit name.

    Args:
        fruit_name: The name of the fruit to get information about (e.g., "apple", "banana", "orange")

    Returns:
        Dictionary containing fruit information including name, family, genus, order, and nutritional data
    """
    # Call the function from app.py
    result = get_fruit_info(fruit_name)
    return result

if __name__ == "__main__":
    mcp.run(transport="stdio")