"""
admin_api/views/html_views.py
=============================
HTML panel views with Django template rendering.
"""

from django.shortcuts import render, redirect
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse

from admin_api.utils.auth import _require_admin, _make_admin_token
from admin_api.utils.mongo import get_admin_col
import json


def _json(request):
    """Request body JSON'ı parse et"""
    try:
        return json.loads(request.body)
    except Exception:
        return {}


# ═══════════════════════════════════════════════════════════════════════════════
# ── HTML Panel - Login ─────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

class AdminLoginHTMLView(View):
    """
    HTML Login sayfası.

    GET /admin/login/
    Return: HTML template
    """

    def get(self, request):
        return render(request, 'admin/login.html')


# ═══════════════════════════════════════════════════════════════════════════════
# ── HTML Panel - Dashboard ─────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

class AdminDashboardView(View):
    """
    HTML Dashboard sayfası (istatistikler + son kullanıcılar).

    GET /admin/
    """

    def get(self, request):
        try:
            _require_admin(request)
        except (ValueError, PermissionError):
            return redirect('/admin/login/')

        return render(request, 'admin/dashboard.html')


# ═══════════════════════════════════════════════════════════════════════════════
# ── HTML Panel - Users ─────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

class AdminUsersView(View):
    """
    HTML Kullanıcı yönetimi sayfası.

    GET /admin/users/
    """

    def get(self, request):
        try:
            _require_admin(request)
        except (ValueError, PermissionError):
            return redirect('/admin/login/')

        return render(request, 'admin/users.html')


# ═══════════════════════════════════════════════════════════════════════════════
# ── HTML Panel - Database ──────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

class AdminDatabaseView(View):
    """
    HTML Veritabanı (sıfat) yönetimi sayfası.

    GET /admin/database/
    """

    def get(self, request):
        try:
            _require_admin(request)
        except (ValueError, PermissionError):
            return redirect('/admin/login/')

        return render(request, 'admin/database.html')


# ═══════════════════════════════════════════════════════════════════════════════
# ── HTML Panel - Renewals (Abonelik Yenileme Otomasyonu) ──────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

class AdminRenewalsView(View):
    """
    HTML Abonelik yenileme otomasyonu yönetimi sayfası.

    GET /admin/renewals/
    """

    def get(self, request):
        try:
            _require_admin(request)
        except (ValueError, PermissionError):
            return redirect('/admin/login/')

        return render(request, 'admin/renewals.html')


# ═══════════════════════════════════════════════════════════════════════════════
# ── HTML Panel - Payments ──────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

class AdminPaymentsView(View):
    """
    HTML Ödeme yönetimi sayfası.

    GET /admin/payments/
    """

    def get(self, request):
        try:
            _require_admin(request)
        except (ValueError, PermissionError):
            return redirect('/admin/login/')

        return render(request, 'admin/payments.html')


# ═══════════════════════════════════════════════════════════════════════════════
# ── HTML Panel - Reviews ───────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

class AdminReviewsView(View):
    """
    HTML Yorum yönetimi sayfası.

    GET /admin/reviews/
    """

    def get(self, request):
        try:
            _require_admin(request)
        except (ValueError, PermissionError):
            return redirect('/admin/login/')

        return render(request, 'admin/reviews.html')


# ═══════════════════════════════════════════════════════════════════════════════
# ── HTML Panel - Coach DB ──────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

class AdminCoachView(View):
    """
    HTML Coach DB yönetimi sayfası.

    GET /admin/coach/
    """

    def get(self, request):
        try:
            _require_admin(request)
        except (ValueError, PermissionError):
            return redirect('/admin/login/')

        return render(request, 'admin/coach.html')


# ═══════════════════════════════════════════════════════════════════════════════
# ── HTML Panel - Subscription Dashboard ────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

class SubscriptionDashboardHTMLView(View):
    """
    HTML Subscription metrics dashboard (MRR, active subs, churn, user lookup).

    GET /admin/subscriptions/
    """

    def get(self, request):
        try:
            _require_admin(request)
        except (ValueError, PermissionError):
            return redirect('/admin/login/')

        return render(request, 'admin/subscriptions.html')


# ═══════════════════════════════════════════════════════════════════════════════
# ── HTML Panel - Reports ────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

class AdminReportsView(View):
    """
    HTML Raporlar sayfası (İstatistikler ve rapor oluşturma).

    GET /admin/reports/
    """

    def get(self, request):
        try:
            _require_admin(request)
        except (ValueError, PermissionError):
            return redirect('/admin/login/')

        return render(request, 'admin/reports.html')


# ═══════════════════════════════════════════════════════════════════════════════
# ── HTML Panel - Analytics Dashboard ────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

class AdminAnalyticsView(View):
    """
    HTML Analytics sayfası (kullanıcı analitikleri).

    GET /admin/analytics/
    """

    def get(self, request):
        try:
            _require_admin(request)
        except (ValueError, PermissionError):
            return redirect('/admin/login/')

        return render(request, 'admin/analytics.html')


# ═══════════════════════════════════════════════════════════════════════════════
# ── HTML Panel - User Insights (Date/Time/Module Analysis) ──────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

class AdminInsightsView(View):
    """
    HTML İçgörüler sayfası (Kullanıcı kayıt analizi, zaman örüntüleri, modül kullanımı).

    GET /admin/insights/
    """

    def get(self, request):
        try:
            _require_admin(request)
        except (ValueError, PermissionError):
            return redirect('/admin/login/')

        return render(request, 'admin/insights.html')


# ═══════════════════════════════════════════════════════════════════════════════
# ── HTML Panel - Live Dashboard ────────────────────────────────────────────────
# ═════════════════════════════════════════════════════════════════════════════════

class AdminLiveDashboardView(View):
    """
    Live Analytics Dashboard — 30-second polling.

    GET /admin/live/
    """

    def get(self, request):
        try:
            _require_admin(request)
        except (ValueError, PermissionError):
            return redirect('/admin/login/')

        return render(request, 'admin/live_dashboard.html')


# ═══════════════════════════════════════════════════════════════════════════════
# ── HTML Panel - Audit Log ─────────────────────────────────────────────────────
# ═════════════════════════════════════════════════════════════════════════════════

class AdminAuditLogView(View):
    """
    Audit Log — Admin activity trail.

    GET /admin/audit/
    """

    def get(self, request):
        try:
            _require_admin(request)
        except (ValueError, PermissionError):
            return redirect('/admin/login/')

        return render(request, 'admin/audit_log.html')


# ═══════════════════════════════════════════════════════════════════════════════
# ── HTML Panel - Alerts ────────────────────────────────────────────────────────
# ═════════════════════════════════════════════════════════════════════════════════

class AdminAlertsView(View):
    """
    Alerts — Automated alert rules.

    GET /admin/alerts/
    """

    def get(self, request):
        try:
            _require_admin(request)
        except (ValueError, PermissionError):
            return redirect('/admin/login/')

        return render(request, 'admin/alerts.html')


# ═══════════════════════════════════════════════════════════════════════════════
# ── Admin Logout ───────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

class AdminLogoutView(View):
    """
    Admin çıkış (localStorage'deki token temizlenir client-side).

    GET /admin/logout/
    Return: Redirect login
    """

    def get(self, request):
        return redirect('/admin/login/')
