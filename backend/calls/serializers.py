from __future__ import annotations

from rest_framework import serializers

from .models import CallLog, CallSession


class CallLogSerializer(serializers.ModelSerializer):
    """Serializer for call logs."""
    
    class Meta:
        model = CallLog
        fields = ["id", "caller", "agent", "queue", "duration", "recording_url", "status", "created_at"]


class CallSessionSerializer(serializers.ModelSerializer):
    """Serializer for active call sessions."""
    
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = CallSession
        fields = ["id", "call_id", "from_number", "to_number", "status", "started_at", "ended_at", "duration"]
    
    def get_duration(self, obj) -> int:
        return obj.duration


class MakeCallRequestSerializer(serializers.Serializer):
    """Serializer for making a call request."""
    
    number = serializers.CharField(
        max_length=20,
        help_text="Phone number to call (destination)"
    )
    from_number = serializers.CharField(
        max_length=20,
        default="",
        required=False,
        help_text="Caller phone number (optional)"
    )


class MakeCallResponseSerializer(serializers.Serializer):
    """Serializer for make call response."""
    
    call_id = serializers.CharField(
        help_text="Unique call identifier"
    )
    status = serializers.CharField(
        help_text="Call status (initiated, ringing, connected, etc.)"
    )
    message = serializers.CharField(
        help_text="Response message"
    )


class HangupCallRequestSerializer(serializers.Serializer):
    """Serializer for hang up call request."""
    
    call_id = serializers.CharField(
        max_length=100,
        help_text="Call ID to hang up"
    )


class HangupCallResponseSerializer(serializers.Serializer):
    """Serializer for hang up call response."""
    
    call_id = serializers.CharField(
        help_text="Hung up call ID"
    )
    status = serializers.CharField(
        help_text="Final call status"
    )
    duration = serializers.IntegerField(
        help_text="Call duration in seconds"
    )
    message = serializers.CharField(
        help_text="Response message"
    )
