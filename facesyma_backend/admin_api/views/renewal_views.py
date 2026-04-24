"""
admin_api/views/renewal_views.py
================================
Subscription renewal automation management

Features:
  - View scheduled job status
  - Manually trigger renewal check
  - View renewal events (expirations, reminders)
"""

import json
import logging
from datetime import datetime, timedelta
import time
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from admin_api.utils.auth import _require_admin
from admin_api.utils.mongo import _get_db

log = logging.getLogger(__name__)

_VALID_RENEWAL_EVENT_TYPES = frozenset({'expired', 'reminder', 'renewed', 'canceled', 'upgraded', 'downgraded'})
_PROJ_SUB_EXPIRY   = {'_id': 0, 'user_id': 1, 'expires_date': 1, 'renews_at': 1}
_PROJ_RENEWAL_TYPE = {'_id': 0, 'user_id': 1, 'type': 1}


@method_decorator(csrf_exempt, name='dispatch')
class RenewalJobStatusView(View):
    """Get renewal scheduler status and upcoming expirations"""

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            from admin_api.scheduler import get_scheduler_status

            db = _get_db()
            subs_col = db["user_subscriptions"]
            events_col = db["subscription_events"]
            notif_col = db["subscription_notifications"]

            now = datetime.utcnow()
            now_iso = now.isoformat()
            now_ts = time.time()

            # Scheduler status
            scheduler_status = get_scheduler_status()

            # Count users expiring today and in 7 days — single $facet
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)
            future_7d = now + timedelta(days=7)

            _rc = next(subs_col.aggregate([{'$facet': {
                'today': [{'$match': {'$or': [
                    {'expires_date': {'$gte': today_start.isoformat(), '$lt': today_end.isoformat()}, 'plan': 'premium'},
                    {'renews_at': {'$gte': now_ts, '$lt': now_ts + 86400}, 'tier': 'premium'},
                ]}}, {'$count': 'n'}],
                'week': [{'$match': {'$or': [
                    {'expires_date': {'$gte': now_iso, '$lt': future_7d.isoformat()}, 'plan': 'premium'},
                    {'renews_at': {'$gte': now_ts, '$lt': now_ts + (7 * 86400)}, 'tier': 'premium'},
                ]}}, {'$count': 'n'}],
            }}]), {})
            _rcget = _rc.get
            expiring_today = (_rcget('today', [{}])[0] or {}).get('n', 0)
            expiring_7d    = (_rcget('week',  [{}])[0] or {}).get('n', 0)

            # Get users expiring soon (max 20)
            expiring_soon_users = []
            future_30d = now + timedelta(days=30)

            users = list(subs_col.find({
                "$or": [
                    {"expires_date": {"$gte": now_iso, "$lt": future_30d.isoformat()}, "plan": "premium"},
                    {"renews_at": {"$gte": now_ts, "$lt": now_ts + (30*86400)}, "tier": "premium"}
                ]
            }, _PROJ_SUB_EXPIRY).sort("expires_date", 1).limit(20))

            for sub in users:
                _sget = sub.get
                user_id = _sget("user_id")
                expires_date = _sget("expires_date")
                renews_at = _sget("renews_at")

                if expires_date:
                    try:
                        exp_dt = datetime.fromisoformat(expires_date.replace("Z", "+00:00"))
                        days_left = (exp_dt - now).days
                    except Exception:
                        days_left = 0
                elif renews_at:
                    days_left = int((renews_at - now_ts) / 86400)
                else:
                    days_left = 0

                expiring_soon_users.append({
                    "user_id": user_id,
                    "expires_date": expires_date or (datetime.fromtimestamp(renews_at).isoformat() if renews_at else ""),
                    "days_left": days_left
                })

            # Recent events (last 10)
            recent_events = list(events_col.find({}).sort("_id", -1).limit(10))
            for event in recent_events:
                _oid = event["_id"]
                event["_id"] = str(_oid)

            return JsonResponse({
                'scheduler': scheduler_status,
                'metrics': {
                    'expiring_today': expiring_today,
                    'expiring_7d': expiring_7d,
                    'expiring_30d': len(expiring_soon_users)
                },
                'expiring_soon': expiring_soon_users,
                'recent_events': recent_events
            })

        except Exception as e:
            log.exception(f'Renewal status error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ManualRenewalTriggerView(View):
    """Manually trigger subscription expiry check"""

    def post(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            from admin_api.scheduler import _job_check_expired_subscriptions

            # Manually trigger the job
            _job_check_expired_subscriptions()

            # Count events from last few seconds
            db = _get_db()
            events_col = db["subscription_events"]
            _cutoff = (datetime.utcnow() - timedelta(seconds=5)).isoformat()
            _q = {"event_at": {"$gte": _cutoff}}

            expired_count = events_col.count_documents(_q)
            recent_events = list(events_col.find(_q, _PROJ_RENEWAL_TYPE, limit=10))

            return JsonResponse({
                'success': True,
                'message': f'Renewal check completed. {expired_count} subscriptions downgraded.',
                'expired_count': expired_count,
                'events': [{'user_id': (_eg := e.get)('user_id'), 'type': _eg('type')} for e in recent_events]
            })

        except Exception as e:
            log.exception(f'Manual renewal trigger error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class RenewalEventsView(View):
    """Get paginated renewal events (expirations, reminders)"""

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            _qget = request.GET.get
            try:
                page = max(1, int(_qget('page', 1)))
                limit = min(max(1, int(_qget('limit', 20))), 100)
            except (ValueError, TypeError):
                page, limit = 1, 20

            event_type = _qget('type', '')
            if event_type not in _VALID_RENEWAL_EVENT_TYPES:
                event_type = ''

            db = _get_db()
            events_col = db["subscription_events"]

            # Build query
            query = {}
            if event_type:
                query['type'] = event_type

            # Total count
            total = events_col.count_documents(query)

            # Paginate
            skip = (page - 1) * limit
            events = list(
                events_col.find(query)
                .sort([('_id', -1)])
                .skip(skip)
                .limit(limit)
            )

            # Format response
            for event in events:
                _oid = event['_id']
                event['_id'] = str(_oid)

            return JsonResponse({
                'events': events,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total,
                    'pages': (total + limit - 1) // limit
                }
            })

        except Exception as e:
            log.exception(f'Renewal events error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class SubscriptionNotificationsView(View):
    """Get paginated renewal reminder notifications"""

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            _qget = request.GET.get
            try:
                page = max(1, int(_qget('page', 1)))
                limit = min(max(1, int(_qget('limit', 20))), 100)
            except (ValueError, TypeError):
                page, limit = 1, 20

            db = _get_db()
            notif_col = db["subscription_notifications"]

            # Total count
            total = notif_col.estimated_document_count()

            # Paginate
            skip = (page - 1) * limit
            notifications = list(
                notif_col.find({})
                .sort([('created_at', -1)])
                .skip(skip)
                .limit(limit)
            )

            # Format response
            for notif in notifications:
                _oid = notif['_id']
                notif['_id'] = str(_oid)

            return JsonResponse({
                'notifications': notifications,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total,
                    'pages': (total + limit - 1) // limit
                }
            })

        except Exception as e:
            log.exception(f'Notifications error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)
