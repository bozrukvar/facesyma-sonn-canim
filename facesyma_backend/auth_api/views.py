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
import hmac
import os
import time
import re
import logging
from datetime import datetime
from django.core.cache import cache

_PBKDF2_ITERATIONS = 260_000
# Pre-computed dummy hash used to equalize login timing for non-existent users
_DUMMY_HASH = 'pbkdf2:sha256:260000$' + ('00' * 16) + '$' + ('00' * 32)

_RE_EMAIL      = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]{2,}$')
_RE_WHITESPACE = re.compile(r'\s+')

_GOOGLE_LOGIN_PROJ = {
    '_id': 1, 'id': 1, 'email': 1, 'username': 1, 'google_id': 1,
    'avatar': 1, 'plan': 1, 'auth_method': 1, 'app_source': 1, 'is_active': 1,
}

import jwt
from django.conf      import settings
from django.http      import JsonResponse
from django.views     import View
from django.views.decorators.csrf  import csrf_exempt
from django.utils.decorators       import method_decorator

log = logging.getLogger(__name__)

try:
    from admin_api.consumers import send_admin_event as _send_admin_event
except Exception:
    _send_admin_event = None

_JWT_SECRET: str = settings.JWT_SECRET
_GOOGLE_CLIENT_ID: str = settings.GOOGLE_CLIENT_ID
_JWT_ACCESS_EXP_SEC: int = settings.JWT_ACCESS_EXP_HOURS * 3600
_JWT_REFRESH_EXP_SEC: int = settings.JWT_REFRESH_EXP_DAYS * 86400

# Connection pooling — her request'te yeni bağlantı açmaz
from admin_api.utils.mongo import get_users_col, _next_id, get_test_results_col


# ── Yardımcı fonksiyonlar ─────────────────────────────────────────────────────
def _hash(pw: str) -> str:
    """Hash password with PBKDF2-HMAC-SHA256 + random salt.
    Format: pbkdf2:sha256:<iterations>$<hex-salt>$<hex-hash>
    """
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha256', pw.encode(), salt, _PBKDF2_ITERATIONS)
    return f'pbkdf2:sha256:{_PBKDF2_ITERATIONS}${salt.hex()}${dk.hex()}'


def _check_hash(pw: str, stored: str) -> bool:
    """Verify password. Supports new PBKDF2 format and legacy bare SHA256."""
    _bfh = bytes.fromhex
    _pwe = pw.encode
    _hcd = hmac.compare_digest
    if stored.startswith('pbkdf2:sha256:'):
        try:
            _, _, rest = stored.split(':', 2)
            iterations_str, salt_hex, dk_hex = rest.split('$')
            iterations = int(iterations_str)
            if not (100_000 <= iterations <= 1_000_000):
                return False
            salt = _bfh(salt_hex)
            expected = _bfh(dk_hex)
            computed = hashlib.pbkdf2_hmac('sha256', _pwe(), salt, iterations)
            return _hcd(computed, expected)
        except Exception:
            return False
    return _hcd(hashlib.sha256(_pwe()).hexdigest(), stored)


def _make_tokens(user_id: int, email: str) -> dict:
    now = int(time.time())
    _je = jwt.encode
    access = _je(
        {'user_id': user_id, 'email': email,
         'exp': now + _JWT_ACCESS_EXP_SEC, 'type': 'access'},
        _JWT_SECRET, algorithm='HS256'
    )
    refresh = _je(
        {'user_id': user_id,
         'exp': now + _JWT_REFRESH_EXP_SEC, 'type': 'refresh'},
        _JWT_SECRET, algorithm='HS256'
    )
    return {'access': access, 'refresh': refresh}


_USER_PROJECTION = {'_id': 0, 'id': 1, 'email': 1, 'username': 1, 'name': 1, 'avatar': 1, 'plan': 1, 'date_joined': 1,
                    'birth_year': 1, 'gender': 1, 'country': 1, 'skin_tone': 1, 'hair_color': 1, 'eye_color': 1, 'goal': 1,
                    'interests': 1, 'lifestyle': 1,
                    'onboarding_completed': 1, 'terms_accepted': 1, 'gdpr_consent': 1,
                    'last_login': 1, 'premium_expires_at': 1, 'cosmetic_surgery_regions': 1}
_LOGIN_PROJECTION = {'id': 1, 'email': 1, 'username': 1, 'name': 1, 'avatar': 1, 'plan': 1, 'date_joined': 1,
                     'password': 1, 'is_active': 1, 'onboarding_completed': 1, 'terms_accepted': 1, 'gdpr_consent': 1,
                     'last_login': 1, 'premium_expires_at': 1, 'cosmetic_surgery_regions': 1}

_VALID_GENDERS           = {'male', 'female', 'prefer_not_to_say'}
_VALID_SKIN_TONES        = {'1', '2', '3', '4', '5', '6'}  # Fitzpatrick scale
_VALID_HAIR_COLORS       = {'black', 'brown', 'blonde', 'red', 'white_gray', 'other'}
_VALID_EYE_COLORS        = {'brown', 'black', 'blue', 'green', 'hazel', 'gray'}
_VALID_GOALS             = {'self_discovery', 'style', 'career', 'fun'}
_VALID_SURGERY_REGIONS   = {'nose', 'eyes', 'lips', 'cheeks', 'jawline', 'forehead', 'chin'}
_VALID_INTERESTS  = {'music', 'film', 'sport', 'travel', 'food', 'art',
                     'tech', 'nature', 'fashion', 'gaming', 'literature', 'health'}
_VALID_LIFESTYLES = {'vegan', 'athlete', 'meditation', 'freelancer',
                     'parent', 'student', 'digital_nomad', 'minimalist'}


def _is_adult(user: dict) -> bool:
    by = user.get('birth_year')
    return bool(by and by <= datetime.utcnow().year - 18)


def _user_dict(u: dict) -> dict:
    _uget = u.get
    _premium_exp        = _uget('premium_expires_at')
    _premium_days_left  = None
    _premium_hours_left = None
    if _premium_exp:
        try:
            _exp_dt     = datetime.fromisoformat(_premium_exp)
            _total_secs = (_exp_dt - datetime.utcnow()).total_seconds()
            if _total_secs > 0:
                _premium_days_left  = int(_total_secs // 86400)
                _premium_hours_left = int((_total_secs % 86400) // 3600)
        except Exception:
            pass
    return {
        'id':                        _uget('id', 0),
        'email':                     _uget('email', ''),
        'name':                      _uget('username', _uget('name', '')),
        'avatar':                    _uget('avatar'),
        'plan':                      _uget('plan', 'free'),
        'created_at':                str(_uget('date_joined', '')),
        'birth_year':                _uget('birth_year'),
        'gender':                    _uget('gender'),
        'country':                   _uget('country'),
        'skin_tone':                 _uget('skin_tone'),
        'hair_color':                _uget('hair_color'),
        'eye_color':                 _uget('eye_color'),
        'goal':                      _uget('goal'),
        'onboarding_completed':      _uget('onboarding_completed', False),
        'terms_accepted':            _uget('terms_accepted', False),
        'gdpr_consent':              _uget('gdpr_consent', False),
        'last_login':                _uget('last_login'),
        'premium_expires_at':        _premium_exp,
        'premium_days_left':         _premium_days_left,
        'premium_hours_left':        _premium_hours_left,
        'cosmetic_surgery_regions':  _uget('cosmetic_surgery_regions', []),
        'interests':                 _uget('interests', []),
        'lifestyle':                 _uget('lifestyle', []),
    }


def _get_test_summary(user_id: int) -> dict:
    """En son test sonuçlarını test tipine göre gruplar; hata durumunda boş dict döner."""
    try:
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$sort": {"created_at": -1}},
            {"$group": {
                "_id": "$test_type",
                "taken_at":      {"$first": "$created_at"},
                "domain_scores": {"$first": "$domain_scores"},
                "stress_details": {"$first": "$stress_details"},
            }},
        ]
        rows = list(get_test_results_col().aggregate(pipeline))
        latest = {}
        for r in rows:
            entry = {"domain_scores": r.get("domain_scores", {}), "taken_at": r.get("taken_at", "")}
            if r.get("stress_details"):
                entry["stress_details"] = r["stress_details"]
            latest[r["_id"]] = entry
        return {
            "total_tests_taken": len(rows),
            "completed_types":   list(latest.keys()),
            "latest_per_type":   latest,
        }
    except Exception:
        return {}


def _decode_token(request) -> dict:
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        raise ValueError('Token not found.')
    token = auth.split(' ', 1)[1]
    return jwt.decode(token, _JWT_SECRET, algorithms=['HS256'])


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
        _dget    = data.get
        email    = _dget('email', '').strip().lower()[:254]
        password = _dget('password', '')
        name     = _RE_WHITESPACE.sub(' ', _dget('name', '').strip())[:100]

        terms_accepted = bool(_dget('terms_accepted', False))
        gdpr_consent   = bool(_dget('gdpr_consent', False))

        if not email or not password or not name:
            return JsonResponse({'detail': 'Email, password and name are required.'}, status=400)
        if not _RE_EMAIL.match(email):
            return JsonResponse({'detail': 'Invalid email address.'}, status=400)
        _pw_len = len(password)
        if _pw_len < 6:
            return JsonResponse({'detail': 'Password must be at least 6 characters.'}, status=400)
        if _pw_len > 128:
            return JsonResponse({'detail': 'Password must be at most 128 characters.'}, status=400)
        if not terms_accepted or not gdpr_consent:
            return JsonResponse({'detail': 'You must accept the Terms of Use and Privacy Policy.'}, status=400)

        col = get_users_col()
        if col.find_one({'email': email}, {'_id': 1}):
            return JsonResponse({'detail': 'This email is already registered.'}, status=400)

        uid = _next_id(col)
        app_source = request.headers.get('X-App-Source', 'mobile').lower()
        if app_source not in ('mobile', 'web'):
            app_source = 'mobile'
        _now_iso = datetime.utcnow().isoformat()
        doc = {
            'id': uid, 'email': email, 'username': name,
            'password': _hash(password), 'plan': 'free',
            'auth_method': 'email',
            'date_joined': _now_iso,
            'is_active': True,
            'app_source': app_source,
            'terms_accepted': terms_accepted,
            'gdpr_consent': gdpr_consent,
            'terms_accepted_at': _now_iso,
            'onboarding_completed': False,
        }
        col.insert_one(doc)
        tokens = _make_tokens(uid, email)

        # Broadcast new user event to admin panel (WS)
        if _send_admin_event:
            try:
                _send_admin_event('new_user', {
                    'user_id': uid,
                    'email': email,
                    'app_source': app_source,
                    'time': _now_iso,
                })
            except Exception:
                pass  # WS broadcast failure shouldn't break registration

        return JsonResponse({**tokens, 'user': _user_dict(doc)}, status=201)


# ── Giriş ─────────────────────────────────────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class LoginView(View):
    _MAX_ATTEMPTS = 10   # 10 hatalı denemeden sonra kilitle
    _LOCKOUT_SECS = 600  # 10 dakika

    def post(self, request):
        data  = _json(request)
        _dget = data.get
        email = _dget('email', '').strip().lower()[:254]
        pw    = _dget('password', '')
        if len(pw) > 128:
            return JsonResponse({'detail': 'Invalid email or password.'}, status=401)

        # Brute-force koruması — IP + email bazlı
        _rmg = request.META.get
        ip        = _rmg('HTTP_X_FORWARDED_FOR', _rmg('REMOTE_ADDR', ''))
        cache_key = f'login_fail:{ip}:{email}'
        fail_count = 0
        try:
            fail_count = cache.get(cache_key, 0)
            if fail_count >= self._MAX_ATTEMPTS:
                return JsonResponse({'detail': 'Too many failed attempts. Please wait 10 minutes.'}, status=429)
        except Exception:
            pass  # Cache access failure should not block login

        col  = get_users_col()
        user = col.find_one({'email': email}, _LOGIN_PROJECTION)
        # Always call _check_hash to prevent timing oracle (user enumeration via response time)
        stored_pw = user.get('password', '') if user else _DUMMY_HASH
        pw_valid  = _check_hash(pw, stored_pw)
        if not user or not pw_valid:
            try:
                cache.set(cache_key, fail_count + 1, timeout=self._LOCKOUT_SECS)
            except Exception:
                pass
            return JsonResponse({'detail': 'Invalid email or password.'}, status=401)

        try:
            cache.delete(cache_key)  # Başarılı girişte sayacı sıfırla
        except Exception:
            pass

        # Upgrade legacy bare-SHA256 to PBKDF2 on successful login
        if not stored_pw.startswith('pbkdf2:'):
            col.update_one({'_id': user['_id']}, {'$set': {'password': _hash(pw)}})

        _now = datetime.utcnow().isoformat()
        col.update_one({'_id': user['_id']}, {'$set': {'last_login': _now}})
        user['last_login'] = _now
        tokens = _make_tokens(user['id'], email)
        return JsonResponse({**tokens, 'user': _user_dict(user)})


# ── Google OAuth ──────────────────────────────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class GoogleAuthView(View):
    def post(self, request):
        data         = _json(request)
        id_token_str = data.get('id_token', '')
        if not id_token_str:
            return JsonResponse({'detail': 'Google token is required.'}, status=400)

        # Google token doğrula
        try:
            from google.oauth2 import id_token
            from google.auth.transport import requests as g_req
            id_info = id_token.verify_oauth2_token(
                id_token_str,
                g_req.Request(),
                _GOOGLE_CLIENT_ID,
            )
        except Exception:
            return JsonResponse({'detail': 'Invalid Google token.'}, status=401)

        _iiget = id_info.get
        google_id = id_info['sub'][:128]
        email     = _iiget('email', '')[:254]
        if not email:
            return JsonResponse({'detail': 'Google account has no email address.'}, status=400)
        name      = _iiget('name', email.split('@')[0])[:100]
        avatar    = _iiget('picture')

        col  = get_users_col()
        user = col.find_one(
            {'$or': [{'google_id': google_id}, {'email': email}]},
            _GOOGLE_LOGIN_PROJ,
        )

        if user:
            existing_gid = user.get('google_id')
            if existing_gid and existing_gid != google_id:
                # Different Google account trying to use an email already linked to another gid
                log.warning(f"Google ID mismatch for email={email}: existing={existing_gid} incoming={google_id}")
                return JsonResponse({'detail': 'This email is already linked to a different Google account.'}, status=409)
            if not existing_gid:
                # Email-registered user logging in with Google for the first time — link accounts
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
                'date_joined': datetime.utcnow().isoformat(),
                'is_active': True,
                'app_source': app_source,
            }
            col.insert_one(user)

        _now = datetime.utcnow().isoformat()
        col.update_one({'_id': user['_id']}, {'$set': {'last_login': _now}})
        user['last_login'] = _now
        tokens = _make_tokens(user['id'], email)
        return JsonResponse({**tokens, 'user': _user_dict(user)})


# ── Token yenile ──────────────────────────────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class TokenRefreshView(View):
    def post(self, request):
        data    = _json(request)
        refresh = data.get('refresh', '')
        try:
            payload = jwt.decode(refresh, _JWT_SECRET, algorithms=['HS256'])
            _pget = payload.get
            if _pget('type') != 'refresh':
                raise ValueError('Invalid token type.')
            user_id = payload['user_id']
            col = get_users_col()
            user = col.find_one({'id': user_id}, {'is_active': 1, 'email': 1})
            if not user or not user.get('is_active', True):
                return JsonResponse({'detail': 'Account is disabled.'}, status=401)
            tokens = _make_tokens(user_id, _pget('email', ''))
            return JsonResponse({'access': tokens['access']})
        except jwt.ExpiredSignatureError:
            return JsonResponse({'detail': 'Token has expired.'}, status=401)
        except Exception:
            return JsonResponse({'detail': 'Invalid or malformed token.'}, status=401)


# ── Profil ────────────────────────────────────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class MeView(View):
    def get(self, request):
        try:
            payload = _decode_token(request)
            uid     = payload['user_id']
            col     = get_users_col()
            user    = col.find_one({'id': uid}, _USER_PROJECTION)
            if not user:
                return JsonResponse({'detail': 'User not found.'}, status=404)
            data = _user_dict(user)
            data['test_summary'] = _get_test_summary(uid)
            return JsonResponse(data)
        except jwt.ExpiredSignatureError:
            return JsonResponse({'detail': 'Token has expired.'}, status=401)
        except Exception as e:
            log.exception('Profile fetch error')
            return JsonResponse({'detail': 'Authentication failed.'}, status=401)

    def patch(self, request):
        """Profil güncelleme — onboarding dahil"""
        try:
            payload  = _decode_token(request)
            data     = _json(request)
            col      = get_users_col()
            update = {}
            if 'username' in data:
                update['username'] = str(data['username'])[:100]
            if 'avatar' in data:
                update['avatar'] = str(data['avatar'])[:512]
            # Onboarding zorunlu alanlar
            if 'birth_year' in data:
                by = int(data['birth_year'])
                if 1900 <= by <= datetime.utcnow().year:
                    update['birth_year'] = by
            if 'gender' in data and data['gender'] in _VALID_GENDERS:
                update['gender'] = data['gender']
            if 'country' in data:
                update['country'] = str(data['country'])[:100]
            # Onboarding isteğe bağlı alanlar
            if 'skin_tone' in data and str(data['skin_tone']) in _VALID_SKIN_TONES:
                update['skin_tone'] = str(data['skin_tone'])
            if 'hair_color' in data and data['hair_color'] in _VALID_HAIR_COLORS:
                update['hair_color'] = data['hair_color']
            if 'eye_color' in data and data['eye_color'] in _VALID_EYE_COLORS:
                update['eye_color'] = data['eye_color']
            if 'goal' in data and data['goal'] in _VALID_GOALS:
                update['goal'] = data['goal']
            if 'onboarding_completed' in data:
                update['onboarding_completed'] = bool(data['onboarding_completed'])
            if 'cosmetic_surgery_regions' in data:
                regions = data['cosmetic_surgery_regions']
                if isinstance(regions, list):
                    update['cosmetic_surgery_regions'] = [r for r in regions if r in _VALID_SURGERY_REGIONS]
            if 'interests' in data and isinstance(data['interests'], list):
                val = [v for v in data['interests'] if v in _VALID_INTERESTS][:3]
                if val:
                    update['interests'] = val
            if 'lifestyle' in data and isinstance(data['lifestyle'], list):
                val = [v for v in data['lifestyle'] if v in _VALID_LIFESTYLES][:3]
                if val:
                    update['lifestyle'] = val
            _puid = payload['user_id']
            if update:
                col.update_one({'id': _puid}, {'$set': update})
                _interests_upd = update.get('interests')
                _lifestyle_upd = update.get('lifestyle')
                if _interests_upd or _lifestyle_upd:
                    try:
                        from analysis_api.community_hooks import auto_add_from_profile
                        auto_add_from_profile(_puid, _interests_upd or [], _lifestyle_upd or [])
                    except Exception:
                        pass
            user = col.find_one({'id': _puid}, _USER_PROJECTION)
            if not user:
                return JsonResponse({'detail': 'User not found.'}, status=404)
            return JsonResponse(_user_dict(user))
        except Exception as e:
            log.exception('Profile update error')
            return JsonResponse({'detail': 'Authentication failed.'}, status=401)


# ── Sağlık Modülü Onayı ───────────────────────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class HealthConsentView(View):
    """
    GET  → kullanıcının sağlık modülü onay durumunu döner
    POST → onayı kaydeder (idempotent)
    """
    _CURRENT_VERSION = 'v1'

    def get(self, request):
        try:
            payload = _decode_token(request)
        except Exception:
            return JsonResponse({'detail': 'Authentication failed.'}, status=401)
        col  = get_users_col()
        user = col.find_one({'id': payload['user_id']}, {'health_consent': 1})
        if not user:
            return JsonResponse({'detail': 'User not found.'}, status=404)
        hc = user.get('health_consent') or {}
        return JsonResponse({
            'accepted':    bool(hc.get('accepted', False)),
            'accepted_at': hc.get('accepted_at'),
            'version':     hc.get('version'),
        })

    def post(self, request):
        try:
            payload = _decode_token(request)
        except Exception:
            return JsonResponse({'detail': 'Authentication failed.'}, status=401)
        now = datetime.utcnow().isoformat()
        get_users_col().update_one(
            {'id': payload['user_id']},
            {'$set': {'health_consent': {
                'accepted':    True,
                'accepted_at': now,
                'version':     self._CURRENT_VERSION,
            }}},
        )
        return JsonResponse({'accepted': True, 'accepted_at': now, 'version': self._CURRENT_VERSION})


# ── Şifre Değiştir ────────────────────────────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class ChangePasswordView(View):
    """Authenticated kullanıcının şifresini değiştirir."""

    _MAX_ATTEMPTS = 5
    _LOCKOUT_SECS = 900  # 15 minutes

    def post(self, request):
        try:
            payload = _decode_token(request)
        except Exception:
            return JsonResponse({'detail': 'Invalid token.'}, status=401)

        # Rate-limit by user_id to prevent old-password brute-forcing
        user_id   = payload.get('user_id', '')
        rate_key  = f'chgpw_fail:{user_id}'
        fail_count = 0
        try:
            fail_count = cache.get(rate_key, 0)
            if fail_count >= self._MAX_ATTEMPTS:
                return JsonResponse({'detail': 'Too many attempts. Please wait 15 minutes.'}, status=429)
        except Exception:
            pass

        data         = _json(request)
        _dget        = data.get
        old_password = _dget('old_password', '')
        new_password = _dget('new_password', '')

        if not old_password or not new_password:
            return JsonResponse({'detail': 'Old and new password are required.'}, status=400)
        _new_pw_len = len(new_password)
        if len(old_password) > 128 or _new_pw_len > 128:
            return JsonResponse({'detail': 'Password must be at most 128 characters.'}, status=400)
        if _new_pw_len < 6:
            return JsonResponse({'detail': 'New password must be at least 6 characters.'}, status=400)

        col  = get_users_col()
        user = col.find_one({'id': user_id}, {'_id': 0, 'password': 1})
        if not user:
            return JsonResponse({'detail': 'User not found.'}, status=404)
        if not _check_hash(old_password, user.get('password', '')):
            try:
                cache.set(rate_key, fail_count + 1, timeout=self._LOCKOUT_SECS)
            except Exception:
                pass
            return JsonResponse({'detail': 'Current password is incorrect.'}, status=400)

        try:
            cache.delete(rate_key)
        except Exception:
            pass
        col.update_one({'id': user_id}, {'$set': {'password': _hash(new_password)}})
        return JsonResponse({'detail': 'Password changed successfully.'})


# ── Şifre Sıfırlama İsteği ────────────────────────────────────────────────────
_RESET_TOKEN_TTL = 3600  # 1 saat

def _reset_cache_key(token: str) -> str:
    return f'pw_reset_token:{token}'


def _send_reset_email(email: str, token: str) -> None:
    """Şifre sıfırlama e-postasını gönder."""
    from django.core.mail import send_mail
    from django.conf import settings

    web_url  = getattr(settings, 'WEB_APP_URL', 'https://facesyma.com')
    reset_url = f'{web_url}/reset-password?token={token}'

    subject = 'Facesyma — Şifre Sıfırlama / Password Reset'
    body = (
        f'Merhaba,\n\n'
        f'Şifre sıfırlama talebiniz alındı.\n\n'
        f'Sıfırlama kodunuz: {token}\n\n'
        f'Uygulamayı açıp bu kodu girin, ya da aşağıdaki bağlantıya tıklayın:\n'
        f'{reset_url}\n\n'
        f'Bu bağlantı 1 saat geçerlidir. Talep etmediyseniz dikkate almayın.\n\n'
        f'---\n'
        f'Hello,\n\n'
        f'A password reset was requested for your Facesyma account.\n\n'
        f'Your reset code: {token}\n\n'
        f'Open the app and enter this code, or click the link below:\n'
        f'{reset_url}\n\n'
        f'This link is valid for 1 hour. If you did not request this, ignore this email.\n\n'
        f'— Facesyma Team'
    )
    send_mail(
        subject,
        body,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )


@method_decorator(csrf_exempt, name='dispatch')
class PasswordResetRequestView(View):
    """Şifre sıfırlama e-postası gönderir.
    Güvenlik gereği kullanıcı var olup olmadığını açıklamaz — her durumda 200 döner.
    """

    def post(self, request):
        import secrets
        data  = _json(request)
        email = data.get('email', '').strip().lower()[:254]
        if not email:
            return JsonResponse({'detail': 'Email zorunlu.'}, status=400)

        # Rate-limit: 3 requests per hour per IP+email to prevent spam
        _rmg = request.META.get
        ip       = _rmg('HTTP_X_FORWARDED_FOR', _rmg('REMOTE_ADDR', ''))
        rate_key = f'pwreset:{ip}:{email}'
        try:
            count = cache.get(rate_key, 0)
            if count >= 3:
                return JsonResponse({'detail': 'Password reset instructions have been sent to your email.'})
            cache.set(rate_key, count + 1, timeout=3600)
        except Exception:
            pass

        col  = get_users_col()
        user = col.find_one({'email': email}, {'_id': 0, 'email': 1})
        if user:
            token = secrets.token_urlsafe(32)
            try:
                cache.set(_reset_cache_key(token), email, timeout=_RESET_TOKEN_TTL)
                _send_reset_email(email, token)
                log.info(f'Password reset email sent: {email}')
            except Exception as e:
                log.error(f'Password reset email failed for {email}: {e}')

        # Güvenlik: kullanıcı var olup olmadığından bağımsız aynı yanıt
        return JsonResponse({'detail': 'Password reset instructions have been sent to your email.'})


# ── Şifre Sıfırlama Onayı ─────────────────────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class PasswordResetConfirmView(View):
    """Token ile yeni şifreyi kaydeder. Token tek kullanımlık, 1 saat geçerli."""

    def post(self, request):
        data         = _json(request)
        token        = (data.get('token') or '').strip()
        new_password = data.get('new_password', '')

        if not token or not new_password:
            return JsonResponse({'detail': 'token and new_password are required.'}, status=400)
        if len(new_password) < 6:
            return JsonResponse({'detail': 'Password must be at least 6 characters.'}, status=400)

        cache_key = _reset_cache_key(token)
        try:
            email = cache.get(cache_key)
        except Exception:
            email = None

        if not email:
            return JsonResponse({'detail': 'Invalid or expired reset token.'}, status=400)

        col = get_users_col()
        result = col.update_one(
            {'email': email},
            {'$set': {'password': _hash(new_password)}},
        )
        if result.matched_count == 0:
            return JsonResponse({'detail': 'User not found.'}, status=404)

        # Tek kullanımlık — token'ı hemen sil
        try:
            cache.delete(cache_key)
        except Exception:
            pass

        log.info(f'Password reset confirmed: {email}')
        return JsonResponse({'detail': 'Password reset successfully.'})


# ── FCM Device Token ─────────────────────────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class DeviceTokenView(View):
    """Register or remove FCM device token for the authenticated user."""

    def post(self, request):
        try:
            payload = _decode_token(request)
        except Exception:
            return JsonResponse({'detail': 'Authentication failed.'}, status=401)

        data     = _json(request)
        token    = (data.get('device_token') or '').strip()
        platform = data.get('platform', 'unknown')

        if not token:
            return JsonResponse({'detail': 'device_token is required.'}, status=400)
        if len(token) > 4096:
            return JsonResponse({'detail': 'device_token too long.'}, status=400)
        if platform not in ('ios', 'android'):
            platform = 'unknown'

        get_users_col().update_one(
            {'id': payload['user_id']},
            {'$set': {
                'device_token':            token,
                'device_platform':         platform,
                'device_token_updated_at': datetime.utcnow().isoformat(),
            }},
        )
        return JsonResponse({'success': True})

    def delete(self, request):
        """Deregister device token on logout."""
        try:
            payload = _decode_token(request)
        except Exception:
            return JsonResponse({'detail': 'Authentication failed.'}, status=401)

        get_users_col().update_one(
            {'id': payload['user_id']},
            {'$unset': {
                'device_token':            '',
                'device_platform':         '',
                'device_token_updated_at': '',
            }},
        )
        return JsonResponse({'success': True})


# ── Hesap Silme (GDPR "right to erasure") ────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class DeleteAccountView(View):
    """Hard delete — kullanıcının tüm verilerini MongoDB'den siler."""

    def delete(self, request):
        try:
            payload = _decode_token(request)
        except Exception:
            return JsonResponse({'detail': 'Authentication failed.'}, status=401)

        uid = payload.get('user_id')
        if not uid:
            return JsonResponse({'detail': 'Invalid token.'}, status=401)

        try:
            from admin_api.utils.mongo import get_db
            db = get_db()

            # 1. Kullanıcı belgesi
            db['users'].delete_one({'id': uid})
            # 2. Analiz geçmişi
            db['analysis_history'].delete_many({'user_id': uid})
            # 3. Assessment sonuçları
            db['assessment_results'].delete_many({'user_id': uid})
            # 4. Chat konuşmaları (ai_chat service'i ayrı db kullanabilir; best-effort)
            try:
                db['conversations'].delete_many({'user_id': uid})
                db['chat_messages'].delete_many({'user_id': uid})
            except Exception:
                pass

            log.info(f'Account deleted: user_id={uid}')
            return JsonResponse({'detail': 'Your account and all associated data have been permanently deleted.'})
        except Exception:
            log.exception(f'Account delete error: user_id={uid}')
            return JsonResponse({'detail': 'Account deletion failed. Please try again.'}, status=500)


# ── Veri Dışa Aktarma (GDPR Madde 20 — taşınabilirlik) ───────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class ExportDataView(View):
    """Kullanıcının tüm verisini JSON olarak döner."""

    def get(self, request):
        try:
            payload = _decode_token(request)
        except Exception:
            return JsonResponse({'detail': 'Authentication failed.'}, status=401)

        uid = payload.get('user_id')
        if not uid:
            return JsonResponse({'detail': 'Invalid token.'}, status=401)

        # Rate-limit: günde 3 istek
        rate_key = f'export:{uid}'
        try:
            count = cache.get(rate_key, 0)
            if count >= 3:
                return JsonResponse({'detail': 'You can export your data up to 3 times per day.'}, status=429)
            cache.set(rate_key, count + 1, timeout=86400)
        except Exception:
            pass

        try:
            from admin_api.utils.mongo import get_db
            db = get_db()

            user = db['users'].find_one({'id': uid}, {'_id': 0, 'password': 0})
            if not user:
                return JsonResponse({'detail': 'User not found.'}, status=404)

            history_cursor     = db['analysis_history'].find({'user_id': uid}, {'_id': 0})
            assessment_cursor  = db['assessment_results'].find({'user_id': uid}, {'_id': 0})

            export = {
                'exported_at': datetime.utcnow().isoformat(),
                'user': user,
                'analysis_history': list(history_cursor),
                'assessment_results': list(assessment_cursor),
            }
            return JsonResponse({'success': True, 'data': export})
        except Exception:
            log.exception(f'Data export error: user_id={uid}')
            return JsonResponse({'detail': 'Data export failed. Please try again.'}, status=500)
