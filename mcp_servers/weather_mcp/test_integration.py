#!/usr/bin/env python3
"""
Integration test for the complete weather system
Tests the MCP server and demonstrates the full workflow
"""

import requests
import json
import time

def test_weather_integration():
    """Test the complete weather integration"""
    print("🌤️  Weather Integration Test")
    print("=" * 50)
    
    # Test cities
    test_cities = ["Istanbul", "Ankara", "İzmir", "London"]
    
    for city in test_cities:
        print(f"\n📍 Testing: {city}")
        print("-" * 30)
        
        # Test current weather
        try:
            response = requests.post(
                "http://localhost:8000/tools/get_current_weather_tool/invoke",
                json={"input": {"city": city}},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                weather = data.get("output", {})
                
                if "error" not in weather:
                    print(f"✅ Current Weather:")
                    print(f"   🌡️  {weather.get('temperature_c', 'N/A')}°C")
                    print(f"   🌤️  {weather.get('weather', 'N/A')}")
                    print(f"   💧 {weather.get('humidity', 'N/A')}% humidity")
                    print(f"   💨 {weather.get('wind_kph', 'N/A')} km/h wind")
                else:
                    print(f"❌ Weather Error: {weather.get('error')}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Request Error: {e}")
        
        # Test forecast
        try:
            response = requests.post(
                "http://localhost:8000/tools/get_weather_forecast_tool/invoke",
                json={"input": {"city": city, "days": 3}},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                forecast = data.get("output", {})
                
                if "error" not in forecast and "forecast" in forecast:
                    print(f"✅ 3-Day Forecast:")
                    for day in forecast["forecast"][:3]:
                        print(f"   📅 {day.get('date')}: {day.get('min_temp_c')}°C - {day.get('max_temp_c')}°C")
                else:
                    print(f"❌ Forecast Error: {forecast.get('error', 'No forecast data')}")
            else:
                print(f"❌ Forecast HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Forecast Request Error: {e}")
        
        time.sleep(1)  # Rate limiting
    
    print("\n" + "=" * 50)
    print("🎉 Integration test completed!")
    print("\nNext steps:")
    print("1. Open the web app: weather_web_app.html")
    print("2. Test the React Native app (if available)")
    print("3. Try different cities and weather conditions")

def test_server_health():
    """Test server health"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server Health: {data.get('status', 'unknown')}")
            return True
        else:
            print(f"❌ Server Health Check Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server Health Check Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Weather System Integration Test")
    print("=" * 60)
    
    # Check server health first
    if test_server_health():
        print("\n🔄 Running integration tests...")
        test_weather_integration()
    else:
        print("\n❌ Server is not responding. Please start the MCP server first:")
        print("   python simple_weather_server.py")
