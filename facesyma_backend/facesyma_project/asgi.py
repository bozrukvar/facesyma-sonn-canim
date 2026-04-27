"""
facesyma_project/asgi.py
========================
ASGI config for Facesyma using Django Channels.

Supports both HTTP (Django) and WebSocket (Channels) protocols.
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facesyma_project.settings')

# Initialize Django ASGI application early to ensure app registry is populated
django_asgi_app = get_asgi_application()

# Import routing after Django initialization
from gamification.routing import websocket_urlpatterns as gamification_ws
from admin_api.routing import websocket_urlpatterns as admin_ws
from analysis_api.routing import websocket_urlpatterns as chat_ws

# Combine all WebSocket patterns
all_ws_patterns = gamification_ws + admin_ws + chat_ws

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            all_ws_patterns
        )
    ),
})

# Start background scheduler for subscription renewals, leaderboard snapshots, etc.
try:
    from admin_api.scheduler import start_scheduler
    start_scheduler()
except Exception as e:
    import logging
    logging.error(f"Failed to start scheduler: {e}")
