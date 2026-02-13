"""
Simple SIP Process Control API
Endpoints:
- GET /
- POST /make_call
- POST /hangup_call
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
from typing import Optional, TypeGuard

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="FastAPI", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CallRequest(BaseModel):
    number: str


HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
  <title>SIP Call UI</title>
  <style>
    body { font-family: sans-serif; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; background: #f0f2f5; }
    .box { background: #fff; padding: 24px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); width: 420px; text-align: center; }
    input { width: 100%; padding: 10px; margin-bottom: 12px; border: 1px solid #ccc; border-radius: 8px; }
    button { padding: 10px 16px; border: 0; border-radius: 8px; color: #fff; cursor: pointer; margin-right: 8px; }
    .call { background: #2e7d32; }
    .hangup { background: #c62828; }
    pre { text-align: left; background: #eef1f4; padding: 10px; border-radius: 8px; min-height: 56px; }
  </style>
</head>
<body>
  <div class="box">
    <h3>SIP Call UI</h3>
    <input id="number" type="text" placeholder="Enter Number" />
    <button class="call" onclick="makeCall()">Make Call</button>
    <button class="hangup" onclick="hangupCall()">Hangup Call</button>
    <pre id="response"></pre>
  </div>

  <script>
    async function makeCall() {
      const number = document.getElementById('number').value;
      const res = await fetch('/make_call', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ number })
      });
      const data = await res.json();
      document.getElementById('response').textContent = JSON.stringify(data, null, 2);
    }

    async function hangupCall() {
      const res = await fetch('/hangup_call', { method: 'POST' });
      const data = await res.json();
      document.getElementById('response').textContent = JSON.stringify(data, null, 2);
    }
  </script>
</body>
</html>
"""

_active_process: Optional[subprocess.Popen[bytes]] = None
_process_lock = threading.Lock()


def _is_running(proc: Optional[subprocess.Popen[bytes]]) -> TypeGuard[subprocess.Popen[bytes]]:
    return proc is not None and proc.poll() is None


def _terminate(proc: subprocess.Popen[bytes]) -> None:
    if proc.poll() is not None:
        return

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    global _active_process
    with _process_lock:
        proc = _active_process
        if _is_running(proc):
            _terminate(proc)
        _active_process = None


@app.get("/", response_class=HTMLResponse)
async def serve_html() -> str:
    """Serve Html"""
    return HTML_PAGE


@app.post("/make_call")
async def make_call(request: CallRequest):
    """Api Make Call"""
    global _active_process

    number = request.number.strip()
    if not number:
        raise HTTPException(status_code=400, detail="Number is required")

    with _process_lock:
        proc = _active_process
        if _is_running(proc):
            return {
                "status": "success",
                "message": f"Call already active. PID: {proc.pid}",
            }

        command = [sys.executable, "sip_minimal.py", number]
        try:
            if os.name == "nt":
                new_proc = subprocess.Popen(
                    command,
                    cwd=os.getcwd(),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                )
            else:
                new_proc = subprocess.Popen(
                    command,
                    cwd=os.getcwd(),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

            _active_process = new_proc
            return {
                "status": "success",
                "message": f"Call initiated to {number}. PID: {new_proc.pid}",
            }
        except Exception as exc:
            _active_process = None
            raise HTTPException(status_code=500, detail=f"Error initiating call: {exc}")


@app.post("/hangup_call")
async def hangup_call():
    """Api Hangup Call"""
    global _active_process

    with _process_lock:
        proc = _active_process
        if not _is_running(proc):
            _active_process = None
            return {
                "status": "success",
                "message": "No active call process found.",
            }

        pid = proc.pid
        try:
            _terminate(proc)
            return {
                "status": "success",
                "message": f"Call terminated. PID: {pid}",
            }
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Error hanging up call: {exc}")
        finally:
            _active_process = None


def _load_api_config() -> dict:
    try:
        with open("config.yaml", "r", encoding="utf-8") as handle:
            config = yaml.safe_load(handle) or {}
            return config.get("api", {})
    except Exception:
        return {}


if __name__ == "__main__":
    import uvicorn

    api_config = _load_api_config()
    uvicorn.run(
        app,
        host=api_config.get("host", "0.0.0.0"),
        port=api_config.get("port", 8000),
        log_level="info",
    )
