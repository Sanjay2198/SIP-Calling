from __future__ import annotations

from django.db import models


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

