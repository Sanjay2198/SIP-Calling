from __future__ import annotations

from django.contrib import admin

from .models import CallLog


@admin.register(CallLog)
class CallLogAdmin(admin.ModelAdmin):
    list_display = ("id", "caller", "agent", "queue", "status", "duration", "created_at")
    list_filter = ("status", "queue", "agent")
    search_fields = ("caller", "agent", "queue")

