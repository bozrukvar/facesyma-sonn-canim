"""
admin_api/utils/auth.py
=======================
Admin JWT token yönetimi ve doğrulaması.
"""

import time
import hashlib
import jwt
from django.conf import settings
from django.http import JsonResponse
from pymongo import MongoClient


def _get_admin_col():
    """MongoDB admin_users collection'ına bağlan"""
    client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=30000)
    return client['facesyma-backend']['admin_users']


def _hash(pw: str) -> str:
    """Şifre hash'le (mevcut pattern)"""
    return hashlib.sha256(pw.encode()).hexdigest()


def _next_admin_id(col) -> int:
    """Sonraki admin ID'si (mevcut pattern)"""
    last = col.find_one(sort=[('id', -1)])
    return (last['id'] + 1) if last and 'id' in last else 1


def _make_admin_token(admin_id: int, email: str, role: str = "admin") -> dict:
    """
    Admin JWT token'ı oluştur.

    Returns: {access, refresh}
    """
    now = int(time.time())
    admin_exp = settings.ADMIN_JWT_EXP_HOURS * 3600

    access = jwt.encode(
        {
            'admin_id': admin_id,
            'email': email,
            'role': role,
            'is_admin': True,
            'type': 'admin_access',
            'exp': now + admin_exp
        },
        settings.ADMIN_JWT_SECRET,
        algorithm='HS256'
    )

    refresh = jwt.encode(
        {
            'admin_id': admin_id,
            'type': 'admin_refresh',
            'exp': now + (7 * 86400)  # 7 gün
        },
        settings.ADMIN_JWT_SECRET,
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
        raise ValueError('Admin token bulunamadı.')

    token = auth.split(' ', 1)[1]
    try:
        payload = jwt.decode(token, settings.ADMIN_JWT_SECRET, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError('Admin token süresi doldu.')
    except Exception as e:
        raise ValueError(f'Geçersiz token: {str(e)}')


def _require_admin(request) -> dict:
    """
    Admin endpoint'lerinde çağrılacak kontrol fonksiyonu.

    Returns: admin payload {admin_id, email, role, ...}
    Raises: ValueError (401) veya PermissionError (403)
    """
    try:
        payload = _decode_admin_token(request)
    except ValueError as e:
        raise ValueError(str(e))

    # Token type kontrol
    if payload.get('type') != 'admin_access':
        raise PermissionError('Geçersiz token tipi.')

    # is_admin kontrol
    if not payload.get('is_admin'):
        raise PermissionError('Admin yetkileri gerekli.')

    # Veritabanında active mi kontrol
    col = _get_admin_col()
    admin = col.find_one({'id': payload['admin_id']})
    if not admin or not admin.get('is_active'):
        raise PermissionError('Admin hesabı deaktif.')

    return payload


def _admin_dict(admin: dict) -> dict:
    """Admin dokümanını API response'unda kullanılacak formata dönüştür"""
    return {
        'id': admin.get('id'),
        'email': admin.get('email'),
        'username': admin.get('username'),
        'role': admin.get('role', 'admin'),
        'created_at': str(admin.get('created_at', '')),
        'last_login': str(admin.get('last_login', '')) if admin.get('last_login') else None,
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
            auth.split(' ', 1)[1], settings.JWT_SECRET, algorithms=['HS256']
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
        raise PermissionError('Kimlik doğrulama gerekli.')
    return uid


def create_default_admin(email='admin@facesyma.com', password='admin123', username='admin') -> bool:
    """
    Varsayılan admin kullanıcısı oluştur.

    Returns: True (yeni oluşturuldu), False (zaten var)
    """
    from datetime import datetime

    col = _get_admin_col()

    # Zaten var mı kontrol et
    existing = col.find_one({'email': email})
    if existing:
        return False

    # Yeni admin oluştur
    admin_id = _next_admin_id(col)
    admin_doc = {
        'id': admin_id,
        'email': email,
        'username': username,
        'password': _hash(password),
        'role': 'superadmin',
        'is_active': True,
        'created_at': datetime.now().isoformat(),
        'last_login': None,
    }

    col.insert_one(admin_doc)
    return True
