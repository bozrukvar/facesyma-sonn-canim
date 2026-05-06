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
        return match_artwork(img_path, lang=lang, user_id=kwargs.get('user_id'))
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
        import json as _json
        real_m = kwargs.get('real_measurements')
        if isinstance(real_m, str):
            try:
                real_m = _json.loads(real_m)
            except Exception:
                real_m = None
        return create_golden_transform_preview(img_path, lang, real_measurements=real_m)
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
            if _mode == 'golden_transform':
                extra['real_measurements'] = _rpget('real_measurements', None)

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
                        from similarity_matcher import get_similarity_matcher

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


def _build_structured_result(plain_text: str, lang: str) -> dict:
    """
    Takes the plain-text character analysis output and enriches it with
    structured career / leadership / social / personality categories by
    looking up the database_categories collection in MongoDB.
    """
    try:
        from admin_api.utils.mongo import _get_main_client
        mongo = _get_main_client()
        col = mongo['database_categories']['traits']

        # Determine language suffix
        lang_base = lang.split('-')[0].lower()
        suf = 'tr' if lang_base == 'tr' else 'en'
        kariyer_key   = f'kariyer_{suf}'
        liderlik_key  = f'liderlik_{suf}'
        sosyal_key    = f'sosyal_{suf}'
        kisilik_key   = f'kisilik_{suf}'

        # Fetch all category sentence docs
        docs = list(col.find({}, {'_id': 1, kariyer_key: 1, liderlik_key: 1, sosyal_key: 1, kisilik_key: 1}))
        if not docs:
            return {'result': plain_text}

        # Pick 3-5 random docs and extract sentences for each category
        picked = random.sample(docs, min(5, len(docs)))
        kariyer_sentences  = [d[kariyer_key]  for d in picked if kariyer_key  in d]
        liderlik_sentences = [d[liderlik_key] for d in picked if liderlik_key in d]
        sosyal_sentences   = [d[sosyal_key]   for d in picked if sosyal_key   in d]
        kisilik_sentences  = [d[kisilik_key]  for d in picked if kisilik_key  in d]

        result: dict = {'result': plain_text}
        if kariyer_sentences:
            result['kariyer'] = ' '.join(kariyer_sentences[:2])
        if liderlik_sentences:
            result['liderlik'] = ' '.join(liderlik_sentences[:2])
        if sosyal_sentences:
            result['sosyal'] = ' '.join(sosyal_sentences[:2])
        if kisilik_sentences:
            result['kisilik'] = ' '.join(kisilik_sentences[:2])
        return result
    except Exception as e:
        log.warning(f'_build_structured_result failed: {e}')
        return {'result': plain_text}


def _detect_face_center(img_path: str) -> dict:
    """OpenCV Haar cascade ile yüz merkezi tespiti. Fallback: merkez."""
    try:
        import cv2
        img = cv2.imread(img_path)
        if img is None:
            return {'cx': 0.50, 'cy': 0.38, 'found': False}
        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        faces = cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=4,
            minSize=(int(w * 0.12), int(h * 0.08)),
        )
        if not isinstance(faces, tuple) and len(faces) > 0:
            fx, fy, fw, fh = max(faces, key=lambda f: f[2] * f[3])
            return {
                'cx':    round((fx + fw / 2) / w, 4),
                'cy':    round((fy + fh / 2) / h, 4),
                'fw':    round(fw / w, 4),
                'fh':    round(fh / h, 4),
                'found': True,
            }
    except Exception as e:
        log.warning(f'Face detect error: {e}')
    return {'cx': 0.50, 'cy': 0.38, 'found': False}


@method_decorator(csrf_exempt, name='dispatch')
class FaceDetectView(View):
    """Hızlı yüz merkezi tespiti — koordinatları döndürür, kayıt yapmaz."""

    def post(self, request):
        img_path = None
        try:
            if 'image' not in request.FILES:
                return JsonResponse({'cx': 0.50, 'cy': 0.38, 'found': False})
            img_path = _save_upload(request.FILES['image'])
            result = _detect_face_center(img_path)
            return JsonResponse({'success': True, **result})
        except Exception as e:
            log.warning(f'FaceDetectView error: {e}')
            return JsonResponse({'cx': 0.50, 'cy': 0.38, 'found': False})
        finally:
            if img_path:
                try:
                    os.remove(img_path)
                except Exception:
                    pass


class AnalyzeView(AnalyzeBaseView):
    mode = 'enhanced_character'

    def post(self, request, **url_kwargs):
        response = super().post(request, **url_kwargs)
        try:
            import json as _json
            body = _json.loads(response.content)
            if body.get('success') and isinstance(body.get('data'), dict):
                data = body['data']
                # enhanced_databases → 'character_analysis'; basic → 'result'
                plain = data.get('result', '') or data.get('character_analysis', '')
                if plain and isinstance(plain, str) and len(plain) > 10:
                    _rget = request.POST.get
                    lang = _rget('lang', request.GET.get('lang', 'tr'))
                    enriched = _build_structured_result(plain, lang)
                    # ensure 'result' key present for mobile backward compat
                    if 'result' not in data:
                        data['result'] = plain
                    data.update(enriched)
                    body['data'] = data
                    return JsonResponse(body)
        except Exception as e:
            log.warning(f'AnalyzeView enrichment failed: {e}')
        return response

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
            # per-person sifat scores extracted within twins() using x/y from Match()
            _p1_scores: dict = {}
            _p2_scores: dict = {}
            try:
                from database_twins import twins
                twins_raw = twins(*images, lang)
            except Exception:
                twins_raw = generate_compatibility_placeholder(images, lang)

            # twins() now returns a structured dict; fall back to plain string for old versions
            if isinstance(twins_raw, dict) and 'text_result' in twins_raw:
                _p1_scores = twins_raw.get('person1_sifat_scores', {})
                _p2_scores = twins_raw.get('person2_sifat_scores', {})
                raw = twins_raw['text_result'].strip()
                if '#text' in raw:
                    parts = raw.split('#text', 1)
                    try:
                        score = round(float(parts[0].strip()))
                    except ValueError:
                        score = 75
                    description = parts[1].strip() if len(parts) > 1 else ''
                    result = {
                        'group_score': score,
                        'overall_harmony': score,
                        'person_count': len(images),
                        'details': description,
                        'pair_scores': {},
                        'recommendations': [],
                    }
                else:
                    result = {'group_score': 75, 'overall_harmony': 75,
                              'person_count': len(images), 'pair_scores': {}, 'recommendations': []}
            elif isinstance(twins_raw, str):
                try:
                    result = json.loads(twins_raw)
                except Exception:
                    raw = twins_raw.strip()
                    if '#text' in raw:
                        parts = raw.split('#text', 1)
                        try:
                            score = round(float(parts[0].strip()))
                        except ValueError:
                            score = 75
                        description = parts[1].strip() if len(parts) > 1 else ''
                        result = {
                            'group_score': score,
                            'overall_harmony': score,
                            'person_count': len(images),
                            'details': description,
                            'pair_scores': {},
                            'recommendations': [],
                        }
                    else:
                        result = {'result': raw}
            else:
                result = twins_raw  # already a plain dict (e.g. placeholder)

            # Build analyses list for dimension calculation.
            # Prefer per-person data from twins() (no extra face detection needed).
            if _p1_scores and _p2_scores:
                analyses = [{'sifat_scores': _p1_scores}, {'sifat_scores': _p2_scores}]
                for i in range(2, len(images)):
                    analyses.append({})  # no per-person data for >2 people
            else:
                # Fallback: run enhanced_character on each image individually
                analyses = []
                for img_path in images:
                    try:
                        person_data = _run_analysis(img_path, 'enhanced_character', lang)
                        if isinstance(person_data, str):
                            try:
                                person_data = json.loads(person_data)
                            except Exception:
                                person_data = {}
                        analyses.append(person_data if isinstance(person_data, dict) else {})
                    except Exception as e:
                        log.warning(f'Per-person twins analysis failed: {e}')
                        analyses.append({})

            dimensions = _calculate_twins_dimensions(analyses, lang)

            if isinstance(result, dict):
                if dimensions:
                    result['dimensions'] = dimensions
                # If engine gave 0, compute group_score from dimension averages
                if not result.get('group_score') and dimensions:
                    gs = round(sum([
                        dimensions['face_similarity'],
                        dimensions['character_compat'],
                        dimensions['complementarity'],
                        dimensions['shared_strengths_score'],
                        dimensions['eq_compat'],
                    ]) / 5)
                    result['group_score'] = gs
                    result['overall_harmony'] = gs

            for p in images:
                try:
                    os.remove(p)
                except Exception:
                    pass

            # Save to history
            try:
                app_source = request.headers.get('X-App-Source', 'mobile').lower()
                if app_source not in ('mobile', 'web'):
                    app_source = 'mobile'
                history_doc = {
                    'group_score':    result.get('group_score', 0) if isinstance(result, dict) else 0,
                    'person_count':   len(images),
                    'community_type': (dimensions or {}).get('community_type', ''),
                    'pair_scores':    result.get('pair_scores', {}) if isinstance(result, dict) else {},
                }
                _save_history(uid, 'twins', lang, history_doc, app_source)
            except Exception:
                pass  # history save failure must not break the response

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


# ── Twins extended analysis helpers ──────────────────────────────────────────
_TWIN_CAT_KW = {
    'romantic': frozenset({
        'romantik', 'duygu', 'hassas', 'sevgi', 'şefkat', 'empat', 'sadakat', 'bağ',
        'aşk', 'tutku', 'love', 'passion', 'tender', 'empath', 'loyal', 'caring', 'intimat',
    }),
    'social': frozenset({
        'sosyal', 'arkadaş', 'iletişim', 'eğlenc', 'espri', 'sohbet', 'neşe', 'samim',
        'dışa', 'social', 'friend', 'communic', 'fun', 'outgo', 'cheerful', 'hospitab',
    }),
    'teamwork': frozenset({
        'liderlik', 'organize', 'sorumlul', 'güvenilir', 'kararlı', 'disiplin',
        'iş', 'planlı', 'methodic', 'leader', 'organiz', 'responsib', 'reliable',
        'disciplin', 'teamwork', 'cooperat',
    }),
}

_ACTIVITY_MAP = [
    (frozenset({'yaratıcı', 'sanat', 'estetik', 'creat', 'art', 'aesthet', 'imag'}),
     {'tr': 'Sanat atölyesi veya müze gezisi', 'en': 'Art workshop or museum visit'}),
    (frozenset({'sosyal', 'eğlenc', 'neşe', 'social', 'fun', 'cheerful', 'playful'}),
     {'tr': 'Grup aktivitesi veya oyun gecesi', 'en': 'Group activity or game night'}),
    (frozenset({'doğa', 'macera', 'enerji', 'spor', 'nature', 'adventur', 'sport', 'energ'}),
     {'tr': 'Doğa yürüyüşü veya spor aktivitesi', 'en': 'Nature hike or sports activity'}),
    (frozenset({'zeka', 'düşünce', 'merak', 'analiz', 'intellect', 'curious', 'analyt'}),
     {'tr': 'Kitap kulübü veya tartışma gecesi', 'en': 'Book club or discussion night'}),
    (frozenset({'yardım', 'empat', 'şefkat', 'help', 'compassion', 'kind', 'volunt'}),
     {'tr': 'Gönüllü çalışma veya topluluk projesi', 'en': 'Volunteering or community project'}),
    (frozenset({'romantik', 'tutku', 'aşk', 'passion', 'intimat', 'roman'}),
     {'tr': 'Romantik akşam yemeği veya seyahat', 'en': 'Romantic dinner or travel'}),
    (frozenset({'müzik', 'dans', 'ritim', 'music', 'danc', 'rhythm'}),
     {'tr': 'Konser veya dans etkinliği', 'en': 'Concert or dance event'}),
    (frozenset({'yemek', 'lezzet', 'mutfak', 'food', 'cook', 'cuisine', 'gourm'}),
     {'tr': 'Yemek kursu veya gastronomi turu', 'en': 'Cooking class or gastronomy tour'}),
    (frozenset({'seyahat', 'keşif', 'travel', 'explor', 'adventur', 'wander'}),
     {'tr': 'Birlikte seyahat veya şehir keşfi', 'en': 'Travel or city exploration together'}),
]

_COMMUNITY_MAP = [
    (frozenset({'yaratıcı', 'sanat', 'estetik', 'creat', 'art', 'aesthet'}),
     {'tr': '🎨 Yaratıcı & Sanat Topluluğu', 'en': '🎨 Creative & Arts Community'}),
    (frozenset({'liderlik', 'kariyer', 'girişim', 'leader', 'career', 'ambit', 'entrepren'}),
     {'tr': '🚀 Kariyer & Girişim Grubu', 'en': '🚀 Career & Startup Group'}),
    (frozenset({'sosyal', 'eğlenc', 'neşe', 'social', 'fun', 'cheerful'}),
     {'tr': '🎉 Sosyal Etkileşim Çevresi', 'en': '🎉 Social Circle'}),
    (frozenset({'doğa', 'macera', 'spor', 'nature', 'adventur', 'sport'}),
     {'tr': '🌿 Macera & Doğa Grubu', 'en': '🌿 Adventure & Nature Group'}),
    (frozenset({'empat', 'yardım', 'şefkat', 'empath', 'help', 'kind', 'compassion'}),
     {'tr': '💝 Destek & Topluluk Grubu', 'en': '💝 Support & Community Group'}),
    (frozenset({'zeka', 'analiz', 'merak', 'intellect', 'analyt', 'curious', 'philos'}),
     {'tr': '🧩 Bilgi & Tartışma Kulübü', 'en': '🧩 Knowledge & Discussion Club'}),
    (frozenset({'müzik', 'dans', 'ritim', 'music', 'danc', 'rhythm'}),
     {'tr': '🎵 Müzik & Dans Topluluğu', 'en': '🎵 Music & Dance Community'}),
    (frozenset({'romantik', 'sevgi', 'aşk', 'love', 'romantic', 'intimat'}),
     {'tr': '💑 Çift & İlişki Topluluğu', 'en': '💑 Couples & Relationships Community'}),
]


def _match_kw(trait: str, keywords: frozenset) -> bool:
    tl = trait.lower()
    return any(kw in tl for kw in keywords)


def _compat_for_cat(all_sifatlar: set, score_maps: list, keywords: frozenset, fallback: int) -> int:
    diffs = [
        max(sm.get(s, 50.0) for sm in score_maps) - min(sm.get(s, 50.0) for sm in score_maps)
        for s in all_sifatlar if _match_kw(s, keywords)
    ]
    return max(0, min(100, round(100.0 - sum(diffs) / len(diffs)))) if diffs else fallback


def _suggest_activities(positive_traits: list, lang: str) -> list:
    lk = 'tr' if lang.startswith('tr') else 'en'
    return [labels[lk] for kws, labels in _ACTIVITY_MAP
            if any(_match_kw(t, kws) for t in positive_traits)][:3]


def _suggest_community(all_traits: list, lang: str) -> str:
    lk = 'tr' if lang.startswith('tr') else 'en'
    best, best_n = None, 0
    for kws, labels in _COMMUNITY_MAP:
        n = sum(1 for t in all_traits if _match_kw(t, kws))
        if n > best_n:
            best_n, best = n, labels[lk]
    return best or ('🤝 Genel Topluluk' if lang.startswith('tr') else '🤝 General Community')


def _calculate_twins_dimensions(analyses: list, lang: str) -> dict:
    """Compute 5 compatibility dimensions from per-person character analyses.

    Each person's analysis must contain a 'sifatlar' list of {sifat, score} dicts.
    Returns an empty dict when there are fewer than 2 non-empty analyses.
    """
    score_maps = []
    for analysis in analyses:
        sm = {}
        if not isinstance(analysis, dict):
            score_maps.append(sm)
            continue

        # Format 1: sifatlar list → [{sifat/name, score}]  (legacy)
        sifatlar = analysis.get('sifatlar', [])
        # Format 2: enhanced_databases → sifat_scores dict {name: 0-1 float}
        sifat_scores = analysis.get('sifat_scores', {})
        # Format 3: enhanced_databases → top_sifatlar list [{sifat, score}]
        top_sifatlar = analysis.get('top_sifatlar', [])

        if sifatlar:
            for item in sifatlar:
                if isinstance(item, dict):
                    name = item.get('sifat', item.get('name', ''))
                    try:
                        s = float(item.get('score', 0))
                        s = s * 100 if s <= 1.0 else s  # normalise 0-1 → 0-100
                    except (TypeError, ValueError):
                        s = 0.0
                    if name:
                        sm[name] = s
        elif sifat_scores:
            for name, s in sifat_scores.items():
                try:
                    s = float(s)
                    s = s * 100 if s <= 1.0 else s
                except (TypeError, ValueError):
                    s = 0.0
                if name:
                    sm[name] = s
        elif top_sifatlar:
            for item in top_sifatlar:
                if isinstance(item, dict):
                    name = item.get('sifat', item.get('name', ''))
                    try:
                        s = float(item.get('score', 0))
                        s = s * 100 if s <= 1.0 else s
                    except (TypeError, ValueError):
                        s = 0.0
                    if name:
                        sm[name] = s
        score_maps.append(sm)

    all_sifatlar = set()
    for sm in score_maps:
        all_sifatlar.update(sm.keys())

    if not all_sifatlar or len([sm for sm in score_maps if sm]) < 2:
        return {}

    n = len(score_maps)

    # 1. Yüz benzerliği — pairwise mean absolute difference across all traits
    pair_sims = []
    for i in range(n):
        for j in range(i + 1, n):
            sm_a, sm_b = score_maps[i], score_maps[j]
            diffs = [abs(sm_a.get(s, 50.0) - sm_b.get(s, 50.0)) for s in all_sifatlar]
            if diffs:
                pair_sims.append(max(0.0, 100.0 - sum(diffs) / len(diffs)))
    face_similarity = round(sum(pair_sims) / len(pair_sims)) if pair_sims else 75

    # 2. Karakter uyumu — alignment on traits all persons share
    common = all_sifatlar.copy()
    for sm in score_maps:
        common &= set(sm.keys())
    if common:
        char_diffs = [max(sm.get(s, 50.0) for sm in score_maps) - min(sm.get(s, 50.0) for sm in score_maps)
                      for s in common]
        character_compat = max(0, min(100, round(100.0 - sum(char_diffs) / len(char_diffs))))
    else:
        character_compat = 65

    # 3. Tamamlayıcılık — where one person excels, the other balances
    HIGH = 65.0
    sm_a, sm_b = score_maps[0], score_maps[1]
    diff_count = complement_count = 0
    for s in all_sifatlar:
        a, b = sm_a.get(s, 50.0), sm_b.get(s, 50.0)
        if abs(a - b) > 20:
            diff_count += 1
            if (a >= HIGH and b < HIGH) or (b >= HIGH and a < HIGH):
                complement_count += 1
    complement_score = round(min(100, 45 + (complement_count / diff_count) * 55)) if diff_count else 65

    # 4. Ortak güçler — traits where everyone scores ≥ 68
    HIGH_THRESHOLD = 68.0
    shared_list = [s for s in common if all(sm.get(s, 0.0) >= HIGH_THRESHOLD for sm in score_maps)]
    shared_strengths_score = min(100, round(50 + len(shared_list) * 4))

    # 5. İletişim & EQ uyumu — closeness on emotional/communication traits
    EQ_KEYWORDS = frozenset({
        'empat', 'iletişim', 'sosyal', 'duygu', 'anlayış', 'dinle', 'saygı', 'güven',
        'empath', 'communic', 'social', 'emotion', 'understand', 'listen', 'trust',
    })
    eq_compat = _compat_for_cat(all_sifatlar, score_maps, EQ_KEYWORDS,
                                 fallback=round((face_similarity + character_compat) / 2))

    # 6. Romantik uyum
    romantic_compat = _compat_for_cat(
        all_sifatlar, score_maps, _TWIN_CAT_KW['romantic'],
        fallback=round((face_similarity * 0.35 + character_compat * 0.35 + complement_score * 0.3)),
    )

    # 7. Sosyal uyum
    social_compat = _compat_for_cat(
        all_sifatlar, score_maps, _TWIN_CAT_KW['social'],
        fallback=round((eq_compat * 0.6 + character_compat * 0.4)),
    )

    # 8. Ekip çalışması uyumu
    teamwork_compat = _compat_for_cat(
        all_sifatlar, score_maps, _TWIN_CAT_KW['teamwork'],
        fallback=round((character_compat * 0.5 + complement_score * 0.5)),
    )

    # 9. Olumlu ortak özellikler — her ikisi ≥ 60
    positive_shared = [s for s in common if all(sm.get(s, 0.0) >= 60.0 for sm in score_maps)]

    # 10. Gelişim alanları — her ikisi ≤ 42 (shared growth opportunities)
    negative_shared = [s for s in common if all(sm.get(s, 100.0) <= 42.0 for sm in score_maps)]

    # 11. Önerilen etkinlikler
    all_traits_list = list(all_sifatlar)
    activity_suggestions = _suggest_activities(positive_shared or all_traits_list, lang)

    # 12. Topluluk önerisi
    community_type = _suggest_community(positive_shared or all_traits_list, lang)

    return {
        'face_similarity':        face_similarity,
        'character_compat':       character_compat,
        'complementarity':        complement_score,
        'shared_strengths_score': shared_strengths_score,
        'shared_strengths_list':  shared_list[:8],
        'eq_compat':              eq_compat,
        'romantic_compat':        romantic_compat,
        'social_compat':          social_compat,
        'teamwork_compat':        teamwork_compat,
        'positive_shared':        positive_shared[:10],
        'negative_shared':        negative_shared[:6],
        'activity_suggestions':   activity_suggestions,
        'community_type':         community_type,
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


# ── Geçmiş silme ─────────────────────────────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class HistoryDeleteView(View):
    """Tek bir analiz kaydını siler (user sadece kendi kaydını silebilir)."""
    def delete(self, request, record_id: str):
        try:
            uid = _require_auth(request)
            col = get_history_col()
            result = col.delete_one({'_id': record_id, 'user_id': uid})
            if result.deleted_count == 0:
                # Farklı id formatı dene (string uuid olabilir)
                from bson import ObjectId
                try:
                    result = col.delete_one({'_id': ObjectId(record_id), 'user_id': uid})
                except Exception:
                    pass
            return JsonResponse({'deleted': result.deleted_count > 0})
        except PermissionError:
            return JsonResponse({'detail': 'Unauthorized.'}, status=401)
        except Exception:
            log.exception('History delete error')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class HistoryDeleteAllView(View):
    """Kullanıcının tüm analiz geçmişini siler."""
    def delete(self, request):
        try:
            uid = _require_auth(request)
            col = get_history_col()
            result = col.delete_many({'user_id': uid})
            return JsonResponse({'deleted_count': result.deleted_count})
        except PermissionError:
            return JsonResponse({'detail': 'Unauthorized.'}, status=401)
        except Exception:
            log.exception('History delete all error')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


# ── Günlük motivasyon — AI üretimli kişisel mesaj ────────────────────────────

_DAILY_AI_PROMPTS: dict = {
    'tr': (
        "Sen bir kişisel gelişim koçusun. Kullanıcının şu kişilik özellikleri var: {sifatlar}. "
        "Bu özelliklere dayanarak bugün için kişiye özel, motive edici 2-3 kısa cümle yaz. "
        "'Sen' diye hitap et, sıcak ve destekleyici ol. Sadece cümleleri yaz, başka hiçbir şey ekleme."
    ),
    'en': (
        "You are a personal development coach. The user has these personality traits: {sifatlar}. "
        "Write 2-3 short, personalized motivational sentences for today based on these traits. "
        "Address them as 'you', keep a warm supportive tone. Write only the sentences, nothing else."
    ),
    'de': (
        "Du bist ein persönlicher Entwicklungscoach. Der Nutzer hat folgende Persönlichkeitsmerkmale: {sifatlar}. "
        "Schreibe 2-3 kurze, personalisierte Motivationssätze für heute. "
        "Sprich sie mit 'du' an, bleib warm und unterstützend. Schreibe nur die Sätze auf Deutsch."
    ),
    'ru': (
        "Ты личный коуч по развитию. У пользователя следующие черты характера: {sifatlar}. "
        "Напиши 2-3 коротких мотивационных предложения на сегодня на русском языке. "
        "Обращайся на 'ты', тон тёплый и поддерживающий. Пиши только предложения."
    ),
    'ar': (
        "أنت مدرب تطوير شخصي. المستخدم لديه هذه الصفات الشخصية: {sifatlar}. "
        "اكتب 2-3 جمل تحفيزية قصيرة لهذا اليوم باللغة العربية. "
        "خاطبه بضمير المفرد، واجعل النبرة دافئة وداعمة. اكتب الجمل فقط."
    ),
    'es': (
        "Eres un coach de desarrollo personal. El usuario tiene estos rasgos de personalidad: {sifatlar}. "
        "Escribe 2-3 frases cortas y motivadoras para hoy en español. "
        "Diríjete a él/ella de 'tú', tono cálido y de apoyo. Escribe solo las frases."
    ),
    'ko': (
        "당신은 개인 발전 코치입니다. 사용자는 다음과 같은 성격 특성을 가지고 있습니다: {sifatlar}. "
        "이러한 특성을 바탕으로 오늘을 위한 짧고 개인화된 동기 부여 문장 2-3개를 한국어로 작성하세요. "
        "'당신'으로 호칭하고 따뜻하고 지지하는 톤으로 문장만 작성하세요."
    ),
    'ja': (
        "あなたはパーソナルコーチです。ユーザーの性格特性は次のとおりです: {sifatlar}。"
        "今日のための短い個人化されたモチベーションの文章を日本語で2-3文書いてください。"
        "「あなた」と呼びかけ、温かいトーンで文章のみ書いてください。"
    ),
    'zh': (
        "你是一位个人发展教练。用户具有以下性格特征：{sifatlar}。"
        "根据这些特征，用中文为今天写2-3句简短的个性化励志话语。"
        "以'你'称呼，保持温暖支持的语气，只写句子。"
    ),
    'hi': (
        "आप एक व्यक्तिगत विकास कोच हैं। उपयोगकर्ता के व्यक्तित्व गुण हैं: {sifatlar}। "
        "इन गुणों के आधार पर आज के लिए हिंदी में 2-3 छोटे प्रेरक वाक्य लिखें। "
        "'आप' से संबोधित करें, गर्म और सहायक स्वर रखें। केवल वाक्य लिखें।"
    ),
    'fr': (
        "Tu es un coach de développement personnel. L'utilisateur a ces traits de personnalité : {sifatlar}. "
        "Écris 2-3 phrases courtes et motivantes pour aujourd'hui en français. "
        "Tutoie-le, garde un ton chaleureux et bienveillant. Écris uniquement les phrases."
    ),
    'pt': (
        "Você é um coach de desenvolvimento pessoal. O usuário tem estas características de personalidade: {sifatlar}. "
        "Escreva 2-3 frases curtas e motivadoras para hoje em português. "
        "Use 'você', mantenha um tom caloroso e de apoio. Escreva apenas as frases."
    ),
    'bn': (
        "আপনি একজন ব্যক্তিগত উন্নয়ন কোচ। ব্যবহারকারীর ব্যক্তিত্বের বৈশিষ্ট্য: {sifatlar}। "
        "এই বৈশিষ্ট্যের উপর ভিত্তি করে আজকের জন্য বাংলায় ২-৩টি সংক্ষিপ্ত অনুপ্রেরণামূলক বাক্য লিখুন। "
        "'আপনি' সম্বোধন করুন, উষ্ণ ও সহায়ক স্বর রাখুন। শুধু বাক্যগুলো লিখুন।"
    ),
    'id': (
        "Kamu adalah pelatih pengembangan pribadi. Pengguna memiliki sifat kepribadian ini: {sifatlar}. "
        "Tulis 2-3 kalimat motivasi singkat dan personal untuk hari ini dalam bahasa Indonesia. "
        "Gunakan 'kamu', jaga nada hangat dan suportif. Tulis kalimat saja."
    ),
    'ur': (
        "آپ ایک ذاتی ترقی کے کوچ ہیں۔ صارف کی شخصیت کی خصوصیات ہیں: {sifatlar}۔ "
        "ان خصوصیات کی بنیاد پر آج کے لیے اردو میں 2-3 مختصر حوصلہ افزا جملے لکھیں۔ "
        "'آپ' سے مخاطب کریں، گرم اور معاون لہجہ رکھیں۔ صرف جملے لکھیں۔"
    ),
    'it': (
        "Sei un coach di sviluppo personale. L'utente ha questi tratti della personalità: {sifatlar}. "
        "Scrivi 2-3 frasi brevi e motivanti per oggi in italiano. "
        "Rivolgiti con 'tu', mantieni un tono caldo e di supporto. Scrivi solo le frasi."
    ),
    'vi': (
        "Bạn là một huấn luyện viên phát triển cá nhân. Người dùng có những đặc điểm tính cách: {sifatlar}. "
        "Viết 2-3 câu động lực ngắn và cá nhân hóa cho hôm nay bằng tiếng Việt. "
        "Dùng 'bạn', giữ giọng ấm áp và hỗ trợ. Chỉ viết các câu."
    ),
    'pl': (
        "Jesteś coachem rozwoju osobistego. Użytkownik ma następujące cechy osobowości: {sifatlar}. "
        "Napisz 2-3 krótkie, spersonalizowane zdania motywacyjne na dziś po polsku. "
        "Zwracaj się 'ty', zachowaj ciepły i wspierający ton. Pisz tylko zdania."
    ),
}

_DAILY_STATIC_FALLBACK: dict = {
    'tr': [
        "Bugün sahip olduğun güçlü yönler seni ileriye taşıyor. Kendine güven.",
        "Her adım, seni en iyi versiyonuna yaklaştırıyor. Devam et.",
        "Senin gibi biri için her gün yeni bir fırsat barındırıyor.",
    ],
    'en': [
        "Your unique strengths carry you forward today. Trust yourself.",
        "Every step brings you closer to your best self. Keep going.",
        "Someone like you finds opportunity in every new day.",
    ],
}


def _get_ai_daily_message(user_id: int, sifatlar: list, lang: str) -> str | None:
    """Generate personalized daily message via Ollama HTTP API. Returns None on failure."""
    if not sifatlar:
        return None
    try:
        import requests as _req
        from datetime import date as _date
        today = _date.today().isoformat()
        cache_key = f'daily_ai:{user_id}:{today}:{lang}'
        cached = cache.get(cache_key)
        if cached:
            return cached
        prompt_tmpl = _DAILY_AI_PROMPTS.get(lang, _DAILY_AI_PROMPTS['en'])
        prompt = prompt_tmpl.format(sifatlar=', '.join(sifatlar[:5]))
        ollama_url = os.environ.get('OLLAMA_URL', 'http://host.docker.internal:11434')
        r = _req.post(
            f'{ollama_url}/api/generate',
            json={'model': 'mistral', 'prompt': prompt, 'stream': False},
            timeout=30,
        )
        if r.ok:
            msg = r.json().get('response', '').strip()
            if msg:
                cache.set(cache_key, msg, timeout=86400)
                return msg
    except Exception:
        pass
    return None


def _get_static_daily(base_lang: str, user_id: int | None = None) -> str:
    """Pick today's message from seeded MongoDB — same message all day, different every day."""
    from datetime import date as _date
    today_str = _date.today().isoformat()
    seed = hash(f'{today_str}:{user_id or 0}:{base_lang}') & 0x7FFFFFFF
    try:
        db_name = _DAILY_DB_MAP.get(base_lang, 'database_daily_en')
        list_key = f'daily_lists:{db_name}'
        lists = cache.get(list_key)
        if lists is None:
            db   = _get_main_client()[db_name]
            pos  = db['positive'].find_one({}, {'_id': 0, 'positive_daily': 1}) or {}
            neg  = db['negative'].find_one({}, {'_id': 0, 'negative_daily': 1}) or {}
            lists = (pos.get('positive_daily', []), neg.get('negative_daily', []))
            cache.set(list_key, lists, timeout=3600)
        pos_list, _ = lists
        if pos_list:
            return pos_list[seed % len(pos_list)]
    except Exception:
        pass
    fallback = _DAILY_STATIC_FALLBACK.get(base_lang, _DAILY_STATIC_FALLBACK['en'])
    return fallback[seed % len(fallback)]


@method_decorator(csrf_exempt, name='dispatch')
class DailyView(View):
    def get(self, request):
        try:
            lang = request.GET.get('lang', 'tr')
            base_lang = lang.split('-')[0].lower() if lang else 'tr'

            # Try AI-generated personalized message for authenticated users
            uid = _get_user_id(request)
            ai_msg = None
            if uid:
                try:
                    db = _get_main_client()['facesyma-backend']
                    doc = db['analysis_history'].find_one(
                        {'user_id': uid},
                        {'positive_sifatlar': 1, 'sifatlar': 1},
                        sort=[('created_at', -1)],
                    )
                    sifatlar = []
                    if doc:
                        sifatlar = doc.get('positive_sifatlar') or doc.get('sifatlar') or []
                        sifatlar = [s for s in sifatlar if s]
                    ai_msg = _get_ai_daily_message(uid, sifatlar, base_lang)
                except Exception:
                    pass

            positive = ai_msg or _get_static_daily(base_lang, uid)

            return JsonResponse({
                'positive':    positive,
                'lang':        base_lang,
                'ai_powered':  bool(ai_msg),
                'is_fallback': False,
            })
        except Exception:
            log.exception('Daily view error')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)
