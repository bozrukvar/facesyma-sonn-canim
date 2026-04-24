"""
admin_api/views/auth_views.py
==============================
Admin kimlik doğrulama endpoint'leri.
"""

import json
import secrets
import string
from datetime import datetime
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.cache import cache

from admin_api.utils.auth import (
    _get_admin_col,
    _hash,
    _check_hash,
    _next_admin_id,
    _make_admin_token,
    _require_admin,
    _admin_dict
)
from admin_api.utils.mongo import get_admin_col

_ADMIN_PROFILE_PROJECTION = {'_id': 0, 'id': 1, 'email': 1, 'username': 1,
                              'role': 1, 'created_at': 1, 'last_login': 1}
_ADMIN_LOGIN_PROJECTION   = {'_id': 1, 'id': 1, 'password': 1, 'is_active': 1, 'role': 1}


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

    _MAX_ATTEMPTS = 5   # stricter than user login — admin is a higher-value target
    _LOCKOUT_SECS = 900  # 15 minutes

    def post(self, request):
        data = _json(request)
        _dget = data.get
        email = _dget('email', '').strip().lower()
        password = _dget('password', '')

        if not email or not password:
            return JsonResponse(
                {'detail': 'Email and password are required.'},
                status=400
            )

        # Brute-force protection — IP + email based
        _rmg = request.META.get
        ip = _rmg('HTTP_X_FORWARDED_FOR', _rmg('REMOTE_ADDR', ''))
        cache_key = f'admin_login_fail:{ip}:{email}'
        fail_count = 0
        try:
            fail_count = cache.get(cache_key, 0)
            if fail_count >= self._MAX_ATTEMPTS:
                return JsonResponse(
                    {'detail': 'Too many failed attempts. Please wait 15 minutes.'},
                    status=429
                )
        except Exception:
            pass

        col = get_admin_col()
        admin = col.find_one({'email': email}, _ADMIN_LOGIN_PROJECTION)

        _stored_pw = admin.get('password', '') if admin else ''
        if not admin or not _check_hash(password, _stored_pw):
            try:
                cache.set(cache_key, fail_count + 1, timeout=self._LOCKOUT_SECS)
            except Exception:
                pass
            return JsonResponse(
                {'detail': 'Invalid email or password.'},
                status=401
            )

        try:
            cache.delete(cache_key)
        except Exception:
            pass

        _adget = admin.get
        if not _adget('is_active'):
            return JsonResponse(
                {'detail': 'Admin account is inactive.'},
                status=403
            )

        # Upgrade legacy bare-SHA256 hash to PBKDF2 on successful login
        _cuo = col.update_one
        if not _stored_pw.startswith('pbkdf2:'):
            _cuo({'_id': admin['_id']}, {'$set': {'password': _hash(password)}})

        # Token üret
        _adid = admin['id']
        tokens = _make_admin_token(
            _adid,
            email,
            _adget('role', 'admin')
        )

        # Last login güncelle
        _cuo(
            {'id': _adid},
            {'$set': {'last_login': datetime.utcnow().isoformat()}}
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
            admin = col.find_one({'id': payload['admin_id']}, _ADMIN_PROFILE_PROJECTION)

            if not admin:
                return JsonResponse(
                    {'detail': 'Admin not found.'},
                    status=404
                )

            return JsonResponse(_admin_dict(admin))

        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)
        except Exception as e:
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


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
    if col.find_one({'email': 'admin@facesyma.com'}, {'_id': 1}):
        return "Admin zaten var."

    alphabet = string.ascii_letters + string.digits + '!@#$%^&*'
    tmp_password = ''.join(secrets.choice(alphabet) for _ in range(20))

    admin = {
        'id': _next_admin_id(col),
        'email': 'admin@facesyma.com',
        'username': 'admin',
        'password': _hash(tmp_password),
        'role': 'superadmin',
        'is_active': True,
        'created_at': datetime.utcnow().isoformat(),
        'last_login': None,
    }

    col.insert_one(admin)
    return f"✅ Admin created: {admin['email']} | Temporary password: {tmp_password}"
