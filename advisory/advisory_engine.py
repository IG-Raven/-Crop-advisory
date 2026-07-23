from .models import CropRule

def get_advisory(crop, weather):
    rules = CropRule.objects.filter(crop=crop)
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
        return {"suitability": "suitable", "recommendations": ["No risks detected"]}
    top_rule = sorted_rules[0]
    recs = [r.action for r in sorted_rules]
    return {
        "suitability": top_rule.severity,
        "recommendations": recs
    }