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
from pathlib import Path
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings

log = logging.getLogger(__name__)


def _load_engine():
    """facesyma_revize'i Python path'e ekle"""
    engine_path = settings.FACESYMA_ENGINE_PATH
    if engine_path not in sys.path:
        sys.path.insert(0, engine_path)


def _get_user_id(request) -> int | None:
    """Token'dan user_id çıkar"""
    import jwt
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
            lang = request.POST.get('lang', 'tr')
            user_id = _get_user_id(request)

            # Sıfatları al - either from POST data or from request header
            sifatlar_str = request.POST.get('sifatlar', '')

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
            except Exception as e:
                return JsonResponse({
                    'detail': f'sifatlar JSON/comma-separated olmalı: {str(e)}'
                }, status=400)

            # Load similarity matcher
            _load_engine()
            try:
                from similarity_matcher import SimilarityMatcher
            except ImportError:
                log.error("Could not import SimilarityMatcher")
                return JsonResponse({
                    'detail': 'Similarity module not available'
                }, status=500)

            # Run matching
            matcher = SimilarityMatcher()

            try:
                results = matcher.match_user_to_similarities(sifatlar, lang)
                summary = matcher.generate_summary(results, lang)
                matcher.close()
            except Exception as e:
                log.exception(f'Similarity matching error: {e}')
                matcher.close()
                return JsonResponse({
                    'detail': f'Matching error: {str(e)}'
                }, status=500)

            # Save to history if user authenticated
            if user_id:
                try:
                    from admin_api.utils.mongo import get_db
                    db = get_db()
                    history = db.get_collection('analysis_history')
                    history.insert_one({
                        'user_id': user_id,
                        'mode': 'similarity',
                        'lang': lang,
                        'result': results,
                        'summary': summary,
                        'created_at': __import__('time').time()
                    })
                except Exception as e:
                    log.warning(f'Could not save to history: {e}')

            return JsonResponse({
                'success': True,
                'data': {
                    'celebrities': results.get('celebrities', []),
                    'historical': results.get('historical', []),
                    'objects': results.get('objects', []),
                    'plants': results.get('plants', []),
                    'animals': results.get('animals', []),
                    'summary': summary
                }
            })

        except Exception as e:
            log.exception(f'Similarity error: {e}')
            return JsonResponse({
                'detail': str(e)
            }, status=500)
