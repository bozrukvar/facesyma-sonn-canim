"""
similarity_views.py
===================
5 Benzeriniz (Similarity) API endpoints.

Endpoints:
  POST /api/v1/analysis/analyze/similarity/  → SimilarityAnalyzeView
"""

import os
import sys
import json
import logging
import time
import jwt
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
from admin_api.utils.mongo import get_db as _get_mongo_db

log = logging.getLogger(__name__)

_ENGINE_PATH: str = settings.FACESYMA_ENGINE_PATH
_JWT_SECRET: str = settings.JWT_SECRET


def _load_engine():
    """facesyma_revize'i Python path'e ekle"""
    _spath = sys.path
    if _ENGINE_PATH not in _spath:
        _spath.insert(0, _ENGINE_PATH)


def _get_user_id(request) -> int | None:
    """Token'dan user_id çıkar"""
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


@method_decorator(csrf_exempt, name='dispatch')
class SimilarityAnalyzeView(View):
    """
    POST /api/v1/analysis/analyze/similarity/

    Kullanıcı fotoğrafını 5 kategoride eşleştir.

    Parameters:
        image: file (JPEG/PNG)
        lang: "tr" or "en" (optional, default: "tr")

    Response:
        {
            "success": true,
            "data": {
                "celebrities": [
                    {
                        "rank": 1,
                        "name": "Angelina Jolie",
                        "score": 95,
                        "image_url": "...",
                        "sifatlar": ["Güzel", "Cesur"],
                        "match_reason": "..."
                    },
                    ...
                ],
                "historical": [...],
                "objects": [...],
                "plants": [...],
                "animals": [...],
                "summary": "..."
            }
        }
    """

    def post(self, request):
        try:
            _rpg = request.POST.get
            lang = _rpg('lang', 'tr')
            user_id = _get_user_id(request)

            # Sıfatları al - either from POST data or from request header
            sifatlar_str = _rpg('sifatlar', '')

            if not sifatlar_str:
                return JsonResponse({
                    'detail': 'sifatlar parametresi gerekli (JSON array or comma-separated)'
                }, status=400)

            # Parse sıfatlar
            try:
                if sifatlar_str.startswith('['):
                    sifatlar = json.loads(sifatlar_str)
                else:
                    sifatlar = [s.strip() for s in sifatlar_str.split(',')]
            except Exception:
                return JsonResponse({
                    'detail': 'sifatlar must be JSON array or comma-separated string.'
                }, status=400)

            # Load similarity matcher
            _load_engine()
            try:
                from similarity_matcher import get_similarity_matcher
            except ImportError:
                log.error("Could not import SimilarityMatcher")
                return JsonResponse({
                    'detail': 'Similarity module not available'
                }, status=500)

            # Run matching
            matcher = get_similarity_matcher()

            try:
                results = matcher.match_user_to_similarities(sifatlar, lang)
                summary = matcher.generate_summary(results, lang)
            except Exception as e:
                log.exception(f'Similarity matching error: {e}')
                return JsonResponse({
                    'detail': 'Similarity matching failed. Please try again.'
                }, status=500)

            # Save to history if user authenticated
            if user_id:
                try:
                    db = _get_mongo_db()
                    history = db.get_collection('analysis_history')
                    history.insert_one({
                        'user_id': user_id,
                        'mode': 'similarity',
                        'lang': lang,
                        'result': results,
                        'summary': summary,
                        'created_at': time.time()
                    })
                except Exception as e:
                    log.warning(f'Could not save to history: {e}')

            _rget = results.get
            return JsonResponse({
                'success': True,
                'data': {
                    'celebrities': _rget('celebrities', []),
                    'historical': _rget('historical', []),
                    'objects': _rget('objects', []),
                    'plants': _rget('plants', []),
                    'animals': _rget('animals', []),
                    'summary': summary
                }
            })

        except Exception as e:
            log.exception(f'Similarity error: {e}')
            return JsonResponse({
                'detail': 'Internal server error.'
            }, status=500)
