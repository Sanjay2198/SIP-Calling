from __future__ import annotations

from django.contrib import admin
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from calls import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.root_handler, name="root"),
    path("health/", views.health, name="health"),
    path("api/calls/", views.call_logs, name="call_logs"),
    path("api/make_call/", views.make_call, name="make_call"),
    path("api/hangup_call/", views.hangup_call, name="hangup_call"),
    # Swagger/OpenAPI endpoints
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/docs/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
