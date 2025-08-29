from mcp.server.fastmcp import FastMCP
from movie_recommender import getMovieSuggestions

mcp = FastMCP("movie-recommender-mcp")

@mcp.tool()
async def get_movies(keyword: str) -> str:
    """
    Get movie suggestions based on keyword.
    """
    result = getMovieSuggestions(keyword)
    return result or "Film bulunamadı."

if __name__ == "__main__":
    mcp.run(transport="stdio")
