"""
admin_api/views/coach_views.py
================================
Coach DB yönetimi endpoint'leri.
"""

import json
import re
from datetime import datetime
from bson import ObjectId
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from admin_api.utils.auth import _require_admin
from admin_api.utils.mongo import (
    get_coach_users_col, get_coach_birth_col, get_coach_goals_col,
    get_coach_sessions_col, get_coach_attributes_col, _get_coach_db,
    ALL_COACH_LANGS, ALL_COACH_MODULES
)


_VALID_SUN_SIGNS     = frozenset({'aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo',
                                   'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces'})
_VALID_GOAL_STATUSES = frozenset({'active', 'completed', 'paused', 'failed', 'cancelled'})
_GOAL_PROJECTION      = {'_id': 1, 'title': 1, 'module': 1, 'status': 1, 'priority': 1, 'target_date': 1}
_GOAL_FULL_PROJECTION = {'_id': 1, 'user_id': 1, 'title': 1, 'module': 1, 'priority': 1, 'status': 1, 'target_date': 1}
_SIFAT_META_PROJ      = {'_id': 1, 'version': 1, 'updated_at': 1}


def _json(request):
    """Request body JSON'ı parse et"""
    try:
        return json.loads(request.body)
    except Exception:
        return {}


def _oid(doc: dict) -> dict:
    """BSON ObjectId'yi string'e çevir (coach_goals için)"""
    if doc and '_id' in doc:
        _id_val = doc['_id']
        doc['_id'] = str(_id_val)
    return doc


# ═══════════════════════════════════════════════════════════════════════════════
# ── Coach Statleri ──────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class CoachOverallStatsView(View):
    """
    Coach DB genel istatistikleri.

    GET /api/v1/admin/coach/stats/
    Return: {total_users, total_goals, total_sessions, attributes_by_lang}
    """

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        db = _get_coach_db()

        total_users    = db['coach_users'].estimated_document_count()
        total_goals    = db['coach_goals'].estimated_document_count()
        total_sessions = db['coach_sessions'].estimated_document_count()

        attrs_by_lang = {}
        for lang in ALL_COACH_LANGS:
            col_name = f'coach_attributes_{lang}'
            attrs_by_lang[lang] = db[col_name].estimated_document_count()

        return JsonResponse({
            'total_users':    total_users,
            'total_goals':    total_goals,
            'total_sessions': total_sessions,
            'attributes_by_lang': attrs_by_lang,
        })


# ═══════════════════════════════════════════════════════════════════════════════
# ── Coach Kullanıcıları ────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class CoachUserListView(View):
    """
    Coach kullanıcılarını listele (sayfalanmış, filtreleme).

    GET /api/v1/admin/coach/users/?page=1&limit=20&lang=tr&sun_sign=Aries
    Query params:
        - page: int (default 1)
        - limit: int (default 20, max 100)
        - lang: str (opsiyonel)
        - sun_sign: str (opsiyonel)
    """

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            _qp = request.GET
            _qpget = _qp.get
            page = max(1, int(_qpget('page', 1)))
            limit = min(max(1, int(_qpget('limit', 20))), 100)
        except (ValueError, TypeError):
            page, limit = 1, 20
        lang = _qpget('lang', '')
        sun_sign = _qpget('sun_sign', '')


        col = get_coach_users_col()

        # Query
        query = {}
        if lang and lang in ALL_COACH_LANGS:
            query['lang'] = lang
        if sun_sign and sun_sign in _VALID_SUN_SIGNS:
            query['sun_sign'] = sun_sign

        # Total count
        total = col.count_documents(query)

        # Sayfalanmış sorgu
        skip = (page - 1) * limit
        users = list(
            col.find(query, {'_id': 0})
            .sort([('created_at', -1)])
            .skip(skip)
            .limit(limit)
        )

        return JsonResponse({
            'data': users,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit,
            }
        })


@method_decorator(csrf_exempt, name='dispatch')
class CoachUserStatsView(View):
    """
    Coach kullanıcı istatistikleri.

    GET /api/v1/admin/coach/users/stats/
    """

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        col = get_coach_users_col()

        _cs = next(col.aggregate([{'$facet': {
            'by_lang':    [{'$group': {'_id': '$lang',     'count': {'$sum': 1}}}],
            'by_sign':    [{'$group': {'_id': '$sun_sign', 'count': {'$sum': 1}}}, {'$sort': {'count': -1}}, {'$limit': 5}],
            'avgs':       [{'$group': {'_id': None, 'avg_saglik': {'$avg': '$saglik_skoru'}, 'avg_ozguven': {'$avg': '$ozguven_skoru'}, 'avg_iletisim': {'$avg': '$iletisim_tipi'}}}],
            'total':      [{'$count': 'n'}],
        }}]), {})
        _csget = _cs.get
        total         = (_csget('total', [{}])[0] or {}).get('n', 0)
        lang_dict     = {_id: doc['count'] for doc in _csget('by_lang', []) if (_id := doc['_id'])}
        sun_sign_dict = {_id: doc['count'] for doc in _csget('by_sign', []) if (_id := doc['_id'])}
        avg_data      = (_csget('avgs', [{}])[0] or {'avg_saglik': 0, 'avg_ozguven': 0, 'avg_iletisim': 0})
        _adget = avg_data.get

        return JsonResponse({
            'total_users': total,
            'by_lang': lang_dict,
            'top_sun_signs': sun_sign_dict,
            'avg_saglik_skoru': round(_adget('avg_saglik') or 0, 2),
            'avg_ozguven_skoru': round(_adget('avg_ozguven') or 0, 2),
        })


@method_decorator(csrf_exempt, name='dispatch')
class CoachUserDetailView(View):
    """
    Coach kullanıcı detayı (+ birth_data + son 10 hedef).

    GET /api/v1/admin/coach/users/<user_id>/
    DELETE /api/v1/admin/coach/users/<user_id>/ — cascade sil
    """

    def get(self, request, user_id):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        _uid = int(user_id)
        col = get_coach_users_col()
        user = col.find_one({'user_id': _uid}, {'_id': 0})

        if not user:
            return JsonResponse({'detail': f'User #{user_id} not found.'}, status=404)

        # Birth data
        birth_col = get_coach_birth_col()
        birth_data = birth_col.find_one({'user_id': _uid}, {'_id': 0})

        # Son 10 hedef
        goal_col = get_coach_goals_col()
        goals = list(goal_col.find(
            {'user_id': _uid}, _GOAL_PROJECTION
        ).sort([('updated_at', -1)]).limit(10))
        goals = [_oid(g) for g in goals]

        return JsonResponse({
            'user': user,
            'birth_data': birth_data,
            'recent_goals': goals,
        })

    def delete(self, request, user_id):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        _uid = int(user_id)
        col = get_coach_users_col()
        user = col.find_one({'user_id': _uid}, {'_id': 1})

        if not user:
            return JsonResponse({'detail': f'User #{user_id} not found.'}, status=404)

        # Cascade delete
        birth_col = get_coach_birth_col()
        birth_col.delete_one({'user_id': _uid})

        goal_col = get_coach_goals_col()
        goal_result = goal_col.delete_many({'user_id': _uid})

        col.delete_one({'user_id': _uid})

        return JsonResponse({
            'message': f'User and {goal_result.deleted_count} goals deleted.',
        })


# ═══════════════════════════════════════════════════════════════════════════════
# ── Coach Hedefleri ────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class CoachGoalListView(View):
    """
    Coach hedeflerini listele (sayfalanmış, filtreleme).

    GET /api/v1/admin/coach/goals/?page=1&limit=20&status=aktif&module=kariyer&user_id=123
    """

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            _qp = request.GET
            _qpget = _qp.get
            page = max(1, int(_qpget('page', 1)))
            limit = min(max(1, int(_qpget('limit', 20))), 100)
        except (ValueError, TypeError):
            page, limit = 1, 20
        status = _qpget('status', '')
        module = _qpget('module', '')
        user_id = _qpget('user_id', '')


        col = get_coach_goals_col()

        # Query
        query = {}
        if status and status in _VALID_GOAL_STATUSES:
            query['status'] = status
        if module and module in ALL_COACH_MODULES:
            query['module'] = module
        if user_id:
            try:
                query['user_id'] = int(user_id)
            except (ValueError, TypeError):
                return JsonResponse({'detail': 'Invalid user_id.'}, status=400)

        # Total count
        total = col.count_documents(query)

        # Sayfalanmış sorgu
        skip = (page - 1) * limit
        goals = list(
            col.find(query, _GOAL_FULL_PROJECTION)
            .sort([('updated_at', -1)])
            .skip(skip)
            .limit(limit)
        )
        goals = [_oid(g) for g in goals]

        return JsonResponse({
            'data': goals,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit,
            }
        })


@method_decorator(csrf_exempt, name='dispatch')
class CoachGoalStatsView(View):
    """
    Coach hedef istatistikleri.

    GET /api/v1/admin/coach/goals/stats/
    """

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        col = get_coach_goals_col()

        _gs = next(col.aggregate([{'$facet': {
            'total':    [{'$count': 'n'}],
            'by_status':   [{'$group': {'_id': '$status',   'count': {'$sum': 1}}}],
            'by_module':   [{'$group': {'_id': '$module',   'count': {'$sum': 1}}}],
            'by_priority': [{'$group': {'_id': '$priority', 'count': {'$sum': 1}}}],
        }}]), {})
        _gsget = _gs.get
        total        = (_gsget('total', [{}])[0] or {}).get('n', 0)
        status_dict  = {_id: doc['count'] for doc in _gsget('by_status',   []) if (_id := doc['_id'])}
        module_dict  = {_id: doc['count'] for doc in _gsget('by_module',   []) if (_id := doc['_id'])}
        priority_dict = {_id: doc['count'] for doc in _gsget('by_priority', []) if (_id := doc['_id'])}

        return JsonResponse({
            'total_goals': total,
            'by_status': status_dict,
            'by_module': module_dict,
            'by_priority': priority_dict,
        })


@method_decorator(csrf_exempt, name='dispatch')
class CoachGoalDetailView(View):
    """
    Coach hedefini güncelle/sil.

    PATCH /api/v1/admin/coach/goals/<goal_id>/ — status değiştir
    DELETE /api/v1/admin/coach/goals/<goal_id>/
    """

    def patch(self, request, goal_id):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            oid = ObjectId(goal_id)
        except Exception:
            return JsonResponse({'detail': 'Invalid goal_id.'}, status=400)

        data = _json(request)
        col = get_coach_goals_col()
        _cfo = col.find_one

        # Hedef var mı?
        goal = _cfo({'_id': oid}, {'_id': 1})
        if not goal:
            return JsonResponse({'detail': f'Goal #{goal_id} not found.'}, status=404)

        # Güncellenebilir alanlar
        update_data = {}
        if 'status' in data:
            update_data['status'] = data['status']
        if 'priority' in data:
            update_data['priority'] = data['priority']

        if not update_data:
            return JsonResponse({'detail': 'No fields to update.'}, status=400)

        update_data['updated_at'] = datetime.utcnow().isoformat()

        # Güncelle
        col.update_one({'_id': oid}, {'$set': update_data})

        # Güncellenmiş goal döner
        updated = _cfo({'_id': oid})
        return JsonResponse({
            'message': 'Goal updated.',
            'goal': _oid(updated),
        })

    def delete(self, request, goal_id):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            oid = ObjectId(goal_id)
        except Exception:
            return JsonResponse({'detail': 'Invalid goal_id.'}, status=400)

        col = get_coach_goals_col()

        result = col.delete_one({'_id': oid})

        if result.deleted_count == 0:
            return JsonResponse({'detail': f'Goal #{goal_id} not found.'}, status=404)

        return JsonResponse({'message': 'Hedef deleted.'})


# ═══════════════════════════════════════════════════════════════════════════════
# ── Coach Sıfatları (Attributes) ───────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class CoachAttributeListView(View):
    """
    Coach sıfat dilleri listesi.

    GET /api/v1/admin/coach/attributes/
    Return: {data: [{lang, sifat_count}, ...]}
    """

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        result = []
        for lang in ALL_COACH_LANGS:
            col = get_coach_attributes_col(lang)
            count = col.estimated_document_count()
            result.append({'lang': lang, 'sifat_count': count})

        return JsonResponse({'data': result})


@method_decorator(csrf_exempt, name='dispatch')
class CoachAttributeLangView(View):
    """
    Dile göre sıfatlar (sayfalanmış, arama).

    GET /api/v1/admin/coach/attributes/<lang>/?page=1&limit=20&search=güzel
    """

    def get(self, request, lang):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        if lang not in ALL_COACH_LANGS:
            return JsonResponse({'detail': f'Invalid language: {lang}'}, status=400)

        try:
            _qp = request.GET
            _qpget = _qp.get
            page = max(1, int(_qpget('page', 1)))
            limit = min(max(1, int(_qpget('limit', 20))), 100)
        except (ValueError, TypeError):
            page, limit = 1, 20
        search = _qpget('search', '').strip()[:100]

        col = get_coach_attributes_col(lang)

        # Query
        query = {}
        if search:
            query['_id'] = {'$regex': re.escape(search), '$options': 'i'}

        # Total count
        total = col.count_documents(query)

        # Sayfalanmış sorgu — sadece metadata al
        skip = (page - 1) * limit
        sifatlar = list(
            col.find(query, _SIFAT_META_PROJ)
            .sort([('_id', 1)])
            .skip(skip)
            .limit(limit)
        )

        # Module count = 27 (hepsinin tüm modülleri var)
        for sifat in sifatlar:
            sifat['module_count'] = 27

        return JsonResponse({
            'lang': lang,
            'data': sifatlar,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit,
            }
        })


@method_decorator(csrf_exempt, name='dispatch')
class CoachAttributeDetailView(View):
    """
    Sıfat detayı — tüm 27 modülü.

    GET /api/v1/admin/coach/attributes/<lang>/<sifat_name>/
    PATCH /api/v1/admin/coach/attributes/<lang>/<sifat_name>/ — modülleri güncelle
    """

    def get(self, request, lang, sifat_name):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        if lang not in ALL_COACH_LANGS:
            return JsonResponse({'detail': f'Invalid language: {lang}'}, status=400)

        col = get_coach_attributes_col(lang)
        sifat = col.find_one({'_id': sifat_name})

        if not sifat:
            return JsonResponse({'detail': f'Adjective "{sifat_name}" not found.'}, status=404)

        # Metadata
        _sget = sifat.get
        result = {
            'sifat_name': sifat_name,
            'lang': lang,
            'version': _sget('version'),
            'updated_at': str(_sget('updated_at', '')),
        }

        # 27 modülü ekle
        for module in ALL_COACH_MODULES:
            result[module] = _sget(module, {})

        return JsonResponse(result)

    def patch(self, request, lang, sifat_name):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        if lang not in ALL_COACH_LANGS:
            return JsonResponse({'detail': f'Invalid language: {lang}'}, status=400)

        data = _json(request)
        col = get_coach_attributes_col(lang)

        # Sıfat var mı?
        sifat = col.find_one({'_id': sifat_name}, {'_id': 1})
        if not sifat:
            return JsonResponse({'detail': f'Adjective "{sifat_name}" not found.'}, status=404)

        # Sadece ALL_COACH_MODULES anahtar'ları kabul et (whitelist)
        update_data = {}
        for module in ALL_COACH_MODULES:
            if module in data:
                update_data[module] = data[module]

        if not update_data:
            return JsonResponse({'detail': 'No module to update.'}, status=400)

        update_data['updated_at'] = datetime.utcnow().isoformat()

        # Güncelle
        col.update_one({'_id': sifat_name}, {'$set': update_data})

        return JsonResponse({'message': 'Adjective updated.'})
