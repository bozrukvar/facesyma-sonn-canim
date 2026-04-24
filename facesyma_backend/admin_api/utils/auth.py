"""
admin_api/utils/auth.py
=======================
Admin JWT token yönetimi ve doğrulaması.
"""

import time
import hashlib
import hmac
import os
import secrets
import string
import jwt
from datetime import datetime
from django.conf import settings
from django.http import JsonResponse
from admin_api.utils.mongo import get_admin_col as _get_admin_col_pooled, _next_id

_PBKDF2_ITERATIONS = 260_000
_ADMIN_JWT_SECRET: str = settings.ADMIN_JWT_SECRET
_ADMIN_JWT_EXP_HOURS: int = settings.ADMIN_JWT_EXP_HOURS
_JWT_SECRET: str = settings.JWT_SECRET


def _get_admin_col():
    """MongoDB admin_users — pooled connection üzerinden döner."""
    return _get_admin_col_pooled()


def _hash(pw: str) -> str:
    """Hash a password with PBKDF2-HMAC-SHA256 + random salt.

    Format: pbkdf2:sha256:<iterations>$<hex-salt>$<hex-hash>
    """
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha256', pw.encode(), salt, _PBKDF2_ITERATIONS)
    return f'pbkdf2:sha256:{_PBKDF2_ITERATIONS}${salt.hex()}${dk.hex()}'


def _check_hash(pw: str, stored: str) -> bool:
    """Verify a password against a stored hash.

    Supports both new PBKDF2 format and legacy bare SHA256 hashes so that
    existing admin accounts continue to work until their password is next changed.
    """
    _bfh = bytes.fromhex
    _pwe = pw.encode
    _hcd = hmac.compare_digest
    if stored.startswith('pbkdf2:sha256:'):
        try:
            _, _, rest = stored.split(':', 2)
            iterations_str, salt_hex, dk_hex = rest.split('$')
            iterations = int(iterations_str)
            salt = _bfh(salt_hex)
            expected = _bfh(dk_hex)
            computed = hashlib.pbkdf2_hmac('sha256', _pwe(), salt, iterations)
            return _hcd(computed, expected)
        except Exception:
            return False
    # Legacy: bare SHA256 (no salt) — accept but plan upgrade on login
    return _hcd(
        hashlib.sha256(_pwe()).hexdigest(),
        stored,
    )


def _next_admin_id(col) -> int:
    """Atomik admin ID üretimi — race condition yok."""
    return _next_id(col)


def _make_admin_token(admin_id: int, email: str, role: str = "admin") -> dict:
    """
    Admin JWT token'ı oluştur.

    Returns: {access, refresh}
    """
    now = int(time.time())
    admin_exp = _ADMIN_JWT_EXP_HOURS * 3600
    _jwe = jwt.encode

    access = _jwe(
        {
            'admin_id': admin_id,
            'email': email,
            'role': role,
            'is_admin': True,
            'type': 'admin_access',
            'exp': now + admin_exp
        },
        _ADMIN_JWT_SECRET,
        algorithm='HS256'
    )

    refresh = _jwe(
        {
            'admin_id': admin_id,
            'type': 'admin_refresh',
            'exp': now + (7 * 86400)  # 7 gün
        },
        _ADMIN_JWT_SECRET,
        algorithm='HS256'
    )

    return {'access': access, 'refresh': refresh}


def _decode_admin_token(request) -> dict:
    """
    Request'ten admin token'ı çıkar ve decode et.

    Raises: ValueError (token yok veya geçersiz)
    Returns: decoded payload
    """
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        raise ValueError('Admin token not found.')

    token = auth.split(' ', 1)[1]
    try:
        payload = jwt.decode(token, _ADMIN_JWT_SECRET, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError('Admin token has expired.')
    except Exception:
        raise ValueError('Invalid or malformed token.')


def _require_admin(request) -> dict:
    """
    Admin endpoint'lerinde çağrılacak kontrol fonksiyonu.

    Returns: admin payload {admin_id, email, role, ...}
    Raises: ValueError (401) veya PermissionError (403)
    """
    try:
        payload = _decode_admin_token(request)
    except ValueError:
        raise

    # Token type kontrol
    _pget = payload.get
    if _pget('type') != 'admin_access':
        raise PermissionError('Invalid token type.')

    # is_admin kontrol
    if not _pget('is_admin'):
        raise PermissionError('Admin permissions required.')

    # Veritabanında active mi kontrol
    col = _get_admin_col()
    admin = col.find_one({'id': payload['admin_id']}, {'_id': 0, 'is_active': 1})
    if not admin or not admin.get('is_active'):
        raise PermissionError('Admin account is inactive.')

    return payload


def _admin_dict(admin: dict) -> dict:
    """Admin dokümanını API response'unda kullanılacak formata dönüştür"""
    _aget = admin.get
    return {
        'id': _aget('id'),
        'email': _aget('email'),
        'username': _aget('username'),
        'role': _aget('role', 'admin'),
        'created_at': str(_aget('created_at', '')),
        'last_login': str(_aget('last_login', '')) if _aget('last_login') else None,
    }


def _get_user_id(request) -> int | None:
    """
    Token'dan user_id çıkar. Token yoksa None döner (anonim izin).
    Regular user authentication helper.
    """
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    try:
        payload = jwt.decode(
            auth.split(' ', 1)[1], _JWT_SECRET, algorithms=['HS256']
        )
        return payload.get('user_id')
    except Exception:
        return None


def _require_auth(request) -> int:
    """
    User authentication control function - extracts user_id from Bearer token.

    Raises: PermissionError (401)
    Returns: user_id
    """
    uid = _get_user_id(request)
    if uid is None:
        raise PermissionError('Authentication required.')
    return uid


def create_default_admin(email='admin@facesyma.com', password=None, username='admin') -> bool:
    """
    Varsayılan admin kullanıcısı oluştur.

    Returns: True (yeni created), False (zaten var)
    """
    col = _get_admin_col()

    # Zaten var mı kontrol et
    existing = col.find_one({'email': email}, {'_id': 1})
    if existing:
        return False

    if password is None:
        alphabet = string.ascii_letters + string.digits + '!@#$%^&*'
        password = ''.join(secrets.choice(alphabet) for _ in range(20))
        print(f'[create_default_admin] Temporary password: {password}')

    # Yeni admin oluştur
    admin_id = _next_admin_id(col)
    admin_doc = {
        'id': admin_id,
        'email': email,
        'username': username,
        'password': _hash(password),
        'role': 'superadmin',
        'is_active': True,
        'created_at': datetime.utcnow().isoformat(),
        'last_login': None,
    }

    col.insert_one(admin_doc)
    return True
