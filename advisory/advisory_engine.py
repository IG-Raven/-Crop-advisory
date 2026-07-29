from .models import CropRule

def get_advisory(crop_name, weather):
    rules = CropRule.objects.filter(crop__name=crop_name)
    triggered = evaluate_rules(rules, weather)
    sorted_rules = sort_by_severity(triggered)
    return build_response(sorted_rules, weather, crop_name)

def evaluate_rules(rules, weather):
    triggered = []
    for rule in rules:
        value = weather.get(rule.parameter)
        if value is None:
            continue
        lower_ok = rule.min_value is None or value >= rule.min_value
        upper_ok = rule.max_value is None or value < rule.max_value
        if lower_ok and upper_ok:
            triggered.append(rule)
    return triggered

def sort_by_severity(triggered):
    order = {"unsuitable": 0, "warning": 1, "suitable": 2}
    return sorted(triggered, key=lambda r: order.get(r.severity, 3))

def build_response(sorted_rules, weather, crop_name):
    temp = weather.get("temperature", 0)
    rain = weather.get("rainfall", 0)
    humidity = weather.get("humidity", 0)

    if not sorted_rules:
        return {
            "suitability": "suitable",
            "recommendations": [
                f"Current conditions are normal for {crop_name} cultivation.",
                f"Temperature {temp}°C is within safe range. No immediate action required.",
                "Continue regular irrigation and field monitoring schedule.",
                "Check your crops for any early signs of pest or disease as a routine precaution.",
            ]
        }

    top_severity = sorted_rules[0].severity

    if top_severity == "unsuitable":
        filtered = [r for r in sorted_rules if r.severity != "suitable"]
    elif top_severity == "warning":
        filtered = [r for r in sorted_rules if r.severity != "suitable"]
    else:
        filtered = sorted_rules

    recs = []
    for r in filtered:
        recs.append(build_detailed_recommendation(r, weather, crop_name))

    # Add general context lines based on weather
    recs += get_context_lines(temp, rain, humidity, crop_name, top_severity)

    return {
        "suitability": top_severity,
        "recommendations": recs
    }

def build_detailed_recommendation(rule, weather, crop_name):
    temp = weather.get("temperature", 0)
    rain = weather.get("rainfall", 0)
    humidity = weather.get("humidity", 0)

    param = rule.parameter
    base = rule.action

    if param == "temperature":
        if rule.severity == "unsuitable" and temp > 38:
            return (f"{base} Current reading: {temp}°C — this is {round(temp - 35, 1)}°C above "
                    f"the safe upper limit for {crop_name}. Avoid any transplanting or sowing "
                    f"activities until temperature drops below 35°C.")
        elif rule.severity == "unsuitable" and temp < 15:
            return (f"{base} Current reading: {temp}°C — dangerously low for {crop_name}. "
                    f"Cover seedlings with plastic mulch or straw to retain soil warmth.")
        elif rule.severity == "warning" and temp > 33:
            return (f"{base} Current reading: {temp}°C. Irrigate in the early morning "
                    f"(before 7 AM) or late evening (after 6 PM) to reduce heat stress. "
                    f"Avoid midday irrigation as it can scorch leaves.")
        else:
            return f"{base} Current temperature: {temp}°C."

    elif param == "rainfall":
        if rule.severity == "unsuitable" and rain < 5:
            return (f"{base} Current rainfall: {rain}mm — critically low. "
                    f"{crop_name} requires consistent soil moisture. "
                    f"Irrigate immediately and apply organic mulch (straw or dry leaves) "
                    f"around the base of plants to retain moisture for 3–4 days.")
        elif rule.severity == "warning" and rain > 40:
            return (f"{base} Current rainfall: {rain}mm/hr — heavy. "
                    f"Clear all drainage channels and field borders immediately. "
                    f"Delay any fertiliser (NPK) application by at least 4–5 days "
                    f"to prevent nutrient runoff and leaching.")
        else:
            return f"{base} Current rainfall: {rain}mm."

    elif param == "humidity":
        if rule.severity == "warning" and humidity > 75:
            return (f"{base} Current humidity: {humidity}% — elevated. "
                    f"Inspect leaves for white powdery patches (powdery mildew) or "
                    f"water-soaked lesions (bacterial blight). "
                    f"Apply copper oxychloride or mancozeb fungicide at recommended dose "
                    f"if symptoms are visible.")
        elif rule.severity == "warning" and humidity < 40:
            return (f"{base} Current humidity: {humidity}% — low. "
                    f"Increase irrigation frequency and consider light foliar spray "
                    f"during early morning to reduce moisture stress.")
        else:
            return f"{base} Current humidity: {humidity}%."

    return base

def get_context_lines(temp, rain, humidity, crop_name, severity):
    lines = []

    # Season context for Nepal — July/August is Kharif/Monsoon
    if rain == 0 and humidity > 70:
        lines.append(
            f"Note: Humidity is {humidity}% but no active rainfall recorded. "
            f"Conditions may change — monitor weather updates every 6 hours during monsoon season."
        )

    if temp > 30 and rain < 5:
        lines.append(
            f"Combined heat ({temp}°C) and dry conditions increase evapotranspiration rate. "
            f"{crop_name} fields may lose 5–7mm of soil moisture daily — "
            f"check soil moisture at 10cm depth before each irrigation."
        )

    if severity in ("unsuitable", "warning"):
        lines.append(
            f"Source: Advisory rules based on MoALD Nepal Crop Calendar 2023 "
            f"and FAO Irrigation & Drainage Paper 56."
        )

    return lines