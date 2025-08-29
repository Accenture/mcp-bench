import express from 'express';
import { weatherAgent } from './mastra/agents/weather-agent';

const app = express();
const PORT = 3000;

app.get('/weather', async (req, res) => {
  const city = req.query.city as string;
  if (!city) return res.status(400).json({ error: 'Şehir adı gerekli.' });
  try {
    const result = await weatherAgent(city);
    res.json({ result });
  } catch (e) {
    res.status(500).json({ error: 'Agent hatası.' });
  }
});

app.listen(PORT, () => {
  console.log(`Agent API ${PORT} portunda çalışıyor.`);
}); 