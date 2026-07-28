from .models import CropRule

def get_advisory(crop_name, weather):
    rules = CropRule.objects.filter(crop__name=crop_name)
    triggered = evaluate_rules(rules, weather)
    sorted_rules = sort_by_severity(triggered)
    return build_response(sorted_rules)

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

def build_response(sorted_rules):
    if not sorted_rules:
        return {
            "suitability": "suitable",
            "recommendations": ["No risks detected. Conditions are normal."]
        }
    
    top_severity = sorted_rules[0].severity
    
    # If unsuitable — only show unsuitable and warning rules, drop suitable ones
    if top_severity == "unsuitable":
        filtered = [r for r in sorted_rules if r.severity != "suitable"]
    # If warning — show warnings only, drop suitable
    elif top_severity == "warning":
        filtered = [r for r in sorted_rules if r.severity != "suitable"]
    else:
        filtered = sorted_rules

    recs = [r.action for r in filtered]
    return {
        "suitability": top_severity,
        "recommendations": recs
    }