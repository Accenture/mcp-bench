# 🌤️ Hava Durumu Uygulaması Kullanım Kılavuzu

Bu proje, WeatherAPI kullanarak MCP (Model Context Protocol) server ve weather agent entegrasyonu içerir.

## 🚀 Kurulum ve Çalıştırma

### 1. MCP Server'ı Başlatın

```bash
python simple_weather_server.py
```

Server `http://localhost:8000` adresinde çalışacak.

### 2. Web Uygulamasını Kullanın

`weather_web_app.html` dosyasını tarayıcınızda açın:

```
file:///c:/Users/guclh/Desktop/mcp/weather_web_app.html
```

**Özellikler:**
- 🔍 Şehir arama
- 🌡️ Anlık hava durumu
- 📅 3 günlük tahmin
- 💨 Detaylı bilgiler (nem, rüzgar, basınç, UV indeksi)
- 📱 Mobil uyumlu tasarım

### 3. React Native Uygulaması

`App.js` dosyası güncellenmiş React Native uygulamasını içerir:

**Özellikler:**
- 🎨 Modern UI tasarım
- 🌤️ Hava durumu ikonları
- 📊 Detaylı hava bilgileri
- 📅 Tahmin verileri
- ⚡ Hızlı ve responsive

## 🧪 Test Etme

### Otomatik Test
```bash
python test_integration.py
```

### Manuel Test
1. Web uygulamasını açın
2. "Istanbul", "Ankara", "London" gibi şehir isimleri deneyin
3. Türkçe ve İngilizce şehir isimleri çalışır

## 📡 API Endpoints

### Mevcut Hava Durumu
```bash
curl -X POST http://localhost:8000/tools/get_current_weather_tool/invoke \
  -H "Content-Type: application/json" \
  -d '{"input": {"city": "Istanbul"}}'
```

### Hava Tahmini
```bash
curl -X POST http://localhost:8000/tools/get_weather_forecast_tool/invoke \
  -H "Content-Type: application/json" \
  -d '{"input": {"city": "Istanbul", "days": 3}}'
```

### Konum Arama
```bash
curl -X POST http://localhost:8000/tools/search_locations_tool/invoke \
  -H "Content-Type: application/json" \
  -d '{"input": {"query": "Istanbul"}}'
```

## 🔧 Sorun Giderme

### "Failed to fetch" Hatası
- MCP server'ın çalıştığından emin olun
- CORS ayarları otomatik olarak yapılandırılmıştır
- Tarayıcı console'unu kontrol edin (F12)

### API Hatası
- WeatherAPI key'inin geçerli olduğundan emin olun
- İnternet bağlantınızı kontrol edin
- Şehir ismini doğru yazdığınızdan emin olun

### React Native Uygulaması
- Android emulator için `http://10.0.2.2:8000` kullanılır
- iOS simulator için `http://localhost:8000` kullanılır
- Gerçek cihazda IP adresini güncelleyin

## 📱 Desteklenen Platformlar

- ✅ Web Tarayıcıları (Chrome, Firefox, Safari, Edge)
- ✅ React Native (Android/iOS)
- ✅ Desktop uygulamaları
- ✅ API entegrasyonları

## 🌍 Desteklenen Şehirler

WeatherAPI global olarak çalışır:
- 🇹🇷 Türkiye: Istanbul, Ankara, İzmir, Antalya, Bursa
- 🇺🇸 ABD: New York, Los Angeles, Chicago, Miami
- 🇬🇧 İngiltere: London, Manchester, Birmingham
- 🇩🇪 Almanya: Berlin, Munich, Hamburg
- 🇫🇷 Fransa: Paris, Lyon, Marseille
- Ve daha fazlası...

## 🎯 Örnek Kullanım Senaryoları

### 1. Günlük Hava Kontrolü
```
Şehir: "Istanbul"
Sonuç: 25°C, Güneşli, %39 nem, 19 km/h rüzgar
```

### 2. Seyahat Planlaması
```
Şehir: "Paris"
3 günlük tahmin ile seyahat kararı
```

### 3. Tarım ve Açık Hava Etkinlikleri
```
UV indeksi, nem oranı, rüzgar hızı bilgileri
```

## 🔄 Güncellemeler

- ✅ MCP Server entegrasyonu
- ✅ CORS desteği
- ✅ Modern web UI
- ✅ React Native uyumluluğu
- ✅ Hata yönetimi
- ✅ Responsive tasarım

## 📞 Destek

Sorun yaşarsanız:
1. Server loglarını kontrol edin
2. Browser console'unu inceleyin
3. API key'inin geçerli olduğundan emin olun
4. İnternet bağlantınızı test edin

## 🎉 Başarılı Entegrasyon!

Artık WeatherAPI MCP server'ınız ve weather agent'ınız hazır! Web uygulaması ve React Native uygulaması ile hava durumu verilerini kolayca alabilirsiniz.
