import requests
import os

API_KEY = os.environ.get("OPENWEATHERMAP_API_KEY")

def fetch_weather(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        if "main" not in data:
            raise Exception(f"API error: {data.get('message', 'unknown')}")
        return {
            "temperature": round(data["main"]["temp"], 1),
            "humidity": data["main"]["humidity"],
            "rainfall": extract_rainfall(data),
            "condition": data["weather"][0]["description"].title(),
            "wind_speed": data["wind"]["speed"],
        }
    except requests.Timeout:
        raise Exception("Weather API timed out. Try again.")
    except requests.ConnectionError:
        raise Exception("No internet connection.")
    except Exception as e:
        raise Exception(f"Weather fetch failed: {str(e)}")

def convert_kelvin_to_celsius(k):
    return round(k - 273.15, 1)

def extract_rainfall(data):
    return data.get("rain", {}).get("1h", 0.0)

def categorize_rainfall(mm):
    if mm < 5: return "low"
    elif mm <= 50: return "moderate"
    else: return "high"