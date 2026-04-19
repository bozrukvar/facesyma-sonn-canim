"""
admin_api/routing.py
====================
WebSocket URL routing for admin dashboard.
"""

from django.urls import re_path
from admin_api.consumers import AdminLiveConsumer

websocket_urlpatterns = [
    re_path(r'ws/admin/live/$', AdminLiveConsumer.as_asgi()),
]
