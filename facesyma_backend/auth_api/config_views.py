"""
auth_api/config_views.py
========================
Public config endpoint — auth gereksiz, app başlangıcında çağrılır.
Maintenance mode, feature flags, min version gibi app-specific konfigürasyonu döner.
"""

import logging
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

log = logging.getLogger(__name__)


def _get_app_registry_col():
    """Get app_registry collection — pooled connection."""
    try:
        from admin_api.utils.mongo import get_app_registry_col
        return get_app_registry_col()
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

        _fb = self._fallback_config
        try:
            col = _get_app_registry_col()
            if not col:
                # Graceful fallback if MongoDB unavailable
                return JsonResponse(_fb(app_source))

            app = col.find_one({'app_id': app_source}, {'_id': 0})
            if not app:
                # Graceful fallback if app not in registry yet
                return JsonResponse(_fb(app_source))

            _appget = app.get
            config = _appget('config', {})
            _cfget = config.get
            return JsonResponse({
                'app_id': _appget('app_id', app_source),
                'status': _appget('status', 'active'),
                'maintenance_mode': _cfget('maintenance_mode', False),
                'maintenance_message': _cfget('maintenance_message', ''),
                'min_version': _cfget('min_version', '0.0.0'),
                'feature_flags': _cfget('feature_flags', {}),
            })

        except Exception as e:
            log.warning(f'Config endpoint error: {e}')
            return JsonResponse(_fb(app_source))

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
