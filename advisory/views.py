import sys
import os
import json
import random

from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from .advisory_engine import get_advisory_with_soil, get_advisory
from .soil_service import get_clay_content, classify_soil_from_clay, get_soil_interpretation

from .models import (
    District,
    Crop,
    FarmerProfile,
    CropRule,
    WeatherData,
    Advisory,
)

from .weather_utils import fetch_weather


BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

sys.path.insert(0, BASE_DIR)


try:
    from bert_bot.advisor import AgricultureAdvisor

    ADVISOR = AgricultureAdvisor(
        api_key=os.environ.get(
            "OPENWEATHERMAP_API_KEY",
            ""
        )
    )

    BERT_READY = True

    print(
        "BERT Agriculture Advisor loaded successfully"
    )

except Exception as e:
    ADVISOR = None
    BERT_READY = False

    print(
        f"BERT Agriculture Advisor load failed: {e}"
    )


def generate_farmer_id():
    while True:
        farmer_id = (
            f"FARM-2026-{random.randint(1000, 9999)}"
        )

        if not FarmerProfile.objects.filter(
            farmer_id=farmer_id
        ).exists():
            return farmer_id


def home(request):
    return render(
        request,
        "advisory/home.html",
        {
            "districts": District.objects.all(),
            "crops": Crop.objects.all(),
        }
    )


def register_view(request):

    if request.user.is_authenticated:
        return redirect("/dashboard/")

    if request.method == "POST":

        full_name = request.POST.get(
            "full_name",
            ""
        ).strip()

        phone = request.POST.get(
            "phone",
            ""
        ).strip()

        district_id = request.POST.get(
            "district"
        )

        village = request.POST.get(
            "village",
            ""
        ).strip()

        field_area = request.POST.get(
            "field_area",
            0
        )

        soil_type = request.POST.get(
            "soil_type"
        )

        crop_id = request.POST.get(
            "primary_crop"
        )

        password = request.POST.get(
            "password"
        )

        password_confirmation = request.POST.get(
            "password_confirmation"
        )

        if not full_name or not phone or not password:
            return render(
                request,
                "advisory/register.html",
                {
                    "districts": District.objects.all(),
                    "crops": Crop.objects.all(),
                    "error": (
                        "Please fill in all required fields."
                    ),
                }
            )

        if not phone.isdigit() or len(phone) != 10:
            return render(
                request,
                "advisory/register.html",
                {
                    "districts": District.objects.all(),
                    "crops": Crop.objects.all(),
                    "error": (
                        "Phone number must be exactly 10 digits."
                    ),
                }
            )

        if password_confirmation is not None:
            if password != password_confirmation:
                return render(
                    request,
                    "advisory/register.html",
                    {
                        "districts": District.objects.all(),
                        "crops": Crop.objects.all(),
                        "error": (
                            "Passwords do not match."
                        ),
                    }
                )

        if FarmerProfile.objects.filter(
            phone=phone
        ).exists():

            return render(
                request,
                "advisory/register.html",
                {
                    "districts": District.objects.all(),
                    "crops": Crop.objects.all(),
                    "error": (
                        "This phone number is already registered."
                    ),
                }
            )

        if User.objects.filter(
            username=phone
        ).exists():

            return render(
                request,
                "advisory/register.html",
                {
                    "districts": District.objects.all(),
                    "crops": Crop.objects.all(),
                    "error": (
                        "This phone number is already registered."
                    ),
                }
            )

        try:
            district = District.objects.get(
                id=district_id
            )

            crop = Crop.objects.get(
                id=crop_id
            )

        except (
            District.DoesNotExist,
            Crop.DoesNotExist
        ):

            return render(
                request,
                "advisory/register.html",
                {
                    "districts": District.objects.all(),
                    "crops": Crop.objects.all(),
                    "error": (
                        "Invalid district or crop selected."
                    ),
                }
            )

        names = full_name.split(
            " ",
            1
        )

        first_name = names[0]

        last_name = (
            names[1]
            if len(names) > 1
            else ""
        )

        user = User.objects.create_user(
            username=phone,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        farmer_id = generate_farmer_id()

        FarmerProfile.objects.create(
            user=user,
            farmer_id=farmer_id,
            phone=phone,
            district=district,
            village=village,
            field_area=field_area,
            soil_type=soil_type,
            primary_crop=crop,
        )

        login(
            request,
            user
        )

        request.session["chat_history"] = []
        request.session.modified = True

        return redirect("/dashboard/")

    return render(
        request,
        "advisory/register.html",
        {
            "districts": District.objects.all(),
            "crops": Crop.objects.all(),
        }
    )


def login_view(request):

    if request.user.is_authenticated:
        return redirect("/dashboard/")

    if request.method == "POST":

        phone = request.POST.get(
            "phone",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        user = authenticate(
            request,
            username=phone,
            password=password
        )

        if user is not None:

            login(
                request,
                user
            )

            if "chat_history" not in request.session:
                request.session["chat_history"] = []

            request.session.modified = True

            return redirect("/dashboard/")

        return render(
            request,
            "advisory/login.html",
            {
                "error": (
                    "Invalid phone number or password."
                )
            }
        )

    return render(
        request,
        "advisory/login.html"
    )


@login_required(login_url="/login/")
def logout_view(request):

    logout(request)

    return redirect("/")


@login_required(login_url="/login/")
def dashboard_view(request):

    try:
        profile = FarmerProfile.objects.get(
            user=request.user
        )

        weather = fetch_weather(
            profile.district.latitude,
            profile.district.longitude
        )

        advisory = get_advisory(
            profile.primary_crop.name,
            weather
        )

    except Exception as e:

        try:
            profile = FarmerProfile.objects.get(
                user=request.user
            )

        except FarmerProfile.DoesNotExist:
            profile = None

        weather = {
            "temperature": "--",
            "humidity": "--",
            "rainfall": "--",
        }

        advisory = {
            "suitability": "unknown",
            "recommendations": [
                "Could not fetch weather data."
            ],
        }

        print(
            f"Dashboard error: {e}"
        )
        
        # Get real soil data from clay.tif
        soil_data = None
        soil_interpretation = None
        if profile.district:
            soil_data = get_clay_content(
                profile.district.latitude,
                profile.district.longitude
            )
            if soil_data and soil_data.get("available"):
                soil_interpretation = get_soil_interpretation(
                    soil_data["clay_percent"]
                )

    return render(
        request,
        "advisory/dashboard.html",
        {
            "profile": profile,
            "weather": weather,
            "advisory": advisory,
            "soil_data": soil_data,
            "soil_interpretation": soil_interpretation,
        }
    )


@login_required(login_url="/login/")
def quick_advisory_view(request):

    profile = FarmerProfile.objects.get(
        user=request.user
    )

    districts = District.objects.all()
    crops = Crop.objects.all()

    weather = None
    advisory = None

    selected_district = None
    selected_crop = None

    if request.method == "POST":

        district_name = request.POST.get(
            "district"
        )

        crop_name = request.POST.get(
            "crop"
        )

        try:
            selected_district = District.objects.get(
                name=district_name
            )

            selected_crop = Crop.objects.get(
                name=crop_name
            )

            weather = fetch_weather(
                selected_district.latitude,
                selected_district.longitude
            )

            advisory = get_advisory(
                crop_name,
                weather
            )

        except Exception as e:

            advisory = {
                "suitability": "error",
                "recommendations": [
                    str(e)
                ],
            }

    return render(
        request,
        "advisory/quick_advisory.html",
        {
            "profile": profile,
            "districts": districts,
            "crops": crops,
            "weather": weather,
            "advisory": advisory,
            "selected_district": selected_district,
            "selected_crop": selected_crop,
        }
    )


@login_required(login_url="/login/")
def more_options_view(request):

    profile = FarmerProfile.objects.get(
        user=request.user
    )

    return render(
        request,
        "advisory/more_options.html",
        {
            "profile": profile
        }
    )


def results(request):

    if request.method == "POST":
        district_name = request.POST.get("district")
        crop_name = request.POST.get("crop")
        try:
            district = District.objects.get(name=district_name)
            crop = Crop.objects.get(name=crop_name)
            weather = fetch_weather(district.latitude, district.longitude)

            # Get real soil data from clay.tif
            clay_data = get_clay_content(district.latitude, district.longitude)
            clay_percent = None
            if clay_data and clay_data.get("available"):
                clay_percent = clay_data["clay_percent"]

            # Enhanced advisory with soil data
            advisory = get_advisory_with_soil(crop_name, weather, clay_percent)

            return render(request, "advisory/results.html", {
                "district": district,
                "crop": crop,
                "weather": weather,
                "advisory": advisory,
                "clay_data": clay_data,
            })
        except Exception as e:
            return render(request, "advisory/home.html", {
                "districts": District.objects.all(),
                "crops": Crop.objects.all(),
                "error": str(e),
            })

    return redirect("/")


def about_view(request):

    return render(
        request,
        "advisory/about.html"
    )


def dashboard_redirect(request):

    return redirect("/dashboard/")


def weather_data_view(request):

    return render(
        request,
        "advisory/weather_data.html"
    )


def chatbot_message(request):

    if request.method != "POST":

        return JsonResponse(
            {
                "error": "Method not allowed"
            },
            status=405
        )

    try:

        data = json.loads(
            request.body
        )

        user_message = data.get(
            "message",
            ""
        ).strip()

        if not user_message:

            return JsonResponse(
                {
                    "reply": "Please type a question."
                }
            )

        if not BERT_READY or ADVISOR is None:

            return JsonResponse(
                {
                    "reply": (
                        "The agriculture AI assistant "
                        "is still loading. Please try again."
                    )
                }
            )

        history = request.session.get(
            "chat_history",
            []
        )

        result = ADVISOR.ask(
            user_message,
            history=history
        )

        if isinstance(result, str):

            result = {
                "answer": result,
                "confidence": 1.0,
                "matched": "",
                "source": "assistant",
                "district": "",
                "crop": "",
            }

        answer = result.get(
            "answer",
            "Sorry, I could not generate an answer."
        )

        confidence = result.get(
            "confidence",
            0.0
        )

        history.append(
            {
                "question": user_message,
                "answer": answer,
                "confidence": confidence,
            }
        )

        request.session["chat_history"] = history[-20:]
        request.session.modified = True

        return JsonResponse(
            {
                "reply": answer,
                "confidence": confidence,
                "source": result.get(
                    "source",
                    ""
                ),
                "district": result.get(
                    "district",
                    ""
                ),
                "crop": result.get(
                    "crop",
                    ""
                ),
            }
        )

    except Exception as e:

        print(
            f"Chatbot error: {e}"
        )

        import traceback

        traceback.print_exc()

        return JsonResponse(
            {
                "reply": (
                    "Sorry, an error occurred "
                    "while processing your question."
                ),
                "error": str(e),
            },
            status=500
        )


@login_required(login_url="/login/")
def chatbot_history(request):

    history = request.session.get(
        "chat_history",
        []
    )

    return JsonResponse(
        {
            "history": history
        }
    )


@login_required(login_url="/login/")
def chatbot_clear_history(request):

    if request.method != "POST":

        return JsonResponse(
            {
                "error": "Method not allowed"
            },
            status=405
        )

    request.session["chat_history"] = []
    request.session.modified = True

    return JsonResponse(
        {
            "success": True
        }
    )
    
from .services import (
    fetch_current_weather, fetch_forecast,
    get_crop_price, generate_notifications,
    get_dashboard_headline, get_soil_care,
    get_sowing_harvesting_advice
)
from .models import FarmerProfile, FarmerCrop, Crop, District


@login_required(login_url="/login/")
def dashboard_view(request):
    profile = FarmerProfile.objects.select_related(
        'user', 'district', 'primary_crop'
    ).get(user=request.user)

    farm_crops = FarmerCrop.objects.filter(
        farmer=profile
    ).select_related('crop').order_by('-added_at')

    all_crops = Crop.objects.all()
    added_crop_ids = set(fc.crop_id for fc in farm_crops if fc.status == 'active')
    not_added_crops = all_crops.exclude(id__in=added_crop_ids)
    # Also exclude primary crop from "not added"
    if profile.primary_crop:
        not_added_crops = not_added_crops.exclude(id=profile.primary_crop_id)

    weather = None
    forecast = None
    if profile.district:
        weather = fetch_current_weather(
            profile.district.latitude,
            profile.district.longitude,
            profile.district.name
        )
        forecast = fetch_forecast(
            profile.district.latitude,
            profile.district.longitude
        )

    notifications = generate_notifications(profile, weather, farm_crops)
    headline, headline_type = get_dashboard_headline(weather, profile, farm_crops)
    soil_care = get_soil_care(profile.soil_type, weather)

    # Prices for active crops
    prices = {}
    active_crops = [fc.crop for fc in farm_crops if fc.status == 'active']
    if profile.primary_crop and profile.primary_crop not in active_crops:
        active_crops.insert(0, profile.primary_crop)
    for crop in active_crops:
        price = get_crop_price(crop.name, profile.district.name if profile.district else "")
        if price:
            prices[crop.name] = price

    # Sowing/harvesting advice per active crop
    sow_harvest = {}
    for crop in active_crops:
        advice = get_sowing_harvesting_advice(crop.name, weather)
        if advice:
            sow_harvest[crop.name] = advice

    return render(request, "advisory/dashboard.html", {
        "profile": profile,
        "farm_crops": farm_crops,
        "not_added_crops": not_added_crops,
        "all_crops": all_crops,
        "weather": weather,
        "forecast": forecast,
        "notifications": notifications,
        "headline": headline,
        "headline_type": headline_type,
        "soil_care": soil_care,
        "prices": prices,
        "sow_harvest": sow_harvest,
        "active_crops": active_crops,
    })


@login_required(login_url="/login/")
@require_POST
def add_farm_crop(request):
    """AJAX: Add a crop to farmer's farm_crops."""
    try:
        data = json.loads(request.body)
        crop_id = data.get("crop_id")
        crop = Crop.objects.get(id=crop_id)
        profile = FarmerProfile.objects.get(user=request.user)

        # Don't duplicate active crops
        existing = FarmerCrop.objects.filter(
            farmer=profile, crop=crop, status='active'
        ).first()
        if existing:
            return JsonResponse({"ok": False, "error": "Crop already active on your farm."})

        FarmerCrop.objects.create(farmer=profile, crop=crop, status='active')
        return JsonResponse({"ok": True, "crop_name": crop.name, "crop_id": crop.id})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)})


@login_required(login_url="/login/")
@require_POST
def remove_farm_crop(request):
    """AJAX: Remove/cancel/mark-harvested a farm crop."""
    try:
        data = json.loads(request.body)
        farm_crop_id = data.get("farm_crop_id")
        action = data.get("action", "cancelled")  # cancelled | completed
        fc = FarmerCrop.objects.get(id=farm_crop_id, farmer__user=request.user)
        fc.status = action
        fc.save()
        return JsonResponse({"ok": True})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)})


@login_required(login_url="/login/")
def weather_forecast_view(request):
    """7-day forecast page."""
    profile = FarmerProfile.objects.select_related('district').get(user=request.user)
    forecast = None
    weather = None
    if profile.district:
        weather = fetch_current_weather(
            profile.district.latitude, profile.district.longitude
        )
        forecast = fetch_forecast(
            profile.district.latitude, profile.district.longitude
        )
    return render(request, "advisory/weather_forecast.html", {
        "profile": profile,
        "weather": weather,
        "forecast": forecast,
    })