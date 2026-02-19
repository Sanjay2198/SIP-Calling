from __future__ import annotations

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

from calls.routing import websocket_urlpatterns

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "call_center.settings")

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": URLRouter(websocket_urlpatterns),
    }
)

