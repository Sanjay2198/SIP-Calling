"""
FastAPI Web API for SIP Client
Provides REST endpoints for controlling the SIP softphone
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import os
from datetime import datetime

from sip_client import SIPClient
from models import Contact, CallHistory, get_session

# Initialize FastAPI app
app = FastAPI(title="SIP Softphone API", version="1.0.0")

# Initialize SIP client (global instance)
sip_client = None

# Data models
class CallRequest(BaseModel):
    destination: str

class DTMFRequest(BaseModel):
    digits: str

class ContactCreate(BaseModel):
    name: str
    sip_uri: str
    phone_number: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize SIP client on startup"""
    global sip_client
    try:
        sip_client = SIPClient()
        sip_client.start()
        print(" SIP Client started successfully")
    except Exception as e:
        print(f" Failed to start SIP client: {e}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global sip_client
    if sip_client:
        sip_client.stop()
        print(" SIP Client stopped")


# === Call Management Endpoints ===

@app.post("/api/call/make")
async def make_call(request: CallRequest):
    """Make an outgoing call"""
    if not sip_client:
        raise HTTPException(status_code=503, detail="SIP client not initialized")
    
    call = sip_client.make_call(request.destination)
    if call:
        return {"success": True, "message": f"Calling {request.destination}"}
    else:
        raise HTTPException(status_code=500, detail="Failed to make call")


@app.post("/api/call/answer")
async def answer_call():
    """Answer incoming call"""
    if not sip_client:
        raise HTTPException(status_code=503, detail="SIP client not initialized")
    
    sip_client.answer_call()
    return {"success": True, "message": "Call answered"}


@app.post("/api/call/hangup")
async def hangup_call():
    """Hangup current call"""
    if not sip_client:
        raise HTTPException(status_code=503, detail="SIP client not initialized")
    
    sip_client.hangup()
    return {"success": True, "message": "Call ended"}


@app.post("/api/call/hold")
async def hold_call():
    """Put call on hold"""
    if not sip_client or not sip_client.account or not sip_client.account.current_call:
        raise HTTPException(status_code=404, detail="No active call")
    
    sip_client.account.current_call.hold()
    return {"success": True, "message": "Call on hold"}


@app.post("/api/call/resume")
async def resume_call():
    """Resume held call"""
    if not sip_client or not sip_client.account or not sip_client.account.current_call:
        raise HTTPException(status_code=404, detail="No active call")
    
    sip_client.account.current_call.resume()
    return {"success": True, "message": "Call resumed"}


@app.post("/api/call/mute")
async def mute_call():
    """Mute microphone"""
    if not sip_client or not sip_client.account or not sip_client.account.current_call:
        raise HTTPException(status_code=404, detail="No active call")
    
    sip_client.account.current_call.mute()
    return {"success": True, "message": "Muted"}


@app.post("/api/call/unmute")
async def unmute_call():
    """Unmute microphone"""
    if not sip_client or not sip_client.account or not sip_client.account.current_call:
        raise HTTPException(status_code=404, detail="No active call")
    
    sip_client.account.current_call.unmute()
    return {"success": True, "message": "Unmuted"}


@app.post("/api/call/dtmf")
async def send_dtmf(request: DTMFRequest):
    """Send DTMF tones"""
    if not sip_client or not sip_client.account or not sip_client.account.current_call:
        raise HTTPException(status_code=404, detail="No active call")
    
    sip_client.account.current_call.send_dtmf(request.digits)
    return {"success": True, "message": f"DTMF sent: {request.digits}"}


@app.get("/api/call/status")
async def get_call_status():
    """Get current call status"""
    if not sip_client:
        raise HTTPException(status_code=503, detail="SIP client not initialized")
    
    status = sip_client.get_call_status()
    return status


# === Call History Endpoints ===

@app.get("/api/history")
async def get_call_history(limit: int = 50, offset: int = 0):
    """Get call history"""
    session = get_session()
    try:
        calls = session.query(CallHistory)\
            .order_by(CallHistory.start_time.desc())\
            .limit(limit)\
            .offset(offset)\
            .all()
        
        return {"calls": [call.to_dict() for call in calls]}
    finally:
        session.close()


@app.get("/api/history/{call_id}")
async def get_call_details(call_id: int):
    """Get specific call details"""
    session = get_session()
    try:
        call = session.query(CallHistory).filter(CallHistory.id == call_id).first()
        if not call:
            raise HTTPException(status_code=404, detail="Call not found")
        
        return call.to_dict()
    finally:
        session.close()


@app.get("/api/history/{call_id}/recording")
async def get_recording(call_id: int):
    """Get call recording file"""
    session = get_session()
    try:
        call = session.query(CallHistory).filter(CallHistory.id == call_id).first()
        if not call:
            raise HTTPException(status_code=404, detail="Call not found")
        
        if not call.recording_path or not os.path.exists(call.recording_path):
            raise HTTPException(status_code=404, detail="Recording not found")
        
        return FileResponse(
            call.recording_path,
            media_type="audio/wav",
            filename=os.path.basename(call.recording_path)
        )
    finally:
        session.close()


# === Contact Management Endpoints ===

@app.get("/api/contacts")
async def get_contacts():
    """Get all contacts"""
    session = get_session()
    try:
        contacts = session.query(Contact).order_by(Contact.name).all()
        return {"contacts": [contact.to_dict() for contact in contacts]}
    finally:
        session.close()


@app.post("/api/contacts")
async def create_contact(contact: ContactCreate):
    """Create new contact"""
    session = get_session()
    try:
        # Check if contact already exists
        existing = session.query(Contact).filter(Contact.sip_uri == contact.sip_uri).first()
        if existing:
            raise HTTPException(status_code=400, detail="Contact already exists")
        
        new_contact = Contact(
            name=contact.name,
            sip_uri=contact.sip_uri,
            phone_number=contact.phone_number,
            email=contact.email,
            notes=contact.notes
        )
        session.add(new_contact)
        session.commit()
        
        return {"success": True, "contact": new_contact.to_dict()}
    finally:
        session.close()


@app.delete("/api/contacts/{contact_id}")
async def delete_contact(contact_id: int):
    """Delete contact"""
    session = get_session()
    try:
        contact = session.query(Contact).filter(Contact.id == contact_id).first()
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        session.delete(contact)
        session.commit()
        
        return {"success": True, "message": "Contact deleted"}
    finally:
        session.close()


# === System Endpoints ===

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "sip_registered": sip_client is not None,
        "timestamp": datetime.utcnow().isoformat()
    }


# Serve static files (HTML/CSS/JS)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    """Serve main HTML page"""
    if os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    return {"message": "SIP Softphone API", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    import yaml
    
    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    api_config = config.get('api', {})
    
    # Run server
    uvicorn.run(
        app,
        host=api_config.get('host', '0.0.0.0'),
        port=api_config.get('port', 8000),
        log_level="info"
    )
