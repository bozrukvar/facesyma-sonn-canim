"""
auth_api/views.py
=================
JWT tabanlı kimlik doğrulama.
- Email + şifre kayıt/giriş
- Google OAuth (idToken doğrulama)
- Token yenileme
- Profil görüntüleme
"""
import json
import hashlib
import time
import re
from datetime import datetime

import jwt
from django.conf      import settings
from django.http      import JsonResponse
from django.views     import View
from django.views.decorators.csrf  import csrf_exempt
from django.utils.decorators       import method_decorator
from pymongo import MongoClient


# ── MongoDB bağlantısı ────────────────────────────────────────────────────────
def get_users_col():
    client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
    return client['facesyma-backend']['appfaceapi_myuser']


# ── Yardımcı fonksiyonlar ─────────────────────────────────────────────────────
def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def _make_tokens(user_id: int, email: str) -> dict:
    now = int(time.time())
    access = jwt.encode(
        {'user_id': user_id, 'email': email,
         'exp': now + settings.JWT_ACCESS_EXP_HOURS * 3600, 'type': 'access'},
        settings.JWT_SECRET, algorithm='HS256'
    )
    refresh = jwt.encode(
        {'user_id': user_id,
         'exp': now + settings.JWT_REFRESH_EXP_DAYS * 86400, 'type': 'refresh'},
        settings.JWT_SECRET, algorithm='HS256'
    )
    return {'access': access, 'refresh': refresh}


def _user_dict(u: dict) -> dict:
    return {
        'id':         u.get('id', 0),
        'email':      u.get('email', ''),
        'name':       u.get('username', u.get('name', '')),
        'avatar':     u.get('avatar'),
        'plan':       u.get('plan', 'free'),
        'created_at': str(u.get('date_joined', '')),
    }


def _next_id(col) -> int:
    last = col.find_one(sort=[('id', -1)])
    return (last['id'] + 1) if last and 'id' in last else 1


def _decode_token(request) -> dict:
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        raise ValueError('Token bulunamadı.')
    token = auth.split(' ', 1)[1]
    return jwt.decode(token, settings.JWT_SECRET, algorithms=['HS256'])


def _json(request):
    try:
        return json.loads(request.body)
    except Exception:
        return {}


# ── Kayıt ─────────────────────────────────────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(View):
    def post(self, request):
        data     = _json(request)
        email    = data.get('email', '').strip().lower()
        password = data.get('password', '')
        name     = data.get('name', '').strip()

        if not email or not password or not name:
            return JsonResponse({'detail': 'Email, şifre ve ad zorunlu.'}, status=400)
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            return JsonResponse({'detail': 'Geçersiz email.'}, status=400)
        if len(password) < 6:
            return JsonResponse({'detail': 'Şifre en az 6 karakter.'}, status=400)

        col = get_users_col()
        if col.find_one({'email': email}):
            return JsonResponse({'detail': 'Bu email zaten kayıtlı.'}, status=400)

        uid = _next_id(col)
        app_source = request.headers.get('X-App-Source', 'mobile').lower()
        if app_source not in ('mobile', 'web'):
            app_source = 'mobile'
        doc = {
            'id': uid, 'email': email, 'username': name,
            'password': _hash(password), 'plan': 'free',
            'auth_method': 'email',
            'date_joined': datetime.now().isoformat(),
            'is_active': True,
            'app_source': app_source,
        }
        col.insert_one(doc)
        tokens = _make_tokens(uid, email)

        # Broadcast new user event to admin panel (WS)
        try:
            from admin_api.consumers import send_admin_event
            send_admin_event('new_user', {
                'user_id': uid,
                'email': email,
                'app_source': app_source,
                'time': datetime.now().isoformat()
            })
        except Exception:
            pass  # WS broadcast failure shouldn't break registration

        return JsonResponse({**tokens, 'user': _user_dict(doc)}, status=201)


# ── Giriş ─────────────────────────────────────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class LoginView(View):
    def post(self, request):
        data  = _json(request)
        email = data.get('email', '').strip().lower()
        pw    = data.get('password', '')

        col  = get_users_col()
        user = col.find_one({'email': email})
        if not user or user.get('password') != _hash(pw):
            return JsonResponse({'detail': 'Email veya şifre hatalı.'}, status=401)

        tokens = _make_tokens(user['id'], email)
        return JsonResponse({**tokens, 'user': _user_dict(user)})


# ── Google OAuth ──────────────────────────────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class GoogleAuthView(View):
    def post(self, request):
        data         = _json(request)
        id_token_str = data.get('id_token', '')
        if not id_token_str:
            return JsonResponse({'detail': 'Google token gerekli.'}, status=400)

        # Google token doğrula
        try:
            from google.oauth2 import id_token
            from google.auth.transport import requests as g_req
            id_info = id_token.verify_oauth2_token(
                id_token_str,
                g_req.Request(),
                settings.GOOGLE_CLIENT_ID,
            )
        except Exception as e:
            return JsonResponse({'detail': f'Geçersiz Google token: {e}'}, status=401)

        google_id = id_info['sub']
        email     = id_info.get('email', '')
        name      = id_info.get('name', email.split('@')[0])
        avatar    = id_info.get('picture')

        col  = get_users_col()
        user = col.find_one({'$or': [{'google_id': google_id}, {'email': email}]})

        if user:
            # Var ama google_id yoksa ekle
            if not user.get('google_id'):
                col.update_one({'_id': user['_id']},
                               {'$set': {'google_id': google_id, 'avatar': avatar}})
                user['google_id'] = google_id
                user['avatar']    = avatar
        else:
            # Otomatik kayıt
            uid  = _next_id(col)
            app_source = request.headers.get('X-App-Source', 'mobile').lower()
            if app_source not in ('mobile', 'web'):
                app_source = 'mobile'
            user = {
                'id': uid, 'email': email, 'username': name,
                'google_id': google_id, 'avatar': avatar,
                'plan': 'free', 'auth_method': 'google',
                'date_joined': datetime.now().isoformat(),
                'is_active': True,
                'app_source': app_source,
            }
            col.insert_one(user)

        tokens = _make_tokens(user['id'], email)
        return JsonResponse({**tokens, 'user': _user_dict(user)})


# ── Token yenile ──────────────────────────────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class TokenRefreshView(View):
    def post(self, request):
        data    = _json(request)
        refresh = data.get('refresh', '')
        try:
            payload = jwt.decode(refresh, settings.JWT_SECRET, algorithms=['HS256'])
            if payload.get('type') != 'refresh':
                raise ValueError('Geçersiz tip.')
            tokens = _make_tokens(payload['user_id'], payload.get('email', ''))
            return JsonResponse({'access': tokens['access']})
        except jwt.ExpiredSignatureError:
            return JsonResponse({'detail': 'Token süresi doldu.'}, status=401)
        except Exception as e:
            return JsonResponse({'detail': str(e)}, status=401)


# ── Profil ────────────────────────────────────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class MeView(View):
    def get(self, request):
        try:
            payload = _decode_token(request)
            col     = get_users_col()
            user    = col.find_one({'id': payload['user_id']})
            if not user:
                return JsonResponse({'detail': 'Kullanıcı bulunamadı.'}, status=404)
            return JsonResponse(_user_dict(user))
        except jwt.ExpiredSignatureError:
            return JsonResponse({'detail': 'Token süresi doldu.'}, status=401)
        except Exception as e:
            return JsonResponse({'detail': str(e)}, status=401)

    def patch(self, request):
        """Profil güncelleme"""
        try:
            payload  = _decode_token(request)
            data     = _json(request)
            col      = get_users_col()
            allowed  = {k: v for k, v in data.items()
                        if k in ('username', 'avatar', 'plan')}
            if allowed:
                col.update_one({'id': payload['user_id']}, {'$set': allowed})
            user = col.find_one({'id': payload['user_id']})
            return JsonResponse(_user_dict(user))
        except Exception as e:
            return JsonResponse({'detail': str(e)}, status=401)
