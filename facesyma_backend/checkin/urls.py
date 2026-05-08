"""checkin/urls.py"""
from django.urls import path
from .views import CheckinView, CheckinHistoryView, CheckinStreakView

urlpatterns = [
    path('',         CheckinView.as_view(),        name='checkin'),
    path('history/', CheckinHistoryView.as_view(), name='checkin-history'),
    path('streak/',  CheckinStreakView.as_view(),  name='checkin-streak'),
]
