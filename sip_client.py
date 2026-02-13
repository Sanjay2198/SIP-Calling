"""
Core SIP Client using PJSUA2
Handles SIP registration, calls, and media
"""
# pyright: reportAttributeAccessIssue=false, reportAssignmentType=false, reportMissingImports=false, reportMissingModuleSource=false, reportOptionalMemberAccess=false
import sys
import time
import os
import wave
from datetime import datetime
from threading import Thread
from typing import Any, Optional
import yaml

pj: Any
try:
    import pjsua2 as pj  # type: ignore[import-not-found]
    PJSUA2_AVAILABLE = True
    print("[OK] PJSUA2 library loaded successfully")
except ImportError:
    PJSUA2_AVAILABLE = False
    print("[WARN] PJSUA2 not available - SIP functionality disabled")
    print("   The web UI and API will work, but calls cannot be made.")
    print("   To enable SIP: See README.md for PJSUA2 installation.")
    
    # Create dummy classes so the code doesn't crash
    class _PjFallback:
        PJSUA_INVALID_ID = -1
        PJMEDIA_TYPE_AUDIO = 1
        PJSUA_CALL_MEDIA_ACTIVE = 1
        PJSUA_CALL_MEDIA_REMOTE_HOLD = 2
        PJSUA_CALL_UPDATE_CONTACT = 1
        PJSIP_TRANSPORT_UDP = 1
        PJSIP_TRANSPORT_TCP = 2

        class Call:
            def __init__(self, *args, **kwargs):
                pass
        class Account:
            def __init__(self, *args, **kwargs):
                pass
        class Endpoint:
            def __init__(self, *args, **kwargs):
                pass
        class Error(Exception):
            pass
        class CallOpParam:
            def __init__(self, *args, **kwargs):
                self.statusCode = 0
                self.opt = type('Opt', (), {'flag': 0})()
    pj = _PjFallback

from models import CallHistory, get_session


class MyCall(pj.Call):
    """Enhanced Call class with recording and controls"""
    
    def __init__(self, account, call_id=None):
        if call_id is None:
            call_id = getattr(pj, "PJSUA_INVALID_ID", -1)
        pj.Call.__init__(self, account, call_id)
        self.account = account
        self.on_hold = False
        self.is_muted = False
        self.recording_id = None
        self.call_start_time = None
        self.db_session = get_session()
        self.call_record: Optional[CallHistory] = None
        
    def onCallState(self, prm):
        """Called when call state changes"""
        ci = self.getInfo()
        status = ci.stateText
        
        print(f" Call state: {status}")
        
        # Update call record in database
        if status == "CONFIRMED" and not self.call_start_time:
            self.call_start_time = datetime.utcnow()
            if self.call_record:
                self.call_record.status = 'answered'
                self.call_record.start_time = self.call_start_time
                self.db_session.commit()
            
            # Start recording if enabled
            config = self.account.client.config
            if config.get('recording', {}).get('auto_record', True):
                self.start_recording()
                
        elif status == "DISCONNECTED":
            # Call ended
            if self.call_start_time:
                duration = (datetime.utcnow() - self.call_start_time).total_seconds()
                if self.call_record:
                    self.call_record.end_time = datetime.utcnow()
                    self.call_record.duration = duration
                    self.db_session.commit()
            
            # Stop recording
            if self.recording_id:
                self.stop_recording()
                
        # Store reference in account for status queries
        self.account.current_call = self if status != "DISCONNECTED" else None
    
    def onCallMediaState(self, prm):
        """Called when media state changes"""
        ci = self.getInfo()
        
        for mi in ci.media:
            if mi.type == pj.PJMEDIA_TYPE_AUDIO:
                if mi.status == pj.PJSUA_CALL_MEDIA_ACTIVE or \
                   mi.status == pj.PJSUA_CALL_MEDIA_REMOTE_HOLD:
                    # Connect audio
                    am = pj.Endpoint.instance().audDevManager()
                    am.getCaptureDevMedia().startTransmit(self.getMedia(mi.index))
                    self.getMedia(mi.index).startTransmit(am.getPlaybackDevMedia())
    
    def start_recording(self):
        """Start call recording"""
        try:
            config = self.account.client.config
            rec_path = config.get('recording', {}).get('path', 'recordings')
            
            # Create recordings directory
            os.makedirs(rec_path, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            ci = self.getInfo()
            remote = ci.remoteUri.split(':')[1].split('@')[0]
            filename = f"{rec_path}/call_{remote}_{timestamp}.wav"
            
            # Start recording
            rp = pj.CallOpParam()
            self.getMedia(0).startRecording(filename)
            
            print(f" Recording started: {filename}")
            
            # Update call record
            if self.call_record:
                self.call_record.recording_path = filename
                self.db_session.commit()
                
        except Exception as e:
            print(f" Recording failed: {e}")
    
    def stop_recording(self):
        """Stop call recording"""
        try:
            self.getMedia(0).stopRecording()
            print(" Recording stopped")
        except Exception as e:
            print(f" Stop recording failed: {e}")
    
    def hold(self):
        """Put call on hold"""
        try:
            prm = pj.CallOpParam()
            prm.opt.flag = pj.PJSUA_CALL_UPDATE_CONTACT
            self.setHold(prm)
            self.on_hold = True
            print(" Call on hold")
        except Exception as e:
            print(f" Hold failed: {e}")
    
    def resume(self):
        """Resume held call"""
        try:
            prm = pj.CallOpParam()
            prm.opt.flag = pj.PJSUA_CALL_UPDATE_CONTACT
            self.reinvite(prm)
            self.on_hold = False
            print(" Call resumed")
        except Exception as e:
            print(f" Resume failed: {e}")
    
    def mute(self):
        """Mute microphone"""
        try:
            ci = self.getInfo()
            for mi in ci.media:
                if mi.type == pj.PJMEDIA_TYPE_AUDIO:
                    am = pj.Endpoint.instance().audDevManager()
                    am.getCaptureDevMedia().adjustTxLevel(0.0)
            self.is_muted = True
            print(" Microphone muted")
        except Exception as e:
            print(f" Mute failed: {e}")
    
    def unmute(self):
        """Unmute microphone"""
        try:
            ci = self.getInfo()
            for mi in ci.media:
                if mi.type == pj.PJMEDIA_TYPE_AUDIO:
                    am = pj.Endpoint.instance().audDevManager()
                    am.getCaptureDevMedia().adjustTxLevel(1.0)
            self.is_muted = False
            print(" Microphone unmuted")
        except Exception as e:
            print(f" Unmute failed: {e}")
    
    def send_dtmf(self, digits):
        """Send DTMF tones"""
        try:
            self.dialDtmf(digits)
            print(f" DTMF sent: {digits}")
        except Exception as e:
            print(f" DTMF failed: {e}")


class MyAccount(pj.Account):
    """Enhanced Account class"""
    
    def __init__(self, client):
        pj.Account.__init__(self)
        self.client = client
        self.current_call: Optional[MyCall] = None
        self.db_session = get_session()
    
    def onRegState(self, prm):
        """Called when registration state changes"""
        ai = self.getInfo()
        status_code = ai.regStatus
        status_text = ai.regStatusText
        
        if status_code == 200:
            print(f" Registration successful: {status_text}")
        else:
            print(f" Registration failed: {status_code} - {status_text}")
    
    def onIncomingCall(self, prm):
        """Called on incoming call"""
        call = MyCall(self, prm.callId)
        call_info = call.getInfo()
        remote_uri = call_info.remoteUri
        
        print(f" Incoming call from: {remote_uri}")
        
        # Create call record
        call_record = CallHistory(
            remote_uri=remote_uri,
            direction='inbound',
            status='ringing',
            start_time=datetime.utcnow()
        )
        self.db_session.add(call_record)
        self.db_session.commit()
        call.call_record = call_record
        
        # Auto-answer if enabled
        if self.client.config.get('call', {}).get('auto_answer', False):
            call_prm = pj.CallOpParam()
            call_prm.statusCode = 200
            call.answer(call_prm)
            print(" Auto-answered call")
        else:
            # Ring
            call_prm = pj.CallOpParam()
            call_prm.statusCode = 180
            call.answer(call_prm)
            print(" Ringing...")


class SIPClient:
    """Main SIP Client"""
    
    def __init__(self, config_path='config.yaml'):
        """Initialize SIP client"""
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.ep = None
        self.account = None
        self.transport = None
        
    def start(self):
        """Start SIP client"""
        if not PJSUA2_AVAILABLE:
            print("[WARN] Skipping SIP client startup - PJSUA2 not available")
            return
            
        try:
            # Create endpoint
            self.ep = pj.Endpoint()
            self.ep.libCreate()
            
            # Initialize endpoint
            ep_cfg = pj.EpConfig()
            ep_cfg.logConfig.level = 4
            ep_cfg.logConfig.consoleLevel = 4
            self.ep.libInit(ep_cfg)
            
            # Create transport
            sip_config = self.config.get('sip', {})
            transport_type = pj.PJSIP_TRANSPORT_UDP if sip_config.get('transport', 'UDP') == 'UDP' else pj.PJSIP_TRANSPORT_TCP
            
            tcfg = pj.TransportConfig()
            tcfg.port = sip_config.get('port', 5060)
            self.transport = self.ep.transportCreate(transport_type, tcfg)
            
            # Start library
            self.ep.libStart()
            
            print(f" SIP Endpoint started on port {tcfg.port}")
            
            # Register account
            self.register()
            
        except pj.Error as e:
            print(f" SIP initialization error: {e}")
            raise
    
    def register(self):
        """Register SIP account"""
        try:
            sip_config = self.config.get('sip', {})
            
            # Create account config
            acc_cfg = pj.AccountConfig()
            acc_cfg.idUri = f"sip:{sip_config['username']}@{sip_config['domain']}"
            acc_cfg.regConfig.registrarUri = f"sip:{sip_config['domain']}"
            
            # Add credentials
            cred = pj.AuthCredInfo()
            cred.scheme = "digest"
            cred.realm = "*"
            cred.username = sip_config['username']
            cred.dataType = 0
            cred.data = sip_config['password']
            acc_cfg.sipConfig.authCreds.append(cred)
            
            # Create account
            self.account = MyAccount(self)
            self.account.create(acc_cfg)
            
            print(f" Registering: {acc_cfg.idUri}")
            
        except pj.Error as e:
            print(f" Registration error: {e}")
            raise
    
    def make_call(self, destination):
        """Make outgoing call"""
        # Feature: Demo Mode / Simulation
        if not PJSUA2_AVAILABLE:
            print(f"[WARN] DEMO MODE: Simulating call to {destination}")
            
            # Create a mock call object
            class MockCall:
                def __init__(self):
                    self.info = type('Info', (), {'stateText': 'CONFIRMED', 'remoteUri': destination, 'connectDuration': type('Dur', (), {'sec': 0})()})()
                    self.on_hold = False
                    self.is_muted = False
                    self.start_time = datetime.utcnow()
                    
                def getInfo(self):
                    # Update duration
                    duration = (datetime.utcnow() - self.start_time).total_seconds()
                    self.info.connectDuration.sec = int(duration)
                    return self.info
                    
                def hangup(self, prm):
                    print("Demo call ended")
                    
                def hold(self):
                    self.on_hold = True
                    print("Demo call held")
                    
                def resume(self):
                    self.on_hold = False
                    print("Demo call resumed")
                    
                def mute(self):
                    self.is_muted = True
                    print("Demo call muted")
                    
                def unmute(self):
                    self.is_muted = False
                    print("Demo call unmuted")
                    
                def send_dtmf(self, digits):
                    print(f"Demo DTMF: {digits}")

            # Assign to account
            if not self.account:
                self.account = type('MockAccount', (), {'current_call': None})()
            
            mock_call = MockCall()
            self.account.current_call = mock_call
            
            # Create database record
            db_session = None
            try:
                db_session = get_session()
                call_record = CallHistory(
                    remote_uri=destination,
                    direction='outbound',
                    status='answered',
                    start_time=datetime.utcnow()
                )
                db_session.add(call_record)
                db_session.commit()
            except Exception as e:
                print(f"[WARN] Demo call history write failed: {e}")
            finally:
                if db_session:
                    db_session.close()
            
            return mock_call

        try:
            if not self.account:
                print(" Not registered!")
                return None
            
            sip_config = self.config.get('sip', {})
            
            # Format destination
            if not destination.startswith('sip:'):
                destination = f"sip:{destination}@{sip_config['domain']}"
            
            print(f" Calling: {destination}")
            
            # Create call record
            db_session = get_session()
            call_record = CallHistory(
                remote_uri=destination,
                direction='outbound',
                status='calling',
                start_time=datetime.utcnow()
            )
            db_session.add(call_record)
            db_session.commit()
            
            # Make call
            call = MyCall(self.account)
            call.call_record = call_record
            
            prm = pj.CallOpParam(True)
            call.makeCall(destination, prm)
            
            return call
            
        except Exception as e:
            print(f"Call failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def answer_call(self):
        """Answer incoming call"""
        if self.account and self.account.current_call:
            if not PJSUA2_AVAILABLE:
                print(" Answered (Demo)")
                return
            try:
                prm = pj.CallOpParam()
                prm.statusCode = 200
                self.account.current_call.answer(prm)
                print(" Call answered")
            except Exception as e:
                print(f" Answer failed: {e}")
        else:
            print(" No incoming call")
    
    def hangup(self):
        """Hangup current call"""
        if self.account and self.account.current_call:
            if not PJSUA2_AVAILABLE:
                try:
                    self.account.current_call.hangup(None)
                except Exception:
                    pass
                self.account.current_call = None
                print(" Call ended (Demo)")
                return
            try:
                prm = pj.CallOpParam()
                self.account.current_call.hangup(prm)
                print(" Call ended")
            except Exception as e:
                print(f" Hangup failed: {e}")
        else:
            print(" No active call")
    
    def get_call_status(self):
        """Get current call status"""
        if self.account and self.account.current_call:
            # Handle Mock/Demo call
            if not PJSUA2_AVAILABLE:
                ci = self.account.current_call.getInfo()
                return {
                    'active': True,
                    'state': ci.stateText,
                    'remote_uri': ci.remoteUri,
                    'duration': ci.connectDuration.sec,
                    'on_hold': self.account.current_call.on_hold,
                    'is_muted': self.account.current_call.is_muted
                }
                
            # Handle Real PJSUA2 call
            ci = self.account.current_call.getInfo()
            return {
                'active': True,
                'state': ci.stateText,
                'remote_uri': ci.remoteUri,
                'duration': ci.connectDuration.sec if ci.connectDuration else 0,
                'on_hold': self.account.current_call.on_hold,
                'is_muted': self.account.current_call.is_muted
            }
        return {'active': False}
    
    def stop(self):
        """Stop SIP client"""
        if not PJSUA2_AVAILABLE:
            print(" SIP client stopped (Demo)")
            return
            
        try:
            if self.account:
                self.account.shutdown()
            if self.transport and self.ep:
                self.ep.transportClose(self.transport)
            if self.ep:
                self.ep.libDestroy()
            print(" SIP client stopped")
        except pj.Error as e:
            print(f" Shutdown error: {e}")


if __name__ == '__main__':
    # Test SIP client
    client = SIPClient()
    client.start()
    
    print("\n=== SIP Client Ready ===")
    print("Commands:")
    print("  call <number> - Make a call")
    print("  answer - Answer incoming call")
    print("  hangup - End call")
    print("  status - Show call status")
    print("  quit - Exit")
    print("========================\n")
    
    try:
        while True:
            cmd = input("> ").strip().lower()
            
            if cmd.startswith('call '):
                number = cmd.split(' ', 1)[1]
                client.make_call(number)
            elif cmd == 'answer':
                client.answer_call()
            elif cmd == 'hangup':
                client.hangup()
            elif cmd == 'status':
                status = client.get_call_status()
                print(f"Status: {status}")
            elif cmd == 'quit':
                break
            else:
                print("Unknown command")
    
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    finally:
        client.stop()

