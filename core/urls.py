from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from advisory import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("advisory/", views.results, name="results"),
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("quick-advisory/", views.quick_advisory_view, name="quick_advisory"),
    path("more-options/", views.more_options_view, name="more_options"),
    path("weather-data/", views.weather_data_view, name="weather_data"),
    path("about/", views.about_view, name="about"),
    path("logout/", views.logout_view, name="logout"),
    path("chatbot/message/", views.chatbot_message, name="chatbot_message"),
    path("chatbot/history/", views.chatbot_history, name="chatbot_history"),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)