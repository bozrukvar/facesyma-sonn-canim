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
