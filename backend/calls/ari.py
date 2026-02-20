from __future__ import annotations

import os
import time
import json
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


def initiate_call(to_number: str, from_number: str = "1000") -> dict[str, Any]:
    """
    Initiate an outbound call via Asterisk ARI.
    
    Uses Asterisk Application (stasis app) to originate a call.
    
    Args:
        to_number: Destination phone number (e.g., "918147747884")
        from_number: Calling from extension (default "1000")
    
    Returns:
        dict with call status: {"success": True, "channel_id": "...", "error": None}
                or {"success": False, "channel_id": None, "error": "..."}
    """
    auth = _ari_auth()
    base_url = _ari_base_url()
    app_name = _ari_app_name()
    
    # Originate call endpoint
    url = f"{base_url}/ari/channels"
    
    # Build channel endpoint (format: SIP/provider/number or SIP/number)
    # Adjust based on your Asterisk setup
    endpoint = f"SIP/{to_number}"
    
    params = {
        "endpoint": endpoint,
        "extension": from_number,
        "context": "from-internal",
        "priority": 1,
        "app": app_name,
    }
    
    try:
        response = requests.post(url, params=params, auth=auth, timeout=5)
        
        if response.status_code in (200, 201):
            data = response.json()
            return {
                "success": True,
                "channel_id": data.get("id", ""),
                "error": None,
            }
        else:
            error_msg = f"ARI Error {response.status_code}: {response.text}"
            return {
                "success": False,
                "channel_id": None,
                "error": error_msg,
            }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "channel_id": None,
            "error": f"Connection error: {str(e)}",
        }


def hangup_call(channel_id: str) -> dict[str, Any]:
    """
    Hang up a call via Asterisk ARI.
    
    Args:
        channel_id: Asterisk channel ID to hang up
    
    Returns:
        dict with status: {"success": True, "error": None}
                or {"success": False, "error": "..."}
    """
    auth = _ari_auth()
    base_url = _ari_base_url()
    
    url = f"{base_url}/ari/channels/{channel_id}"
    
    try:
        response = requests.delete(url, auth=auth, timeout=5)
        
        if response.status_code in (200, 204):
            return {
                "success": True,
                "error": None,
            }
        else:
            error_msg = f"ARI Error {response.status_code}: {response.text}"
            return {
                "success": False,
                "error": error_msg,
            }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Connection error: {str(e)}",
        }


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
                "id": call.pk,
                "caller": call.caller,
                "agent": call.agent,
                "queue": call.queue,
                "status": call.status,
                "created_at": call.created_at.isoformat(),
            },
        },
    )
    return call

