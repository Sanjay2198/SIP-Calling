from __future__ import annotations

from django.db import models
from django.utils import timezone


class CallLog(models.Model):
    caller = models.CharField(max_length=20)
    agent = models.CharField(max_length=50, blank=True)
    queue = models.CharField(max_length=50, blank=True)
    duration = models.IntegerField(default=0)
    recording_url = models.URLField(blank=True)
    status = models.CharField(max_length=20)  # answered, missed, abandoned, ringing
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.caller} -> {self.agent or '-'} ({self.status})"


class CallSession(models.Model):
    """Active call session tracking."""
    
    STATUS_CHOICES = [
        ("initiated", "Initiated"),
        ("ringing", "Ringing"),
        ("connected", "Connected"),
        ("on_hold", "On Hold"),
        ("ended", "Ended"),
    ]
    
    call_id = models.CharField(max_length=100, unique=True)
    channel_id = models.CharField(max_length=100, blank=True, help_text="Asterisk channel ID")
    from_number = models.CharField(max_length=20)
    to_number = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="initiated")
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self) -> str:
        return f"{self.call_id}: {self.from_number} -> {self.to_number} ({self.status})"
    
    @property
    def duration(self) -> int:
        """Return call duration in seconds."""
        end_time = self.ended_at or timezone.now()
        return int((end_time - self.started_at).total_seconds())

