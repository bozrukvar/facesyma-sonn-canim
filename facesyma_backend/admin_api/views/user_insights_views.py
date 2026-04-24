"""
admin_api/views/user_insights_views.py
=====================================
Kullanıcı İçgörüleri — Tarih, Zaman, Modül Analizi

Detaylı kullanıcı analitikleri:
- Kayıt tarihi zaman çizelgesi
- Kayıt örüntüleri (saat, gün, ay)
- Modül/analiz modu kullanım analizi
"""

import logging
import time
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from admin_api.utils.auth import _require_admin
from admin_api.utils.mongo import get_users_col, get_history_col

_DAY_NAMES = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']
_MONTH_NAMES = ['', 'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
                'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']

log = logging.getLogger(__name__)

_VALID_INSIGHT_PERIODS = frozenset({'day', 'week', 'month'})


@method_decorator(csrf_exempt, name='dispatch')
class UserRegistrationTimelineView(View):
    """Kullanıcı kayıt zaman çizelgesi — günlük/haftalık/aylık trend"""

    def get(self, request):
        try:
            _require_admin(request)
        except (ValueError, PermissionError):
            return JsonResponse({'detail': 'Unauthorized'}, status=403)

        _qget = request.GET.get
        period = _qget('period', 'day')
        try:
            days = min(max(1, int(_qget('days', 30))), 365)
        except (ValueError, TypeError):
            days = 30

        if period not in _VALID_INSIGHT_PERIODS:
            period = 'day'

        user_col = get_users_col()
        now = datetime.utcnow()

        # Single aggregation: group by date prefix, then roll up in Python
        window_start_iso = (now - timedelta(days=days)).isoformat()
        counts_by_date = {
            doc['_id']: doc['count']
            for doc in user_col.aggregate([
                {'$match': {'date_joined': {'$gte': window_start_iso}}},
                {'$group': {'_id': {'$substr': ['$date_joined', 0, 10]}, 'count': {'$sum': 1}}}
            ])
        }

        timeline_data = []
        _tdappend = timeline_data.append
        cumulative = 0

        if period == 'day':
            for day_offset in range(days - 1, -1, -1):
                iso_str = (now - timedelta(days=day_offset)).date().isoformat()
                count = counts_by_date.get(iso_str, 0)
                cumulative += count
                _tdappend({'date': iso_str, 'new_users': count, 'cumulative_total': cumulative})

        elif period == 'week':
            for week_offset in range(days // 7 - 1, -1, -1):
                week_start = (now - timedelta(weeks=week_offset + 1, days=now.weekday())).date()
                week_end = week_start + timedelta(days=7)
                count = sum(counts_by_date.get((week_start + timedelta(days=d)).isoformat(), 0) for d in range(7))
                cumulative += count
                _tdappend({
                    'date': f"{week_start.isoformat()} to {(week_end - timedelta(days=1)).isoformat()}",
                    'new_users': count,
                    'cumulative_total': cumulative
                })

        elif period == 'month':
            for month_offset in range(days // 30, -1, -1):
                month_date = now - timedelta(days=month_offset * 30)
                month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0).date()
                month_str = month_start.strftime('%Y-%m')
                count = sum(v for k, v in counts_by_date.items() if k.startswith(month_str))
                cumulative += count
                _tdappend({'date': month_str, 'new_users': count, 'cumulative_total': cumulative})

        return JsonResponse({
            'success': True,
            'data': {
                'period': period,
                'days_analyzed': days,
                'timeline': timeline_data,
                'total_users': cumulative
            }
        })


@method_decorator(csrf_exempt, name='dispatch')
class UserRegistrationPatternsView(View):
    """Kullanıcı kayıt örüntüleri — saat, gün, ay dağılımı"""

    def get(self, request):
        try:
            _require_admin(request)
        except (ValueError, PermissionError):
            return JsonResponse({'detail': 'Unauthorized'}, status=403)

        user_col = get_users_col()

        # Single $facet aggregation — no unbounded find()
        facet_result = list(user_col.aggregate([
            {'$facet': {
                'by_hour_raw': [
                    {'$group': {'_id': {'$toInt': {'$substr': ['$date_joined', 11, 2]}}, 'count': {'$sum': 1}}}
                ],
                'by_month_raw': [
                    {'$group': {'_id': {'$toInt': {'$substr': ['$date_joined', 5, 2]}}, 'count': {'$sum': 1}}}
                ],
                'by_dow_raw': [
                    {'$group': {
                        '_id': {'$dayOfWeek': {
                            '$dateFromString': {
                                'dateString': {'$substr': ['$date_joined', 0, 19]},
                                'onError': None, 'onNull': None
                            }
                        }},
                        'count': {'$sum': 1}
                    }}
                ],
                'total': [{'$count': 'n'}]
            }}
        ]))[0]

        _frget = facet_result.get
        by_hour = {i: 0 for i in range(24)}
        for item in _frget('by_hour_raw', []):
            _iid = item['_id']
            if _iid is not None and 0 <= _iid <= 23:
                by_hour[_iid] = item['count']

        by_month = {i: 0 for i in range(1, 13)}
        for item in _frget('by_month_raw', []):
            _iid = item['_id']
            if _iid is not None and 1 <= _iid <= 12:
                by_month[_iid] = item['count']

        # MongoDB $dayOfWeek: 1=Sun,2=Mon,...,7=Sat → Python weekday: 0=Mon,...,6=Sun
        by_day_of_week = {i: 0 for i in range(7)}
        for item in _frget('by_dow_raw', []):
            _iid = item['_id']
            if _iid is not None:
                py_dow = (_iid - 2) % 7
                by_day_of_week[py_dow] = item['count']

        _total_facet = _frget('total')
        total_analyzed = _total_facet[0].get('n', 0) if _total_facet else 0

        return JsonResponse({
            'success': True,
            'data': {
                'by_hour': by_hour,
                'by_day_of_week': by_day_of_week,
                'by_month': by_month,
                'total_analyzed': total_analyzed,
                'day_names': _DAY_NAMES,
                'month_names': _MONTH_NAMES
            }
        })


@method_decorator(csrf_exempt, name='dispatch')
class UserModuleUsageView(View):
    """Modül/analiz modu kullanım analizi"""

    def get(self, request):
        try:
            _require_admin(request)
        except (ValueError, PermissionError):
            return JsonResponse({'detail': 'Unauthorized'}, status=403)

        history_col = get_history_col()

        now_ts = time.time()
        seven_days_ago_ts = now_ts - 7 * 86400

        facet_result = next(history_col.aggregate([{'$facet': {
            'by_mode':   [{'$group': {'_id': '$mode',    'count': {'$sum': 1}}}],
            'top_users': [{'$group': {'_id': '$user_id', 'count': {'$sum': 1}}}, {'$sort': {'count': -1}}, {'$limit': 10}],
            'total':     [{'$count': 'n'}],
            'trend_7d':  [
                {'$match': {'created_at': {'$gte': seven_days_ago_ts}}},
                {'$group': {'_id': {'$dateToString': {'format': '%Y-%m-%d', 'date': {'$toDate': {'$multiply': [{'$toLong': '$created_at'}, 1000]}}}}, 'count': {'$sum': 1}}},
            ],
        }}]), {})

        _frget2 = facet_result.get
        by_mode        = {(doc['_id'] or 'unknown'): doc['count'] for doc in _frget2('by_mode', [])}
        top_users_list = [{'user_id': doc['_id'], 'analysis_count': doc['count']} for doc in _frget2('top_users', [])]
        total_analyses = (_frget2('total', [{}])[0] or {}).get('n', 0)
        trend_by_date  = {doc['_id']: doc['count'] for doc in _frget2('trend_7d', [])}

        mode_trend_7d = {}
        for day_offset in range(6, -1, -1):
            date_str = datetime.utcfromtimestamp(now_ts - day_offset * 86400).date().isoformat()
            mode_trend_7d[date_str] = trend_by_date.get(date_str, 0)

        return JsonResponse({
            'success': True,
            'data': {
                'by_mode': by_mode,
                'total_analyses': total_analyses,
                'top_users': top_users_list,
                'mode_trend_7d': mode_trend_7d
            }
        })
