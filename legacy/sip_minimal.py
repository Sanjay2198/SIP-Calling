# pyright: reportMissingImports=false, reportAssignmentType=false, reportAttributeAccessIssue=false
import sys
import time
import os
import yaml
import threading
from typing import Any

# Minimal Configuration - Edit directly if needed or loads from config.yaml
DEFAULT_CONFIG = {
    'sip': {
        'domain': 'pbx.example.com',
        'username': '1001',
        'password': 'change-me',
        'port': 5060,
        'transport': 'UDP'
    }
}

pj: Any
ALLOW_DEMO = os.getenv("ALLOW_DEMO", "false").strip().lower() in {"1", "true", "yes", "on"}
try:
    import pjsua2 as pj  # type: ignore[import-not-found]
    PJSUA2_AVAILABLE = True
    print(" PJSUA2 Library found")
except ImportError:
    PJSUA2_AVAILABLE = False
    print("  PJSUA2 Library NOT found - Running in DEMO MODE (Simulation)")
    # Mock classes for simulation
    class _PjFallback:
        class Call:
            def __init__(self, acc, call_id=None): pass
            def makeCall(self, dst, prm): pass
            def hangup(self, prm): pass
            def answer(self, prm): pass
        class Account:
            def __init__(self): pass
            def create(self, cfg): pass
            def shutdown(self): pass
        class Endpoint:
            def libCreate(self): pass
            def libInit(self, cfg): pass
            def libStart(self): pass
            def transportCreate(self, type, cfg): pass
            def libDestroy(self): pass
            def instance(self): return self
        class Error(Exception): pass
        class AccountConfig: 
            def __init__(self):
                self.regConfig = type('RegConfig', (), {'registrarUri': ''})()
                self.sipConfig = type('SipConfig', (), {'authCreds': []})()
        class EpConfig:
            def __init__(self):
                self.logConfig = type('LogConfig', (), {'level': 0, 'consoleLevel': 0})()
        class TransportConfig: pass
        class AuthCredInfo: pass
        class CallOpParam: 
            def __init__(self, useDefaultCallOp=False): 
                self.opt = type('Opt', (), {'flag': 0})()
                self.statusCode = 0
            
        PJSIP_TRANSPORT_UDP = 1
        PJSIP_TRANSPORT_TCP = 2
    pj = _PjFallback

class SimpleCall(pj.Call):
    def __init__(self, acc, call_id=None):
        pj.Call.__init__(self, acc, call_id)
        
    def onCallState(self, prm):
        print(f" Call State Change")

class SimpleAccount(pj.Account):
    def onRegState(self, prm):
        if not PJSUA2_AVAILABLE:
            print(" [DEMO] Registered successfully")
            return
        
        info = self.getInfo()
        print(f" Registration Status: {info.regStatusText} ({info.regStatus})")

    def onIncomingCall(self, prm):
        print(" Incoming Call!")
        call = SimpleCall(self, prm.callId)
        prm_op = pj.CallOpParam()
        prm_op.statusCode = 200
        call.answer(prm_op)
        print(" [DEMO] Auto-answered call")

class MinimalClient:
    def __init__(self):
        self.ep = None
        self.account = None
        
        # Try to load config.yaml, fallback to default
        try:
            with open('config.yaml', 'r') as f:
                self.config = yaml.safe_load(f)
        except:
            self.config = DEFAULT_CONFIG
            
    def start(self):
        print(f" Starting Minimal SIP Client...")
        print(f" Server: {self.config['sip']['domain']}")
        print(f" User: {self.config['sip']['username']}")
        
        if not PJSUA2_AVAILABLE:
            if not ALLOW_DEMO:
                raise RuntimeError(
                    "PJSUA2 is not installed. Real SIP calling is unavailable. "
                    "Set ALLOW_DEMO=true to allow simulated calls."
                )
            # Simulation startup
            self.account = SimpleAccount()
            self.account.onRegState(None)
            return

        try:
            self.ep = pj.Endpoint()
            self.ep.libCreate()
            
            ep_cfg = pj.EpConfig()
            self.ep.libInit(ep_cfg)
            
            tcfg = pj.TransportConfig()
            tcfg.port = self.config['sip'].get('port', 5060)
            self.ep.transportCreate(pj.PJSIP_TRANSPORT_UDP, tcfg)
            
            self.ep.libStart()
            
            # Account Config
            acc_cfg = pj.AccountConfig()
            domain = self.config['sip']['domain']
            user = self.config['sip']['username']
            pwd = self.config['sip']['password']
            
            acc_cfg.idUri = f"sip:{user}@{domain}"
            acc_cfg.regConfig.registrarUri = f"sip:{domain}"
            
            cred = pj.AuthCredInfo()
            cred.scheme = "digest"
            cred.realm = "*"
            cred.username = user
            cred.dataType = 0
            cred.data = pwd
            acc_cfg.sipConfig.authCreds.append(cred)
            
            self.account = SimpleAccount()
            self.account.create(acc_cfg)
            
        except pj.Error as e:
            print(f" Initialization Error: {e}")

    def make_call(self, uri):
        if not uri.startswith('sip:'):
            uri = f"sip:{uri}@{self.config['sip']['domain']}"
            
        print(f" Calling {uri}...")
        
        if PJSUA2_AVAILABLE:
            try:
                call = SimpleCall(self.account)
                prm = pj.CallOpParam(True)
                call.makeCall(uri, prm)
            except pj.Error as e:
                print(f" Call Failed: {e}")
        else:
            if not ALLOW_DEMO:
                raise RuntimeError("PJSUA2 is required for real calling.")
            print(" [DEMO] Call simulated successfully")
            print("  Call active (Press Ctrl+C to hangup)")

    def cleanup(self):
        if self.ep:
            self.ep.libDestroy()

if __name__ == "__main__":
    client = MinimalClient()
    try:
        client.start()
    except RuntimeError as exc:
        print(f" ERROR: {exc}")
        sys.exit(2)
    
    if len(sys.argv) > 1:
        destination = sys.argv[1]
        try:
            client.make_call(destination)
        except RuntimeError as exc:
            print(f" ERROR: {exc}")
            sys.exit(2)
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nUpdating...")
    else:
        print("\nUsage: python sip_minimal.py <number_to_call>")
        print("Example: python sip_minimal.py 1001")
        
    client.cleanup()
