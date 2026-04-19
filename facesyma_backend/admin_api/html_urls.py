"""
admin_api/html_urls.py
======================
HTML Panel routing (included at /admin/).
"""

from django.urls import path
from admin_api.views.html_views import (
    AdminLoginHTMLView, AdminDashboardView, AdminUsersView,
    AdminDatabaseView, AdminReviewsView, AdminCoachView,
    SubscriptionDashboardHTMLView, AdminLogoutView
)
from admin_api.views.subscription_dashboard_views import (
    SubscriptionMetricsView, UserSubscriptionDetailView, SubscriptionSearchView,
    ChurnAnalysisView
)

urlpatterns = [
    path('login/', AdminLoginHTMLView.as_view(), name='admin-html-login'),
    path('', AdminDashboardView.as_view(), name='admin-html-dashboard'),
    path('users/', AdminUsersView.as_view(), name='admin-html-users'),
    path('database/', AdminDatabaseView.as_view(), name='admin-html-database'),
    path('reviews/', AdminReviewsView.as_view(), name='admin-html-reviews'),
    path('coach/', AdminCoachView.as_view(), name='admin-html-coach'),
    path('subscriptions/', SubscriptionDashboardHTMLView.as_view(), name='admin-html-subscriptions'),

    path('logout/', AdminLogoutView.as_view(), name='admin-html-logout'),
]
