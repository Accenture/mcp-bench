#!/usr/bin/env python3
"""
Test script for the WeatherAPI MCP Server
This script tests the MCP server functionality before integrating with the weather agent.
"""

import requests
import json
import time

MCP_SERVER_URL = "http://localhost:8000"

def test_mcp_tool(tool_name: str, input_data: dict):
    """Test a specific MCP tool"""
    url = f"{MCP_SERVER_URL}/tools/{tool_name}/invoke"
    payload = {"input": input_data}
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}

def main():
    print("🌤️  Testing WeatherAPI MCP Server")
    print("=" * 50)
    
    # Test cities
    test_cities = ["Istanbul", "London", "New York", "Tokyo"]
    
    print("\n1. Testing Current Weather Tool")
    print("-" * 30)
    
    for city in test_cities:
        print(f"\n📍 Testing weather for: {city}")
        result = test_mcp_tool("get_current_weather_tool", {"city": city})
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            output = result.get("output", result)
            if "error" in output:
                print(f"❌ API Error: {output['error']}")
            else:
                print(f"✅ Success!")
                print(f"   🌡️  Temperature: {output.get('temperature_c', 'N/A')}°C")
                print(f"   🌤️  Condition: {output.get('weather', 'N/A')}")
                print(f"   💧 Humidity: {output.get('humidity', 'N/A')}%")
                print(f"   💨 Wind: {output.get('wind_kph', 'N/A')} km/h {output.get('wind_dir', '')}")
    
    print("\n\n2. Testing Weather Forecast Tool")
    print("-" * 30)
    
    test_city = "Istanbul"
    print(f"\n📍 Testing 3-day forecast for: {test_city}")
    result = test_mcp_tool("get_weather_forecast_tool", {"city": test_city, "days": 3})
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
    else:
        output = result.get("output", result)
        if "error" in output:
            print(f"❌ API Error: {output['error']}")
        else:
            print(f"✅ Success!")
            forecast = output.get("forecast", [])
            for day in forecast[:3]:  # Show first 3 days
                print(f"   📅 {day.get('date', 'N/A')}: {day.get('min_temp_c', 'N/A')}°C - {day.get('max_temp_c', 'N/A')}°C, {day.get('condition', 'N/A')}")
    
    print("\n\n3. Testing Location Search Tool")
    print("-" * 30)
    
    search_query = "Istanbul"
    print(f"\n🔍 Searching for locations: {search_query}")
    result = test_mcp_tool("search_locations_tool", {"query": search_query})
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
    else:
        output = result.get("output", result)
        if "error" in output:
            print(f"❌ API Error: {output['error']}")
        else:
            print(f"✅ Success!")
            locations = output.get("locations", [])
            for i, location in enumerate(locations[:3]):  # Show first 3 results
                print(f"   {i+1}. {location.get('name', 'N/A')}, {location.get('region', 'N/A')}, {location.get('country', 'N/A')}")
    
    print("\n\n4. Testing Legacy Tool (Backward Compatibility)")
    print("-" * 30)
    
    test_city = "Istanbul"
    print(f"\n📍 Testing legacy tool for: {test_city}")
    result = test_mcp_tool("get_live_temp", {"city": test_city})
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
    else:
        output = result.get("output", result)
        if "error" in output:
            print(f"❌ API Error: {output['error']}")
        else:
            print(f"✅ Success!")
            print(f"   🌡️  Temperature: {output.get('temperature_c', 'N/A')}°C")
            print(f"   🌤️  Condition: {output.get('weather', 'N/A')}")
    
    print("\n" + "=" * 50)
    print("🎉 MCP Server testing completed!")
    print("\nNext steps:")
    print("1. Start the MCP server: python server.py")
    print("2. Test the weather agent integration")
    print("3. Run the Mastra development server")

if __name__ == "__main__":
    main()
