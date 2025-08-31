# 🌤️ WeatherAPI MCP Server

A Model Context Protocol (MCP) server that provides access to current weather data and forecasts using WeatherAPI.com.

## 🚀 Features

- **Current Weather**: Get real-time weather data for any city worldwide
- **Weather Forecasts**: Get weather predictions for up to 10 days
- **Location Search**: Search for locations by name with autocomplete
- **Multi-language Support**: Weather descriptions in 10+ languages
- **Comprehensive Data**: Temperature, humidity, wind, pressure, UV index, visibility
- **Error Handling**: Robust error handling and timeout management

## 📦 Installation

### For Smithery Deployment

1. **Get WeatherAPI Key**:
   - Sign up at [WeatherAPI.com](https://www.weatherapi.com/)
   - Get your free API key

2. **Deploy to Smithery**:
   - Upload this MCP package to Smithery
   - Configure with your WeatherAPI key
   - Start using the weather tools

### For Local Development

1. **Clone and Setup**:
   ```bash
   cd weather-mcp
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your WeatherAPI key
   ```

3. **Run Server**:
   ```bash
   python server.py
   ```

## 🛠️ Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `WEATHER_API_KEY` | Your WeatherAPI.com API key | - | ✅ |
| `API_LANGUAGE` | Language for weather descriptions | `tr` | ❌ |
| `API_TIMEOUT` | Request timeout in seconds | `10` | ❌ |

### Supported Languages

- `tr` - Turkish (Default)
- `en` - English
- `es` - Spanish
- `fr` - French
- `de` - German
- `it` - Italian
- `pt` - Portuguese
- `ru` - Russian
- `zh` - Chinese
- `ja` - Japanese

## 🔧 Available Tools

### 1. `get_current_weather_tool`

Get current weather information for a specific city.

**Parameters:**
- `city` (string, required): Name of the city

**Example:**
```json
{
  "city": "Istanbul"
}
```

**Response:**
```json
{
  "city": "Istanbul",
  "country": "Turkey",
  "temperature_c": 25.0,
  "weather": "Güneşli",
  "humidity": 65,
  "wind_kph": 15.5,
  "pressure_mb": 1013.0,
  "uv_index": 6
}
```

### 2. `get_weather_forecast_tool`

Get weather forecast for a specific city.

**Parameters:**
- `city` (string, required): Name of the city
- `days` (integer, optional): Number of days (1-10, default: 3)

**Example:**
```json
{
  "city": "London",
  "days": 5
}
```

### 3. `search_locations_tool`

Search for locations by name.

**Parameters:**
- `query` (string, required): Location name or partial name

**Example:**
```json
{
  "query": "New York"
}
```

## 📊 Data Sources

This MCP server uses [WeatherAPI.com](https://www.weatherapi.com/) which provides:

- **Global Coverage**: Weather data for cities worldwide
- **Real-time Data**: Current weather conditions updated frequently
- **Accurate Forecasts**: Weather predictions up to 10 days ahead
- **Detailed Information**: Comprehensive weather metrics
- **Reliable Service**: 99.9% uptime with fast response times

## 🔒 Security

- API keys are handled securely through environment variables
- No sensitive data is logged or stored
- All API requests use HTTPS
- Rate limiting is handled automatically

## 🧪 Testing

### Local Testing

```bash
# Test current weather
curl -X POST http://localhost:8000/tools/get_current_weather_tool/invoke \
  -H "Content-Type: application/json" \
  -d '{"input": {"city": "Istanbul"}}'

# Test forecast
curl -X POST http://localhost:8000/tools/get_weather_forecast_tool/invoke \
  -H "Content-Type: application/json" \
  -d '{"input": {"city": "London", "days": 3}}'
```

### Integration Testing

```bash
python test_integration.py
```

## 🌍 Example Use Cases

### 1. Travel Planning
```
get_weather_forecast_tool(city="Paris", days=7)
```
Get a week's weather forecast for your destination.

### 2. Daily Weather Check
```
get_current_weather_tool(city="Istanbul")
```
Check current conditions before heading out.

### 3. Location Discovery
```
search_locations_tool(query="San Francisco")
```
Find the exact location name for weather queries.

### 4. Agricultural Planning
```
get_weather_forecast_tool(city="Ankara", days=5)
```
Get detailed weather data including humidity and UV index.

## 📝 Changelog

### v1.0.0
- Initial release
- Current weather data
- Weather forecasts (up to 10 days)
- Location search
- Multi-language support
- Smithery deployment ready

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

- **Documentation**: Check this README and inline code comments
- **Issues**: Report bugs and feature requests on GitHub
- **WeatherAPI**: Visit [WeatherAPI.com](https://www.weatherapi.com/) for API documentation

## 🙏 Acknowledgments

- [WeatherAPI.com](https://www.weatherapi.com/) for providing reliable weather data
- [FastMCP](https://github.com/jlowin/fastmcp) for the MCP framework
- [Smithery](https://smithery.ai/) for MCP deployment platform
