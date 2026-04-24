"""
analysis_api/views.py
=====================
Yüz analizi endpoint'leri.
Mevcut facesyma_revize/main.py motorunu çağırır.

Endpoint'ler:
  POST /api/v1/analysis/analyze/          → Temel karakter analizi
  POST /api/v1/analysis/analyze/modules/  → Tüm 13 modül
  POST /api/v1/analysis/analyze/golden/   → Altın oran
  POST /api/v1/analysis/analyze/face_type/→ Yüz tipi
  POST /api/v1/analysis/analyze/art/      → Sanat eşleşmesi
  POST /api/v1/analysis/analyze/astrology/→ Astroloji
  POST /api/v1/analysis/twins/            → 2-5 kişi uyum
  GET  /api/v1/analysis/history/          → Analiz geçmişi
  GET  /api/v1/analysis/daily/            → Günlük motivasyon
"""
import os
import sys
import json
import re
import random
import uuid
import time
import logging
from datetime import datetime
from pathlib import Path

import jwt
from django.conf       import settings
from django.http       import JsonResponse
from django.views      import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators      import method_decorator
from django.core.cache import cache
from admin_api.utils.mongo import get_history_col, _get_main_client

try:
    from admin_api.consumers import send_admin_event as _send_admin_event
except Exception:
    _send_admin_event = None

try:
    from analysis_api.image_validator import ImageQualityValidator as _ImageQualityValidator
except Exception:
    _ImageQualityValidator = None


log = logging.getLogger(__name__)

_JWT_SECRET: str = settings.JWT_SECRET

_CHARACTER_MODES    = frozenset({'character', 'enhanced_character'})
_DAILY_NATIVE_LANGS = frozenset({'tr', 'en', 'de', 'ru', 'ar'})
_DAILY_DB_MAP: dict = {
    'tr': 'database_daily_tr', 'en': 'database_daily_en',
    'de': 'database_daily_de', 'ru': 'database_daily_ru', 'ar': 'database_daily_ar',
    'es': 'database_daily_en', 'ko': 'database_daily_en', 'ja': 'database_daily_en',
    'zh': 'database_daily_en', 'hi': 'database_daily_en', 'fr': 'database_daily_en',
    'pt': 'database_daily_en', 'bn': 'database_daily_en', 'id': 'database_daily_en',
    'ur': 'database_daily_en', 'it': 'database_daily_en', 'vi': 'database_daily_en',
    'pl': 'database_daily_en',
}

_RE_DATE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
_RE_TIME = re.compile(r'^\d{2}:\d{2}(:\d{2})?$')

# ── Motor yükleme ─────────────────────────────────────────────────────────────
_ENGINE_PATH: str = settings.FACESYMA_ENGINE_PATH

def _load_engine():
    """facesyma_revize'i Python path'e ekle"""
    _spath = sys.path
    if _ENGINE_PATH not in _spath:
        _spath.insert(0, _ENGINE_PATH)


# ── JWT yardımcısı ────────────────────────────────────────────────────────────
def _get_user_id(request) -> int | None:
    """Token'dan user_id çıkar. Token yoksa None döner (anonim izin)."""
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


def _require_auth(request):
    uid = _get_user_id(request)
    if uid is None:
        raise PermissionError('Authentication required.')
    return uid


# ── Fotoğraf kaydetme ─────────────────────────────────────────────────────────
_MAX_UPLOAD_BYTES = 15 * 1024 * 1024  # 15 MB
_ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif'}
_UPLOAD_DIR = Path(settings.UPLOAD_TMP)

_IMAGE_MAGIC = [
    b'\xff\xd8\xff',            # JPEG
    b'\x89PNG\r\n\x1a\n',      # PNG
    b'RIFF',                    # WebP (checked with offset 8 below)
    b'\x00\x00\x00\x18ftypheic',  # HEIC
    b'\x00\x00\x00\x18ftypheix',  # HEIF
    b'\x00\x00\x00\x1cftypheic',
    b'\x00\x00\x00\x1cftypheix',
]


def _is_image_bytes(header: bytes) -> bool:
    """Check magic bytes to confirm file is an image, not a disguised script."""
    if header[:3] == b'\xff\xd8\xff':
        return True
    if header[:8] == b'\x89PNG\r\n\x1a\n':
        return True
    if header[:4] == b'RIFF' and header[8:12] == b'WEBP':
        return True
    if b'ftyp' in header[:32]:  # HEIC/HEIF ISO base media
        return True
    return False


def _save_upload(file_obj) -> str:
    """Save uploaded photo to tmp dir. Returns path. Raises ValueError on invalid input."""
    ext = Path(file_obj.name).suffix.lower() or '.jpg'
    if ext not in _ALLOWED_EXTENSIONS:
        raise ValueError(f'Unsupported file type: {ext}. Allowed: jpg, png, webp, heic.')

    _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}{ext}"
    path = _UPLOAD_DIR / name
    _punlink = path.unlink
    total = 0
    header_checked = False
    with open(path, 'wb') as f:
        for chunk in file_obj.chunks():
            total += len(chunk)
            if total > _MAX_UPLOAD_BYTES:
                _punlink(missing_ok=True)
                raise ValueError('File too large. Maximum allowed size is 15 MB.')
            if not header_checked:
                if not _is_image_bytes(chunk[:32]):
                    _punlink(missing_ok=True)
                    raise ValueError('File content does not match an image format.')
                header_checked = True
            f.write(chunk)
    return str(path)


# ── Geçmiş koleksiyonu ────────────────────────────────────────────────────────
def _save_history(user_id: int, mode: str, lang: str, result: dict, app_source: str = 'mobile'):
    try:
        _ts = time.time()
        get_history_col().insert_one({
            'user_id': user_id, 'mode': mode, 'lang': lang,
            'result':  result,
            'created_at': _ts,
            'app_source': app_source,
        })

        # Broadcast new analysis event to admin panel (WS)
        if _send_admin_event:
            try:
                _send_admin_event('new_analysis', {
                    'user_id': user_id,
                    'mode': mode,
                    'app_source': app_source,
                    'time': datetime.utcfromtimestamp(_ts).isoformat(),
                })
            except Exception:
                pass  # WS broadcast failure shouldn't break analysis saving

    except Exception as e:
        log.warning(f'Failed to save history: {e}')


# ── Temel analiz yardımcısı ───────────────────────────────────────────────────
def _check_image_quality(img_path: str) -> dict | None:
    """Run quality validation once; returns quality dict or None on failure."""
    try:
        if _ImageQualityValidator is None:
            return None
        quality = _ImageQualityValidator.validate_image_quality(img_path)
        _qcu = quality['can_upload']
        log.info(f'Image quality check: overall_score={quality["overall_score"]}, '
                 f'brightness={quality["brightness"]["value"]}, '
                 f'contrast={quality["contrast"]["value"]}, '
                 f'face_offset={quality["face_position"]["offset"]}, '
                 f'can_upload={_qcu}')
        if not _qcu:
            log.warning(f'Low quality image received: {quality["errors"]}')
        return quality
    except Exception as e:
        log.warning(f'Image quality validation failed: {e}')
        return None


def _run_analysis(img_path: str, mode: str, lang: str = 'tr', **kwargs):
    """facesyma_revize motorunu çağırır."""
    _load_engine()

    if mode == 'character':
        from database import databases
        return databases(img_path, lang)
    elif mode == 'enhanced_character':
        try:
            from database import enhanced_databases
            return enhanced_databases(img_path, lang)
        except (ImportError, AttributeError):
            from database import databases
            return databases(img_path, lang)  # Graceful fallback
    elif mode == 'modules':
        from database_modules import get_all_modules
        return get_all_modules(img_path, lang)
    elif mode == 'golden':
        from golden_ratio import analyze_golden_ratio
        r = analyze_golden_ratio(img_path, lang=lang, save_output=False)
        return {'score': r['score'], 'grade': r['grade'],
                'phi': r['phi'], 'features': r['features'],
                'image_b64': r.get('image_b64', '')}
    elif mode == 'face_type':
        from face_type import analyze_face_type
        return analyze_face_type(img_path, lang=lang)
    elif mode == 'art':
        from art_match import match_artwork
        return match_artwork(img_path, lang=lang)
    elif mode == 'astrology':
        from astrology import analyze_astrology
        _kget = kwargs.get
        return analyze_astrology(img_path, lang=lang,
                                  birth_date=_kget('birth_date', ''),
                                  birth_time=_kget('birth_time', ''))
    elif mode == 'advisor':
        from database_advisor import advisor
        return {'result': advisor(img_path, lang)}
    elif mode == 'daily':
        from database_daily import daily
        user_id = kwargs.get('user_id', 1)
        return {'result': daily(img_path, user_id, lang)}
    elif mode == 'golden_transform':
        from golden_transform import create_golden_transform_preview
        return create_golden_transform_preview(img_path, lang)
    else:
        from database import databases
        return databases(img_path, lang)


# ── Analysis rate limiter ─────────────────────────────────────────────────────
# ML inference is expensive; allow 10 req/min per IP (anon) or 20/min (authed user)
_ANALYZE_RATE_ANON   = 10
_ANALYZE_RATE_AUTHED = 20
_ANALYZE_WINDOW_SECS = 60

_VALID_LANGS = frozenset({'tr','en','de','ru','ar','es','ko','ja','zh','hi','fr','pt','bn','id','ur','it','vi','pl'})


def _check_analyze_rate(request, uid: int | None) -> bool:
    """Return True if request is allowed, False if rate limit exceeded."""
    try:
        _rmg = request.META.get
        ip = _rmg('HTTP_X_FORWARDED_FOR', _rmg('REMOTE_ADDR', 'unknown'))
        key = f'analyze_rate:{uid if uid else ip}'
        limit = _ANALYZE_RATE_AUTHED if uid else _ANALYZE_RATE_ANON
        count = cache.get(key, 0)
        if count >= limit:
            return False
        cache.set(key, count + 1, timeout=_ANALYZE_WINDOW_SECS)
    except Exception:
        pass  # Cache failure → allow request
    return True


# ── View mixin ─────────────────────────────────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class AnalyzeBaseView(View):
    mode = 'character'

    def post(self, request, **url_kwargs):
        try:
            uid  = _get_user_id(request)

            if not _check_analyze_rate(request, uid):
                return JsonResponse(
                    {'detail': 'Too many analysis requests. Please wait a moment.'},
                    status=429
                )

            _rpost = request.POST
            _rpget = _rpost.get
            lang = _rpget('lang', request.GET.get('lang', 'tr'))
            if lang not in _VALID_LANGS:
                lang = 'en'

            _rf = request.FILES
            if 'image' not in _rf:
                return JsonResponse({'detail': 'Photo required. (key: image)'}, status=400)

            img_path = _save_upload(_rf['image'])
            image_quality = _check_image_quality(img_path)

            extra = {}
            _mode = self.mode
            if _mode == 'astrology':
                birth_date = _rpget('birth_date', '')
                birth_time = _rpget('birth_time', '')
                if birth_date and not _RE_DATE.match(birth_date):
                    return JsonResponse({'detail': 'Invalid birth_date format. Use YYYY-MM-DD.'}, status=400)
                if birth_time and not _RE_TIME.match(birth_time):
                    return JsonResponse({'detail': 'Invalid birth_time format. Use HH:MM or HH:MM:SS.'}, status=400)
                extra['birth_date'] = birth_date
                extra['birth_time'] = birth_time
            if uid:
                extra['user_id'] = uid

            result = _run_analysis(img_path, _mode, lang, **extra)

            # JSON string geliyorsa parse et
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except Exception:
                    result = {'result': result}

            # ── Image Quality Metrics (Ollama Context için) ─────────────────
            if image_quality and isinstance(result, dict) and 'image_quality' not in result:
                result['image_quality'] = {
                    'overall_score':  image_quality['overall_score'],
                    'brightness':     image_quality['brightness'],
                    'contrast':       image_quality['contrast'],
                    'face_centering': image_quality['face_position'],
                    'can_upload':     image_quality['can_upload'],
                    'recommendation': image_quality['recommendation'],
                }

            if uid:
                app_source = request.headers.get('X-App-Source', 'mobile').lower()
                if app_source not in ('mobile', 'web'):
                    app_source = 'mobile'
                _save_history(uid, _mode, lang, result, app_source)
                _lwarn = log.warning

                # ── Community Auto-Creation Hook (Phase 1) ─────────────────────────
                # 'character' ve 'enhanced_character' modları için topluluğa ekle
                if _mode in _CHARACTER_MODES:
                    try:
                        from .community_hooks import auto_add_to_communities
                        community_result = auto_add_to_communities(uid, result)
                        # Result'a community info ekle
                        result['_community_join'] = community_result
                    except Exception as e:
                        _lwarn(f'Community auto-add error: {e}')

                # ── Similarity Module Integration (Phase 1) ──────────────────────────
                # 'character' ve 'enhanced_character' modları için benzeşme analizi
                if _mode in _CHARACTER_MODES:
                    try:
                        from facesyma_revize.similarity_matcher import get_similarity_matcher

                        # Sıfatları al
                        if isinstance(result, dict):
                            sifatlar = result.get('sifatlar', [])
                            if sifatlar:
                                matcher = get_similarity_matcher()
                                similarity = matcher.match_user_to_similarities(sifatlar, lang)
                                summary = matcher.generate_summary(similarity, lang)

                                # Result'a similarity ekle
                                _simget = similarity.get
                                result['similarity'] = {
                                    'celebrities': _simget('celebrities', []),
                                    'historical': _simget('historical', []),
                                    'objects': _simget('objects', []),
                                    'plants': _simget('plants', []),
                                    'animals': _simget('animals', []),
                                    'summary': summary
                                }
                    except Exception as e:
                        _lwarn(f'Similarity matching error: {e}')

            # Temp dosyayı sil
            try:
                os.remove(img_path)
            except Exception:
                pass

            return JsonResponse({'success': True, 'data': result})

        except PermissionError:
            return JsonResponse({'detail': 'Unauthorized.'}, status=401)
        except ValueError:
            return JsonResponse({'detail': 'Invalid request.'}, status=400)
        except Exception as e:
            log.exception('Analiz error')
            return JsonResponse({'detail': 'Analysis failed. Please try again.'}, status=500)


class AnalyzeView(AnalyzeBaseView):
    mode = 'character'

class AnalyzeModulesView(AnalyzeBaseView):
    mode = 'modules'

class AnalyzeGoldenView(AnalyzeBaseView):
    mode = 'golden'

class AnalyzeFaceTypeView(AnalyzeBaseView):
    mode = 'face_type'

class AnalyzeArtView(AnalyzeBaseView):
    mode = 'art'

class AnalyzeAstrologyView(AnalyzeBaseView):
    mode = 'astrology'

class AnalyzeEnhancedView(AnalyzeBaseView):
    mode = 'enhanced_character'

class AnalyzeGoldenTransformView(AnalyzeBaseView):
    mode = 'golden_transform'


# ── Twins analizi ─────────────────────────────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class TwinsView(View):
    def post(self, request):
        try:
            uid = _get_user_id(request)
            if not _check_analyze_rate(request, uid):
                return JsonResponse({'detail': 'Too many analysis requests. Please wait a moment.'}, status=429)

            lang = request.POST.get('lang', 'tr')

            # 2-5 arası fotoğraf al
            images = []
            _rf = request.FILES
            for i in range(5):
                key = f'image_{i}'
                if key in _rf:
                    images.append(_save_upload(_rf[key]))

            if len(images) < 2:
                msg = 'En az 2 fotoğraf gerekli.' if lang.startswith('tr') else 'At least 2 photos required.'
                return JsonResponse({'detail': msg}, status=400)

            _load_engine()
            try:
                from database_twins import twins
                result = twins(*images, lang)
            except ImportError:
                # Fallback: Return placeholder compatibility analysis
                result = generate_compatibility_placeholder(images, lang)

            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except Exception:
                    result = {'result': result}

            for p in images:
                try:
                    os.remove(p)
                except Exception:
                    pass

            return JsonResponse({'success': True, 'data': result})

        except Exception as e:
            log.exception('Twins error')
            return JsonResponse({'detail': 'Twins analysis failed. Please try again.'}, status=500)


_COMPAT_STRINGS = {
    'tr': {
        'title':   'Uyum Analizi',
        'detail':  '{n} kişi arasında uyum analizi yapılmıştır',
        'rec1':    'Altın Oran uyumluluğu kontrol ediliyor',
        'rec2':    'Yüz simetrisi analizi yapılıyor',
        'rec3':    'İç uyum özellikleri hesaplanıyor',
    },
    'en': {
        'title':   'Compatibility Analysis',
        'detail':  'Compatibility analysis for {n} people',
        'rec1':    'Checking Golden Ratio harmony',
        'rec2':    'Analyzing facial symmetry',
        'rec3':    'Computing compatibility features',
    },
}


def generate_compatibility_placeholder(images, lang='tr'):
    """Fallback compatibility analysis when database_twins is unavailable.

    Returns consistent keys regardless of lang so the mobile app can rely
    on a stable response shape (compatibility_score, person_count, …).
    """
    base = lang.split('-')[0].lower() if lang else 'tr'
    s    = _COMPAT_STRINGS.get(base, _COMPAT_STRINGS['en'])
    n    = len(images)
    score = min(99, 85 + n * 2)
    return {
        'compatibility_score': s['title'],
        'person_count':        n,
        'group_score':         score,   # used by TwinsScreen
        'overall_harmony':     score,
        'details':             s['detail'].format(n=n),
        'pair_scores':         {},      # no pair breakdown in fallback
        'recommendations':     [s['rec1'], s['rec2'], s['rec3']],
    }


# ── Geçmiş ────────────────────────────────────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class HistoryView(View):
    def get(self, request):
        try:
            uid = _require_auth(request)
            col = get_history_col()
            records = list(
                col.find({'user_id': uid}, {'_id': 0})
                   .sort('created_at', -1)
                   .limit(20)
            )
            return JsonResponse({'results': records})
        except PermissionError:
            return JsonResponse({'detail': 'Unauthorized.'}, status=401)
        except Exception as e:
            log.exception('History fetch error')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


# ── Günlük motivasyon ─────────────────────────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class DailyView(View):
    def get(self, request):
        try:
            lang = request.GET.get('lang', 'tr')
            base_lang = lang.split('-')[0].lower() if lang else 'tr'
            _load_engine()
            # Daily motivation doesn't need photos — fetches directly from MongoDB
            db_name = _DAILY_DB_MAP.get(base_lang, 'database_daily_en')
            cache_key = f'daily_lists:{db_name}'
            lists = cache.get(cache_key)
            if lists is None:
                db   = _get_main_client()[db_name]
                pos  = db['positive'].find_one({}, {'_id': 0, 'positive_daily': 1}) or {}
                neg  = db['negative'].find_one({}, {'_id': 0, 'negative_daily': 1}) or {}
                lists = (pos.get('positive_daily', []), neg.get('negative_daily', []))
                cache.set(cache_key, lists, timeout=3600)
            pos_list, neg_list = lists

            # Get fallback status if using English default
            is_fallback = base_lang not in _DAILY_NATIVE_LANGS
            _rc = random.choice
            return JsonResponse({
                'positive': _rc(pos_list) if pos_list else '',
                'negative': _rc(neg_list) if neg_list else '',
                'lang': base_lang,
                'is_fallback': is_fallback,
                'note': f'Using English fallback for {base_lang}' if is_fallback else None
            })
        except Exception as e:
            log.exception('Daily view error')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)
