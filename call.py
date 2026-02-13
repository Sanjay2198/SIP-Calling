"""
SIP Softphone - Main Application
Integrates SIP client, web API, and AI analytics
"""
import sys
import socket
import yaml
from models import init_db
from ai_analytics import get_ai_analytics


def _is_port_available(host, port):
    """Return True if host:port can be bound by this process."""
    bind_host = "0.0.0.0" if host in ("0.0.0.0", "", "*") else host
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((bind_host, int(port)))
        return True
    except OSError:
        return False
    finally:
        sock.close()


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
    
    # Start web server
    print("\n" + "=" * 60)
    print(" Starting Web Server...")
    print("=" * 60)
    
    api_config = config.get('api', {})
    host = api_config.get('host', '0.0.0.0')
    port = api_config.get('port', 8000)

    if not _is_port_available(host, port):
        print(f" Port {port} is already in use on host {host}.")
        print(" Stop the existing process or change api.port in config.yaml.")
        sys.exit(1)
    
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
        print(" Goodbye!")
    except Exception as e:
        print(f" Server error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
