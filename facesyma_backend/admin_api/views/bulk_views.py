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
from admin_api.utils.auth import _require_admin
from admin_api.utils.mongo import get_users_col, get_plan_log_col, _get_db, _next_id

log = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class BulkUserUpdateView(View):
    """Toplu kullanıcı güncelleme"""

    def post(self, request):
        """Birden fazla kullanıcının plan/status'ünü güncelle"""
        try:
            _require_admin(request)
            data = json.loads(request.body)
            user_ids = data.get('user_ids', [])
            plan = data.get('plan')
            is_active = data.get('is_active')

            if not user_ids:
                return JsonResponse({'detail': 'user_ids boş olamaz'}, status=400)

            if not isinstance(user_ids, list):
                return JsonResponse({'detail': 'user_ids bir liste olmalı'}, status=400)

            # MongoDB update
            users_col = get_users_col()
            update_data = {}
            if plan is not None:
                update_data['plan'] = plan
            if is_active is not None:
                update_data['is_active'] = is_active

            if not update_data:
                return JsonResponse({'detail': 'Güncellenecek alan seçin'}, status=400)

            result = users_col.update_many(
                {'id': {'$in': user_ids}},
                {'$set': update_data}
            )

            # Log plan changes
            if plan is not None:
                plan_log_col = get_plan_log_col()
                for uid in user_ids:
                    user = users_col.find_one({'id': uid})
                    if user:
                        log_entry = {
                            'id': _next_id(plan_log_col),
                            'user_id': uid,
                            'user_email': user.get('email'),
                            'old_plan': user.get('plan'),
                            'new_plan': plan,
                            'changed_by': 'bulk_update',
                            'changed_at': datetime.utcnow().isoformat()
                        }
                        plan_log_col.insert_one(log_entry)

            log.info(f"Bulk update: {result.modified_count} kullanıcı güncellendi")

            return JsonResponse({
                'success': True,
                'data': {
                    'message': f'{result.modified_count} kullanıcı güncellendi',
                    'updated': result.modified_count,
                    'user_ids': user_ids
                }
            })

        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)
        except Exception as e:
            log.exception(f'Bulk update hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class BulkUserDeleteView(View):
    """Toplu kullanıcı silme"""

    def delete(self, request):
        """Birden fazla kullanıcıyı sil"""
        try:
            _require_admin(request)
            data = json.loads(request.body)
            user_ids = data.get('user_ids', [])

            if not user_ids:
                return JsonResponse({'detail': 'user_ids boş olamaz'}, status=400)

            if not isinstance(user_ids, list):
                return JsonResponse({'detail': 'user_ids bir liste olmalı'}, status=400)

            # MongoDB delete
            db = _get_db()
            users_col = db['appfaceapi_myuser']
            analysis_col = db['analysis_history']

            # Delete users
            user_result = users_col.delete_many({'id': {'$in': user_ids}})

            # Delete related analysis
            analysis_result = analysis_col.delete_many({'user_id': {'$in': user_ids}})

            log.info(f"Bulk delete: {user_result.deleted_count} kullanıcı silindi, "
                     f"{analysis_result.deleted_count} analiz silindi")

            return JsonResponse({
                'success': True,
                'data': {
                    'message': f'{user_result.deleted_count} kullanıcı silindi',
                    'deleted': user_result.deleted_count,
                    'analyses_deleted': analysis_result.deleted_count
                }
            })

        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)
        except Exception as e:
            log.exception(f'Bulk delete hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class BulkUserExportView(View):
    """Toplu kullanıcı dışa aktarma"""

    def get(self, request):
        """Filtreli kullanıcıları CSV/JSON olarak dışa aktar"""
        try:
            _require_admin(request)

            # Filters
            plan = request.GET.get('plan')  # free, premium
            is_active = request.GET.get('is_active')  # true, false
            export_format = request.GET.get('format', 'csv')  # csv, json
            limit = int(request.GET.get('limit', 10000))

            # Build query
            query = {}
            if plan:
                query['plan'] = plan
            if is_active is not None:
                query['is_active'] = is_active.lower() == 'true'

            # Get users
            users_col = get_users_col()
            users = list(users_col.find(query).limit(limit))

            if not users:
                return JsonResponse({'detail': 'Hiçbir kullanıcı bulunamadı'}, status=404)

            if export_format == 'json':
                # JSON export
                for u in users:
                    u['_id'] = str(u['_id'])
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
                    fieldnames = ['id', 'email', 'username', 'plan', 'is_active', 'date_joined']
                    writer = csv.DictWriter(output, fieldnames=fieldnames)
                    writer.writeheader()

                    for user in users:
                        row = {
                            'id': user.get('id'),
                            'email': user.get('email'),
                            'username': user.get('username'),
                            'plan': user.get('plan'),
                            'is_active': user.get('is_active'),
                            'date_joined': user.get('date_joined')
                        }
                        writer.writerow(row)

                response = HttpResponse(output.getvalue(), content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
                return response

            else:
                return JsonResponse({'detail': 'Geçersiz format. csv veya json seçin'}, status=400)

        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)
        except Exception as e:
            log.exception(f'Bulk export hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)
