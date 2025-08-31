#!/usr/bin/env python3
"""
Test script for WeatherAPI MCP Server
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import get_current_weather, get_weather_forecast, search_locations

async def test_weather_functions():
    """Test the weather functions"""
    print("🌤️  Testing WeatherAPI MCP Server Functions")
    print("=" * 50)
    
    # Test cities
    test_cities = ["Istanbul", "London", "New York", "Tokyo"]
    
    print("\n1. Testing Current Weather")
    print("-" * 30)
    
    for city in test_cities:
        print(f"\n📍 Testing: {city}")
        result = get_current_weather(city)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            print(f"✅ Success!")
            print(f"   🌡️  Temperature: {result.get('temperature_c', 'N/A')}°C")
            print(f"   🌤️  Condition: {result.get('weather', 'N/A')}")
            print(f"   💧 Humidity: {result.get('humidity', 'N/A')}%")
            print(f"   💨 Wind: {result.get('wind_kph', 'N/A')} km/h")
    
    print("\n\n2. Testing Weather Forecast")
    print("-" * 30)
    
    test_city = "Istanbul"
    print(f"\n📍 Testing 3-day forecast for: {test_city}")
    result = get_weather_forecast(test_city, 3)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
    else:
        print(f"✅ Success!")
        forecast = result.get("forecast", [])
        for day in forecast[:3]:
            print(f"   📅 {day.get('date', 'N/A')}: {day.get('min_temp_c', 'N/A')}°C - {day.get('max_temp_c', 'N/A')}°C")
    
    print("\n\n3. Testing Location Search")
    print("-" * 30)
    
    search_query = "Istanbul"
    print(f"\n🔍 Searching for: {search_query}")
    result = search_locations(search_query)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
    else:
        print(f"✅ Success!")
        locations = result.get("locations", [])
        for i, location in enumerate(locations[:3]):
            print(f"   {i+1}. {location.get('name', 'N/A')}, {location.get('region', 'N/A')}, {location.get('country', 'N/A')}")
    
    print("\n" + "=" * 50)
    print("🎉 Testing completed!")

def check_environment():
    """Check if environment is properly configured"""
    print("🔧 Checking Environment Configuration")
    print("-" * 40)
    
    api_key = os.getenv("WEATHER_API_KEY")
    if api_key:
        print(f"✅ WEATHER_API_KEY: {api_key[:10]}...")
    else:
        print("❌ WEATHER_API_KEY: Not set")
        return False
    
    api_language = os.getenv("API_LANGUAGE", "tr")
    print(f"✅ API_LANGUAGE: {api_language}")
    
    api_timeout = os.getenv("API_TIMEOUT", "10")
    print(f"✅ API_TIMEOUT: {api_timeout}")
    
    return True

if __name__ == "__main__":
    print("🚀 WeatherAPI MCP Server Test Suite")
    print("=" * 60)
    
    if check_environment():
        print("\n🔄 Running function tests...")
        asyncio.run(test_weather_functions())
    else:
        print("\n❌ Environment not configured properly.")
        print("Please check your .env file and ensure WEATHER_API_KEY is set.")
