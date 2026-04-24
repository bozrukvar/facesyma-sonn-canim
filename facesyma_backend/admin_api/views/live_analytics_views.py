"""
admin_api/views/live_analytics_views.py
========================================
Real-time Live Analytics Dashboard — 30 second polling.

Features:
  - KPI cards (active users, registrations, analyses, MRR)
  - Error rate tracking
  - Hourly trend chart
  - Activity feed
  - System health status
"""

import json
import logging
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from admin_api.utils.auth import _require_admin
from admin_api.utils.mongo import (
    _get_db, get_users_col, get_history_col
)

log = logging.getLogger(__name__)

_PROJ_HISTORY_FEED = {'_id': 0, 'user_id': 1, 'created_at': 1, 'mode': 1}
_PROJ_USERS_FEED   = {'_id': 0, 'id': 1, 'date_joined': 1, 'plan': 1}


@method_decorator(csrf_exempt, name='dispatch')
class LiveStatsView(View):
    """
    GET /api/v1/admin/live/stats/

    Real-time snapshot for 30s polling dashboard.
    Returns KPIs, error rate, hourly chart, activity feed, system health.
    """

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            users_col = get_users_col()
            history_col = get_history_col()
            db = _get_db()

            now = datetime.utcnow()
            now_ts = now.timestamp()
            today_start = datetime(now.year, now.month, now.day)
            today_start_iso = today_start.isoformat()
            today_start_ts = today_start.timestamp()
            one_hour_ago_ts = (now - timedelta(hours=1)).timestamp()

            # ── KPIs — single $facet per collection ───────────────────────────
            _u = next(users_col.aggregate([{'$facet': {
                'active5m':     [{'$match': {'last_active': {'$gte': now_ts - 300}}},            {'$count': 'n'}],
                'reg_today':    [{'$match': {'date_joined': {'$gte': today_start_iso}}},          {'$count': 'n'}],
                'premium':      [{'$match': {'plan': 'premium'}},                                 {'$count': 'n'}],
                'web_today':    [{'$match': {'app_source': 'web', 'date_joined': {'$gte': today_start_iso}}}, {'$count': 'n'}],
                'mobile_today': [{'$match': {'$or': [{'app_source': 'mobile'}, {'app_source': {'$exists': False}}],
                                             'date_joined': {'$gte': today_start_iso}}},          {'$count': 'n'}],
            }}]), {})
            _luget = _u.get
            active_users_5min       = (_luget('active5m',     [{}])[0] or {}).get('n', 0)
            new_registrations_today = (_luget('reg_today',    [{}])[0] or {}).get('n', 0)
            premium_users           = (_luget('premium',      [{}])[0] or {}).get('n', 0)
            web_users_today         = (_luget('web_today',    [{}])[0] or {}).get('n', 0)
            mobile_users_today      = (_luget('mobile_today', [{}])[0] or {}).get('n', 0)
            mrr = premium_users * 9.99

            _h = next(history_col.aggregate([{'$facet': {
                'analyses_today':   [{'$match': {'created_at': {'$gte': today_start_ts}}},        {'$count': 'n'}],
                'web_analyses':     [{'$match': {'app_source': 'web', 'created_at': {'$gte': today_start_ts}}}, {'$count': 'n'}],
                'mobile_analyses':  [{'$match': {'app_source': {'$ne': 'web'}, 'created_at': {'$gte': today_start_ts}}}, {'$count': 'n'}],
            }}]), {})
            _hget = _h.get
            analyses_today       = (_hget('analyses_today',  [{}])[0] or {}).get('n', 0)
            web_analyses_today   = (_hget('web_analyses',    [{}])[0] or {}).get('n', 0)
            mobile_analyses_today= (_hget('mobile_analyses', [{}])[0] or {}).get('n', 0)

            kpis = {
                'active_users_5min': active_users_5min,
                'new_registrations_today': new_registrations_today,
                'analyses_today': analyses_today,
                'mrr': round(mrr, 2),
            }

            # App sources breakdown
            app_sources = {
                'web_users_today': web_users_today,
                'mobile_users_today': mobile_users_today,
                'web_analyses_today': web_analyses_today,
                'mobile_analyses_today': mobile_analyses_today,
            }

            # ── Error Rate (last 1 hour) ──────────────────────────────────────
            # Uses admin_activity_log if it exists (Feature 2). Otherwise returns 0.
            error_rate = self._get_error_rate(db, one_hour_ago_ts)

            # ── Hourly Chart (24 hours) ────────────────────────────────────────
            hourly_chart = self._get_hourly_chart(history_col, users_col, today_start_ts)

            # ── Activity Feed (last 10 events) ──────────────────────────────────
            activity_feed = self._get_activity_feed(history_col, users_col)

            # ── System Health ──────────────────────────────────────────────────
            system_health = self._get_system_health(db)

            return JsonResponse({
                'kpis': kpis,
                'app_sources': app_sources,
                'error_rate_1h': error_rate,
                'hourly_chart': hourly_chart,
                'activity_feed': activity_feed,
                'system_health': system_health,
                'generated_at': now.isoformat(),
            })

        except Exception as e:
            log.exception(f'Live stats error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)

    def _get_error_rate(self, db, one_hour_ago_ts):
        """Calculate error rate from admin_activity_log (1 hour)."""
        try:
            audit_col = db['admin_activity_log']
            one_hour_ago_dt = datetime.utcfromtimestamp(one_hour_ago_ts)

            _er = next(audit_col.aggregate([
                {'$match': {'timestamp': {'$gte': one_hour_ago_dt}}},
                {'$facet': {
                    'total':  [{'$count': 'n'}],
                    'errors': [
                        {'$match': {'action': {'$regex': 'delete|error', '$options': 'i'}}},
                        {'$count': 'n'},
                    ],
                }}
            ]), {})
            _erget = _er.get
            total_requests = (_erget('total',  [{}])[0] or {}).get('n', 0)
            error_requests = (_erget('errors', [{}])[0] or {}).get('n', 0)
            rate_pct = round((error_requests / total_requests) * 100, 2) if total_requests else 0.0

            return {'total_requests': total_requests, 'errors': error_requests, 'rate_pct': rate_pct}
        except Exception:
            return {'total_requests': 0, 'errors': 0, 'rate_pct': 0.0}

    def _get_hourly_chart(self, history_col, users_col, today_start_ts):
        """Return 24 hours of analyses and registrations by hour."""
        now = datetime.utcnow()
        today_start_dt = datetime(now.year, now.month, now.day)
        today_end_ts = today_start_ts + 86400

        # Single aggregation per collection for all 24 hours
        analyses_agg = {
            _id: doc['count']
            for doc in history_col.aggregate([
                {'$match': {'created_at': {'$gte': today_start_ts, '$lt': today_end_ts}}},
                {'$group': {'_id': {'$floor': {'$divide': [{'$subtract': ['$created_at', today_start_ts]}, 3600]}},
                            'count': {'$sum': 1}}},
            ])
            if isinstance((_id := doc['_id']), (int, float))
        }

        reg_agg = {
            doc['_id']: doc['count']
            for doc in users_col.aggregate([
                {'$match': {'date_joined': {
                    '$gte': today_start_dt.isoformat(),
                    '$lt': (today_start_dt + timedelta(hours=24)).isoformat()
                }}},
                {'$group': {'_id': {'$hour': {'$dateFromString': {'dateString': '$date_joined'}}},
                            'count': {'$sum': 1}}},
            ])
        }

        _aaget = analyses_agg.get
        _raget = reg_agg.get
        return [
            {'hour': h, 'analyses': _aaget(h, 0), 'registrations': _raget(h, 0)}
            for h in range(24)
        ]

    def _get_activity_feed(self, history_col, users_col):
        """Return last 10 activities (analyses + registrations)."""
        feed = []
        _fappend = feed.append

        _one_day_ago = datetime.utcnow() - timedelta(days=1)
        one_day_ago_ts = _one_day_ago.timestamp()
        one_day_ago_iso = _one_day_ago.isoformat()

        # Last 10 analyses (created_at stored as Unix timestamp float)
        for doc in history_col.find(
            {'created_at': {'$gte': one_day_ago_ts}},
            _PROJ_HISTORY_FEED,
            sort=[('created_at', -1)],
            limit=10
        ):
            try:
                ts = doc['created_at']
                time_iso = datetime.utcfromtimestamp(float(ts)).isoformat() if ts else None
            except (TypeError, ValueError, OSError):
                time_iso = None
            _dget = doc.get
            _fappend({
                'type': 'analysis',
                'user_id': _dget('user_id'),
                'time': time_iso,
                'detail': f"Mode: {_dget('mode', 'unknown')}",
            })

        # Last 5 registrations (date_joined stored as ISO string)
        for doc in users_col.find(
            {'date_joined': {'$gte': one_day_ago_iso}},
            _PROJ_USERS_FEED,
            sort=[('date_joined', -1)],
            limit=5
        ):
            _dget = doc.get
            _fappend({
                'type': 'registration',
                'user_id': doc['id'],
                'time': _dget('date_joined'),
                'detail': f"Plan: {_dget('plan', 'free')}",
            })

        # Sort by time descending (both are ISO strings or None), return first 10
        feed.sort(key=lambda x: x['time'] or '', reverse=True)
        return feed[:10]

    def _get_system_health(self, db):
        """Check MongoDB and scheduler health."""
        health = {}

        # MongoDB status
        try:
            db.command('ping')
            health['mongodb'] = 'ok'
        except Exception:
            health['mongodb'] = 'error'

        # Scheduler status (if scheduler is running)
        try:
            from admin_api.scheduler import get_scheduler_status
            status = get_scheduler_status()
            _stget = status.get
            health['scheduler_running'] = _stget('running', False)
            health['scheduler_jobs'] = len(_stget('jobs', []))
        except Exception:
            health['scheduler_running'] = False
            health['scheduler_jobs'] = 0

        return health
