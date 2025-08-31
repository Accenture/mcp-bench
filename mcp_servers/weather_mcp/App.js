import React, { useState } from 'react';
import { SafeAreaView, TextInput, TouchableOpacity, Text, StyleSheet, View, ScrollView, ActivityIndicator } from 'react-native';

export default function App() {
  const [city, setCity] = useState('');
  const [weatherData, setWeatherData] = useState(null);
  const [forecastData, setForecastData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const MCP_SERVER_URL = 'http://10.0.2.2:8000'; // Android emulator için localhost

  const getWeather = async () => {
    if (!city.trim()) {
      setError('Lütfen bir şehir adı girin.');
      return;
    }

    setLoading(true);
    setError('');
    setWeatherData(null);
    setForecastData(null);

    try {
      // Mevcut hava durumunu al
      const currentResponse = await fetch(`${MCP_SERVER_URL}/tools/get_current_weather_tool/invoke`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          input: { city: city.trim() }
        })
      });

      if (!currentResponse.ok) {
        throw new Error(`Sunucu hatası: ${currentResponse.status}`);
      }

      const currentData = await currentResponse.json();
      const weather = currentData.output;

      if (weather.error) {
        throw new Error(weather.error);
      }

      setWeatherData(weather);

      // Tahmin verilerini al
      try {
        const forecastResponse = await fetch(`${MCP_SERVER_URL}/tools/get_weather_forecast_tool/invoke`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            input: { city: city.trim(), days: 3 }
          })
        });

        if (forecastResponse.ok) {
          const forecastResult = await forecastResponse.json();
          if (forecastResult.output && !forecastResult.output.error) {
            setForecastData(forecastResult.output);
          }
        }
      } catch (forecastError) {
        console.warn('Tahmin verileri alınamadı:', forecastError);
      }

    } catch (e) {
      setError(e.message || 'Bir hata oluştu.');
    }
    setLoading(false);
  };

  const getWeatherEmoji = (condition) => {
    if (!condition) return '🌤️';

    const conditionLower = condition.toLowerCase();
    if (conditionLower.includes('güneş') || conditionLower.includes('açık') || conditionLower.includes('sunny')) return '☀️';
    if (conditionLower.includes('bulut') || conditionLower.includes('cloud')) return '☁️';
    if (conditionLower.includes('yağmur') || conditionLower.includes('rain')) return '🌧️';
    if (conditionLower.includes('kar') || conditionLower.includes('snow')) return '❄️';
    if (conditionLower.includes('fırtına') || conditionLower.includes('storm')) return '⛈️';
    if (conditionLower.includes('sis') || conditionLower.includes('fog')) return '🌫️';
    return '🌤️';
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContainer}>
        <Text style={styles.appTitle}>🌤️ Hava Durumu</Text>

        <View style={styles.searchContainer}>
          <TextInput
            style={styles.input}
            value={city}
            onChangeText={setCity}
            placeholder="Şehir adı girin (örn: Istanbul, Ankara)"
            placeholderTextColor="#666"
          />
          <TouchableOpacity
            style={[styles.button, loading && styles.buttonDisabled]}
            onPress={getWeather}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.buttonText}>🔍 Hava Durumunu Getir</Text>
            )}
          </TouchableOpacity>
        </View>

        {error ? (
          <View style={styles.errorContainer}>
            <Text style={styles.errorText}>❌ {error}</Text>
          </View>
        ) : null}

        {weatherData ? (
          <View style={styles.weatherContainer}>
            <Text style={styles.locationText}>
              {weatherData.city}{weatherData.country ? `, ${weatherData.country}` : ''}
            </Text>
            <Text style={styles.conditionText}>{weatherData.weather}</Text>

            <View style={styles.mainWeather}>
              <Text style={styles.weatherIcon}>{getWeatherEmoji(weatherData.weather)}</Text>
              <Text style={styles.temperature}>{weatherData.temperature_c}°C</Text>
            </View>

            <View style={styles.detailsContainer}>
              <View style={styles.detailItem}>
                <Text style={styles.detailLabel}>Hissedilen</Text>
                <Text style={styles.detailValue}>{weatherData.feelslike_c}°C</Text>
              </View>
              <View style={styles.detailItem}>
                <Text style={styles.detailLabel}>Nem</Text>
                <Text style={styles.detailValue}>{weatherData.humidity}%</Text>
              </View>
              <View style={styles.detailItem}>
                <Text style={styles.detailLabel}>Rüzgar</Text>
                <Text style={styles.detailValue}>{weatherData.wind_kph} km/h</Text>
              </View>
              <View style={styles.detailItem}>
                <Text style={styles.detailLabel}>Basınç</Text>
                <Text style={styles.detailValue}>{weatherData.pressure_mb} mb</Text>
              </View>
              <View style={styles.detailItem}>
                <Text style={styles.detailLabel}>Görüş</Text>
                <Text style={styles.detailValue}>{weatherData.visibility_km} km</Text>
              </View>
              <View style={styles.detailItem}>
                <Text style={styles.detailLabel}>UV İndeksi</Text>
                <Text style={styles.detailValue}>{weatherData.uv_index}</Text>
              </View>
            </View>
          </View>
        ) : null}

        {forecastData && forecastData.forecast ? (
          <View style={styles.forecastContainer}>
            <Text style={styles.forecastTitle}>📅 3 Günlük Tahmin</Text>
            <View style={styles.forecastDays}>
              {forecastData.forecast.slice(0, 3).map((day, index) => {
                const date = new Date(day.date);
                const dayName = date.toLocaleDateString('tr-TR', { weekday: 'short' });

                return (
                  <View key={index} style={styles.forecastDay}>
                    <Text style={styles.forecastDate}>{dayName}</Text>
                    <Text style={styles.forecastTemps}>
                      {day.max_temp_c}° / {day.min_temp_c}°
                    </Text>
                    <Text style={styles.forecastCondition}>{day.condition}</Text>
                  </View>
                );
              })}
            </View>
          </View>
        ) : null}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f0f8ff',
  },
  scrollContainer: {
    flexGrow: 1,
    padding: 20,
  },
  appTitle: {
    fontSize: 32,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 30,
    color: '#2c3e50',
  },
  searchContainer: {
    marginBottom: 20,
  },
  input: {
    borderWidth: 2,
    borderColor: '#74b9ff',
    borderRadius: 25,
    padding: 15,
    fontSize: 16,
    marginBottom: 15,
    backgroundColor: '#fff',
  },
  button: {
    backgroundColor: '#74b9ff',
    borderRadius: 25,
    padding: 15,
    alignItems: 'center',
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  errorContainer: {
    backgroundColor: '#ff7675',
    borderRadius: 15,
    padding: 15,
    marginBottom: 20,
  },
  errorText: {
    color: '#fff',
    fontSize: 16,
    textAlign: 'center',
  },
  weatherContainer: {
    backgroundColor: '#a8e6cf',
    borderRadius: 20,
    padding: 25,
    marginBottom: 20,
  },
  locationText: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 10,
    color: '#2d3436',
  },
  conditionText: {
    fontSize: 18,
    textAlign: 'center',
    marginBottom: 20,
    color: '#636e72',
  },
  mainWeather: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 25,
  },
  weatherIcon: {
    fontSize: 60,
    marginRight: 20,
  },
  temperature: {
    fontSize: 48,
    fontWeight: '300',
    color: '#2d3436',
  },
  detailsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  detailItem: {
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
    borderRadius: 10,
    padding: 15,
    width: '48%',
    marginBottom: 10,
    alignItems: 'center',
  },
  detailLabel: {
    fontSize: 12,
    color: '#636e72',
    marginBottom: 5,
  },
  detailValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2d3436',
  },
  forecastContainer: {
    backgroundColor: '#ddd6fe',
    borderRadius: 20,
    padding: 20,
  },
  forecastTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 15,
    color: '#2d3436',
  },
  forecastDays: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  forecastDay: {
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
    borderRadius: 10,
    padding: 15,
    flex: 1,
    marginHorizontal: 5,
    alignItems: 'center',
  },
  forecastDate: {
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 8,
    color: '#2d3436',
  },
  forecastTemps: {
    fontSize: 14,
    marginBottom: 5,
    color: '#2d3436',
  },
  forecastCondition: {
    fontSize: 12,
    textAlign: 'center',
    color: '#636e72',
  },
});