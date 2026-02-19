from __future__ import annotations

from pathlib import Path
from typing import Optional


def transcribe_recording(path: str) -> Optional[str]:
    """
    Placeholder for transcription.

    Swap in Whisper / Vosk / cloud STT here. Keep this module small so you can
    change providers without touching the call logging + dashboard code.
    """
    p = Path(path)
    if not p.exists():
        return None
    return None

