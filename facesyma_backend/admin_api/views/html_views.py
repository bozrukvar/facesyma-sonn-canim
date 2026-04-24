"""
admin_api/views/html_views.py
=============================
HTML panel views with Django template rendering.
API calls inside templates require a valid JWT (enforced server-side).
HTML shell is also gated by an 'admin_session' cookie set at login.
"""

from django.shortcuts import render, redirect
from django.views import View


def _admin_session_required(request):
    """Return a redirect response if admin_session cookie is absent, else None."""
    if not request.COOKIES.get('admin_session'):
        return redirect('/admin/login/')
    return None


class AdminLoginHTMLView(View):
    def get(self, request):
        if request.COOKIES.get('admin_session'):
            return redirect('/admin/')
        return render(request, 'admin/login.html')


class AdminDashboardView(View):
    def get(self, request):
        guard = _admin_session_required(request)
        if guard:
            return guard
        return render(request, 'admin/dashboard.html')


class AdminUsersView(View):
    def get(self, request):
        guard = _admin_session_required(request)
        if guard:
            return guard
        return render(request, 'admin/users.html')


class AdminDatabaseView(View):
    def get(self, request):
        guard = _admin_session_required(request)
        if guard:
            return guard
        return render(request, 'admin/database.html')


class AdminRenewalsView(View):
    def get(self, request):
        guard = _admin_session_required(request)
        if guard:
            return guard
        return render(request, 'admin/renewals.html')


class AdminPaymentsView(View):
    def get(self, request):
        guard = _admin_session_required(request)
        if guard:
            return guard
        return render(request, 'admin/payments.html')


class AdminReviewsView(View):
    def get(self, request):
        guard = _admin_session_required(request)
        if guard:
            return guard
        return render(request, 'admin/reviews.html')


class AdminCoachView(View):
    def get(self, request):
        guard = _admin_session_required(request)
        if guard:
            return guard
        return render(request, 'admin/coach.html')


class SubscriptionDashboardHTMLView(View):
    def get(self, request):
        guard = _admin_session_required(request)
        if guard:
            return guard
        return render(request, 'admin/subscriptions.html')


class AdminReportsView(View):
    def get(self, request):
        guard = _admin_session_required(request)
        if guard:
            return guard
        return render(request, 'admin/reports.html')


class AdminAnalyticsView(View):
    def get(self, request):
        guard = _admin_session_required(request)
        if guard:
            return guard
        return render(request, 'admin/analytics.html')


class AdminInsightsView(View):
    def get(self, request):
        guard = _admin_session_required(request)
        if guard:
            return guard
        return render(request, 'admin/insights.html')


class AdminLiveDashboardView(View):
    def get(self, request):
        guard = _admin_session_required(request)
        if guard:
            return guard
        return render(request, 'admin/live_dashboard.html')


class AdminAuditLogView(View):
    def get(self, request):
        guard = _admin_session_required(request)
        if guard:
            return guard
        return render(request, 'admin/audit_log.html')


class AdminAlertsView(View):
    def get(self, request):
        guard = _admin_session_required(request)
        if guard:
            return guard
        return render(request, 'admin/alerts.html')


class AdminLogoutView(View):
    def get(self, request):
        response = redirect('/admin/login/')
        response.delete_cookie('admin_session', path='/')
        return response
