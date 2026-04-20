"""
admin_api/views/payment_views.py
================================
Payment Integration & Management

Features:
  - Stripe integration
  - iyzico integration (Turkey)
  - Payment webhook handling
  - Transaction logs
  - Refund management
"""

import json
import logging
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from pymongo import MongoClient
from django.conf import settings
from admin_api.utils.auth import _require_admin

log = logging.getLogger(__name__)

# Stripe & iyzico API keys (from environment)
STRIPE_API_KEY = getattr(settings, 'STRIPE_API_KEY', 'sk_test_xxxxx')
STRIPE_WEBHOOK_SECRET = getattr(settings, 'STRIPE_WEBHOOK_SECRET', 'whsec_xxxxx')
IYZICO_API_KEY = getattr(settings, 'IYZICO_API_KEY', 'your-key')
IYZICO_SECRET_KEY = getattr(settings, 'IYZICO_SECRET_KEY', 'your-secret')


def _get_db():
    """MongoDB bağlantısı"""
    client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
    return client['facesyma-backend']


@method_decorator(csrf_exempt, name='dispatch')
class PaymentTransactionsView(View):
    """Ödeme işlemleri listesi"""

    def get(self, request):
        try:
            _require_admin(request)
            db = _get_db()
            trans_col = db['payment_transactions']

            # Filter by status
            status = request.GET.get('status', None)  # success, failed, pending
            limit = int(request.GET.get('limit', 50))

            query = {}
            if status:
                query['status'] = status

            # Son işlemleri al
            transactions = list(trans_col.find(query)
                               .sort('created_at', -1)
                               .limit(limit))

            # ID field'ini string'e çevir
            for t in transactions:
                t['_id'] = str(t['_id'])

            return JsonResponse({
                'success': True,
                'data': {
                    'total': trans_col.count_documents(query),
                    'limit': limit,
                    'transactions': transactions
                }
            })

        except Exception as e:
            log.exception(f'Transactions list hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class PaymentWebhookStripeView(View):
    """Stripe webhook handler"""

    def post(self, request):
        try:
            payload = request.body.decode('utf-8')
            event = json.loads(payload)

            db = _get_db()
            trans_col = db['payment_transactions']

            if event['type'] == 'payment_intent.succeeded':
                payment_intent = event['data']['object']

                # MongoDB'ye kaydet
                trans_col.insert_one({
                    'provider': 'stripe',
                    'payment_intent_id': payment_intent['id'],
                    'user_id': payment_intent['metadata'].get('user_id'),
                    'amount': payment_intent['amount'] / 100,  # Cents to dollars
                    'currency': payment_intent['currency'].upper(),
                    'status': 'success',
                    'created_at': datetime.utcnow(),
                    'metadata': payment_intent['metadata']
                })

                log.info(f"✓ Stripe payment succeeded: {payment_intent['id']}")

                return JsonResponse({'success': True})

            elif event['type'] == 'charge.failed':
                charge = event['data']['object']

                trans_col.insert_one({
                    'provider': 'stripe',
                    'charge_id': charge['id'],
                    'user_id': charge['metadata'].get('user_id'),
                    'amount': charge['amount'] / 100,
                    'currency': charge['currency'].upper(),
                    'status': 'failed',
                    'failure_reason': charge['failure_message'],
                    'created_at': datetime.utcnow(),
                    'metadata': charge['metadata']
                })

                log.warning(f"⚠️  Stripe payment failed: {charge['id']}")

                return JsonResponse({'success': True})

            else:
                log.info(f"Unhandled Stripe event: {event['type']}")
                return JsonResponse({'success': True})

        except Exception as e:
            log.exception(f'Stripe webhook hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class PaymentWebhookIyzicoView(View):
    """iyzico webhook handler"""

    def post(self, request):
        try:
            payload = request.body.decode('utf-8')
            event = json.loads(payload)

            db = _get_db()
            trans_col = db['payment_transactions']

            if event.get('eventType') == 'ThreeDsAuthentication.AuthenticationCompleted':
                result = event.get('resource', {})

                trans_col.insert_one({
                    'provider': 'iyzico',
                    'payment_id': result.get('paymentId'),
                    'conversation_id': result.get('conversationId'),
                    'user_id': result.get('metadata', {}).get('user_id'),
                    'amount': result.get('paidPrice'),
                    'currency': 'TRY',
                    'status': 'success' if result.get('status') == 'success' else 'failed',
                    'created_at': datetime.utcnow(),
                    'metadata': result.get('metadata', {})
                })

                log.info(f"✓ iyzico payment: {result.get('paymentId')}")
                return JsonResponse({'success': True})

            else:
                log.info(f"Unhandled iyzico event: {event.get('eventType')}")
                return JsonResponse({'success': True})

        except Exception as e:
            log.exception(f'iyzico webhook hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class RefundView(View):
    """Refund işlemleri"""

    def post(self, request):
        """Refund talebini işle"""
        try:
            _require_admin(request)
            data = json.loads(request.body)
            transaction_id = data.get('transaction_id')
            reason = data.get('reason')

            db = _get_db()
            trans_col = db['payment_transactions']
            refund_col = db['payment_refunds']

            # Transaction'ı bul
            transaction = trans_col.find_one({'_id': transaction_id})

            if not transaction:
                return JsonResponse({'detail': 'Transaction bulunamadı'}, status=404)

            if transaction['status'] != 'success':
                return JsonResponse({'detail': 'Sadece başarılı işlemler refund edilebilir'}, status=400)

            # Refund request kaydet
            refund = {
                'transaction_id': transaction_id,
                'provider': transaction['provider'],
                'amount': transaction['amount'],
                'currency': transaction['currency'],
                'reason': reason,
                'status': 'pending',
                'created_at': datetime.utcnow(),
                'processed_at': None
            }

            result = refund_col.insert_one(refund)

            log.info(f"Refund request created: {result.inserted_id}")

            return JsonResponse({
                'success': True,
                'data': {
                    'refund_id': str(result.inserted_id),
                    'status': 'pending',
                    'message': 'Refund talebiniz alındı. Admin tarafından işlenecektir.'
                }
            })

        except Exception as e:
            log.exception(f'Refund hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class PaymentStatsView(View):
    """Ödeme istatistikleri"""

    def get(self, request):
        try:
            _require_admin(request)
            db = _get_db()
            trans_col = db['payment_transactions']

            period = request.GET.get('period', '30')  # days
            period_days = int(period)

            start_date = datetime.utcnow() - timedelta(days=period_days)

            # Total transactions
            total_trans = trans_col.count_documents({
                'created_at': {'$gte': start_date}
            })

            # Successful transactions
            successful = trans_col.count_documents({
                'created_at': {'$gte': start_date},
                'status': 'success'
            })

            # Failed transactions
            failed = trans_col.count_documents({
                'created_at': {'$gte': start_date},
                'status': 'failed'
            })

            # Total revenue
            revenue_result = list(trans_col.aggregate([
                {'$match': {
                    'created_at': {'$gte': start_date},
                    'status': 'success'
                }},
                {'$group': {
                    '_id': None,
                    'total': {'$sum': '$amount'}
                }}
            ]))

            total_revenue = revenue_result[0]['total'] if revenue_result else 0

            # By provider
            provider_stats = {}
            for provider in ['stripe', 'iyzico']:
                count = trans_col.count_documents({
                    'created_at': {'$gte': start_date},
                    'provider': provider,
                    'status': 'success'
                })
                provider_stats[provider] = count

            stats = {
                'period_days': period_days,
                'total_transactions': total_trans,
                'successful_transactions': successful,
                'failed_transactions': failed,
                'success_rate': round((successful / max(total_trans, 1)) * 100, 2),
                'total_revenue': round(total_revenue, 2),
                'currency': 'USD+TRY',
                'by_provider': provider_stats
            }

            return JsonResponse({
                'success': True,
                'data': stats
            })

        except Exception as e:
            log.exception(f'Payment stats hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class PaymentSettingsView(View):
    """Ödeme ayarları"""

    def get(self, request):
        """Mevcut ödeme ayarlarını al"""
        try:
            settings_data = {
                'stripe': {
                    'enabled': bool(STRIPE_API_KEY and STRIPE_API_KEY != 'sk_test_xxxxx'),
                    'test_mode': 'sk_test' in STRIPE_API_KEY,
                    'webhook_configured': bool(STRIPE_WEBHOOK_SECRET)
                },
                'iyzico': {
                    'enabled': bool(IYZICO_API_KEY and IYZICO_API_KEY != 'your-key'),
                    'region': 'Turkey',
                    'currency': 'TRY'
                },
                'general': {
                    'premium_price_usd': 9.99,
                    'premium_price_try': 199.99,
                    'currency_auto_detect': True,
                    'auto_upgrade_on_payment': True
                }
            }

            return JsonResponse({
                'success': True,
                'data': settings_data
            })

        except Exception as e:
            log.exception(f'Settings hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)
