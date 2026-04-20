"""
gamification/routing.py
=======================
WebSocket URL routing for Channels.
"""

from django.urls import re_path
from gamification.consumers import LeaderboardConsumer

websocket_urlpatterns = [
    # Global leaderboard: ws://host/ws/leaderboards/global/
    re_path(
        r'ws/leaderboards/global/$',
        LeaderboardConsumer.as_asgi(),
        kwargs={'leaderboard_type': 'global'}
    ),

    # Trait-based leaderboard: ws://host/ws/leaderboards/trait/{trait_id}/
    re_path(
        r'ws/leaderboards/trait/(?P<trait_id>[\w-]+)/$',
        LeaderboardConsumer.as_asgi(),
        kwargs={'leaderboard_type': 'trait'}
    ),

    # Community leaderboard: ws://host/ws/leaderboards/community/{community_id}/
    re_path(
        r'ws/leaderboards/community/(?P<community_id>\d+)/$',
        LeaderboardConsumer.as_asgi(),
        kwargs={'leaderboard_type': 'community'}
    ),
]
