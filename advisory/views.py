import sys
import os
import json

from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.core.cache import cache
from .models import District, Crop, CropRule, WeatherData, Advisory
from .weather_utils import fetch_weather
from .advisory_engine import get_advisory


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

try:
    from bert_bot.advisor import AgricultureAdvisor
    ADVISOR = AgricultureAdvisor(
        data_path=os.path.join(
            BASE_DIR, 'bert_bot', 'agriculture_data.json'
        ),
        api_key=os.environ.get("OPENWEATHERMAP_API_KEY", "")
    )
    BERT_READY = True
    print("System loaded successfully")
except Exception as e:
    ADVISOR = None
    BERT_READY = False
    print(f"Load failed: {e}")
    
def home(request):
    return render(request, "advisory/home.html", {
        "districts": District.objects.all(),
        "crops": Crop.objects.all()
    })

def results(request):
    if request.method == "POST":
        district_name = request.POST.get("district")
        crop_name = request.POST.get("crop")
        try:
            district = District.objects.get(name=district_name)
            crop = Crop.objects.get(name=crop_name)
            weather = fetch_weather(district.latitude, district.longitude)
            advisory = get_advisory(crop_name, weather)
            return render(request, "advisory/results.html", {
                "district": district,
                "crop": crop,
                "weather": weather,
                "advisory": advisory,
            })
        except Exception as e:
            return render(request, "advisory/home.html", {
                "districts": District.objects.all(),
                "crops": Crop.objects.all(),
                "error": str(e),
            })
    return render(request, "advisory/home.html", {
        "districts": District.objects.all(),
        "crops": Crop.objects.all(),
    })

def login_view(request):
    if request.method == "POST":
        request.session['logged_in'] = True
        return redirect("/dashboard/")
    return render(request, "advisory/login.html")

def dashboard_view(request):
    if not request.session.get('logged_in'):
        return redirect("/login/")
    return render(request, "advisory/dashboard.html", {
        "farmer_name": "Ram Bahadur",
        "farmer_name_ne": "राम बहादुर",
        "district": "Chitwan",
        "ward": "4",
        "crop": "Rice (Dhan)",
        "temp": "32°C, Sunny",
        "humidity": "45%",
    })

def logout_view(request):
    request.session.flush()
    return redirect("/")

def weather_data_view(request):
    return render(request, "advisory/weather_data.html")

def register_view(request):
    return render(request, "advisory/register.html")

def about_view(request):
    return render(request, "advisory/about.html")

def chatbot_message(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("message", "").strip()

            if not user_message:
                return JsonResponse({"reply": "Please type a message."})

            if not BERT_READY or ADVISOR is None:
                return JsonResponse({
                    "reply": "System loading. Please try again."
                })

            # Get conversation history for context
            history = request.session.get("chat_history", [])

            # Ask with history
            result = ADVISOR.ask(user_message, history=history)

            # Save to session
            history.append({
                "question": user_message,
                "answer":   result["answer"],
                "confidence": result["confidence"]
            })
            request.session["chat_history"] = history[-20:]
            request.session.modified = True

            return JsonResponse({
                "reply":      result["answer"],
                "confidence": result["confidence"],
                "source":     result.get("source", ""),
                "district":   result.get("district", ""),
                "crop":       result.get("crop", "")
            })

        except Exception as e:
            print(f"Chatbot error: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                "reply": f"System error: {str(e)}"
            })

    return JsonResponse({"error": "Method not allowed"}, status=405)

def chatbot_history(request):
    history = request.session.get("chat_history", [])
    return JsonResponse({"history": history})

