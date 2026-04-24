"""
admin_api/views/bulk_views.py
=============================
Bulk operations for user management

Features:
  - Bulk plan updates
  - Bulk user deletion
  - Bulk user export
"""

import json
import logging
import csv
import io
from datetime import datetime
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

_USER_EXPORT_FIELDS = ['id', 'email', 'username', 'plan', 'is_active', 'date_joined']
from admin_api.utils.auth import _require_admin
from admin_api.utils.mongo import get_users_col, get_plan_log_col, _get_db, _next_id

log = logging.getLogger(__name__)

_BULK_UPDATE_PLANS = frozenset({'free', 'premium'})
_BULK_EXPORT_PLANS = frozenset({'free', 'premium', 'tier_a', 'tier_b', 'tier_c', 'tier_d'})


@method_decorator(csrf_exempt, name='dispatch')
class BulkUserUpdateView(View):
    """Toplu kullanıcı güncelleme"""

    def post(self, request):
        """Birden fazla kullanıcının plan/status'ünü güncelle"""
        try:
            _require_admin(request)
            data = json.loads(request.body)
            _dget = data.get
            user_ids = _dget('user_ids', [])
            plan = _dget('plan')
            is_active = _dget('is_active')

            if not user_ids:
                return JsonResponse({'detail': 'user_ids cannot be empty'}, status=400)

            if not isinstance(user_ids, list):
                return JsonResponse({'detail': 'user_ids must be a list'}, status=400)

            if len(user_ids) > 100:
                return JsonResponse({'detail': 'Maximum 100 users per bulk operation.'}, status=400)

            if plan is not None and plan not in _BULK_UPDATE_PLANS:
                return JsonResponse({'detail': f'Invalid plan. Allowed: {", ".join(sorted(_BULK_UPDATE_PLANS))}'}, status=400)

            # MongoDB update
            users_col = get_users_col()
            update_data = {}
            if plan is not None:
                update_data['plan'] = plan
            if is_active is not None:
                update_data['is_active'] = bool(is_active)

            if not update_data:
                return JsonResponse({'detail': 'Select a field to update'}, status=400)

            # Snapshot old plans BEFORE the bulk update (for accurate change log)
            old_plan_map = {}
            if plan is not None:
                for user in users_col.find({'id': {'$in': user_ids}}, {'id': 1, 'email': 1, 'plan': 1}):
                    _uget = user.get
                    old_plan_map[user['id']] = {'email': _uget('email'), 'old_plan': _uget('plan')}

            result = users_col.update_many(
                {'id': {'$in': user_ids}},
                {'$set': update_data}
            )

            # Log plan changes using pre-update snapshot
            if plan is not None:
                plan_log_col = get_plan_log_col()
                _now_iso = datetime.utcnow().isoformat()
                log_entries = []
                for uid in user_ids:
                    snap = old_plan_map.get(uid)
                    if snap:
                        log_entries.append({
                            'id': _next_id(plan_log_col),
                            'user_id': uid,
                            'user_email': snap['email'],
                            'old_plan': snap['old_plan'],
                            'new_plan': plan,
                            'changed_by': 'bulk_update',
                            'changed_at': _now_iso
                        })
                if log_entries:
                    plan_log_col.insert_many(log_entries, ordered=False)

            _mod_count = result.modified_count
            log.info(f"Bulk update: {_mod_count} users updated")

            return JsonResponse({
                'success': True,
                'data': {
                    'message': f'{_mod_count} users updated',
                    'updated': _mod_count,
                    'user_ids': user_ids
                }
            })

        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)
        except Exception as e:
            log.exception(f'Bulk update error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class BulkUserDeleteView(View):
    """Toplu kullanıcı silme"""

    def delete(self, request):
        """Birden fazla kullanıcıyı sil"""
        try:
            payload = _require_admin(request)
            if payload.get('role') != 'superadmin':
                return JsonResponse({'detail': 'Bulk delete requires superadmin role.'}, status=403)

            data = json.loads(request.body)
            user_ids = data.get('user_ids', [])

            if not user_ids:
                return JsonResponse({'detail': 'user_ids cannot be empty'}, status=400)

            if not isinstance(user_ids, list):
                return JsonResponse({'detail': 'user_ids must be a list'}, status=400)

            if len(user_ids) > 50:
                return JsonResponse({'detail': 'Maximum 50 users per bulk delete.'}, status=400)

            # MongoDB delete
            db = _get_db()
            users_col = db['appfaceapi_myuser']
            analysis_col = db['analysis_history']

            # Delete users
            user_result = users_col.delete_many({'id': {'$in': user_ids}})

            # Delete related analysis
            analysis_result = analysis_col.delete_many({'user_id': {'$in': user_ids}})

            _del_users = user_result.deleted_count
            _del_analyses = analysis_result.deleted_count
            log.info(f"Bulk delete: {_del_users} users deleted, {_del_analyses} analyses deleted")

            return JsonResponse({
                'success': True,
                'data': {
                    'message': f'{_del_users} users deleted',
                    'deleted': _del_users,
                    'analyses_deleted': _del_analyses
                }
            })

        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)
        except Exception as e:
            log.exception(f'Bulk delete error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class BulkUserExportView(View):
    """Toplu kullanıcı dışa aktarma"""

    def get(self, request):
        """Filtreli kullanıcıları CSV/JSON olarak dışa aktar"""
        try:
            _require_admin(request)

            # Filters
            _qp = request.GET
            _qpget = _qp.get
            plan = _qpget('plan')  # free, premium
            is_active = _qpget('is_active')  # true, false
            export_format = _qpget('format', 'csv')  # csv, json
            try:
                limit = min(max(1, int(_qpget('limit', 10000))), 50000)
            except (ValueError, TypeError):
                limit = 10000

            # Build query
            query = {}
            if plan and plan in _BULK_EXPORT_PLANS:
                query['plan'] = plan
            if is_active is not None:
                query['is_active'] = is_active.lower() == 'true'

            # Get users
            users_col = get_users_col()
            users = list(users_col.find(query).limit(limit))

            if not users:
                return JsonResponse({'detail': 'No users found'}, status=404)

            if export_format == 'json':
                # JSON export
                for u in users:
                    _oid = u['_id']
                    u['_id'] = str(_oid)
                response = HttpResponse(
                    json.dumps(users, indent=2, ensure_ascii=False),
                    content_type='application/json'
                )
                response['Content-Disposition'] = 'attachment; filename="users_export.json"'
                return response

            elif export_format == 'csv':
                # CSV export
                output = io.StringIO()
                if users:
                    writer = csv.DictWriter(output, fieldnames=_USER_EXPORT_FIELDS)
                    writer.writeheader()

                    for user in users:
                        _uget = user.get
                        row = {
                            'id': _uget('id'),
                            'email': _uget('email'),
                            'username': _uget('username'),
                            'plan': _uget('plan'),
                            'is_active': _uget('is_active'),
                            'date_joined': _uget('date_joined')
                        }
                        writer.writerow(row)

                response = HttpResponse(output.getvalue(), content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
                return response

            else:
                return JsonResponse({'detail': 'Invalid format. Choose csv or json'}, status=400)

        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)
        except Exception as e:
            log.exception(f'Bulk export error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)
