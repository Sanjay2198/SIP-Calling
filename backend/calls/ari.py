from __future__ import annotations

import os
import time
from typing import Any

import requests
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone

from .models import CallLog


def _ari_auth() -> tuple[str, str]:
    return (
        os.getenv("ARI_USERNAME", "ariuser"),
        os.getenv("ARI_PASSWORD", "aripass"),
    )


def _ari_base_url() -> str:
    return os.getenv("ARI_BASE_URL", "http://localhost:8088").rstrip("/")


def _ari_app_name() -> str:
    return os.getenv("ARI_APP_NAME", "call-center-app")


def run_ari_event_loop(poll_seconds: float = 1.0) -> None:
    """
    Minimal ARI event loop stub.

    Real ARI apps typically use ARI WebSocket events:
    - ws://<host>:8088/ari/events?app=<app>&api_key=<user>:<pass>

    This stub keeps the project structure in place and demonstrates how
    to fan out call updates to Channels.
    """
    channel_layer = get_channel_layer()
    group = "call_dashboard"

    while True:
        # Placeholder: replace with WebSocket ARI event consumption.
        payload: dict[str, Any] = {
            "type": "heartbeat",
            "ts": timezone.now().isoformat(),
        }
        async_to_sync(channel_layer.group_send)(group, {"type": "send_call_update", "data": payload})
        time.sleep(poll_seconds)


def log_incoming_call(caller: str, queue: str = "", agent: str = "") -> CallLog:
    call = CallLog.objects.create(
        caller=caller,
        agent=agent,
        queue=queue,
        duration=0,
        recording_url="",
        status="ringing",
    )

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "call_dashboard",
        {
            "type": "send_call_update",
            "data": {
                "type": "call_created",
                "id": call.id,
                "caller": call.caller,
                "agent": call.agent,
                "queue": call.queue,
                "status": call.status,
                "created_at": call.created_at.isoformat(),
            },
        },
    )
    return call

