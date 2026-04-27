"""analysis_api/routing.py — P2P chat WebSocket URL patterns."""
from django.urls import re_path
from analysis_api.peer_chat_consumers import PeerChatConsumer

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_id>[\w-]+)/$', PeerChatConsumer.as_asgi()),
]
