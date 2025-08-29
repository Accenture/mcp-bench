import { getWeatherFromMCP } from '../tools';

export async function weatherAgent(city: string) {
    const weather = await getWeatherFromMCP(city);
    return `Şehir: ${weather.city}, Hava Durumu: ${weather.weather}`;
} 