import requests

API_KEY = "05837f62afa880aa9c2b90ef1b987f48"

def fetch_weather(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    
    response = requests.get(url, timeout=5)
    data = response.json()

    if "main" not in data:
        raise Exception(f"API error: {data.get('message', 'unknown error')}")

    return {
        "temperature": round(data["main"]["temp"], 1),
        "humidity": data["main"]["humidity"],
        "rainfall": extract_rainfall(data),
        "condition": data["weather"][0]["description"].title(),
        "wind_speed": data["wind"]["speed"],
    }

def extract_rainfall(data):
    return data.get("rain", {}).get("1h", 0.0)

def categorize_rainfall(mm):
    if mm < 5:
        return "low"
    elif mm <= 50:
        return "moderate"
    else:
        return "high"