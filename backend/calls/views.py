from __future__ import annotations

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .models import CallLog


@require_GET
def health(request):
    return JsonResponse({"ok": True})


@require_GET
def call_logs(request):
    qs = CallLog.objects.order_by("-created_at")[:200]
    return JsonResponse(
        {
            "calls": [
                {
                    "id": c.id,
                    "caller": c.caller,
                    "agent": c.agent,
                    "queue": c.queue,
                    "duration": c.duration,
                    "recording_url": c.recording_url,
                    "status": c.status,
                    "created_at": c.created_at.isoformat(),
                }
                for c in qs
            ]
        }
    )

