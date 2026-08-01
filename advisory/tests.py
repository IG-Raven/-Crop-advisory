from django.test import TestCase, Client
from django.urls import reverse
from .models import District, Crop, CropRule
# Create your tests here.

class WeatherUtilsTest(TestCase):

    def test_rainfall_exactly_at_low_boundary(self):
        from .weather_utils import categorize_rainfall
        self.assertEqual(categorize_rainfall(5), "moderate")

    def test_rainfall_exactly_at_high_boundary(self):
        from .weather_utils import categorize_rainfall
        self.assertEqual(categorize_rainfall(50), "moderate")

    def test_rainfall_just_above_high_boundary(self):
        from .weather_utils import categorize_rainfall
        self.assertEqual(categorize_rainfall(51), "high")

    def test_rainfall_zero(self):
        from .weather_utils import categorize_rainfall
        self.assertEqual(categorize_rainfall(0), "low")

    def test_extract_rainfall_3h_key(self):
        from .weather_utils import extract_rainfall
        data = {"rain": {"3h": 9.0}}
        self.assertEqual(extract_rainfall(data), 0.0)

    def test_kelvin_negative_result(self):
        from .weather_utils import convert_kelvin_to_celsius
        # Below freezing
        self.assertEqual(convert_kelvin_to_celsius(263.15), -10.0)

    def test_categorize_rainfall_low(self):
        from .weather_utils import categorize_rainfall
        self.assertEqual(categorize_rainfall(3), "low")

    def test_categorize_rainfall_moderate(self):
        from .weather_utils import categorize_rainfall
        self.assertEqual(categorize_rainfall(25), "moderate")

    def test_categorize_rainfall_high(self):
        from .weather_utils import categorize_rainfall
        self.assertEqual(categorize_rainfall(60), "high")


class AdvisoryEngineTest(TestCase):

    def setUp(self):
        # Rice
        rice = Crop.objects.create(name="Rice", season="Kharif")
        CropRule.objects.create(crop=rice, parameter="temperature",
            min_value=20, max_value=35, action="Suitable temp for rice.",
            severity="suitable", source="MoALD", condition="ok")
        CropRule.objects.create(crop=rice, parameter="temperature",
            min_value=35, max_value=40, action="High heat — irrigate early.",
            severity="warning", source="FAO", condition="ok")
        CropRule.objects.create(crop=rice, parameter="rainfall",
            min_value=0, max_value=5, action="Irrigate now — rainfall too low.",
            severity="unsuitable", source="MoALD", condition="ok")

        # Wheat
        wheat = Crop.objects.create(name="Wheat", season="Rabi")
        CropRule.objects.create(crop=wheat, parameter="temperature",
            min_value=15, max_value=25, action="Ideal temp for wheat.",
            severity="suitable", source="MoALD", condition="ok")
        CropRule.objects.create(crop=wheat, parameter="temperature",
            min_value=25, max_value=35, action="Rising temp — monitor aphids.",
            severity="warning", source="FAO", condition="ok")

        # Maize
        maize = Crop.objects.create(name="Maize", season="Kharif")
        CropRule.objects.create(crop=maize, parameter="temperature",
            min_value=20, max_value=32, action="Good conditions for maize.",
            severity="suitable", source="MoALD", condition="ok")

        # Vegetables
        veg = Crop.objects.create(name="Vegetables", season="Year-round")
        CropRule.objects.create(crop=veg, parameter="temperature",
            min_value=15, max_value=28, action="Suitable for vegetables.",
            severity="suitable", source="MoALD", condition="ok")

    # Rice tests
    def test_rice_suitable(self):
        from .advisory_engine import get_advisory
        result = get_advisory("Rice", {"temperature": 28, "humidity": 70, "rainfall": 20})
        self.assertEqual(result["suitability"], "suitable")

    def test_rice_warning_high_temp(self):
        from .advisory_engine import get_advisory
        result = get_advisory("Rice", {"temperature": 37, "humidity": 70, "rainfall": 20})
        self.assertEqual(result["suitability"], "warning")

    def test_rice_unsuitable_no_rain(self):
        from .advisory_engine import get_advisory
        result = get_advisory("Rice", {"temperature": 28, "humidity": 60, "rainfall": 2})
        self.assertEqual(result["suitability"], "unsuitable")

    def test_rice_at_exact_boundary_35(self):
        from .advisory_engine import get_advisory
        # 35 is the boundary — should trigger warning not suitable
        result = get_advisory("Rice", {"temperature": 35, "humidity": 70, "rainfall": 20})
        self.assertEqual(result["suitability"], "warning")

    # Wheat tests
    def test_wheat_suitable(self):
        from .advisory_engine import get_advisory
        result = get_advisory("Wheat", {"temperature": 20, "humidity": 60, "rainfall": 15})
        self.assertEqual(result["suitability"], "suitable")

    def test_wheat_warning(self):
        from .advisory_engine import get_advisory
        result = get_advisory("Wheat", {"temperature": 30, "humidity": 60, "rainfall": 15})
        self.assertEqual(result["suitability"], "warning")

    # Maize tests
    def test_maize_suitable(self):
        from .advisory_engine import get_advisory
        result = get_advisory("Maize", {"temperature": 26, "humidity": 65, "rainfall": 18})
        self.assertEqual(result["suitability"], "suitable")

    # Vegetables tests
    def test_vegetables_suitable(self):
        from .advisory_engine import get_advisory
        result = get_advisory("Vegetables", {"temperature": 22, "humidity": 65, "rainfall": 15})
        self.assertEqual(result["suitability"], "suitable")

    # Edge cases
    def test_missing_weather_parameter(self):
        from .advisory_engine import get_advisory
        # Should not crash when parameter missing
        result = get_advisory("Rice", {"temperature": 28})
        self.assertIn("suitability", result)

    def test_unknown_crop_returns_response(self):
        from .advisory_engine import get_advisory
        result = get_advisory("UnknownCrop", {"temperature": 28, "humidity": 60, "rainfall": 20})
        self.assertIn("recommendations", result)

    def test_recommendations_is_list(self):
        from .advisory_engine import get_advisory
        result = get_advisory("Rice", {"temperature": 28, "humidity": 60, "rainfall": 20})
        self.assertIsInstance(result["recommendations"], list)

    def test_unsuitable_does_not_show_suitable_message(self):
        from .advisory_engine import get_advisory
        result = get_advisory("Rice", {"temperature": 28, "humidity": 60, "rainfall": 2})
        for rec in result["recommendations"]:
            self.assertNotIn("Suitable temp", rec)

    def test_suitable_conditions(self):
        from .advisory_engine import get_advisory
        weather = {"temperature": 28, "humidity": 70, "rainfall": 20}
        result = get_advisory("Rice", weather)
        self.assertEqual(result["suitability"], "suitable")

    def test_warning_conditions(self):
        from .advisory_engine import get_advisory
        weather = {"temperature": 37, "humidity": 60, "rainfall": 20}
        result = get_advisory("Rice", weather)
        self.assertEqual(result["suitability"], "warning")

    def test_unsuitable_conditions(self):
        from .advisory_engine import get_advisory
        weather = {"temperature": 28, "humidity": 60, "rainfall": 2}
        result = get_advisory("Rice", weather)
        self.assertEqual(result["suitability"], "unsuitable")

    def test_no_rules_triggered(self):
        from .advisory_engine import get_advisory
        weather = {"temperature": 28, "humidity": 60, "rainfall": 20}
        result = get_advisory("Wheat", weather)
        self.assertIn("recommendations", result)

    def test_recommendations_not_empty(self):
        from .advisory_engine import get_advisory
        weather = {"temperature": 37, "humidity": 60, "rainfall": 2}
        result = get_advisory("Rice", weather)
        self.assertGreater(len(result["recommendations"]), 0)


class ViewTest(TestCase):

    def test_dashboard_requires_login(self):
        response = self.client.get("/dashboard/")
        self.assertRedirects(response, "/login/")

    def test_dashboard_accessible_when_logged_in(self):
        session = self.client.session
        session["logged_in"] = True
        session.save()

        response = self.client.get("/dashboard/")
        self.assertEqual(response.status_code, 200)

    def test_login_post_sets_session(self):
        self.client.post("/login/", {
            "phone": "9876543210",
            "password": "test123"
        })
        self.assertEqual(self.client.session.get("logged_in"), True)

    def test_logout_clears_session(self):
        session = self.client.session
        session["logged_in"] = True
        session.save()

        self.client.get("/logout/")
        self.assertIsNone(self.client.session.get("logged_in"))


class DatabaseTest(TestCase):

    def setUp(self):
        self.district = District.objects.create(
            name="Bardiya", latitude=28.39, longitude=81.50, province="Lumbini"
        )
        self.crop = Crop.objects.create(name="Wheat", season="Rabi")

    def test_district_created(self):
        self.assertEqual(District.objects.count(), 1)

    def test_crop_created(self):
        self.assertEqual(Crop.objects.count(), 1)

    def test_district_str(self):
        self.assertEqual(str(self.district), "Bardiya")

    def test_crop_str(self):
        self.assertEqual(str(self.crop), "Wheat")

    def test_croprule_linked_to_crop(self):
        rule = CropRule.objects.create(
            crop=self.crop, parameter="temperature",
            condition="suitable", min_value=15, max_value=25,
            action="Good conditions for wheat.",
            severity="suitable", source="MoALD"
        )
        self.assertEqual(rule.crop.name, "Wheat")