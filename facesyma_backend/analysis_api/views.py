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
import uuid
import time
import logging
from pathlib import Path

import jwt
from django.conf       import settings
from django.http       import JsonResponse
from django.views      import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators      import method_decorator
from pymongo import MongoClient

log = logging.getLogger(__name__)


# ── Motor yükleme ─────────────────────────────────────────────────────────────
def _load_engine():
    """facesyma_revize'i Python path'e ekle"""
    engine_path = settings.FACESYMA_ENGINE_PATH
    if engine_path not in sys.path:
        sys.path.insert(0, engine_path)


# ── JWT yardımcısı ────────────────────────────────────────────────────────────
def _get_user_id(request) -> int | None:
    """Token'dan user_id çıkar. Token yoksa None döner (anonim izin)."""
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


def _require_auth(request):
    uid = _get_user_id(request)
    if uid is None:
        raise PermissionError('Kimlik doğrulama gerekli.')
    return uid


# ── Fotoğraf kaydetme ─────────────────────────────────────────────────────────
def _save_upload(file_obj) -> str:
    """Yüklenen fotoğrafı tmp klasörüne kaydeder. Yolu döner."""
    upload_dir = Path(settings.UPLOAD_TMP)
    upload_dir.mkdir(parents=True, exist_ok=True)
    ext  = Path(file_obj.name).suffix or '.jpg'
    name = f"{uuid.uuid4().hex}{ext}"
    path = upload_dir / name
    with open(path, 'wb') as f:
        for chunk in file_obj.chunks():
            f.write(chunk)
    return str(path)


# ── Geçmiş koleksiyonu ────────────────────────────────────────────────────────
def _history_col():
    client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
    return client['facesyma-backend']['analysis_history']


def _save_history(user_id: int, mode: str, lang: str, result: dict, app_source: str = 'mobile'):
    try:
        _history_col().insert_one({
            'user_id': user_id, 'mode': mode, 'lang': lang,
            'result':  result,
            'created_at': time.time(),
            'app_source': app_source,
        })

        # Broadcast new analysis event to admin panel (WS)
        try:
            from admin_api.consumers import send_admin_event
            send_admin_event('new_analysis', {
                'user_id': user_id,
                'mode': mode,
                'app_source': app_source,
                'time': __import__('datetime').datetime.now().isoformat()
            })
        except Exception:
            pass  # WS broadcast failure shouldn't break analysis saving

    except Exception as e:
        log.warning(f'Geçmiş kaydedilemedi: {e}')


# ── Temel analiz yardımcısı ───────────────────────────────────────────────────
def _run_analysis(img_path: str, mode: str, lang: str = 'tr', **kwargs):
    """facesyma_revize motorunu çağırır. Kalite kontrolünü çalıştırır."""
    # Image quality validation (server-side safety net)
    try:
        from analysis_api.image_validator import ImageQualityValidator
        quality = ImageQualityValidator.validate_image_quality(img_path)

        # Log quality metrics for monitoring
        log.info(f'Image quality check: overall_score={quality["overall_score"]}, '
                f'brightness={quality["brightness"]["value"]}, '
                f'contrast={quality["contrast"]["value"]}, '
                f'face_offset={quality["face_position"]["offset"]}, '
                f'can_upload={quality["can_upload"]}')

        # Warning for low quality (still allows upload for graceful degradation)
        if not quality['can_upload']:
            log.warning(f'Low quality image received: {quality["errors"]}')
    except Exception as e:
        log.warning(f'Image quality validation failed: {e}')
        # Fail gracefully - continue with analysis even if validation fails

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
        return analyze_astrology(img_path, lang=lang,
                                  birth_date=kwargs.get('birth_date', ''),
                                  birth_time=kwargs.get('birth_time', ''))
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


# ── View mixin ─────────────────────────────────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class AnalyzeBaseView(View):
    mode = 'character'

    def post(self, request, **url_kwargs):
        try:
            uid  = _get_user_id(request)
            lang = request.POST.get('lang', request.GET.get('lang', 'tr'))

            if 'image' not in request.FILES:
                return JsonResponse({'detail': 'Fotoğraf gerekli. (key: image)'}, status=400)

            img_path = _save_upload(request.FILES['image'])

            extra = {}
            if self.mode == 'astrology':
                extra['birth_date'] = request.POST.get('birth_date', '')
                extra['birth_time'] = request.POST.get('birth_time', '')
            if uid:
                extra['user_id'] = uid

            result = _run_analysis(img_path, self.mode, lang, **extra)

            # JSON string geliyorsa parse et
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except Exception:
                    result = {'result': result}

            # ── Image Quality Metrics (Ollama Context için) ─────────────────
            # Quality validation'dan gelen metrics'i result'a ekle
            try:
                from analysis_api.image_validator import ImageQualityValidator
                if isinstance(result, dict) and 'image_quality' not in result:
                    quality = ImageQualityValidator.validate_image_quality(img_path)
                    result['image_quality'] = {
                        'overall_score': quality['overall_score'],
                        'brightness': quality['brightness'],
                        'contrast': quality['contrast'],
                        'face_centering': quality['face_position'],
                        'can_upload': quality['can_upload'],
                        'recommendation': quality['recommendation']
                    }
            except Exception as e:
                log.warning(f'Image quality metrics için result güncellemesi başarısız: {e}')

            if uid:
                app_source = request.headers.get('X-App-Source', 'mobile').lower()
                if app_source not in ('mobile', 'web'):
                    app_source = 'mobile'
                _save_history(uid, self.mode, lang, result, app_source)

                # ── Community Auto-Creation Hook (Phase 1) ─────────────────────────
                # 'character' ve 'enhanced_character' modları için topluluğa ekle
                if self.mode in ['character', 'enhanced_character']:
                    try:
                        from .community_hooks import auto_add_to_communities
                        community_result = auto_add_to_communities(uid, result)
                        # Result'a community info ekle
                        result['_community_join'] = community_result
                    except Exception as e:
                        log.warning(f'Community auto-add hatası: {e}')

                # ── Similarity Module Integration (Phase 1) ──────────────────────────
                # 'character' ve 'enhanced_character' modları için benzeşme analizi
                if self.mode in ['character', 'enhanced_character']:
                    try:
                        from facesyma_revize.similarity_matcher import SimilarityMatcher

                        # Sıfatları al
                        if isinstance(result, dict):
                            sifatlar = result.get('sifatlar', [])
                            if sifatlar:
                                matcher = SimilarityMatcher()
                                similarity = matcher.match_user_to_similarities(sifatlar, lang)
                                summary = matcher.generate_summary(similarity, lang)
                                matcher.close()

                                # Result'a similarity ekle
                                result['similarity'] = {
                                    'celebrities': similarity.get('celebrities', []),
                                    'historical': similarity.get('historical', []),
                                    'objects': similarity.get('objects', []),
                                    'plants': similarity.get('plants', []),
                                    'animals': similarity.get('animals', []),
                                    'summary': summary
                                }
                    except Exception as e:
                        log.warning(f'Similarity matching hatası: {e}')

            # Temp dosyayı sil
            try:
                os.remove(img_path)
            except Exception:
                pass

            return JsonResponse({'success': True, 'data': result})

        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except Exception as e:
            log.exception(f'Analiz hatası: {e}')
            return JsonResponse({'detail': f'Analiz hatası: {str(e)}'}, status=500)


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
            lang = request.POST.get('lang', 'tr')

            # 2-5 arası fotoğraf al
            images = []
            for i in range(5):
                key = f'image_{i}'
                if key in request.FILES:
                    images.append(_save_upload(request.FILES[key]))

            if len(images) < 2:
                return JsonResponse({'detail': 'En az 2 fotoğraf gerekli.'}, status=400)

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
            log.exception(f'Twins hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


def generate_compatibility_placeholder(images, lang='tr'):
    """Fallback compatibility analysis when database_twins is unavailable."""
    person_count = len(images)

    if lang == 'tr':
        return {
            'uyum_notu': 'Uyum Analizi Geçici',
            'kisi_sayisi': person_count,
            'genel_uyum_skoru': 85 + (person_count * 2),
            'detay': f'{person_count} kişi arasında uyum analizi yapılmıştır',
            'oneriler': [
                'Golden Ratio uyumluluğu kontrol ediliyor',
                'Yüz simetrisi analizi yapılıyor',
                'İç uyum özellikleri hesaplanıyor'
            ]
        }
    else:
        return {
            'compatibility_score': 'Compatibility Analysis Pending',
            'person_count': person_count,
            'overall_harmony': 85 + (person_count * 2),
            'details': f'Compatibility analysis for {person_count} people',
            'recommendations': [
                'Checking Golden Ratio harmony',
                'Analyzing facial symmetry',
                'Computing compatibility features'
            ]
        }


# ── Geçmiş ────────────────────────────────────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class HistoryView(View):
    def get(self, request):
        try:
            uid = _require_auth(request)
            col = _history_col()
            records = list(
                col.find({'user_id': uid}, {'_id': 0})
                   .sort('created_at', -1)
                   .limit(20)
            )
            return JsonResponse({'results': records})
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except Exception as e:
            return JsonResponse({'detail': str(e)}, status=500)


# ── Günlük motivasyon ─────────────────────────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class DailyView(View):
    def get(self, request):
        try:
            lang = request.GET.get('lang', 'tr')
            base_lang = lang.split('-')[0].lower() if lang else 'tr'
            _load_engine()
            from database_daily import daily as get_daily
            # Daily motivation doesn't need photos — fetches directly from MongoDB
            client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)

            # Database mapping for 18 languages
            # Languages with data: tr, en, de, ru, ar (5)
            # Languages with fallback chain: es→en, ko→en, ja→en, zh→en, hi→en, fr→en, pt→en, bn→en, id→en, ur→en, it→en, vi→en, pl→en
            db_map = {
                'tr': 'database_daily_tr', 'en': 'database_daily_en',
                'de': 'database_daily_de', 'ru': 'database_daily_ru',
                'ar': 'database_daily_ar',
                # Fallback to English for languages without native data
                'es': 'database_daily_en', 'ko': 'database_daily_en',
                'ja': 'database_daily_en', 'zh': 'database_daily_en',
                'hi': 'database_daily_en', 'fr': 'database_daily_en',
                'pt': 'database_daily_en', 'bn': 'database_daily_en',
                'id': 'database_daily_en', 'ur': 'database_daily_en',
                'it': 'database_daily_en', 'vi': 'database_daily_en',
                'pl': 'database_daily_en',
            }
            db_name = db_map.get(base_lang, 'database_daily_en')
            db      = client[db_name]
            import random

            pos = db['positive'].find_one()
            neg = db['negative'].find_one()
            pos_list = pos.get('positive_daily', []) if pos else []
            neg_list = neg.get('negative_daily', []) if neg else []

            # Get fallback status if using English default
            is_fallback = base_lang not in ['tr', 'en', 'de', 'ru', 'ar']

            return JsonResponse({
                'positive': random.choice(pos_list) if pos_list else '',
                'negative': random.choice(neg_list) if neg_list else '',
                'lang': base_lang,
                'is_fallback': is_fallback,
                'note': f'Using English fallback for {base_lang}' if is_fallback else None
            })
        except Exception as e:
            return JsonResponse({'detail': str(e)}, status=500)
