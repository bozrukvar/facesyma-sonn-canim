"""
admin_api/views/app_management_views.py
=======================================
Multi-app management admin endpoints.
Manages app status, configs, and generates per-app statistics.
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

            apps = list(registry_col.find({}, {'_id': 0}))
            thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()

            result = []
            for app in apps:
                app_id = app['app_id']
                source_query = _get_source_query(app_id)

                # User stats
                total_users = users_col.count_documents(source_query)
                active_users = users_col.count_documents({
                    **source_query,
                    'is_active': True
                })

                # Analysis stats (with backward compat for app_source)
                analyses_total = history_col.count_documents(source_query)

                # Last 30 days (Unix timestamp)
                thirty_ago_ts = (datetime.utcnow() - timedelta(days=30)).timestamp()
                analyses_30d = history_col.count_documents({
                    **source_query,
                    'created_at': {'$gte': thirty_ago_ts}
                })

                # New users last 30 days
                new_users_30d = users_col.count_documents({
                    **source_query,
                    'date_joined': {'$gte': thirty_days_ago}
                })

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
            return JsonResponse({'detail': str(e)}, status=500)


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
            thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()

            total_users = users_col.count_documents(source_query)
            active_users = users_col.count_documents({
                **source_query,
                'is_active': True
            })
            analyses_total = history_col.count_documents(source_query)
            thirty_ago_ts = (datetime.utcnow() - timedelta(days=30)).timestamp()
            analyses_30d = history_col.count_documents({
                **source_query,
                'created_at': {'$gte': thirty_ago_ts}
            })
            new_users_30d = users_col.count_documents({
                **source_query,
                'date_joined': {'$gte': thirty_days_ago}
            })

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
            return JsonResponse({'detail': str(e)}, status=500)


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

            # Check if app exists
            app = registry_col.find_one({'app_id': app_id})
            if not app:
                return JsonResponse({'detail': 'App not found'}, status=404)

            # Build update operations (dot-notation for nested fields)
            update_ops = {'updated_at': datetime.now().isoformat()}

            if 'maintenance_mode' in data:
                update_ops['config.maintenance_mode'] = bool(data['maintenance_mode'])
            if 'maintenance_message' in data:
                update_ops['config.maintenance_message'] = str(data['maintenance_message'])
            if 'min_version' in data:
                update_ops['config.min_version'] = str(data['min_version'])
            if 'status' in data and data['status'] in ('active', 'inactive', 'maintenance'):
                update_ops['status'] = data['status']

            # Handle feature flags (merge, don't overwrite)
            if 'feature_flags' in data and isinstance(data['feature_flags'], dict):
                for flag, val in data['feature_flags'].items():
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
            updated_app = registry_col.find_one({'app_id': app_id}, {'_id': 0})
            return JsonResponse({'app': updated_app, 'message': 'Config updated'})

        except Exception as e:
            log.exception(f'App config update error: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


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
            week_ago = (now - timedelta(days=7)).isoformat()
            month_ago = (now - timedelta(days=30)).isoformat()
            month_ago_ts = (now - timedelta(days=30)).timestamp()

            # User stats
            total_users = users_col.count_documents(source_query)
            active_users = users_col.count_documents({
                **source_query,
                'is_active': True
            })
            inactive_users = total_users - active_users

            # By plan
            plan_stats = users_col.aggregate([
                {'$match': source_query},
                {'$group': {'_id': '$plan', 'count': {'$sum': 1}}}
            ])
            by_plan = {doc['_id'] or 'free': doc['count'] for doc in plan_stats}

            # By auth method
            auth_stats = users_col.aggregate([
                {'$match': source_query},
                {'$group': {'_id': '$auth_method', 'count': {'$sum': 1}}}
            ])
            by_auth_method = {doc['_id']: doc['count'] for doc in auth_stats}

            registered_today = users_col.count_documents({
                **source_query,
                'date_joined': {'$gte': today_start}
            })
            registered_this_week = users_col.count_documents({
                **source_query,
                'date_joined': {'$gte': week_ago}
            })

            # Analysis stats
            total_analyses = history_col.count_documents(source_query)
            today_analyses = history_col.count_documents({
                **source_query,
                'created_at': {'$gte': (datetime.utcnow()).timestamp() - 86400}  # Last 24 hours
            })
            week_analyses = history_col.count_documents({
                **source_query,
                'created_at': {'$gte': (now - timedelta(days=7)).timestamp()}
            })
            month_analyses = history_col.count_documents({
                **source_query,
                'created_at': {'$gte': month_ago_ts}
            })

            # By mode
            mode_stats = history_col.aggregate([
                {'$match': source_query},
                {'$group': {'_id': '$mode', 'count': {'$sum': 1}}}
            ])
            by_mode = {doc['_id']: doc['count'] for doc in mode_stats}

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
            return JsonResponse({'detail': str(e)}, status=500)
