# Call Center (SIP + WebRTC + AI) — Project Skeleton

This repo is now organized as an end-to-end call-center roadmap project:

- **Asterisk config templates** (SIP/queues/routing/WebSocket)
- **Backend**: Django + Channels + ARI integration (events + call logs)
- **Frontend**: browser softphone (JsSIP/WebRTC) starter
- **Docker**: local dev stack (backend + postgres + redis)

> **Security**: This repo contains **no real credentials**. Use `.env` locally.

## ✅ Target Structure

```
SIP-Calling/
├── asterisk/
│   ├── sip.conf
│   ├── extensions.conf
│   ├── queues.conf
│   └── http.conf
├── backend/                 # Django project
│   ├── manage.py
│   ├── call_center/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── asgi.py
│   │   └── wsgi.py
│   ├── calls/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── consumers.py
│   │   └── ari.py
│   └── ai/
│       └── transcribe.py
├── frontend/
│   └── softphone.js
└── docker-compose.yml
```

## 🚀 Quick Start (Backend)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt

copy .env.example .env

python backend\manage.py migrate
python backend\manage.py runserver 0.0.0.0:8001
```

## 🧩 Next Steps

- **Asterisk**: copy the templates in `asterisk/` into your server under `/etc/asterisk/` and adjust extensions/agents.
- **Frontend**: use `frontend/softphone.js` as a starting point for JsSIP registration + call control.
- **ARI**: configure ARI credentials and run the Django ARI listener for call events.

## 🔐 Your SIP Credentials (local only)

Put your SIP values in `.env` (this file is **gitignored**). Example:

```env
SIP_ID=193636@157.51.150.247
SIP_DOMAIN=176.9.190.89
SIP_USERNAME=193636
SIP_PASSWORD=Salesforce@123
SIP_PORT=5060
SIP_TRANSPORT=UDP
```
