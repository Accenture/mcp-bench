import fetch from 'node-fetch';

export async function getWeatherFromMCP(city: string) {
    const response = await fetch('http://localhost:8000/tools/get_live_temp/invoke', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ input: { city } })
    });
    if (!response.ok) throw new Error('MCP servisinden veri alınamadı');
    const data = await response.json();
    // MCP'nin response formatına göre ayarla
    return data.output || data;
} 