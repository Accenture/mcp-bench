from mcp.server.fastmcp import FastMCP
from app import getCarBrands, searchCarPrice, getCarsByType

# Initialize MCP server
mcp = FastMCP("car-price-mcp")

@mcp.tool()
async def get_car_brands() -> str:
    """
    Get all available car brands from FIPE API.
    
    Returns:
        List of car brands with their codes and names
    """
    # Get car brands from the app
    brands_info = getCarBrands()
    if not brands_info:
        return "No car brands information found."

    return brands_info

@mcp.tool()
async def search_car_price(brand_name: str) -> str:
    """
    Search for car models and prices by brand name.
    
    Args:
        brand_name: The car brand name to search for (e.g., "Toyota", "Honda", "Ford")
    
    Returns:
        Car models with current market prices from FIPE database
    """
    if not brand_name or not brand_name.strip():
        return "Please provide a car brand name to search for."
    
    # Search for car prices
    car_info = searchCarPrice(brand_name.strip())
    if not car_info:
        return f"No car information found for '{brand_name}'."

    return car_info

@mcp.tool()
async def get_vehicles_by_type(vehicle_type: str = "carros") -> str:
    """
    Get vehicles by type (cars, motorcycles, trucks).
    
    Args:
        vehicle_type: Type of vehicles to fetch ("carros"/"cars", "motos"/"motorcycles", "caminhoes"/"trucks")
    
    Returns:
        List of vehicle brands for the specified type
    """
    if not vehicle_type or not vehicle_type.strip():
        vehicle_type = "carros"
    
    # Get vehicles by type
    vehicles_info = getCarsByType(vehicle_type.strip())
    if not vehicles_info:
        return f"No {vehicle_type} information found."

    return vehicles_info

if __name__ == "__main__":
    mcp.run(transport="stdio")
