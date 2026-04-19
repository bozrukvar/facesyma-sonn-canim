"""
admin_api/html_urls.py
======================
HTML Panel routing (included at /admin/).
"""

from django.urls import path
from admin_api.views.html_views import (
    AdminLoginHTMLView, AdminDashboardView, AdminUsersView,
    AdminPaymentsView, AdminRenewalsView, AdminDatabaseView, AdminReviewsView, AdminCoachView,
    SubscriptionDashboardHTMLView, AdminAnalyticsView, AdminReportsView, AdminInsightsView, AdminLiveDashboardView, AdminAuditLogView, AdminAlertsView, AdminLogoutView
)

urlpatterns = [
    path('login/', AdminLoginHTMLView.as_view(), name='admin-html-login'),
    path('', AdminDashboardView.as_view(), name='admin-html-dashboard'),
    path('users/', AdminUsersView.as_view(), name='admin-html-users'),
    path('payments/', AdminPaymentsView.as_view(), name='admin-html-payments'),
    path('renewals/', AdminRenewalsView.as_view(), name='admin-html-renewals'),
    path('analytics/', AdminAnalyticsView.as_view(), name='admin-html-analytics'),
    path('reports/', AdminReportsView.as_view(), name='admin-html-reports'),
    path('insights/', AdminInsightsView.as_view(), name='admin-html-insights'),
    path('live/', AdminLiveDashboardView.as_view(), name='admin-html-live'),
    path('audit/', AdminAuditLogView.as_view(), name='admin-html-audit'),
    path('alerts/', AdminAlertsView.as_view(), name='admin-html-alerts'),
    path('database/', AdminDatabaseView.as_view(), name='admin-html-database'),
    path('reviews/', AdminReviewsView.as_view(), name='admin-html-reviews'),
    path('coach/', AdminCoachView.as_view(), name='admin-html-coach'),
    path('subscriptions/', SubscriptionDashboardHTMLView.as_view(), name='admin-html-subscriptions'),
    path('logout/', AdminLogoutView.as_view(), name='admin-html-logout'),
]
