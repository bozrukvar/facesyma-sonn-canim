"""
admin_api/views/user_insights_views.py
=====================================
Kullanıcı İçgörüleri — Tarih, Zaman, Modül Analizi

Detaylı kullanıcı analitikleri:
- Kayıt tarihi zaman çizelgesi
- Kayıt örüntüleri (saat, gün, ay)
- Modül/analiz modu kullanım analizi
"""

import json
import logging
import time
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from admin_api.utils.auth import _require_admin
from admin_api.utils.mongo import get_users_col, get_history_col

log = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class UserRegistrationTimelineView(View):
    """Kullanıcı kayıt zaman çizelgesi — günlük/haftalık/aylık trend"""

    def get(self, request):
        try:
            _require_admin(request)
        except (ValueError, PermissionError):
            return JsonResponse({'detail': 'Unauthorized'}, status=403)

        period = request.GET.get('period', 'day')  # day, week, month
        days = int(request.GET.get('days', 30))

        if period not in ['day', 'week', 'month']:
            period = 'day'

        user_col = get_users_col()
        now = datetime.utcnow()

        timeline_data = []
        cumulative = 0

        if period == 'day':
            # Günlük — son N gün
            for day_offset in range(days - 1, -1, -1):
                date = (now - timedelta(days=day_offset)).date()
                iso_str = date.isoformat()

                # Bu gün kayıt olan kullanıcı sayısı
                # date_joined ISO string olduğu için string karşılaştırması kullan
                count = user_col.count_documents({
                    'date_joined': {
                        '$gte': iso_str + 'T00:00:00',
                        '$lt': iso_str + 'T23:59:59'
                    }
                })

                cumulative += count
                timeline_data.append({
                    'date': iso_str,
                    'new_users': count,
                    'cumulative_total': cumulative
                })

        elif period == 'week':
            # Haftalık — son N/7 hafta
            for week_offset in range(days // 7 - 1, -1, -1):
                week_start = now - timedelta(weeks=week_offset + 1, days=now.weekday())
                week_end = week_start + timedelta(days=7)

                week_start_str = week_start.date().isoformat()
                week_end_str = (week_end.date() - timedelta(days=1)).isoformat()

                count = user_col.count_documents({
                    'date_joined': {
                        '$gte': week_start_str + 'T00:00:00',
                        '$lt': week_end_str + 'T23:59:59'
                    }
                })

                cumulative += count
                timeline_data.append({
                    'date': f"{week_start_str} to {week_end_str}",
                    'new_users': count,
                    'cumulative_total': cumulative
                })

        elif period == 'month':
            # Aylık — son N ay
            for month_offset in range(days // 30, -1, -1):
                month_date = now - timedelta(days=month_offset * 30)
                # Ay'ın başına git
                month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

                if month_offset == 0:
                    # Bu ay
                    month_end = now
                else:
                    # Sonraki ayın başı
                    if month_date.month == 12:
                        month_end = month_date.replace(year=month_date.year + 1, month=1, day=1)
                    else:
                        month_end = month_date.replace(month=month_date.month + 1, day=1)

                month_str = month_start.strftime('%Y-%m')
                month_start_str = month_start.date().isoformat()
                month_end_str = (month_end.date() - timedelta(days=1)).isoformat()

                count = user_col.count_documents({
                    'date_joined': {
                        '$gte': month_start_str + 'T00:00:00',
                        '$lt': month_end_str + 'T23:59:59'
                    }
                })

                cumulative += count
                timeline_data.append({
                    'date': month_str,
                    'new_users': count,
                    'cumulative_total': cumulative
                })

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
        users = list(user_col.find({}, {'date_joined': 1}))

        # Saat, gün, ay dağılımı
        by_hour = {}
        by_day_of_week = {}
        by_month = {}

        for user in users:
            date_str = user.get('date_joined', '')
            if not date_str:
                continue

            try:
                # ISO string'den datetime'e çevir
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))

                # Saat (UTC)
                hour = dt.hour
                by_hour[hour] = by_hour.get(hour, 0) + 1

                # Haftanın günü (0=Pazartesi, 6=Pazar)
                dow = dt.weekday()
                by_day_of_week[dow] = by_day_of_week.get(dow, 0) + 1

                # Ay (1=Ocak, 12=Aralık)
                month = dt.month
                by_month[month] = by_month.get(month, 0) + 1

            except Exception as e:
                log.warning(f"Error parsing date_joined: {date_str}, {e}")
                continue

        # Eksik saatleri doldur (0-23)
        by_hour_full = {i: by_hour.get(i, 0) for i in range(24)}

        # Eksik günleri doldur (0-6)
        by_day_of_week_full = {i: by_day_of_week.get(i, 0) for i in range(7)}

        # Eksik ayları doldur (1-12)
        by_month_full = {i: by_month.get(i, 0) for i in range(1, 13)}

        return JsonResponse({
            'success': True,
            'data': {
                'by_hour': by_hour_full,
                'by_day_of_week': by_day_of_week_full,
                'by_month': by_month_full,
                'total_analyzed': len(users),
                'day_names': ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar'],
                'month_names': ['', 'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
                               'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
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

        # Mod dağılımı
        by_mode = {}
        total_analyses = 0

        history_docs = list(history_col.find({}, {'mode': 1, 'user_id': 1, 'created_at': 1}))

        for doc in history_docs:
            mode = doc.get('mode', 'unknown')
            by_mode[mode] = by_mode.get(mode, 0) + 1
            total_analyses += 1

        # En aktif kullanıcılar (analiz sayısına göre)
        user_analysis_count = {}
        for doc in history_docs:
            user_id = doc.get('user_id')
            if user_id:
                user_analysis_count[user_id] = user_analysis_count.get(user_id, 0) + 1

        # Top 10
        top_users = sorted(user_analysis_count.items(), key=lambda x: x[1], reverse=True)[:10]
        top_users_list = [
            {'user_id': uid, 'analysis_count': count}
            for uid, count in top_users
        ]

        # Son 7 gün trend
        now_ts = time.time()
        seven_days_ago_ts = now_ts - (7 * 24 * 3600)

        mode_trend_7d = {}
        for day_offset in range(6, -1, -1):
            date_ts = now_ts - (day_offset * 24 * 3600)
            next_date_ts = date_ts + (24 * 3600)

            date_obj = datetime.utcfromtimestamp(date_ts)
            date_str = date_obj.date().isoformat()

            day_count = history_col.count_documents({
                'created_at': {
                    '$gte': date_ts,
                    '$lt': next_date_ts
                }
            })

            mode_trend_7d[date_str] = day_count

        return JsonResponse({
            'success': True,
            'data': {
                'by_mode': by_mode,
                'total_analyses': total_analyses,
                'top_users': top_users_list,
                'mode_trend_7d': mode_trend_7d
            }
        })
