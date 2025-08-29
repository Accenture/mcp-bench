import { createTool } from '@mastra/core/tools';
import { z } from 'zod';

interface WeatherAPIResponse {
  city?: string;
  country?: string;
  region?: string;
  weather?: string;
  temperature_c?: number;
  temperature_f?: number;
  feelslike_c?: number;
  feelslike_f?: number;
  humidity?: number;
  wind_kph?: number;
  wind_mph?: number;
  wind_dir?: string;
  pressure_mb?: number;
  visibility_km?: number;
  uv_index?: number;
  icon?: string;
  last_updated?: string;
  error?: string;
}

interface ForecastResponse {
  city?: string;
  country?: string;
  region?: string;
  forecast?: Array<{
    date: string;
    max_temp_c: number;
    min_temp_c: number;
    condition: string;
    icon: string;
    chance_of_rain: number;
    chance_of_snow: number;
  }>;
  error?: string;
}

export const weatherTool = createTool({
  id: 'get-weather',
  description: 'Get current weather for a location using WeatherAPI',
  inputSchema: z.object({
    location: z.string().describe('City name'),
  }),
  outputSchema: z.object({
    temperature: z.number(),
    feelsLike: z.number(),
    humidity: z.number(),
    windSpeed: z.number(),
    conditions: z.string(),
    location: z.string(),
    country: z.string().optional(),
    region: z.string().optional(),
    pressure: z.number().optional(),
    visibility: z.number().optional(),
    uvIndex: z.number().optional(),
    icon: z.string().optional(),
  }),
  execute: async ({ context }) => {
    return await getWeatherFromMCP(context.location);
  },
});

export const forecastTool = createTool({
  id: 'get-forecast',
  description: 'Get weather forecast for a location using WeatherAPI',
  inputSchema: z.object({
    location: z.string().describe('City name'),
    days: z.number().min(1).max(10).default(3).describe('Number of days to forecast'),
  }),
  outputSchema: z.object({
    location: z.string(),
    country: z.string().optional(),
    region: z.string().optional(),
    forecast: z.array(z.object({
      date: z.string(),
      maxTemp: z.number(),
      minTemp: z.number(),
      condition: z.string(),
      icon: z.string(),
      chanceOfRain: z.number(),
      chanceOfSnow: z.number(),
    })),
  }),
  execute: async ({ context }) => {
    return await getForecastFromMCP(context.location, context.days);
  },
});

const getWeatherFromMCP = async (location: string) => {
  try {
    const response = await fetch('http://localhost:8000/tools/get_current_weather_tool/invoke', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ input: { city: location } })
    });

    if (!response.ok) {
      throw new Error(`MCP server responded with status: ${response.status}`);
    }

    const data = await response.json();
    const weatherData = data.output || data;

    if (weatherData.error) {
      throw new Error(weatherData.error);
    }

    return {
      temperature: weatherData.temperature_c || 0,
      feelsLike: weatherData.feelslike_c || 0,
      humidity: weatherData.humidity || 0,
      windSpeed: weatherData.wind_kph || 0,
      conditions: weatherData.weather || 'Unknown',
      location: weatherData.city || location,
      country: weatherData.country,
      region: weatherData.region,
      pressure: weatherData.pressure_mb,
      visibility: weatherData.visibility_km,
      uvIndex: weatherData.uv_index,
      icon: weatherData.icon,
    };
  } catch (error) {
    console.error('Error fetching weather from MCP:', error);
    throw new Error(`Failed to get weather data: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
};

const getForecastFromMCP = async (location: string, days: number = 3) => {
  try {
    const response = await fetch('http://localhost:8000/tools/get_weather_forecast_tool/invoke', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ input: { city: location, days } })
    });

    if (!response.ok) {
      throw new Error(`MCP server responded with status: ${response.status}`);
    }

    const data = await response.json();
    const forecastData = data.output || data;

    if (forecastData.error) {
      throw new Error(forecastData.error);
    }

    return {
      location: forecastData.city || location,
      country: forecastData.country,
      region: forecastData.region,
      forecast: forecastData.forecast?.map((day: any) => ({
        date: day.date,
        maxTemp: day.max_temp_c,
        minTemp: day.min_temp_c,
        condition: day.condition,
        icon: day.icon,
        chanceOfRain: day.chance_of_rain,
        chanceOfSnow: day.chance_of_snow,
      })) || [],
    };
  } catch (error) {
    console.error('Error fetching forecast from MCP:', error);
    throw new Error(`Failed to get forecast data: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
};
