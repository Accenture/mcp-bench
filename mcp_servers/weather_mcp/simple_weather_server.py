#!/usr/bin/env python3
"""
Simple HTTP server for weather API testing
This provides a simple REST API that mimics the MCP server structure for testing
"""

from flask import Flask, request, jsonify
import requests
from typing import Dict, Any

# WeatherAPI configuration
API_KEY = "366fd563131a4af1bd962603252105"
BASE_URL = "http://api.weatherapi.com/v1"

app = Flask(__name__)

# Add CORS headers to all responses
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

def get_current_weather(city: str) -> Dict[str, Any]:
    """Get current weather for a city using WeatherAPI"""
    url = f"{BASE_URL}/current.json?key={API_KEY}&q={city}&lang=tr"
    try:
        response = requests.get(url, timeout=10)
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
    url = f"{BASE_URL}/forecast.json?key={API_KEY}&q={city}&days={days}&lang=tr"
    try:
        response = requests.get(url, timeout=10)
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
        response = requests.get(url, timeout=10)
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

@app.route('/tools/get_current_weather_tool/invoke', methods=['POST'])
def current_weather_endpoint():
    """MCP-style endpoint for current weather"""
    try:
        data = request.get_json()
        city = data.get('input', {}).get('city', '')
        if not city:
            return jsonify({"error": "City parameter is required"}), 400
        
        result = get_current_weather(city)
        return jsonify({"output": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/tools/get_weather_forecast_tool/invoke', methods=['POST'])
def forecast_endpoint():
    """MCP-style endpoint for weather forecast"""
    try:
        data = request.get_json()
        city = data.get('input', {}).get('city', '')
        days = data.get('input', {}).get('days', 3)
        
        if not city:
            return jsonify({"error": "City parameter is required"}), 400
        
        if days < 1 or days > 10:
            return jsonify({"error": "Days must be between 1 and 10"}), 400
        
        result = get_weather_forecast(city, days)
        return jsonify({"output": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/tools/search_locations_tool/invoke', methods=['POST'])
def search_locations_endpoint():
    """MCP-style endpoint for location search"""
    try:
        data = request.get_json()
        query = data.get('input', {}).get('query', '')
        if not query:
            return jsonify({"error": "Query parameter is required"}), 400

        result = search_locations(query)
        return jsonify({"output": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/tools/get_live_temp/invoke', methods=['POST'])
def legacy_endpoint():
    """Legacy endpoint for backward compatibility"""
    try:
        data = request.get_json()
        city = data.get('input', {}).get('city', '')
        if not city:
            return jsonify({"error": "City parameter is required"}), 400

        result = get_current_weather(city)
        return jsonify({"output": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "WeatherAPI MCP Server"})

@app.route('/', methods=['GET'])
def root():
    """Root endpoint with API information"""
    return jsonify({
        "service": "WeatherAPI MCP Server",
        "version": "1.0.0",
        "endpoints": [
            "/tools/get_current_weather_tool/invoke",
            "/tools/get_weather_forecast_tool/invoke",
            "/tools/search_locations_tool/invoke",
            "/tools/get_live_temp/invoke",
            "/health"
        ],
        "api_key_status": "configured" if API_KEY else "missing"
    })

if __name__ == "__main__":
    print("🌤️  Starting WeatherAPI MCP Server (Flask)")
    print(f"Using API Key: {API_KEY[:10]}...")
    print("Server will be available at http://localhost:8000")
    print("Available endpoints:")
    print("  - POST /tools/get_current_weather_tool/invoke")
    print("  - POST /tools/get_weather_forecast_tool/invoke")
    print("  - POST /tools/search_locations_tool/invoke")
    print("  - POST /tools/get_live_temp/invoke")
    print("  - GET /health")
    print("  - GET /")
    
    app.run(host='0.0.0.0', port=8000, debug=True)
