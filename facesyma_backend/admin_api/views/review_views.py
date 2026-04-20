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


def _json(request):
    """Request body JSON'ı parse et"""
    try:
        return json.loads(request.body)
    except Exception:
        return {}


def _review_dict(review: dict) -> dict:
    """Review dokümanını response formatına dönüştür"""
    return {
        'id': review.get('id'),
        'user_id': review.get('user_id'),
        'user_email': review.get('user_email'),
        'text': review.get('text'),
        'rating': review.get('rating'),
        'platform': review.get('platform'),
        'sentiment': review.get('sentiment'),
        'sentiment_score': review.get('sentiment_score'),
        'is_visible': review.get('is_visible'),
        'created_at': str(review.get('created_at', '')),
        'tags': review.get('tags', []),
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
        page = max(1, int(request.GET.get('page', 1)))
        limit = min(int(request.GET.get('limit', 20)), 100)
        sentiment = request.GET.get('sentiment', '')
        platform = request.GET.get('platform', '')
        visible = request.GET.get('visible', '')
        user_id = request.GET.get('user_id', '')

        col = get_reviews_col()

        # Query
        query = {}
        if sentiment:
            query['sentiment'] = sentiment
        if platform:
            query['platform'] = platform
        if visible:
            query['is_visible'] = visible.lower() == 'true'
        if user_id:
            query['user_id'] = int(user_id)

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
        text = data.get('text', '').strip()
        platform = data.get('platform', 'web').strip()

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
            'user_id': data.get('user_id'),
            'user_email': data.get('user_email'),
            'text': text,
            'rating': data.get('rating'),
            'platform': platform,
            'sentiment': sentiment_analysis['sentiment'],
            'sentiment_score': sentiment_analysis['score'],
            'is_visible': True,
            'created_at': datetime.now().isoformat(),
            'tags': data.get('tags', []),
        }

        col.insert_one(review)

        return JsonResponse({
            'message': 'Yorum kaydedildi.',
            'review': _review_dict(review)
        }, status=201)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Yorum İstatistikleri ──────────────────────────────────────────────────────
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

        # Toplam yorum
        total = col.count_documents({})

        # Sentiment dağılımı
        sentiment_stats = col.aggregate([
            {'$group': {'_id': '$sentiment', 'count': {'$sum': 1}}},
        ])
        sentiment_dict = {doc['_id']: doc['count'] for doc in sentiment_stats}

        # Platform dağılımı
        platform_stats = col.aggregate([
            {'$group': {'_id': '$platform', 'count': {'$sum': 1}}},
        ])
        platform_dict = {doc['_id']: doc['count'] for doc in platform_stats}

        # Ortalama rating
        rating_stats = col.aggregate([
            {'$match': {'rating': {'$ne': None}}},
            {'$group': {'_id': None, 'avg_rating': {'$avg': '$rating'}}},
        ])
        avg_rating = 0
        for doc in rating_stats:
            avg_rating = round(doc['avg_rating'], 2)

        # Görünürlük
        visible = col.count_documents({'is_visible': True})
        hidden = col.count_documents({'is_visible': False})

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
        col = get_reviews_col()

        # Yorum var mı?
        review = col.find_one({'id': int(rid)})
        if not review:
            return JsonResponse(
                {'detail': f'Yorum #{rid} bulunamadı.'},
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
                {'detail': 'Güncellenecek alan yok.'},
                status=400
            )

        # Güncelle
        col.update_one({'id': int(rid)}, {'$set': update_data})

        # Güncellenmiş review döner
        updated = col.find_one({'id': int(rid)})
        return JsonResponse({
            'message': 'Yorum güncellendi.',
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
        format_type = request.GET.get('format', 'json').lower()
        limit = min(int(request.GET.get('limit', 100)), 10000)
        sentiment = request.GET.get('sentiment', '')

        col = get_reviews_col()

        # Query
        query = {}
        if sentiment:
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

            # Header
            headers = ['id', 'user_id', 'user_email', 'text', 'rating', 'platform',
                      'sentiment', 'sentiment_score', 'is_visible', 'created_at']
            writer.writerow(headers)

            # Rows
            for review in reviews:
                writer.writerow([
                    review.get('id'),
                    review.get('user_id'),
                    review.get('user_email'),
                    review.get('text', '').replace('\n', ' '),  # Yeni satırları kaldır
                    review.get('rating'),
                    review.get('platform'),
                    review.get('sentiment'),
                    review.get('sentiment_score'),
                    review.get('is_visible'),
                    review.get('created_at'),
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
                'export_date': datetime.now().isoformat(),
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

        period = request.GET.get('period', 'daily').lower()
        days = min(int(request.GET.get('days', 30)), 365)

        if period not in ['daily', 'weekly', 'monthly']:
            return JsonResponse({'detail': 'period daily/weekly/monthly olmalı'}, status=400)

        col = get_reviews_col()
        start_date = datetime.utcnow() - timedelta(days=days)

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
                        '$gte': start_date.isoformat(),
                        '$lte': datetime.utcnow().isoformat()
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
                    '$gte': start_date.isoformat(),
                    '$lte': datetime.utcnow().isoformat()
                }
            }, {'created_at': 1, 'rating': 1}).sort('created_at', 1))

            # Group manually
            grouped = {}
            for review in all_reviews:
                created = review.get('created_at', '')
                if period == 'daily':
                    key = created[:10]  # YYYY-MM-DD
                elif period == 'weekly':
                    dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    key = dt.strftime('%Y-W%U')
                else:  # monthly
                    key = created[:7]  # YYYY-MM

                if key not in grouped:
                    grouped[key] = {'count': 0, 'ratings': []}
                grouped[key]['count'] += 1
                if review.get('rating'):
                    grouped[key]['ratings'].append(review.get('rating'))

            results = []
            for key in sorted(grouped.keys()):
                group = grouped[key]
                avg_rating = sum(group['ratings']) / len(group['ratings']) if group['ratings'] else 0
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

        limit = min(int(request.GET.get('limit', 20)), 100)

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
