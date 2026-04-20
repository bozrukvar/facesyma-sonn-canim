"""
auth_api/config_views.py
========================
Public config endpoint — auth gereksiz, app başlangıcında çağrılır.
Maintenance mode, feature flags, min version gibi app-specific konfigürasyonu döner.
"""

from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from pymongo import MongoClient
from django.conf import settings


def _get_app_registry_col():
    """Get app_registry collection"""
    try:
        client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
        return client['facesyma-backend']['app_registry']
    except Exception:
        return None


@method_decorator(csrf_exempt, name='dispatch')
class AppConfigView(View):
    """
    GET /api/v1/config/

    Public configuration endpoint — No auth required.
    Called by frontend apps at startup to check maintenance status and feature flags.

    Headers:
        X-App-Source: 'mobile' | 'web'  (default: 'mobile')

    Response:
    {
        "app_id": "mobile",
        "status": "active",
        "maintenance_mode": false,
        "maintenance_message": "",
        "min_version": "1.0.0",
        "feature_flags": {
            "golden_ratio": true,
            "ai_chat": true,
            ...
        }
    }
    """

    def get(self, request):
        # Determine app source from header
        app_source = request.headers.get('X-App-Source', 'mobile').lower()
        if app_source not in ('mobile', 'web'):
            app_source = 'mobile'

        try:
            col = _get_app_registry_col()
            if not col:
                # Graceful fallback if MongoDB unavailable
                return JsonResponse(self._fallback_config(app_source))

            app = col.find_one({'app_id': app_source}, {'_id': 0})
            if not app:
                # Graceful fallback if app not in registry yet
                return JsonResponse(self._fallback_config(app_source))

            config = app.get('config', {})
            return JsonResponse({
                'app_id': app['app_id'],
                'status': app.get('status', 'active'),
                'maintenance_mode': config.get('maintenance_mode', False),
                'maintenance_message': config.get('maintenance_message', ''),
                'min_version': config.get('min_version', '0.0.0'),
                'feature_flags': config.get('feature_flags', {}),
            })

        except Exception as e:
            # Never block app startup due to config failure
            import logging
            logging.warning(f'Config endpoint error: {e}')
            return JsonResponse(self._fallback_config(app_source))

    @staticmethod
    def _fallback_config(app_source: str) -> dict:
        """Graceful fallback — app never blocked by config issues"""
        return {
            'app_id': app_source,
            'status': 'active',
            'maintenance_mode': False,
            'maintenance_message': '',
            'min_version': '0.0.0',
            'feature_flags': {},
        }
