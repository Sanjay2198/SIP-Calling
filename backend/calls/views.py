from __future__ import annotations

import uuid
from typing import Any, Dict, cast
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET, require_http_methods
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.request import Request

from .models import CallLog, CallSession
from .serializers import (
    CallLogSerializer,
    CallSessionSerializer,
    MakeCallRequestSerializer,
    MakeCallResponseSerializer,
    HangupCallRequestSerializer,
    HangupCallResponseSerializer,
)
from .ari import initiate_call, hangup_call as ari_hangup_call


ROOT_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>SIP Call UI</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex; 
            flex-direction: column; 
            align-items: center; 
            justify-content: center; 
            height: 100vh; 
            margin: 0; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .container { 
            padding: 2.5rem; 
            background: white; 
            border-radius: 16px; 
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3); 
            text-align: center; 
            max-width: 500px;
            width: 90%;
        }
        h1 { 
            color: #333; 
            margin: 0 0 0.5rem 0;
            font-size: 2rem;
        }
        .subtitle {
            color: #666;
            font-size: 0.9rem;
            margin-bottom: 2rem;
        }
        .input-group {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1.5rem;
            flex-wrap: wrap;
        }
        input[type="text"] { 
            padding: 0.75rem 1rem; 
            border: 2px solid #e1e8ed;
            border-radius: 8px; 
            font-size: 1rem; 
            flex: 1;
            min-width: 200px;
            transition: border-color 0.3s;
        }
        input[type="text"]:focus {
            outline: none;
            border-color: #667eea;
        }
        button { 
            padding: 0.75rem 1.5rem; 
            border: none; 
            border-radius: 8px; 
            color: white; 
            font-size: 1rem; 
            font-weight: 600;
            cursor: pointer; 
            transition: all 0.3s;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
        }
        button:active {
            transform: translateY(0);
        }
        #makeCallBtn { 
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            flex: 1;
            min-width: 150px;
        }
        #makeCallBtn:hover { 
            background: linear-gradient(135deg, #45a049 0%, #3d8b40 100%);
        }
        #hangupCallBtn { 
            background: linear-gradient(135deg, #f44336 0%, #da190b 100%);
            min-width: 150px;
        }
        #hangupCallBtn:hover { 
            background: linear-gradient(135deg, #da190b 0%, #c41c00 100%);
        }
        #response { 
            margin-top: 2rem; 
            padding: 1.5rem; 
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            border-radius: 8px; 
            width: 100%;
            word-wrap: break-word; 
            text-align: left; 
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
            color: #333;
            max-height: 300px;
            overflow-y: auto;
            display: none;
        }
        #response.active {
            display: block;
        }
        .response-title {
            font-weight: 600;
            color: #667eea;
            margin-bottom: 0.5rem;
        }
        .success { border-left-color: #4CAF50; }
        .success .response-title { color: #4CAF50; }
        .error { border-left-color: #f44336; }
        .error .response-title { color: #f44336; }
    </style>
</head>
<body>
    <div class="container">
        <h1> SIP Call Center</h1>
        <p class="subtitle">Make and manage VoIP calls</p>
        
        <div class="input-group">
            <input 
                type="text" 
                id="number" 
                placeholder="Enter phone number (e.g., 918147747884)"
                autocomplete="off"
            >
            <button id="makeCallBtn" onclick="makeCall()"> Make Call</button>
        </div>
        
        <button id="hangupCallBtn" onclick="hangupCall()"> Hangup Call</button>
        
        <div id="response"></div>
    </div>

    <script>
        let lastCallId = null;

        async function makeCall() {
            const number = document.getElementById("number").value.trim();
            
            if (!number) {
                showResponse("Please enter a phone number", "error");
                return;
            }

            try {
                const response = await fetch("/api/make_call/", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ number })
                });
                
                const result = await response.json();
                lastCallId = result.call_id;
                
                showResponse(
                    JSON.stringify(result, null, 2),
                    response.ok ? "success" : "error"
                );
            } catch (error) {
                showResponse("Error: " + error.message, "error");
            }
        }

        async function hangupCall() {
            if (!lastCallId) {
                showResponse("No active call to hangup", "error");
                return;
            }

            try {
                const response = await fetch("/api/hangup_call/", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ call_id: lastCallId })
                });
                
                const result = await response.json();
                lastCallId = null;
                
                showResponse(
                    JSON.stringify(result, null, 2),
                    response.ok ? "success" : "error"
                );
            } catch (error) {
                showResponse("Error: " + error.message, "error");
            }
        }

        function showResponse(text, type = "success") {
            const responseDiv = document.getElementById("response");
            responseDiv.textContent = text;
            responseDiv.className = "active " + type;
        }

        // Allow Enter key to make call
        document.getElementById("number").addEventListener("keypress", function(event) {
            if (event.key === "Enter") {
                makeCall();
            }
        });
    </script>
</body>
</html>
"""


@require_GET
def root_handler(request):
    """
    Serve the root HTML page.
    
    Returns a simple HTML page with links to API documentation and features.
    """
    return HttpResponse(ROOT_HTML, content_type="text/html")


@require_GET
def health(request):
    """
    Health check endpoint.
    
    Returns a simple JSON response to indicate the API is running.
    """
    return JsonResponse({"ok": True})


@require_GET
def call_logs(request):
    """
    List recent call logs.
    
    Returns the last 200 call log records ordered by creation date (newest first).
    
    Returns:
        JSON response with a "calls" array containing call details:
        - id: Call log ID
        - caller: Caller phone number
        - agent: Agent assigned to the call
        - queue: Queue the call was routed to
        - duration: Call duration in seconds
        - recording_url: URL to the call recording (if available)
        - status: Call status (completed, failed, etc.)
        - created_at: ISO format timestamp
    """
    qs = CallLog.objects.order_by("-created_at")[:200]
    return JsonResponse(
        {
            "calls": [
                {
                    "id": c.pk,
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


@api_view(["POST"])
def make_call(request: Request) -> Response:
    """
    Initiate a new outbound call.
    
    Creates a new call session and initiates the call to the specified number.
    
    Args:
        request: HTTP request with JSON body containing:
            - number: Phone number to call (required)
            - from_number: Caller phone number (optional)
    
    Returns:
        201 Created: Call initiated successfully with call_id
        400 Bad Request: Invalid request data
    """
    serializer = MakeCallRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    validated_data: Dict[str, Any] = cast(Dict[str, Any], serializer.validated_data)
    to_number: str = validated_data.get("number", "")
    from_number: str = validated_data.get("from_number", "1000")
    
    # Generate unique call ID
    call_id = f"call_{uuid.uuid4().hex[:12]}"
    
    # Initiate call via Asterisk ARI
    ari_result = initiate_call(to_number=to_number, from_number=from_number)
    
    # Create call session in database
    call_session = CallSession.objects.create(
        call_id=call_id,
        channel_id=ari_result.get("channel_id", ""),
        from_number=from_number,
        to_number=to_number,
        status="ringing" if ari_result.get("success") else "initiated",
    )
    
    if ari_result.get("success"):
        response_data = {
            "status": "success",
            "message": f"Call initiated to {to_number}. Channel: {ari_result.get('channel_id')}",
            "call_id": call_id,
        }
        return Response(response_data, status=status.HTTP_201_CREATED)
    else:
        response_data = {
            "status": "error",
            "message": f"Failed to initiate call: {ari_result.get('error')}",
            "call_id": call_id,
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def hangup_call(request: Request) -> Response:
    """
    End an active call.
    
    Terminates the call session and records final status.
    
    Args:
        request: HTTP request with JSON body containing:
            - call_id: ID of the call to hang up
    
    Returns:
        200 OK: Call ended successfully
        400 Bad Request: Invalid request data
        404 Not Found: Call session not found
    """
    serializer = HangupCallRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    validated_data_hangup: Dict[str, Any] = cast(Dict[str, Any], serializer.validated_data)
    call_id: str = validated_data_hangup.get("call_id", "")
    
    try:
        call_session = CallSession.objects.get(call_id=call_id)
    except CallSession.DoesNotExist:
        return Response(
            {"status": "error", "message": f"Call {call_id} not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    
    # Hang up the call via Asterisk ARI if channel_id exists
    ari_result = {"success": True}
    if call_session.channel_id:
        ari_result = ari_hangup_call(call_session.channel_id)
    
    # End the call session
    call_session.status = "ended"
    call_session.ended_at = timezone.now()
    call_session.save()
    
    # Create call log entry
    CallLog.objects.create(
        caller=call_session.from_number,
        queue="default",
        duration=call_session.duration,
        status="completed",
    )
    
    if ari_result.get("success"):
        response_data = {
            "status": "success",
            "message": f"Call ({call_id}) terminated successfully.",
        }
        return Response(response_data)
    else:
        response_data = {
            "status": "warning",
            "message": f"Call ({call_id}) logged but Asterisk error: {ari_result.get('error')}",
        }
        return Response(response_data, status=status.HTTP_206_PARTIAL_CONTENT)

