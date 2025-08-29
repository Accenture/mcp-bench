import requests

API_KEY = "366fd563131a4af1bd962603252105"

def getliveTemp(city: str):
    url = f"http://api.weatherapi.com/v1/current.json?key={API_KEY}&q={city}&lang=tr"
    response = requests.get(url)
    if response.status_code != 200:
        return {"error": "API'den veri alınamadı"}
    data = response.json()
    # İstediğin bilgileri buradan çekebilirsin
    return {
        "city": data.get("location", {}).get("name"),
        "country": data.get("location", {}).get("country"),
        "weather": data.get("current", {}).get("condition", {}).get("text"),
        "temperature_c": data.get("current", {}).get("temp_c"),
        "feelslike_c": data.get("current", {}).get("feelslike_c"),
        "icon": data.get("current", {}).get("condition", {}).get("icon"),
    }