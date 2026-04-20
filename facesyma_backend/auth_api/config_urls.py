"""
auth_api/config_urls.py
=======================
Config endpoint routing.
"""

from django.urls import path
from .config_views import AppConfigView

urlpatterns = [
    path('', AppConfigView.as_view(), name='app-config'),
]
