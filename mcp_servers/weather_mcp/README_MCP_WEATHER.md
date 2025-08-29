# WeatherAPI MCP Server & Weather Agent Integration

This project implements a Model Context Protocol (MCP) server using WeatherAPI and integrates it with a Mastra-based weather agent.

## 🌟 Features

### MCP Server (`server.py`)
- **Current Weather**: Get real-time weather data for any city
- **Weather Forecast**: Get weather predictions for up to 10 days
- **Location Search**: Search for locations by name
- **Comprehensive Data**: Temperature, humidity, wind, pressure, UV index, visibility
- **Error Handling**: Robust error handling and timeout management
- **Backward Compatibility**: Legacy tool support

### Weather Agent (`weather_agent/`)
- **Mastra Framework**: Built on the Mastra agent framework
- **Dual Tools**: Current weather and forecast capabilities
- **Natural Language**: Conversational interface for weather queries
- **Memory**: Persistent conversation memory
- **OpenAI Integration**: Uses GPT-4o-mini for natural responses

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies for the weather agent
cd weather_agent/my-mastra-app
npm install
cd ../..
```

### 2. Start the MCP Server

```bash
python server.py
```

The server will start on `http://localhost:8000`

### 3. Test the MCP Server

```bash
python test_mcp_server.py
```

### 4. Start the Weather Agent

```bash
cd weather_agent/my-mastra-app
npm run dev
```

## 🔧 Configuration

### API Key
The WeatherAPI key is configured in both:
- `server.py` (line 7): `API_KEY = "366fd563131a4af1bd962603252105"`
- `app.py` (line 3): `API_KEY = "366fd563131a4af1bd962603252105"`

### MCP Server URL
The weather agent connects to the MCP server at `http://localhost:8000`. This is configured in:
- `weather_agent/my-mastra-app/src/mastra/tools/weather-tool.ts`

## 📡 MCP Server API

### Available Tools

#### 1. `get_current_weather_tool`
Get current weather for a city.

**Input:**
```json
{
  "input": {
    "city": "Istanbul"
  }
}
```

**Output:**
```json
{
  "output": {
    "city": "Istanbul",
    "country": "Turkey",
    "temperature_c": 15.0,
    "weather": "Partly cloudy",
    "humidity": 65,
    "wind_kph": 10.8,
    "pressure_mb": 1013.0,
    "uv_index": 4
  }
}
```

#### 2. `get_weather_forecast_tool`
Get weather forecast for a city.

**Input:**
```json
{
  "input": {
    "city": "Istanbul",
    "days": 3
  }
}
```

#### 3. `search_locations_tool`
Search for locations by name.

**Input:**
```json
{
  "input": {
    "query": "Istanbul"
  }
}
```

#### 4. `get_live_temp` (Legacy)
Backward compatibility tool.

## 🏗️ Architecture

```
┌─────────────────┐    HTTP/JSON    ┌─────────────────┐
│   Weather Agent │ ──────────────► │   MCP Server    │
│   (Mastra)      │                 │   (FastMCP)     │
└─────────────────┘                 └─────────────────┘
                                             │
                                             │ HTTPS/JSON
                                             ▼
                                    ┌─────────────────┐
                                    │   WeatherAPI    │
                                    │   (External)    │
                                    └─────────────────┘
```

## 🧪 Testing

### Manual Testing
1. Start the MCP server: `python server.py`
2. Run the test script: `python test_mcp_server.py`
3. Check the output for successful API calls

### Integration Testing
1. Start both the MCP server and the weather agent
2. Interact with the weather agent through the Mastra interface
3. Verify that weather data is retrieved correctly

## 🔍 Troubleshooting

### Common Issues

1. **MCP Server Connection Failed**
   - Ensure the MCP server is running on port 8000
   - Check firewall settings
   - Verify the server URL in the weather tool

2. **WeatherAPI Errors**
   - Verify the API key is valid
   - Check API quota limits
   - Ensure internet connectivity

3. **Weather Agent Issues**
   - Ensure all npm dependencies are installed
   - Check Node.js version (>=20.9.0 required)
   - Verify Mastra configuration

### Debug Mode
Enable debug logging by modifying the server startup:

```python
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG)
    print("Starting WeatherAPI MCP Server...")
    mcp.run(transport="http", port=8000)
```

## 📝 Development Notes

- The MCP server uses FastMCP for easy tool definition and HTTP transport
- The weather agent uses Mastra's tool system for seamless integration
- All weather data is sourced from WeatherAPI.com
- The system supports both current weather and multi-day forecasts
- Error handling is implemented at both the MCP and agent levels

## 🔗 Related Files

- `server.py` - Main MCP server implementation
- `app.py` - Original weather function (legacy)
- `weather_agent/my-mastra-app/src/mastra/tools/weather-tool.ts` - Weather tools for Mastra
- `weather_agent/my-mastra-app/src/mastra/agents/weather-agent.ts` - Weather agent configuration
- `test_mcp_server.py` - MCP server testing script
- `requirements.txt` - Python dependencies
