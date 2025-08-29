#!/usr/bin/env python3
"""
WeatherAPI MCP Server
A Model Context Protocol server for weather data using WeatherAPI.com
"""

import os
import requests
from typing import Dict, Any
from dotenv import load_dotenv
from fastmcp import FastMCP

# Load environment variables
load_dotenv()

# Configuration from environment
API_KEY = os.getenv("WEATHER_API_KEY")
BASE_URL = "http://api.weatherapi.com/v1"
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "10"))
API_LANGUAGE = os.getenv("API_LANGUAGE", "tr")

if not API_KEY:
    raise ValueError("WEATHER_API_KEY environment variable is required")

# Initialize MCP server
mcp = FastMCP("weather-api-mcp")

def get_current_weather(city: str) -> Dict[str, Any]:
    """Get current weather for a city using WeatherAPI"""
    url = f"{BASE_URL}/current.json?key={API_KEY}&q={city}&lang={API_LANGUAGE}"
    try:
        response = requests.get(url, timeout=API_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        return {
            "city": data.get("location", {}).get("name"),
            "country": data.get("location", {}).get("country"),
            "region": data.get("location", {}).get("region"),
            "weather": data.get("current", {}).get("condition", {}).get("text"),
            "temperature_c": data.get("current", {}).get("temp_c"),
            "temperature_f": data.get("current", {}).get("temp_f"),
            "feelslike_c": data.get("current", {}).get("feelslike_c"),
            "feelslike_f": data.get("current", {}).get("feelslike_f"),
            "humidity": data.get("current", {}).get("humidity"),
            "wind_kph": data.get("current", {}).get("wind_kph"),
            "wind_mph": data.get("current", {}).get("wind_mph"),
            "wind_dir": data.get("current", {}).get("wind_dir"),
            "pressure_mb": data.get("current", {}).get("pressure_mb"),
            "visibility_km": data.get("current", {}).get("vis_km"),
            "uv_index": data.get("current", {}).get("uv"),
            "icon": data.get("current", {}).get("condition", {}).get("icon"),
            "last_updated": data.get("current", {}).get("last_updated")
        }
    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

def get_weather_forecast(city: str, days: int = 3) -> Dict[str, Any]:
    """Get weather forecast for a city using WeatherAPI"""
    url = f"{BASE_URL}/forecast.json?key={API_KEY}&q={city}&days={days}&lang={API_LANGUAGE}"
    try:
        response = requests.get(url, timeout=API_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        forecast_days = []
        for day in data.get("forecast", {}).get("forecastday", []):
            forecast_days.append({
                "date": day.get("date"),
                "max_temp_c": day.get("day", {}).get("maxtemp_c"),
                "min_temp_c": day.get("day", {}).get("mintemp_c"),
                "max_temp_f": day.get("day", {}).get("maxtemp_f"),
                "min_temp_f": day.get("day", {}).get("mintemp_f"),
                "condition": day.get("day", {}).get("condition", {}).get("text"),
                "icon": day.get("day", {}).get("condition", {}).get("icon"),
                "chance_of_rain": day.get("day", {}).get("daily_chance_of_rain"),
                "chance_of_snow": day.get("day", {}).get("daily_chance_of_snow"),
                "max_wind_kph": day.get("day", {}).get("maxwind_kph"),
                "avg_humidity": day.get("day", {}).get("avghumidity"),
                "uv_index": day.get("day", {}).get("uv")
            })
        
        return {
            "city": data.get("location", {}).get("name"),
            "country": data.get("location", {}).get("country"),
            "region": data.get("location", {}).get("region"),
            "forecast": forecast_days
        }
    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

def search_locations(query: str) -> Dict[str, Any]:
    """Search for locations using WeatherAPI"""
    url = f"{BASE_URL}/search.json?key={API_KEY}&q={query}"
    try:
        response = requests.get(url, timeout=API_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        locations = []
        for location in data:
            locations.append({
                "name": location.get("name"),
                "region": location.get("region"),
                "country": location.get("country"),
                "lat": location.get("lat"),
                "lon": location.get("lon"),
                "url": location.get("url")
            })
        
        return {"locations": locations}
    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

@mcp.tool()
async def get_current_weather_tool(city: str) -> dict:
    """
    Get current weather information for a specific city.
    
    Args:
        city: Name of the city to get weather for
        
    Returns:
        Current weather data including temperature, conditions, humidity, wind, etc.
    """
    return get_current_weather(city)

@mcp.tool()
async def get_weather_forecast_tool(city: str, days: int = 3) -> dict:
    """
    Get weather forecast for a specific city.
    
    Args:
        city: Name of the city to get forecast for
        days: Number of days to forecast (1-10, default: 3)
        
    Returns:
        Weather forecast data for the specified number of days
    """
    if days < 1 or days > 10:
        return {"error": "Days must be between 1 and 10"}
    return get_weather_forecast(city, days)

@mcp.tool()
async def search_locations_tool(query: str) -> dict:
    """
    Search for locations by name.
    
    Args:
        query: Location name or partial name to search for
        
    Returns:
        List of matching locations with their details
    """
    return search_locations(query)

if __name__ == "__main__":
    print("🌤️  Starting WeatherAPI MCP Server...")
    print(f"Using API Key: {API_KEY[:10] if API_KEY else 'NOT SET'}...")
    print("Server starting...")
    mcp.run()
