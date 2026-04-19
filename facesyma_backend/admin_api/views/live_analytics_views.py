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

            # ── KPIs ───────────────────────────────────────────────────────────

            # Active users (last 5 minutes)
            active_users_5min = users_col.count_documents({
                'last_active': {'$gte': now_ts - 300}
            })

            # New registrations today
            new_registrations_today = users_col.count_documents({
                'date_joined': {'$gte': today_start_iso}
            })

            # Analyses today
            analyses_today = history_col.count_documents({
                'created_at': {'$gte': today_start_ts}
            })

            # MRR (Monthly Recurring Revenue) — premium users * 9.99
            premium_users = users_col.count_documents({'plan': 'premium'})
            mrr = premium_users * 9.99

            # App source breakdown
            web_users_today = users_col.count_documents({
                'app_source': 'web',
                'date_joined': {'$gte': today_start_iso}
            })
            mobile_users_today = users_col.count_documents({
                '$or': [{'app_source': 'mobile'}, {'app_source': {'$exists': False}}],
                'date_joined': {'$gte': today_start_iso}
            })
            web_analyses_today = history_col.count_documents({
                'app_source': 'web',
                'created_at': {'$gte': today_start_ts}
            })
            mobile_analyses_today = history_col.count_documents({
                '$or': [{'app_source': {'$exists': False}}, {'app_source': {'$ne': 'web'}}],
                'created_at': {'$gte': today_start_ts}
            })

            kpis = {
                'active_users_5min': active_users_5min,
                'new_registrations_today': new_registrations_today,
                'analyses_today': analyses_today,
                'mrr': round(mrr, 2),
            }

            # App sources breakdown
            app_sources = {  # YENİ
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
                'app_sources': app_sources,  # YENİ
                'error_rate_1h': error_rate,
                'hourly_chart': hourly_chart,
                'activity_feed': activity_feed,
                'system_health': system_health,
                'generated_at': now.isoformat(),
            })

        except Exception as e:
            log.exception(f'Live stats error: {e}')
            return JsonResponse({'detail': str(e)}, status=500)

    def _get_error_rate(self, db, one_hour_ago_ts):
        """Calculate error rate from admin_activity_log (1 hour)."""
        try:
            audit_col = db['admin_activity_log']

            # Assume errors are logged with 'error' or 'delete' in action
            total_requests = audit_col.count_documents({
                'timestamp': {'$gte': datetime.utcfromtimestamp(one_hour_ago_ts).isoformat()}
            })

            error_requests = audit_col.count_documents({
                'timestamp': {'$gte': datetime.utcfromtimestamp(one_hour_ago_ts).isoformat()},
                'action': {'$regex': 'delete|error', '$options': 'i'}
            })

            if total_requests == 0:
                rate_pct = 0.0
            else:
                rate_pct = round((error_requests / total_requests) * 100, 2)

            return {
                'total_requests': total_requests,
                'errors': error_requests,
                'rate_pct': rate_pct,
            }
        except Exception:
            # Collection doesn't exist yet (Feature 2 not implemented)
            return {'total_requests': 0, 'errors': 0, 'rate_pct': 0.0}

    def _get_hourly_chart(self, history_col, users_col, today_start_ts):
        """Return 24 hours of analyses and registrations by hour."""
        chart = []
        now = datetime.utcnow()

        for hour in range(24):
            hour_start = (datetime(now.year, now.month, now.day) + timedelta(hours=hour)).timestamp()
            hour_end = hour_start + 3600

            analyses_count = history_col.count_documents({
                'created_at': {'$gte': hour_start, '$lt': hour_end}
            })

            registrations_count = users_col.count_documents({
                'date_joined': {
                    '$gte': datetime.utcfromtimestamp(hour_start).isoformat(),
                    '$lt': datetime.utcfromtimestamp(hour_end).isoformat(),
                }
            })

            chart.append({
                'hour': hour,
                'analyses': analyses_count,
                'registrations': registrations_count,
            })

        return chart

    def _get_activity_feed(self, history_col, users_col):
        """Return last 10 activities (analyses + registrations)."""
        feed = []

        # Last 10 analyses
        for doc in history_col.find(
            {'created_at': {'$gte': (datetime.utcnow() - timedelta(days=1)).timestamp()}},
            sort=[('created_at', -1)],
            limit=10
        ):
            feed.append({
                'type': 'analysis',
                'user_id': doc.get('user_id'),
                'time': datetime.utcfromtimestamp(doc['created_at']).isoformat(),
                'detail': f"Mode: {doc.get('mode', 'unknown')}",
            })

        # Last 5 registrations
        for doc in users_col.find(
            {'date_joined': {'$gte': (datetime.utcnow() - timedelta(days=1)).isoformat()}},
            sort=[('date_joined', -1)],
            limit=5
        ):
            feed.append({
                'type': 'registration',
                'user_id': doc['id'],
                'time': doc.get('date_joined'),
                'detail': f"Plan: {doc.get('plan', 'free')}",
            })

        # Sort by time descending, return first 10
        feed.sort(key=lambda x: x['time'], reverse=True)
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
            health['scheduler_running'] = status.get('running', False)
            health['scheduler_jobs'] = len(status.get('jobs', []))
        except Exception:
            health['scheduler_running'] = False
            health['scheduler_jobs'] = 0

        return health
