"""analysis_api/routing.py — WebSocket URL patterns."""
from django.urls import re_path
from analysis_api.peer_chat_consumers import PeerChatConsumer
from analysis_api.community_chat_consumer import CommunityChatConsumer

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_id>[\w-]+)/$', PeerChatConsumer.as_asgi()),
    re_path(r'ws/community/(?P<community_id>[\w-]+)/chat/$', CommunityChatConsumer.as_asgi()),
]
