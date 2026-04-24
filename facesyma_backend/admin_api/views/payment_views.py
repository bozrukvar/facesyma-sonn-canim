"""
admin_api/views/payment_views.py
================================
Payment Integration & Management

Providers:
  - Google Pay  (client-side, no server webhook needed)
  - Apple Pay   (client-side, no server webhook needed)
  - Vakıfbank Sanal Pos (TODO: ileriki güncelleme ile entegre edilecek)

Transaction logs, refund management, and stats are provider-agnostic.
"""

import json
import logging
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from bson import ObjectId
from admin_api.utils.mongo import _get_db
from admin_api.utils.auth import _require_admin

log = logging.getLogger(__name__)

_TX_STATUS_PROJ = {'_id': 0, 'status': 1, 'provider': 1, 'amount': 1, 'currency': 1}

# Active payment providers
ACTIVE_PROVIDERS = ('google_pay', 'apple_pay')
# VAKIFBANK_VPP_MERCHANT_ID = getattr(settings, 'VAKIFBANK_VPP_MERCHANT_ID', '')  # TODO: ileriki versiyon





@method_decorator(csrf_exempt, name='dispatch')
class PaymentTransactionsView(View):
    """Ödeme işlemleri listesi"""

    def get(self, request):
        try:
            _require_admin(request)
            db = _get_db()
            trans_col = db['payment_transactions']

            # Filter by status
            _qget = request.GET.get
            status = _qget('status', None)  # success, failed, pending
            try:
                limit = min(max(1, int(_qget('limit', 50))), 200)
            except (ValueError, TypeError):
                limit = 50

            query = {}
            if status:
                query['status'] = status

            # Son işlemleri al
            transactions = list(trans_col.find(query)
                               .sort('created_at', -1)
                               .limit(limit))

            # ID field'ini string'e çevir
            for t in transactions:
                _oid = t['_id']
                t['_id'] = str(_oid)

            return JsonResponse({
                'success': True,
                'data': {
                    'total': trans_col.count_documents(query),
                    'limit': limit,
                    'transactions': transactions
                }
            })

        except ValueError:
            return JsonResponse({'detail': 'Unauthorized.'}, status=401)
        except PermissionError:
            return JsonResponse({'detail': 'Admin access required.'}, status=403)
        except Exception as e:
            log.exception(f'Transactions list error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class RefundView(View):
    """Refund işlemleri"""

    def post(self, request):
        """Refund talebini işle"""
        try:
            _require_admin(request)
            data = json.loads(request.body)
            _dget = data.get
            transaction_id = _dget('transaction_id')
            reason = _dget('reason')

            db = _get_db()
            trans_col = db['payment_transactions']
            refund_col = db['payment_refunds']

            # Transaction'ı bul
            try:
                _tx_oid = ObjectId(transaction_id)
            except Exception:
                return JsonResponse({'detail': 'Invalid transaction_id'}, status=400)
            transaction = trans_col.find_one({'_id': _tx_oid}, _TX_STATUS_PROJ)

            if not transaction:
                return JsonResponse({'detail': 'Transaction not found'}, status=404)

            if transaction['status'] != 'success':
                return JsonResponse({'detail': 'Only successful transactions can be refunded'}, status=400)

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
            _rid = result.inserted_id

            log.info(f"Refund request created: {_rid}")

            return JsonResponse({
                'success': True,
                'data': {
                    'refund_id': str(_rid),
                    'status': 'pending',
                    'message': 'Refund request received. It will be processed by an admin.'
                }
            })

        except (ValueError, PermissionError) as e:
            status = 401 if isinstance(e, ValueError) else 403
            return JsonResponse({'detail': str(e)}, status=status)
        except Exception as e:
            log.exception(f'Refund error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class PaymentStatsView(View):
    """Ödeme istatistikleri"""

    def get(self, request):
        try:
            _require_admin(request)
            db = _get_db()
            trans_col = db['payment_transactions']

            try:
                period_days = min(max(1, int(request.GET.get('period', '30'))), 365)
            except (ValueError, TypeError):
                period_days = 30

            start_date = datetime.utcnow() - timedelta(days=period_days)

            _tf = next(trans_col.aggregate([{'$facet': {
                'total':      [{'$match': {'created_at': {'$gte': start_date}}},                                        {'$count': 'n'}],
                'successful': [{'$match': {'created_at': {'$gte': start_date}, 'status': 'success'}},          {'$count': 'n'}],
                'failed':     [{'$match': {'created_at': {'$gte': start_date}, 'status': 'failed'}},           {'$count': 'n'}],
                'revenue':    [{'$match': {'created_at': {'$gte': start_date}, 'status': 'success'}},
                               {'$group': {'_id': None, 'total': {'$sum': '$amount'}}}],
                'google_pay': [{'$match': {'created_at': {'$gte': start_date}, 'status': 'success', 'provider': 'google_pay'}}, {'$count': 'n'}],
                'apple_pay':  [{'$match': {'created_at': {'$gte': start_date}, 'status': 'success', 'provider': 'apple_pay'}},  {'$count': 'n'}],
            }}]), {})
            _tfget = _tf.get
            total_trans   = (_tfget('total',      [{}])[0] or {}).get('n', 0)
            successful    = (_tfget('successful', [{}])[0] or {}).get('n', 0)
            failed        = (_tfget('failed',     [{}])[0] or {}).get('n', 0)
            total_revenue = (_tfget('revenue',    [{}])[0] or {}).get('total', 0) or 0
            provider_stats = {
                'google_pay': (_tfget('google_pay', [{}])[0] or {}).get('n', 0),
                'apple_pay':  (_tfget('apple_pay',  [{}])[0] or {}).get('n', 0),
                # vakifbank_vpp: TODO — ileriki versiyon
            }

            stats = {
                'period_days': period_days,
                'total_transactions': total_trans,
                'successful_transactions': successful,
                'failed_transactions': failed,
                'success_rate': round((successful / max(total_trans, 1)) * 100, 2),
                'total_revenue': round(total_revenue, 2),
                'currency': 'TRY',
                'by_provider': provider_stats
            }

            return JsonResponse({
                'success': True,
                'data': stats
            })

        except (ValueError, PermissionError) as e:
            status = 401 if isinstance(e, ValueError) else 403
            return JsonResponse({'detail': str(e)}, status=status)
        except Exception as e:
            log.exception(f'Payment stats error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class PaymentSettingsView(View):
    """Ödeme ayarları"""

    def get(self, request):
        """Mevcut ödeme ayarlarını al"""
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            settings_data = {
                'google_pay': {
                    'enabled': True,
                    'note': 'Client-side — no server webhook required'
                },
                'apple_pay': {
                    'enabled': True,
                    'note': 'Client-side — no server webhook required'
                },
                'vakifbank_vpp': {
                    'enabled': False,
                    'note': 'TODO: ileriki versiyon güncellemesi ile entegre edilecek'
                },
                'general': {
                    'premium_price_try': 199.99,
                    'currency': 'TRY',
                    'auto_upgrade_on_payment': True
                }
            }

            return JsonResponse({
                'success': True,
                'data': settings_data
            })

        except Exception as e:
            log.exception(f'Settings error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)
