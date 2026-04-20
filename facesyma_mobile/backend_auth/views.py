"""
facesyma_auth/views.py
======================
Mevcut Django backend'i bozmadan eklenen auth servisi.
appfaceapi_myuser koleksiyonunu kullanır.

Kurulum:
    pip install djangorestframework djangorestframework-simplejwt
    pip install social-auth-app-django google-auth

URL'ler (urls.py'ye ekle):
    path('auth/', include('facesyma_auth.urls')),
"""
import json
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from pymongo import MongoClient
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import jwt
import hashlib
import os
import re

MONGO_URI = os.environ.get(
    'MONGO_URI',
    'mongodb+srv://facesyma:FaceSyma2021@cluster0.io98c.mongodb.net/'
    'myFirstDatabase?ssl=true&ssl_cert_reqs=CERT_NONE'
)
SECRET_KEY = os.environ.get('JWT_SECRET', 'facesyma-secret-change-in-production')
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client['facesyma-backend']
users_col = db['appfaceapi_myuser']


def _hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def _make_tokens(user_id: int, email: str) -> dict:
    import time
    access_payload = {
        'user_id': user_id,
        'email':   email,
        'exp':     int(time.time()) + 3600,      # 1 saat
        'type':    'access',
    }
    refresh_payload = {
        'user_id': user_id,
        'exp':     int(time.time()) + 86400 * 30, # 30 gün
        'type':    'refresh',
    }
    return {
        'access':  jwt.encode(access_payload,  SECRET_KEY, algorithm='HS256'),
        'refresh': jwt.encode(refresh_payload, SECRET_KEY, algorithm='HS256'),
    }


def _user_to_dict(user: dict) -> dict:
    return {
        'id':         user.get('id', 0),
        'email':      user.get('email', ''),
        'name':       user.get('username', user.get('name', '')),
        'avatar':     user.get('avatar', None),
        'plan':       user.get('plan', 'free'),
        'created_at': str(user.get('date_joined', datetime.now().isoformat())),
    }


def _get_next_id() -> int:
    last = users_col.find_one(sort=[('id', -1)])
    return (last['id'] + 1) if last and 'id' in last else 1


# ── Email kayıt ────────────────────────────────────────────────────────────────
@csrf_exempt
@require_http_methods(['POST'])
def register(request):
    try:
        data = json.loads(request.body)
        email    = data.get('email', '').strip().lower()
        password = data.get('password', '')
        name     = data.get('name', '').strip()

        if not email or not password or not name:
            return JsonResponse({'detail': 'Email, şifre ve ad gerekli.'}, status=400)

        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            return JsonResponse({'detail': 'Geçerli bir email adresi girin.'}, status=400)

        if len(password) < 6:
            return JsonResponse({'detail': 'Şifre en az 6 karakter olmalı.'}, status=400)

        # Mevcut kullanıcı kontrolü — appfaceapi_myuser'daki email alanı
        existing = users_col.find_one({'email': email})
        if existing:
            return JsonResponse({'detail': 'Bu email zaten kayıtlı.'}, status=400)

        new_id = _get_next_id()
        user_doc = {
            'id':          new_id,
            'email':       email,
            'username':    name,
            'password':    _hash_password(password),
            'plan':        'free',
            'auth_method': 'email',
            'date_joined': datetime.now().isoformat(),
            'is_active':   True,
        }
        users_col.insert_one(user_doc)

        tokens = _make_tokens(new_id, email)
        return JsonResponse({
            **tokens,
            'user': _user_to_dict(user_doc),
        }, status=201)

    except Exception as e:
        return JsonResponse({'detail': str(e)}, status=500)


# ── Email giriş (JWT token) ────────────────────────────────────────────────────
@csrf_exempt
@require_http_methods(['POST'])
def login(request):
    try:
        data  = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        pw    = data.get('password', '')

        user = users_col.find_one({'email': email})
        if not user:
            return JsonResponse({'detail': 'Email veya şifre hatalı.'}, status=401)

        if user.get('password') != _hash_password(pw):
            return JsonResponse({'detail': 'Email veya şifre hatalı.'}, status=401)

        tokens = _make_tokens(user['id'], email)
        return JsonResponse({**tokens, 'user': _user_to_dict(user)})

    except Exception as e:
        return JsonResponse({'detail': str(e)}, status=500)


# ── Google OAuth ───────────────────────────────────────────────────────────────
@csrf_exempt
@require_http_methods(['POST'])
def google_auth(request):
    """
    React Native'den Google id_token alır, doğrular.
    Kullanıcı yoksa otomatik kayıt yapar — mevcut sistemi bozmaz.
    """
    try:
        data     = json.loads(request.body)
        id_token_str = data.get('id_token', '')

        if not id_token_str:
            return JsonResponse({'detail': 'Google token gerekli.'}, status=400)

        # Google token doğrula
        try:
            id_info = id_token.verify_oauth2_token(
                id_token_str,
                google_requests.Request(),
                GOOGLE_CLIENT_ID,
            )
        except ValueError as e:
            return JsonResponse({'detail': f'Geçersiz Google token: {e}'}, status=401)

        google_id = id_info['sub']
        email     = id_info.get('email', '')
        name      = id_info.get('name', email.split('@')[0])
        avatar    = id_info.get('picture', None)

        # Mevcut kullanıcı kontrolü (google_id veya email ile)
        user = users_col.find_one({'$or': [
            {'google_id': google_id},
            {'email':     email},
        ]})

        if user:
            # Varsa google_id ekle (email ile kayıtlıysa)
            if not user.get('google_id'):
                users_col.update_one(
                    {'_id': user['_id']},
                    {'$set': {'google_id': google_id, 'avatar': avatar}}
                )
                user['google_id'] = google_id
                user['avatar']    = avatar
        else:
            # Yoksa otomatik kayıt
            new_id = _get_next_id()
            user = {
                'id':          new_id,
                'email':       email,
                'username':    name,
                'google_id':   google_id,
                'avatar':      avatar,
                'plan':        'free',
                'auth_method': 'google',
                'date_joined': datetime.now().isoformat(),
                'is_active':   True,
            }
            users_col.insert_one(user)

        tokens = _make_tokens(user['id'], email)
        return JsonResponse({**tokens, 'user': _user_to_dict(user)})

    except Exception as e:
        return JsonResponse({'detail': str(e)}, status=500)


# ── Token yenile ───────────────────────────────────────────────────────────────
@csrf_exempt
@require_http_methods(['POST'])
def token_refresh(request):
    try:
        data    = json.loads(request.body)
        refresh = data.get('refresh', '')
        payload = jwt.decode(refresh, SECRET_KEY, algorithms=['HS256'])

        if payload.get('type') != 'refresh':
            return JsonResponse({'detail': 'Geçersiz token tipi.'}, status=401)

        tokens = _make_tokens(payload['user_id'], payload.get('email', ''))
        return JsonResponse({'access': tokens['access']})

    except jwt.ExpiredSignatureError:
        return JsonResponse({'detail': 'Token süresi doldu.'}, status=401)
    except Exception as e:
        return JsonResponse({'detail': str(e)}, status=401)


# ── Profil ─────────────────────────────────────────────────────────────────────
@require_http_methods(['GET'])
def me(request):
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return JsonResponse({'detail': 'Token gerekli.'}, status=401)
    try:
        token   = auth.split(' ')[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        user    = users_col.find_one({'id': payload['user_id']})
        if not user:
            return JsonResponse({'detail': 'Kullanıcı bulunamadı.'}, status=404)
        return JsonResponse(_user_to_dict(user))
    except Exception as e:
        return JsonResponse({'detail': str(e)}, status=401)
