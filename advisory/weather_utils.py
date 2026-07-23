import requests

API_KEY = "05837f62afa880aa9c2b90ef1b987f48"

def fetch_weather(lat, lon):
    # TEMPORARY — remove when API key activates
    return {
        "temperature": 35.0,
        "humidity": 87,
        "rainfall": 12.4,
    }
    
# def fetch_weather(lat, lon):
#     url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}"
    
#     try:
#         response = requests.get(url, timeout=5)
#         data = response.json()

#         if "main" not in data:
#             raise Exception(f"API error: {data.get('message', 'unknown error')}")

#         return {
#             "temperature": convert_kelvin_to_celsius(data["main"]["temp"]),
#             "humidity": data["main"]["humidity"],
#             "rainfall": extract_rainfall(data),
#         }
#     except Exception as e:
#         raise Exception(f"Weather fetch failed: {str(e)}")

def convert_kelvin_to_celsius(k):
    return round(k - 273.15, 1)

def extract_rainfall(data):
    return data.get("rain", {}).get("1h", 0.0)

def categorize_rainfall(mm):
    if mm < 5:
        return "low"
    elif mm <= 50:
        return "moderate"
    else:
        return "high"
    
    