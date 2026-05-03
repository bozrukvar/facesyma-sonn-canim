"""
similarity_views.py
===================
Archetype similarity API — cluster-based matching with rotation.

Endpoint:
  POST /api/v1/analysis/analyze/similarity/  → SimilarityAnalyzeView

Request body (form-data or JSON):
  sifatlar  — JSON array or comma-separated list of personality adjectives
  lang      — language code, default "tr"

Response:
  {
    "success": true,
    "data": {
      "celebrity": {"id":"..","name":"..","emoji":"..","reason":"..","primary_cluster":"..","score":0.87},
      "animal":    { … },
      "plant":     { … },
      "object":    { … },
      "blend":          "…blend sentence…",
      "primary_cluster":   "intelligence",
      "secondary_cluster": "creativity"
    }
  }
"""

import json
import logging
import sys
import time

import jwt
from django.conf import settings
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from admin_api.utils.mongo import _get_db as _get_mongo_db

log = logging.getLogger(__name__)

_ENGINE_PATH: str = settings.FACESYMA_ENGINE_PATH
_JWT_SECRET:  str = settings.JWT_SECRET


def _load_engine():
    if _ENGINE_PATH not in sys.path:
        sys.path.insert(0, _ENGINE_PATH)


def _get_user_id(request) -> int | None:
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    try:
        payload = jwt.decode(auth.split(' ', 1)[1], _JWT_SECRET, algorithms=['HS256'])
        return payload.get('user_id')
    except Exception:
        return None


@method_decorator(csrf_exempt, name='dispatch')
class SimilarityAnalyzeView(View):

    def post(self, request):
        try:
            # ── parse request ──────────────────────────────────────────────
            content_type = request.content_type or ''
            if 'application/json' in content_type:
                try:
                    body = json.loads(request.body)
                except Exception:
                    body = {}
                sifatlar_raw = body.get('sifatlar', '')
                lang = body.get('lang', 'tr')
            else:
                sifatlar_raw = request.POST.get('sifatlar', '')
                lang = request.POST.get('lang', 'tr')

            if not sifatlar_raw:
                return JsonResponse(
                    {'detail': 'sifatlar parametresi gerekli (JSON array veya virgülle ayrılmış liste)'},
                    status=400,
                )

            if isinstance(sifatlar_raw, list):
                sifatlar = sifatlar_raw
            elif isinstance(sifatlar_raw, str) and sifatlar_raw.startswith('['):
                try:
                    sifatlar = json.loads(sifatlar_raw)
                except Exception:
                    return JsonResponse({'detail': 'sifatlar JSON array geçersiz'}, status=400)
            else:
                sifatlar = [s.strip() for s in sifatlar_raw.split(',') if s.strip()]

            user_id = _get_user_id(request)

            # ── run archetype matching ─────────────────────────────────────
            _load_engine()
            try:
                from facesyma_revize.archetype_mapper import pick_archetypes
            except ImportError:
                try:
                    from archetype_mapper import pick_archetypes
                except ImportError:
                    log.error('Cannot import archetype_mapper')
                    return JsonResponse({'detail': 'Archetype module not available'}, status=500)

            try:
                result = pick_archetypes(sifatlar, lang=lang, user_id=user_id)
            except Exception as e:
                log.exception(f'Archetype pick error: {e}')
                return JsonResponse({'detail': 'Archetype matching failed'}, status=500)

            # ── persist to analysis_history (best-effort) ──────────────────
            if user_id:
                try:
                    db = _get_mongo_db()
                    db.get_collection('analysis_history').insert_one({
                        'user_id':    user_id,
                        'mode':       'similarity',
                        'lang':       lang,
                        'sifatlar':   sifatlar,
                        'result':     result,
                        'created_at': time.time(),
                    })
                except Exception as e:
                    log.warning(f'Could not save similarity history: {e}')

            return JsonResponse({'success': True, 'data': result})

        except Exception as e:
            log.exception(f'SimilarityAnalyzeView error: {e}')
            return JsonResponse({'detail': 'Internal server error'}, status=500)
