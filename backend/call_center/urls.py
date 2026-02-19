from __future__ import annotations

from django.contrib import admin
from django.urls import path

from calls import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", views.health, name="health"),
    path("api/calls/", views.call_logs, name="call_logs"),
]
