"""
admin_api/views/auth_views.py
==============================
Admin kimlik doğrulama endpoint'leri.
"""

import json
from datetime import datetime
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from admin_api.utils.auth import (
    _get_admin_col,
    _hash,
    _next_admin_id,
    _make_admin_token,
    _require_admin,
    _admin_dict
)
from admin_api.utils.mongo import get_admin_col


def _json(request):
    """Request body JSON'ı parse et"""
    try:
        return json.loads(request.body)
    except Exception:
        return {}


# ═══════════════════════════════════════════════════════════════════════════════
# ── Admin Giriş ────────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class AdminLoginView(View):
    """
    Admin giriş endpoint'i.

    POST /api/v1/admin/auth/login/
    Body: {email, password}
    Return: {access, refresh, admin}
    """

    def post(self, request):
        data = _json(request)
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not email or not password:
            return JsonResponse(
                {'detail': 'Email ve şifre zorunlu.'},
                status=400
            )

        col = get_admin_col()
        admin = col.find_one({'email': email})

        if not admin or admin.get('password') != _hash(password):
            return JsonResponse(
                {'detail': 'Email veya şifre hatalı.'},
                status=401
            )

        if not admin.get('is_active'):
            return JsonResponse(
                {'detail': 'Admin hesabı deaktif.'},
                status=403
            )

        # Token üret
        tokens = _make_admin_token(
            admin['id'],
            email,
            admin.get('role', 'admin')
        )

        # Last login güncelle
        col.update_one(
            {'id': admin['id']},
            {'$set': {'last_login': datetime.now().isoformat()}}
        )

        return JsonResponse({
            **tokens,
            'admin': _admin_dict(admin)
        })


# ═══════════════════════════════════════════════════════════════════════════════
# ── Admin Profili ──────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class AdminMeView(View):
    """
    Admin profili getir.

    GET /api/v1/admin/auth/me/
    Header: Authorization: Bearer <token>
    Return: {id, email, username, role, created_at, last_login}
    """

    def get(self, request):
        try:
            payload = _require_admin(request)
            col = get_admin_col()
            admin = col.find_one({'id': payload['admin_id']})

            if not admin:
                return JsonResponse(
                    {'detail': 'Admin bulunamadı.'},
                    status=404
                )

            return JsonResponse(_admin_dict(admin))

        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)
        except Exception as e:
            return JsonResponse({'detail': str(e)}, status=500)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Admin Oluştur (Seed) ───────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

def create_default_admin():
    """
    İlk admin kullanıcısını oluştur.
    Veritabanında admin yoksa çağrılabilir.

    Kullanımı (Django shell'de):
        from admin_api.views.auth_views import create_default_admin
        create_default_admin()
    """
    col = get_admin_col()

    # Zaten varsa, yapma
    if col.find_one({'email': 'admin@facesyma.com'}):
        return "Admin zaten var."

    admin = {
        'id': _next_admin_id(col),
        'email': 'admin@facesyma.com',
        'username': 'admin',
        'password': _hash('admin123'),
        'role': 'superadmin',
        'is_active': True,
        'created_at': datetime.now().isoformat(),
        'last_login': None,
    }

    col.insert_one(admin)
    return f"✅ Admin oluşturuldu: {admin['email']}"
