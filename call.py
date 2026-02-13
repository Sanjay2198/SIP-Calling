"""
SIP Softphone - Main Application
Integrates SIP client, web API, and AI analytics
"""
import sys
import yaml
import threading
import uvicorn
import time
from models import init_db
from sip_client import SIPClient
from ai_analytics import get_ai_analytics

def main():
    """Main application entry point"""
    print("=" * 60)
    print(" SIP Softphone Starting...")
    print("=" * 60)
    
    # Load configuration
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        print(" Configuration loaded")
    except Exception as e:
        print(f" Failed to load config: {e}")
        sys.exit(1)
    
    # Initialize database
    try:
        init_db()
        print(" Database initialized")
    except Exception as e:
        print(f" Database initialization failed: {e}")
        sys.exit(1)
    
    # Initialize AI analytics
    try:
        ai = get_ai_analytics()
        print("AI analytics initialized")
    except Exception as e:
        print(f" AI analytics initialization failed: {e}")
    
    # Start SIP client in background
    sip_client = None
    def start_sip():
        nonlocal sip_client
        try:
            from sip_client import PJSUA2_AVAILABLE
            if not PJSUA2_AVAILABLE:
                print("  SIP client disabled - PJSUA2 not installed")
                print("   Web UI and API will work in demo mode")
                return
            
            sip_client = SIPClient()
            sip_client.start()
        except Exception as e:
            print(f" SIP client failed: {e}")
            print("   Continuing without SIP functionality...")
    
    sip_thread = threading.Thread(target=start_sip, daemon=True)
    sip_thread.start()
    
    # Give SIP client time to start
    time.sleep(2)
    
    # Start web server
    print("\n" + "=" * 60)
    print(" Starting Web Server...")
    print("=" * 60)
    
    api_config = config.get('api', {})
    host = api_config.get('host', '0.0.0.0')
    port = api_config.get('port', 8000)
    
    print(f"\n SIP Softphone is ready!")
    print(f" Web UI: http://localhost:{port}")
    print(f" API Docs: http://localhost:{port}/docs")
    print(f" SIP Server: {config['sip']['domain']}:{config['sip']['port']}")
    print(f" SIP User: {config['sip']['username']}\n")
    print("Press Ctrl+C to stop\n")
    
    try:
        import uvicorn
        from api import app
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n Shutting down...")
        if sip_client:
            sip_client.stop()
        print(" Goodbye!")
    except Exception as e:
        print(f" Server error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
