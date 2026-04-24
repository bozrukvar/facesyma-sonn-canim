"""
admin_api/views/review_views.py
================================
Yorum yönetimi (CRUD + sentiment analizi + CSV export).
"""

import json
import csv
import io
from datetime import datetime, timedelta
from django.http import JsonResponse, StreamingHttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from admin_api.utils.auth import _require_admin
from admin_api.utils.mongo import get_reviews_col, _next_id
from admin_api.utils.sentiment import analyze_sentiment

_REVIEW_CSV_HEADERS = ['id', 'user_id', 'user_email', 'text', 'rating', 'platform',
                        'sentiment', 'sentiment_score', 'is_visible', 'created_at']


_VALID_REVIEW_PERIODS = frozenset({'daily', 'weekly', 'monthly'})
_VALID_SENTIMENTS     = frozenset({'positive', 'negative', 'neutral'})
_VALID_PLATFORMS      = frozenset({'mobile', 'web', 'api'})
_REVIEW_PROJECTION    = {'_id': 0, 'id': 1, 'user_id': 1, 'user_email': 1, 'text': 1,
                         'rating': 1, 'platform': 1, 'sentiment': 1, 'sentiment_score': 1,
                         'is_visible': 1, 'created_at': 1, 'tags': 1}


def _json(request):
    """Request body JSON'ı parse et"""
    try:
        return json.loads(request.body)
    except Exception:
        return {}


def _review_dict(review: dict) -> dict:
    """Review dokümanını response formatına dönüştür"""
    _rget = review.get
    return {
        'id': _rget('id'),
        'user_id': _rget('user_id'),
        'user_email': _rget('user_email'),
        'text': _rget('text'),
        'rating': _rget('rating'),
        'platform': _rget('platform'),
        'sentiment': _rget('sentiment'),
        'sentiment_score': _rget('sentiment_score'),
        'is_visible': _rget('is_visible'),
        'created_at': str(_rget('created_at', '')),
        'tags': _rget('tags', []),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ── Yorum Listesi ──────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class ReviewListView(View):
    """
    Yorum listesi (sayfalanmış, filtreleme).

    GET /api/v1/admin/reviews/?page=1&limit=20&sentiment=positive&platform=mobile&visible=true
    Query params:
        - page: int (default 1)
        - limit: int (default 20, max 100)
        - sentiment: str ("positive" | "negative" | "neutral")
        - platform: str ("mobile" | "web" | "api")
        - visible: bool (true | false)
        - user_id: int (opsiyonel)
    """

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        # Query params
        try:
            _qp = request.GET
            _qpget = _qp.get
            page = max(1, int(_qpget('page', 1)))
            limit = min(max(1, int(_qpget('limit', 20))), 100)
        except (ValueError, TypeError):
            page, limit = 1, 20
        sentiment = _qpget('sentiment', '')
        platform = _qpget('platform', '')
        visible = _qpget('visible', '')
        user_id = _qpget('user_id', '')

        col = get_reviews_col()

        # Query
        query = {}
        if sentiment and sentiment in _VALID_SENTIMENTS:
            query['sentiment'] = sentiment
        if platform and platform in _VALID_PLATFORMS:
            query['platform'] = platform
        if visible:
            query['is_visible'] = visible.lower() == 'true'
        if user_id:
            try:
                query['user_id'] = int(user_id)
            except (ValueError, TypeError):
                pass

        # Total count
        total = col.count_documents(query)

        # Sayfalanmış sorgu
        skip = (page - 1) * limit
        reviews = list(
            col.find(query, {'_id': 0})
            .sort([('created_at', -1)])
            .skip(skip)
            .limit(limit)
        )

        return JsonResponse({
            'reviews': [_review_dict(r) for r in reviews],
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit,
            }
        })


# ═══════════════════════════════════════════════════════════════════════════════
# ── Yorum Oluştur ──────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class ReviewCreateView(View):
    """
    Yorum kaydet (otomatik sentiment analizi).

    POST /api/v1/admin/reviews/
    Body: {
        user_id?: int,
        user_email?: str,
        text: str,
        rating?: int (1-5),
        platform: str ("mobile" | "web" | "api"),
        tags?: [str]
    }
    Return: {review} (sentiment otomatik eklenir)
    """

    def post(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        data = _json(request)
        _dget = data.get
        text = _dget('text', '').strip()
        platform = _dget('platform', 'web').strip()

        # Doğrulama
        if not text:
            return JsonResponse({'detail': 'Yorum metni zorunlu.'}, status=400)
        if not platform:
            return JsonResponse({'detail': 'Platform zorunlu.'}, status=400)

        # Sentiment analizi
        sentiment_analysis = analyze_sentiment(text)

        col = get_reviews_col()
        review_id = _next_id(col)

        review = {
            'id': review_id,
            'user_id': _dget('user_id'),
            'user_email': _dget('user_email'),
            'text': text,
            'rating': _dget('rating'),
            'platform': platform,
            'sentiment': sentiment_analysis['sentiment'],
            'sentiment_score': sentiment_analysis['score'],
            'is_visible': True,
            'created_at': datetime.utcnow().isoformat(),
            'tags': _dget('tags', []),
        }

        col.insert_one(review)

        return JsonResponse({
            'message': 'Yorum kaydedildi.',
            'review': _review_dict(review)
        }, status=201)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Yorum Statleri ──────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class ReviewStatsView(View):
    """
    Yorum istatistikleri.

    GET /api/v1/admin/reviews/stats/
    Return: {
        total_reviews,
        by_sentiment: {positive, negative, neutral},
        by_platform: {mobile, web, api},
        average_rating,
        visible_count,
        hidden_count
    }
    """

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        col = get_reviews_col()

        # Single $facet replaces 5 separate queries
        _r = next(col.aggregate([{'$facet': {
            'total':        [{'$count': 'n'}],
            'visible':      [{'$match': {'is_visible': True}},  {'$count': 'n'}],
            'hidden':       [{'$match': {'is_visible': False}}, {'$count': 'n'}],
            'by_sentiment': [{'$group': {'_id': '$sentiment', 'count': {'$sum': 1}}}],
            'by_platform':  [{'$group': {'_id': '$platform',  'count': {'$sum': 1}}}],
            'avg_rating':   [
                {'$match': {'rating': {'$ne': None}}},
                {'$group': {'_id': None, 'avg': {'$avg': '$rating'}}},
            ],
        }}]), {})
        _rget2 = _r.get
        total   = (_rget2('total',   [{}])[0] or {}).get('n', 0)
        visible = (_rget2('visible', [{}])[0] or {}).get('n', 0)
        hidden  = (_rget2('hidden',  [{}])[0] or {}).get('n', 0)
        sentiment_dict = {doc['_id']: doc['count'] for doc in _rget2('by_sentiment', [])}
        platform_dict  = {doc['_id']: doc['count'] for doc in _rget2('by_platform',  [])}
        avg_rating = round((_rget2('avg_rating', [{}])[0] or {}).get('avg', 0) or 0, 2)

        return JsonResponse({
            'total_reviews': total,
            'by_sentiment': sentiment_dict,
            'by_platform': platform_dict,
            'average_rating': avg_rating,
            'visible_reviews': visible,
            'hidden_reviews': hidden,
            'visible_percentage': round((visible / total * 100) if total > 0 else 0, 2),
        })


# ═══════════════════════════════════════════════════════════════════════════════
# ── Yorum Güncelle (Moderasyon) ────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class ReviewUpdateView(View):
    """
    Yorum güncelle (moderasyon: is_visible, tags).

    PATCH /api/v1/admin/reviews/<rid>/
    Body: {is_visible?, tags?}
    """

    def patch(self, request, rid):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        data = _json(request)
        _rid = int(rid)
        col = get_reviews_col()
        _cfo = col.find_one

        # Yorum var mı?
        review = _cfo({'id': _rid}, {'_id': 1})
        if not review:
            return JsonResponse(
                {'detail': f'Review #{rid} not found.'},
                status=404
            )

        # Güncellenebilir alanlar
        update_data = {}
        if 'is_visible' in data:
            update_data['is_visible'] = bool(data['is_visible'])
        if 'tags' in data:
            update_data['tags'] = data['tags']

        if not update_data:
            return JsonResponse(
                {'detail': 'No fields to update.'},
                status=400
            )

        # Güncelle
        col.update_one({'id': _rid}, {'$set': update_data})

        # Güncellenmiş review döner
        updated = _cfo({'id': _rid}, _REVIEW_PROJECTION)
        if not updated:
            return JsonResponse({'detail': 'Review not found after update.'}, status=404)
        return JsonResponse({
            'message': 'Review updated.',
            'review': _review_dict(updated)
        })


# ═══════════════════════════════════════════════════════════════════════════════
# ── Yorum Export (JSON/CSV) ───────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class ReviewExportView(View):
    """
    Yorum listesini export et (JSON veya CSV).

    GET /api/v1/admin/reviews/export/?format=csv&limit=1000
    Query params:
        - format: "json" (default) | "csv"
        - limit: int (default 100, max 10000) — çok veri memory sorununa neden olabilir
        - sentiment: str (opsiyonel filtre)
    """

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        # Query params
        _qp = request.GET
        _qpget = _qp.get
        format_type = _qpget('format', 'json').lower()
        try:
            limit = min(max(1, int(_qpget('limit', 100))), 10000)
        except (ValueError, TypeError):
            limit = 100
        sentiment = _qpget('sentiment', '')

        col = get_reviews_col()

        # Query
        query = {}
        if sentiment and sentiment in _VALID_SENTIMENTS:
            query['sentiment'] = sentiment

        # Reviewları al
        reviews = list(
            col.find(query, {'_id': 0})
            .sort([('created_at', -1)])
            .limit(limit)
        )

        if format_type == 'csv':
            # CSV format
            output = io.StringIO()
            writer = csv.writer(output)
            _wrw = writer.writerow

            # Header
            _wrw(_REVIEW_CSV_HEADERS)

            # Rows
            for review in reviews:
                _rget = review.get
                _wrw([
                    _rget('id'),
                    _rget('user_id'),
                    _rget('user_email'),
                    _rget('text', '').replace('\n', ' '),  # Yeni satırları kaldır
                    _rget('rating'),
                    _rget('platform'),
                    _rget('sentiment'),
                    _rget('sentiment_score'),
                    _rget('is_visible'),
                    _rget('created_at'),
                ])

            # Response
            response = StreamingHttpResponse(
                iter([output.getvalue()]),
                content_type='text/csv'
            )
            response['Content-Disposition'] = 'attachment; filename="reviews_export.csv"'
            return response

        else:
            # JSON format (default)
            response = JsonResponse({
                'reviews': [_review_dict(r) for r in reviews],
                'export_date': datetime.utcnow().isoformat(),
                'count': len(reviews),
                'format': 'json'
            })
            response['Content-Disposition'] = 'attachment; filename="reviews_export.json"'
            return response


# ═══════════════════════════════════════════════════════════════════════════════
# ── Yorum Zaman Serisi (Trend) ───────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class ReviewTrendView(View):
    """
    Yorum zaman serisi analizi (günlük/haftalık/aylık).

    GET /api/v1/admin/reviews/trend/?period=daily&days=30
    Query params:
        - period: "daily" | "weekly" | "monthly" (default: daily)
        - days: int (default 30, max 365)
    Return: [{date, count, avg_rating}, ...]
    """

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        _qp = request.GET
        _qpget = _qp.get
        period = _qpget('period', 'daily').lower()
        try:
            days = min(max(1, int(_qpget('days', 30))), 365)
        except (ValueError, TypeError):
            days = 30

        if period not in _VALID_REVIEW_PERIODS:
            return JsonResponse({'detail': 'period must be daily/weekly/monthly'}, status=400)

        _now = datetime.utcnow()
        _now_iso = _now.isoformat()
        col = get_reviews_col()
        start_date = _now - timedelta(days=days)
        _start_iso = start_date.isoformat()

        # Group by date format
        if period == 'daily':
            date_format = '%Y-%m-%d'
        elif period == 'weekly':
            date_format = '%Y-W%U'  # ISO week
        else:  # monthly
            date_format = '%Y-%m'

        pipeline = [
            {
                '$match': {
                    'created_at': {
                        '$gte': _start_iso,
                        '$lte': _now_iso,
                    }
                }
            },
            {
                '$group': {
                    '_id': {
                        '$dateToString': {
                            'format': date_format,
                            'date': {
                                '$dateFromString': {
                                    'dateString': '$created_at'
                                }
                            }
                        }
                    },
                    'count': {'$sum': 1},
                    'avg_rating': {'$avg': '$rating'}
                }
            },
            {
                '$sort': {'_id': 1}
            }
        ]

        try:
            results = list(col.aggregate(pipeline))
        except Exception:
            # Fallback: simple grouping if dateToString not available
            results = []
            all_reviews = list(col.find({
                'created_at': {
                    '$gte': _start_iso,
                    '$lte': _now_iso,
                }
            }, {'created_at': 1, 'rating': 1}).sort('created_at', 1).limit(10000))

            # Group manually
            grouped = {}
            for review in all_reviews:
                _rvget = review.get
                created = _rvget('created_at', '')
                if period == 'daily':
                    key = created[:10]  # YYYY-MM-DD
                elif period == 'weekly':
                    dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    key = dt.strftime('%Y-W%U')
                else:  # monthly
                    key = created[:7]  # YYYY-MM

                entry = grouped.setdefault(key, {'count': 0, 'ratings': []})
                entry['count'] += 1
                _rating = _rvget('rating')
                if _rating:
                    entry['ratings'].append(_rating)

            results = []
            for key in sorted(grouped.keys()):
                group = grouped[key]
                _ratings = group['ratings']
                avg_rating = sum(_ratings) / len(_ratings) if _ratings else 0
                results.append({
                    '_id': key,
                    'count': group['count'],
                    'avg_rating': round(avg_rating, 2)
                })

        # Format response
        trend_data = []
        for doc in results:
            trend_data.append({
                'date': doc['_id'],
                'count': doc['count'],
                'avg_rating': round(doc.get('avg_rating', 0), 2)
            })

        return JsonResponse({
            'trend': trend_data,
            'period': period,
            'days': days,
            'total_count': sum(d['count'] for d in trend_data)
        })


# ═══════════════════════════════════════════════════════════════════════════════
# ── En Çok Kullanılan Etiketler ───────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class ReviewTagsView(View):
    """
    En çok kullanılan etiketler analizi.

    GET /api/v1/admin/reviews/tags/?limit=20
    Query params:
        - limit: int (default 20, max 100)
    Return: [{tag, count}, ...]
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
            limit = min(max(1, int(_qpget('limit', 20))), 100)
        except (ValueError, TypeError):
            limit = 20

        col = get_reviews_col()

        # Aggregate tags
        pipeline = [
            {
                '$unwind': {
                    'path': '$tags',
                    'preserveNullAndEmptyArrays': False
                }
            },
            {
                '$group': {
                    '_id': '$tags',
                    'count': {'$sum': 1}
                }
            },
            {
                '$sort': {'count': -1}
            },
            {
                '$limit': limit
            }
        ]

        try:
            results = list(col.aggregate(pipeline))
        except Exception:
            results = []

        tags_data = [
            {'tag': doc['_id'], 'count': doc['count']}
            for doc in results
        ]

        return JsonResponse({
            'tags': tags_data,
            'total_unique_tags': len(tags_data),
            'limit': limit
        })
