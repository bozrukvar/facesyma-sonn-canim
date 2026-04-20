"""
admin_api/views/dashboard_html_views.py
======================================
HTML dashboard views for Gamification Phase 2 monitoring.
"""

import logging
from django.http import HttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.template.loader import render_to_string

from admin_api.utils.auth import _require_auth

log = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class GamificationDashboardHTMLView(View):
    """
    GET /api/v1/admin/gamification-dashboard

    Serve the Gamification monitoring dashboard HTML page.
    """

    def get(self, request):
        try:
            # Require authentication
            _require_auth(request)

            # Render HTML template
            html = render_to_string('gamification_dashboard.html', {})

            return HttpResponse(html, content_type='text/html')

        except Exception as e:
            log.error(f"GamificationDashboardHTMLView error: {e}", exc_info=True)
            return HttpResponse(
                f"<h1>Error</h1><p>{str(e)}</p>",
                content_type='text/html',
                status=500
            )
