# 🚀 Smithery Deployment Guide

Bu kılavuz, WeatherAPI MCP'sini Smithery platformuna deploy etmek için gerekli adımları açıklar.

## 📋 Ön Gereksinimler

### 1. API Keys
- ✅ **WeatherAPI Key**: `366fd563131a4af1bd962603252105`
- ✅ **Smithery API Key**: `bbcaba83-59df-4878-ac95-4d75ad740977`

### 2. Gerekli Dosyalar
- ✅ `server.py` - Ana MCP server dosyası
- ✅ `requirements.txt` - Python bağımlılıkları
- ✅ `smithery.yaml` - Smithery konfigürasyonu
- ✅ `README.md` - Dokümantasyon
- ✅ `.env` - Environment variables
- ✅ `deploy.py` - Deployment script

## 🚀 Deployment Adımları

### Yöntem 1: Otomatik Deployment (Önerilen)

```bash
cd weather-mcp
python deploy.py
```

Bu script:
1. Environment variables'ları kontrol eder
2. Deployment package'ı oluşturur
3. Smithery'ye otomatik upload eder

### Yöntem 2: Manuel Deployment

1. **Package Oluştur**:
   ```bash
   zip -r weather-mcp.zip server.py requirements.txt smithery.yaml README.md .env.example
   ```

2. **Smithery Dashboard'a Git**:
   - https://smithery.ai/dashboard
   - API key ile giriş yap: `bbcaba83-59df-4878-ac95-4d75ad740977`

3. **MCP Upload Et**:
   - "New MCP" butonuna tıkla
   - `weather-mcp.zip` dosyasını upload et
   - Konfigürasyon ayarlarını yap

## ⚙️ Smithery Konfigürasyonu

Deployment sonrası Smithery dashboard'da şu ayarları yap:

### Environment Variables
```
WEATHER_API_KEY=366fd563131a4af1bd962603252105
API_LANGUAGE=tr
API_TIMEOUT=10
```

### MCP Settings
- **Name**: `weather-api-mcp`
- **Version**: `1.0.0`
- **Description**: `WeatherAPI MCP Server for current weather and forecasts`

## 🧪 Deployment Testi

### 1. Health Check
```bash
curl -X GET https://your-mcp-url.smithery.ai/health
```

### 2. Weather Test
```bash
curl -X POST https://your-mcp-url.smithery.ai/tools/get_current_weather_tool/invoke \
  -H "Content-Type: application/json" \
  -d '{"input": {"city": "Istanbul"}}'
```

### 3. Forecast Test
```bash
curl -X POST https://your-mcp-url.smithery.ai/tools/get_weather_forecast_tool/invoke \
  -H "Content-Type: application/json" \
  -d '{"input": {"city": "London", "days": 3}}'
```

## 📊 Monitoring

### Smithery Dashboard
- **Logs**: Real-time server logs
- **Metrics**: Request count, response times
- **Errors**: Error tracking and alerts
- **Usage**: API usage statistics

### Health Monitoring
```bash
# Check server status
curl https://your-mcp-url.smithery.ai/health

# Expected response:
{
  "status": "healthy",
  "service": "WeatherAPI MCP Server"
}
```

## 🔧 Troubleshooting

### Common Issues

#### 1. API Key Errors
```
Error: WEATHER_API_KEY environment variable is required
```
**Solution**: Smithery dashboard'da environment variables'ı kontrol et

#### 2. Network Timeouts
```
Error: API request failed: timeout
```
**Solution**: `API_TIMEOUT` değerini artır (default: 10 saniye)

#### 3. Invalid City Names
```
Error: Location 'XYZ' not found
```
**Solution**: `search_locations_tool` ile geçerli şehir isimlerini bul

### Debug Mode

Development için debug mode'u aktif et:
```
DEBUG=true
```

### Log Monitoring

Smithery dashboard'da real-time logları izle:
- Request/Response logları
- Error messages
- Performance metrics

## 🔄 Updates

### Version Update
1. Kodu güncelle
2. `smithery.yaml`'da version'ı artır
3. Yeniden deploy et:
   ```bash
   python deploy.py
   ```

### Configuration Update
- Smithery dashboard'dan environment variables'ı güncelle
- Restart gerekmez, otomatik olarak uygulanır

## 📈 Scaling

### Performance Optimization
- **Caching**: WeatherAPI responses cache'lenir
- **Rate Limiting**: Otomatik rate limiting
- **Load Balancing**: Smithery otomatik load balancing sağlar

### Usage Limits
- **WeatherAPI**: 1M requests/month (free tier)
- **Smithery**: Platform limitlerini kontrol et

## 🔒 Security

### API Key Security
- Environment variables güvenli şekilde saklanır
- API keys loglanmaz
- HTTPS zorunlu

### Access Control
- Smithery dashboard'dan access control ayarları
- IP whitelisting (opsiyonel)
- Rate limiting

## 📞 Support

### Smithery Support
- Dashboard: https://smithery.ai/dashboard
- Documentation: https://docs.smithery.ai
- Support: support@smithery.ai

### WeatherAPI Support
- Dashboard: https://www.weatherapi.com/my/
- Documentation: https://www.weatherapi.com/docs/
- Support: support@weatherapi.com

## ✅ Deployment Checklist

- [ ] WeatherAPI key alındı ve test edildi
- [ ] Smithery API key alındı
- [ ] Environment variables ayarlandı
- [ ] Kod test edildi (local)
- [ ] Deployment package oluşturuldu
- [ ] Smithery'ye upload edildi
- [ ] Konfigürasyon ayarları yapıldı
- [ ] Health check başarılı
- [ ] Weather tools test edildi
- [ ] Monitoring kuruldu
- [ ] Documentation güncellendi

## 🎉 Başarılı Deployment!

Deployment tamamlandıktan sonra:

1. **MCP URL'ini not al**: `https://your-mcp-url.smithery.ai`
2. **API documentation'ı paylaş**: README.md
3. **Monitoring'i aktif et**: Smithery dashboard
4. **Usage tracking'i başlat**: Analytics

Artık WeatherAPI MCP'niz Smithery'de live! 🌤️
