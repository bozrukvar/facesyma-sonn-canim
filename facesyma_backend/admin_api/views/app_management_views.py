"""
admin_api/views/app_management_views.py
=======================================
Multi-app management admin endpoints.
Manages app status, configs, and generates per-app statistics.
"""

import json
import logging
import re as _re
from datetime import datetime, timedelta

_RE_FLAG_KEY = _re.compile(r'^[a-z_][a-z0-9_]{0,49}$')
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from admin_api.utils.auth import _require_admin
from admin_api.utils.mongo import (
    get_app_registry_col, get_users_col, get_history_col
)
from admin_api.utils.audit import log_admin_action, extract_ip

log = logging.getLogger(__name__)


def _json(request):
    """Parse request body JSON"""
    try:
        return json.loads(request.body)
    except Exception:
        return {}


def _get_source_query(app_id: str):
    """
    Build MongoDB query for a specific app_source.
    Mobile is special: includes docs with app_source='mobile' OR missing app_source field (backward compat).
    """
    if app_id == 'mobile':
        return {
            '$or': [
                {'app_source': 'mobile'},
                {'app_source': {'$exists': False}}  # Backward compat: old users without field
            ]
        }
    else:
        return {'app_source': app_id}


# ═════════════════════════════════════════════════════════════════════════════════
# ── App List View ──────────────────────────────────────────────────────────────────
# ═════════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class AppListView(View):
    """
    GET /api/v1/admin/apps/

    List both apps with real-time stats (users, analyses, revenue).

    Response:
    {
      "apps": [
        {
          "app_id": "mobile",
          "name": "Facesyma Mobile",
          "status": "active",
          "config": {...},
          "stats": {
            "total_users": N,
            "active_users": N,
            "analyses_total": N,
            "analyses_last_30d": N,
            "new_users_last_30d": N
          },
          "created_at": "ISO",
          "updated_at": "ISO"
        },
        ...
      ]
    }
    """

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            registry_col = get_app_registry_col()
            users_col = get_users_col()
            history_col = get_history_col()

            apps = list(registry_col.find({}, {'_id': 0}).limit(100))
            _thirty_ago = datetime.utcnow() - timedelta(days=30)
            thirty_days_ago = _thirty_ago.isoformat()
            thirty_ago_ts = _thirty_ago.timestamp()

            result = []
            for app in apps:
                app_id = app['app_id']
                source_query = _get_source_query(app_id)

                _uf = next(users_col.aggregate([{'$facet': {
                    'total':    [{'$match': source_query},                                                   {'$count': 'n'}],
                    'active':   [{'$match': {**source_query, 'is_active': True}},                           {'$count': 'n'}],
                    'new_30d':  [{'$match': {**source_query, 'date_joined': {'$gte': thirty_days_ago}}},    {'$count': 'n'}],
                }}]), {})
                _ufget = _uf.get
                total_users   = (_ufget('total',   [{}])[0] or {}).get('n', 0)
                active_users  = (_ufget('active',  [{}])[0] or {}).get('n', 0)
                new_users_30d = (_ufget('new_30d', [{}])[0] or {}).get('n', 0)

                _hf = next(history_col.aggregate([{'$facet': {
                    'total': [{'$match': source_query},                                                      {'$count': 'n'}],
                    '30d':   [{'$match': {**source_query, 'created_at': {'$gte': thirty_ago_ts}}},           {'$count': 'n'}],
                }}]), {})
                _hfget = _hf.get
                analyses_total = (_hfget('total', [{}])[0] or {}).get('n', 0)
                analyses_30d   = (_hfget('30d',   [{}])[0] or {}).get('n', 0)

                result.append({
                    **app,
                    'stats': {
                        'total_users': total_users,
                        'active_users': active_users,
                        'analyses_total': analyses_total,
                        'analyses_last_30d': analyses_30d,
                        'new_users_last_30d': new_users_30d,
                    }
                })

            return JsonResponse({'apps': result})

        except Exception as e:
            log.exception(f'App list error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


# ═════════════════════════════════════════════════════════════════════════════════
# ── App Detail View ────────────────────────────────────────────────────────────────
# ═════════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class AppDetailView(View):
    """
    GET /api/v1/admin/apps/<app_id>/

    Get single app details with stats.
    Returns 404 if app not found.
    """

    def get(self, request, app_id):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            registry_col = get_app_registry_col()
            app = registry_col.find_one({'app_id': app_id}, {'_id': 0})

            if not app:
                return JsonResponse({'detail': 'App not found'}, status=404)

            # Use AppListView's logic to get stats
            list_view = AppListView()
            users_col = get_users_col()
            history_col = get_history_col()

            source_query = _get_source_query(app_id)
            _thirty_ago = datetime.utcnow() - timedelta(days=30)
            thirty_days_ago = _thirty_ago.isoformat()
            thirty_ago_ts = _thirty_ago.timestamp()

            _uf = next(users_col.aggregate([{'$facet': {
                'total':   [{'$match': source_query},                                                  {'$count': 'n'}],
                'active':  [{'$match': {**source_query, 'is_active': True}},                          {'$count': 'n'}],
                'new_30d': [{'$match': {**source_query, 'date_joined': {'$gte': thirty_days_ago}}},   {'$count': 'n'}],
            }}]), {})
            _ufget = _uf.get
            total_users   = (_ufget('total',   [{}])[0] or {}).get('n', 0)
            active_users  = (_ufget('active',  [{}])[0] or {}).get('n', 0)
            new_users_30d = (_ufget('new_30d', [{}])[0] or {}).get('n', 0)

            _hf = next(history_col.aggregate([{'$facet': {
                'total': [{'$match': source_query},                                                    {'$count': 'n'}],
                '30d':   [{'$match': {**source_query, 'created_at': {'$gte': thirty_ago_ts}}},         {'$count': 'n'}],
            }}]), {})
            _hfget2 = _hf.get
            analyses_total = (_hfget2('total', [{}])[0] or {}).get('n', 0)
            analyses_30d   = (_hfget2('30d',   [{}])[0] or {}).get('n', 0)

            app['stats'] = {
                'total_users': total_users,
                'active_users': active_users,
                'analyses_total': analyses_total,
                'analyses_last_30d': analyses_30d,
                'new_users_last_30d': new_users_30d,
            }

            return JsonResponse({'app': app})

        except Exception as e:
            log.exception(f'App detail error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


# ═════════════════════════════════════════════════════════════════════════════════
# ── App Config Update View ─────────────────────────────────────────────────────────
# ═════════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class AppConfigUpdateView(View):
    """
    PATCH /api/v1/admin/apps/<app_id>/config/

    Update app configuration (maintenance mode, feature flags, version, etc.).
    Uses MongoDB dot-notation for partial updates (doesn't overwrite other fields).

    Body (all optional):
    {
      "maintenance_mode": true,
      "maintenance_message": "Scheduled maintenance",
      "min_version": "2.0.0",
      "status": "inactive",
      "feature_flags": {
        "ai_chat": false,
        "leaderboard": false
      }
    }
    """

    def patch(self, request, app_id):
        try:
            admin = _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            data = _json(request)
            registry_col = get_app_registry_col()
            _rcfo = registry_col.find_one

            # Check if app exists
            app = _rcfo({'app_id': app_id}, {'_id': 1})
            if not app:
                return JsonResponse({'detail': 'App not found'}, status=404)

            # Build update operations (dot-notation for nested fields)
            update_ops = {'updated_at': datetime.utcnow().isoformat()}

            if 'maintenance_mode' in data:
                update_ops['config.maintenance_mode'] = bool(data['maintenance_mode'])
            if 'maintenance_message' in data:
                update_ops['config.maintenance_message'] = str(data['maintenance_message'])
            if 'min_version' in data:
                update_ops['config.min_version'] = str(data['min_version'])
            if 'status' in data:
                _dstatus = data['status']
                if _dstatus in ('active', 'inactive', 'maintenance'):
                    update_ops['status'] = _dstatus

            # Handle feature flags (merge, don't overwrite)
            if 'feature_flags' in data:
                _dff = data['feature_flags']
                if isinstance(_dff, dict):
                    for flag, val in _dff.items():
                        if not isinstance(flag, str) or not _RE_FLAG_KEY.match(flag):
                            continue
                        update_ops[f'config.feature_flags.{flag}'] = bool(val)

            if len(update_ops) > 1:  # If more than just updated_at
                registry_col.update_one({'app_id': app_id}, {'$set': update_ops})

            # Audit log
            log_admin_action(
                admin, 'update_app_config', 'app_config', app_id,
                old_value=app, new_value=update_ops,
                ip_address=extract_ip(request)
            )

            # Return updated app
            updated_app = _rcfo({'app_id': app_id}, {'_id': 0})
            if not updated_app:
                return JsonResponse({'detail': 'App not found after update.'}, status=404)
            return JsonResponse({'app': updated_app, 'message': 'Config updated'})

        except Exception as e:
            log.exception(f'App config update error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


# ═════════════════════════════════════════════════════════════════════════════════
# ── App Stats View ─────────────────────────────────────────────────────────────────
# ═════════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class AppStatsView(View):
    """
    GET /api/v1/admin/apps/<app_id>/stats/

    Get detailed app-specific analytics.

    Response:
    {
      "app_id": "mobile",
      "stats": {
        "users": {
          "total": N,
          "active": N,
          "inactive": N,
          "by_plan": {"free": N, "premium": N},
          "by_auth_method": {"email": N, "google": N},
          "registered_today": N,
          "registered_this_week": N
        },
        "analyses": {
          "total": N,
          "today": N,
          "this_week": N,
          "last_30d": N,
          "by_mode": {"character": N, "golden": N, ...}
        }
      }
    }
    """

    def get(self, request, app_id):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            registry_col = get_app_registry_col()
            app = registry_col.find_one({'app_id': app_id}, {'_id': 0})

            if not app:
                return JsonResponse({'detail': 'App not found'}, status=404)

            users_col = get_users_col()
            history_col = get_history_col()
            source_query = _get_source_query(app_id)

            now = datetime.utcnow()
            today_start = datetime(now.year, now.month, now.day).isoformat()
            _week_ago_dt  = now - timedelta(days=7)
            _month_ago_dt = now - timedelta(days=30)
            week_ago      = _week_ago_dt.isoformat()
            month_ago     = _month_ago_dt.isoformat()
            month_ago_ts  = _month_ago_dt.timestamp()

            day_ago_ts  = (now - timedelta(days=1)).timestamp()
            week_ago_ts = _week_ago_dt.timestamp()

            _uf = next(users_col.aggregate([{'$facet': {
                'total':        [{'$match': source_query},                                                    {'$count': 'n'}],
                'active':       [{'$match': {**source_query, 'is_active': True}},                            {'$count': 'n'}],
                'today':        [{'$match': {**source_query, 'date_joined': {'$gte': today_start}}},         {'$count': 'n'}],
                'this_week':    [{'$match': {**source_query, 'date_joined': {'$gte': week_ago}}},            {'$count': 'n'}],
                'by_plan':      [{'$match': source_query}, {'$group': {'_id': '$plan',        'count': {'$sum': 1}}}],
                'by_auth':      [{'$match': source_query}, {'$group': {'_id': '$auth_method', 'count': {'$sum': 1}}}],
            }}]), {})
            _ufget = _uf.get
            total_users          = (_ufget('total',     [{}])[0] or {}).get('n', 0)
            active_users         = (_ufget('active',    [{}])[0] or {}).get('n', 0)
            inactive_users       = total_users - active_users
            registered_today     = (_ufget('today',     [{}])[0] or {}).get('n', 0)
            registered_this_week = (_ufget('this_week', [{}])[0] or {}).get('n', 0)
            by_plan              = {doc['_id'] or 'free': doc['count'] for doc in _ufget('by_plan', [])}
            by_auth_method       = {doc['_id']: doc['count']           for doc in _ufget('by_auth', [])}

            _hf = next(history_col.aggregate([{'$facet': {
                'total':   [{'$match': source_query},                                                                 {'$count': 'n'}],
                'today':   [{'$match': {**source_query, 'created_at': {'$gte': day_ago_ts}}},                        {'$count': 'n'}],
                'week':    [{'$match': {**source_query, 'created_at': {'$gte': week_ago_ts}}},                       {'$count': 'n'}],
                'month':   [{'$match': {**source_query, 'created_at': {'$gte': month_ago_ts}}},                      {'$count': 'n'}],
                'by_mode': [{'$match': source_query}, {'$group': {'_id': '$mode', 'count': {'$sum': 1}}}],
            }}]), {})
            _hfget = _hf.get
            total_analyses  = (_hfget('total', [{}])[0] or {}).get('n', 0)
            today_analyses  = (_hfget('today', [{}])[0] or {}).get('n', 0)
            week_analyses   = (_hfget('week',  [{}])[0] or {}).get('n', 0)
            month_analyses  = (_hfget('month', [{}])[0] or {}).get('n', 0)
            by_mode         = {doc['_id']: doc['count'] for doc in _hfget('by_mode', [])}

            return JsonResponse({
                'app_id': app_id,
                'stats': {
                    'users': {
                        'total': total_users,
                        'active': active_users,
                        'inactive': inactive_users,
                        'by_plan': by_plan,
                        'by_auth_method': by_auth_method,
                        'registered_today': registered_today,
                        'registered_this_week': registered_this_week,
                    },
                    'analyses': {
                        'total': total_analyses,
                        'today': today_analyses,
                        'this_week': week_analyses,
                        'last_30d': month_analyses,
                        'by_mode': by_mode,
                    }
                }
            })

        except Exception as e:
            log.exception(f'App stats error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)
