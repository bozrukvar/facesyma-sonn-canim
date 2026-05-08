"""goals/urls.py"""
from django.urls import path
from .views import GoalsView, GoalDetailView

urlpatterns = [
    path('',          GoalsView.as_view(),       name='goals-list'),
    path('<str:goal_id>/', GoalDetailView.as_view(), name='goal-detail'),
]
