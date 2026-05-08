"""
checkin/views.py
================
Günlük duygu check-in API.
Koleksiyon: daily_checkins (MongoDB)

Doküman yapısı:
  {
    "user_id": int,
    "date": "2026-05-08",       # YYYY-MM-DD (UTC)
    "mood_score": 1-5,
    "tags": ["stresli", ...],   # opsiyonel etiketler
    "created_at": datetime
  }
"""
import json
import logging
from datetime import datetime, timedelta, timezone

from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

log = logging.getLogger(__name__)

_VALID_SCORES = {1, 2, 3, 4, 5}
_VALID_TAGS   = {'stresli', 'yorgun', 'enerjik', 'sakin', 'mutlu',
                 'stressed', 'tired', 'energetic', 'calm', 'happy'}


def _decode_token(request):
    from auth_api.views import _decode_token as _dt
    return _dt(request)


def _get_col():
    from admin_api.utils.mongo import get_db
    return get_db()['daily_checkins']


def _today_utc() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%d')


# ── POST + GET /api/v1/checkin/ ───────────────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class CheckinView(View):

    def post(self, request):
        """Bugünün check-in'ini kaydet (günde bir kez, upsert)."""
        try:
            payload = _decode_token(request)
        except Exception:
            return JsonResponse({'detail': 'Authentication failed.'}, status=401)
        uid = payload.get('user_id')
        if not uid:
            return JsonResponse({'detail': 'Invalid token.'}, status=401)

        try:
            data = json.loads(request.body or b'{}')
        except Exception:
            return JsonResponse({'detail': 'Invalid JSON.'}, status=400)

        score = data.get('mood_score')
        if score not in _VALID_SCORES:
            return JsonResponse({'detail': 'mood_score must be 1-5.'}, status=400)

        raw_tags = data.get('tags', [])
        tags = [t for t in (raw_tags if isinstance(raw_tags, list) else []) if t in _VALID_TAGS][:3]

        today = _today_utc()
        now   = datetime.now(timezone.utc)

        try:
            col = _get_col()
            col.update_one(
                {'user_id': uid, 'date': today},
                {'$set': {
                    'mood_score': score,
                    'tags':       tags,
                    'created_at': now,
                }, '$setOnInsert': {
                    'user_id': uid,
                    'date':    today,
                }},
                upsert=True,
            )
            return JsonResponse({'success': True, 'date': today, 'mood_score': score, 'tags': tags})
        except Exception as e:
            log.exception(f'Checkin save error: user_id={uid}')
            return JsonResponse({'detail': 'Save failed.'}, status=500)

    def get(self, request):
        """Bugünün check-in durumunu döner (checked_in: bool, mood_score, streak)."""
        try:
            payload = _decode_token(request)
        except Exception:
            return JsonResponse({'detail': 'Authentication failed.'}, status=401)
        uid = payload.get('user_id')
        if not uid:
            return JsonResponse({'detail': 'Invalid token.'}, status=401)

        today = _today_utc()
        try:
            col    = _get_col()
            doc    = col.find_one({'user_id': uid, 'date': today}, {'_id': 0})
            streak = _calc_streak(col, uid, today)
            return JsonResponse({
                'success':     True,
                'checked_in':  doc is not None,
                'mood_score':  doc.get('mood_score') if doc else None,
                'tags':        doc.get('tags', []) if doc else [],
                'streak':      streak,
                'date':        today,
            })
        except Exception:
            log.exception(f'Checkin get error: user_id={uid}')
            return JsonResponse({'detail': 'Internal error.'}, status=500)


# ── GET /api/v1/checkin/history/ ─────────────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class CheckinHistoryView(View):

    def get(self, request):
        """Son N günlük check-in geçmişi."""
        try:
            payload = _decode_token(request)
        except Exception:
            return JsonResponse({'detail': 'Authentication failed.'}, status=401)
        uid = payload.get('user_id')
        if not uid:
            return JsonResponse({'detail': 'Invalid token.'}, status=401)

        try:
            days = min(max(1, int(request.GET.get('days', 30))), 90)
        except (ValueError, TypeError):
            days = 30

        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime('%Y-%m-%d')

        try:
            col    = _get_col()
            docs   = list(col.find(
                {'user_id': uid, 'date': {'$gte': cutoff}},
                {'_id': 0},
                sort=[('date', 1)],
            ))
            today  = _today_utc()
            streak = _calc_streak(col, uid, today)
            # serialize datetimes
            for d in docs:
                if hasattr(d.get('created_at'), 'isoformat'):
                    d['created_at'] = d['created_at'].isoformat()
            return JsonResponse({'success': True, 'history': docs, 'streak': streak})
        except Exception:
            log.exception(f'Checkin history error: user_id={uid}')
            return JsonResponse({'detail': 'Internal error.'}, status=500)


# ── GET /api/v1/checkin/streak/ ──────────────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class CheckinStreakView(View):

    def get(self, request):
        """Mevcut seri uzunluğu."""
        try:
            payload = _decode_token(request)
        except Exception:
            return JsonResponse({'detail': 'Authentication failed.'}, status=401)
        uid = payload.get('user_id')
        if not uid:
            return JsonResponse({'detail': 'Invalid token.'}, status=401)

        today = _today_utc()
        try:
            col    = _get_col()
            streak = _calc_streak(col, uid, today)
            return JsonResponse({'success': True, 'streak': streak})
        except Exception:
            log.exception(f'Checkin streak error: user_id={uid}')
            return JsonResponse({'detail': 'Internal error.'}, status=500)


# ── Streak hesaplama ──────────────────────────────────────────────────────────
def _calc_streak(col, user_id: int, today: str) -> int:
    """Consecutive daily check-in streak ending today (or yesterday)."""
    docs = list(col.find(
        {'user_id': user_id},
        {'date': 1, '_id': 0},
        sort=[('date', -1)],
    ).limit(100))

    dates = {d['date'] for d in docs if d.get('date')}
    if not dates:
        return 0

    # Start from today; if no today check-in, start from yesterday
    check = today if today in dates else (
        (datetime.strptime(today, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
    )
    if check not in dates:
        return 0

    streak = 0
    cursor = datetime.strptime(check, '%Y-%m-%d')
    while cursor.strftime('%Y-%m-%d') in dates:
        streak += 1
        cursor -= timedelta(days=1)
    return streak
