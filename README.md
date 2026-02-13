# 📞 SIP Softphone Client

A modern, full-featured SIP softphone built with Python, PJSUA2, FastAPI, and AI-powered analytics.

## ✨ Features

- 📱 **Full SIP Client**: Register, make/receive calls, hold, mute, DTMF
- 🎙️ **Call Recording**: Automatic recording with WAV format
- 🌐 **Modern Web UI**: Beautiful glassmorphism design with real-time updates
- 👥 **Contact Management**: Save and quick-dial contacts
- 📜 **Call History**: Track all calls with duration and status
- 🤖 **AI Analytics**: 
  - Speech-to-text transcription
  - Sentiment analysis
  - Call summarization
- 🎨 **Premium Design**: Gradient backgrounds, smooth animations, responsive layout

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **Visual Studio Build Tools** (for Windows)
- **SIP Account** (server IP, username, password)

### Installation

#### Option 1: Automatic Setup (Recommended)

```powershell
# Run the setup script
.\setup.ps1
```

#### Option 2: Manual Setup

```powershell
# 1. Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Initialize database
python models.py

# 4. Configure SIP credentials (edit config.yaml)
# Update with your SIP server details
```

### ⚙️ Configuration

Your SIP credentials are already configured in `config.yaml`:

```yaml
sip:
  domain: "176.9.190.89"
  username: "193636"
  password: "Salesforce@123"
  port: 5060
  transport: "UDP"
```

To change settings, edit `config.yaml` and customize:
- Audio settings (sample rate, echo cancellation)
- Recording options (path, auto-record)
- AI features (enable/disable transcription, sentiment)
- Web API port

### 🎯 Running the Application

```powershell
# Start the SIP softphone
python call.py
```

The application will:
1. ✅ Initialize the database
2. ✅ Load AI models (if enabled)
3. ✅ Register to SIP server (176.9.190.89)
4. ✅ Start web server on http://localhost:8000

### 🌐 Using the Web Interface

Open your browser to **http://localhost:8000**

**Features:**
- **Dialer**: Enter number or SIP URI and click Call
- **Dialpad**: Click numbers or use for DTMF during calls
- **Call Controls**: Mute, hold, answer, hangup
- **Contacts Tab**: Add and manage contacts for quick dialing
- **History Tab**: View past calls, play recordings, see AI analytics

## 📚 API Documentation

Interactive API docs available at: **http://localhost:8000/docs**

### Key Endpoints

#### Call Control
- `POST /api/call/make` - Make outgoing call
- `POST /api/call/answer` - Answer incoming call
- `POST /api/call/hangup` - End call
- `POST /api/call/hold` - Put call on hold
- `POST /api/call/resume` - Resume held call
- `POST /api/call/mute` - Mute microphone
- `POST /api/call/unmute` - Unmute microphone
- `POST /api/call/dtmf` - Send DTMF tones
- `GET /api/call/status` - Get current call status

#### Call History
- `GET /api/history` - Get call history
- `GET /api/history/{id}` - Get specific call details
- `GET /api/history/{id}/recording` - Download recording

#### Contacts
- `GET /api/contacts` - List all contacts
- `POST /api/contacts` - Add new contact
- `DELETE /api/contacts/{id}` - Delete contact

## 🔧 PJSUA2 Installation

### Windows Installation

PJSUA2 is required but not available via pip on Windows. Here are your options:

#### Option 1: Try pip (may work)
```powershell
pip install pjsua2
```

#### Option 2: Build from source

1. **Install Visual Studio Build Tools**
   - Download from: https://visualstudio.microsoft.com/downloads/
   - Install "Desktop development with C++"

2. **Clone and build PJSIP**
   ```powershell
   git clone https://github.com/pjsip/pjproject.git
   cd pjproject
   
   # Build for Python
   python configure
   nmake
   nmake install
   ```

3. **Build Python bindings**
   ```powershell
   cd pjsip-apps/src/swig/python
   python setup.py install
   ```

#### Option 3: Docker (Easiest)

Use the pre-configured Docker image (coming soon).

## 🤖 AI Features

AI analytics automatically process call recordings:

### Speech-to-Text
- Uses Google Speech Recognition API
- Transcribes call audio to text
- No API key required for basic usage

### Sentiment Analysis
- Analyzes emotional tone of conversation
- Provides positive/negative/neutral classification
- Uses DistilBERT model from HuggingFace

### Call Summarization
- Generates concise summary of call content
- Uses BART model from Facebook AI
- Minimum 50 words required for meaningful summary

**Configure in config.yaml:**
```yaml
ai:
  enabled: true
  transcription: true
  sentiment_analysis: true
  call_summary: true
```

## 📁 Project Structure

```
SIP-Calling/
├── call.py              # Main application entry point
├── sip_client.py        # PJSUA2 SIP client implementation
├── api.py               # FastAPI REST API server
├── models.py            # Database models (SQLAlchemy)
├── ai_analytics.py      # AI/ML processing
├── config.yaml          # Configuration file
├── requirements.txt     # Python dependencies
├── static/
│   ├── index.html       # Web UI
│   ├── style.css        # Glassmorphism styling
│   └── app.js           # Frontend JavaScript
├── recordings/          # Call recordings (auto-created)
└── sip_client.db        # SQLite database (auto-created)
```

## 🎨 Web UI Features

- **Glassmorphism Design**: Frosted glass effect with backdrop blur
- **Gradient Backgrounds**: Animated color gradients
- **Smooth Animations**: Pulse effects, hover states, transitions
- **Real-time Updates**: Call status updates every second
- **Responsive Layout**: Works on desktop and mobile
- **Modern Typography**: Inter font family

## 🔒 Security Notes

- **Credentials**: Your SIP password is stored in `config.yaml`
- **Gitignore**: `.env` and `config.yaml` should be added to `.gitignore` for production
- **Network**: The API server binds to `0.0.0.0` by default (accessible from network)
- **Production**: Use HTTPS and authentication for production deployments

## 🐛 Troubleshooting

### PJSUA2 Import Error
```
ImportError: No module named 'pjsua2'
```
**Solution**: Install PJSUA2 using one of the methods above

### SIP Registration Failed
```
❌ Registration failed: 401 - Unauthorized
```
**Solution**: Check SIP credentials in `config.yaml`

### No Audio During Call
**Solution**: 
- Check audio devices (mic/speakers)
- Verify firewall allows RTP ports (typically 8000-8100)
- Check SIP server firewall/NAT settings

### AI Models Not Loading
```
⚠️ Failed to load AI models
```
**Solution**:
```powershell
pip install transformers torch sentencepiece
```

## 📝 Usage Examples

### Make a Call via API

```python
import requests

response = requests.post('http://localhost:8000/api/call/make', 
    json={'destination': '1002'})
print(response.json())
```

### Get Call History via API

```python
import requests

response = requests.get('http://localhost:8000/api/history')
calls = response.json()['calls']

for call in calls:
    print(f"{call['remote_uri']} - {call['duration']}s")
```

### Add Contact via API

```python
import requests

response = requests.post('http://localhost:8000/api/contacts',
    json={
        'name': 'John Doe',
        'sip_uri': 'sip:john@example.com'
    })
print(response.json())
```

## 🚧 Roadmap

- [ ] Video calling support
- [ ] Conference calls
- [ ] Call transfer
- [ ] Voicemail
- [ ] Push notifications for incoming calls
- [ ] Mobile app (React Native)
- [ ] Call quality metrics
- [ ] Detailed analytics dashboard

## 📄 License

MIT License - Feel free to use and modify

## 🤝 Contributing

Contributions welcome! Please open an issue or PR.

## 📧 Support

For issues or questions:
- Check the troubleshooting section
- Review API docs at `/docs`
- Check PJSIP documentation: https://www.pjsip.org/

---

**Built with ❤️ using Python, PJSUA2, FastAPI, and AI**
