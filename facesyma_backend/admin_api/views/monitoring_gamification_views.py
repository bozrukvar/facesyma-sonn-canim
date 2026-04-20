"""
admin_api/views/monitoring_gamification_views.py
================================================
Monitoring dashboard API endpoints for Gamification Phase 2.

Endpoints:
  GET  /api/v1/admin/monitoring/gamification/dashboard - Complete dashboard data
  GET  /api/v1/admin/monitoring/gamification/cache - Cache statistics
  GET  /api/v1/admin/monitoring/gamification/performance - Leaderboard performance
  GET  /api/v1/admin/monitoring/gamification/websocket - WebSocket metrics
  GET  /api/v1/admin/monitoring/gamification/trends - Trend analysis metrics
  GET  /api/v1/admin/monitoring/gamification/health - System health
"""

import logging
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from admin_api.utils.auth import _require_auth
from admin_api.services.metrics_service import MetricsService

log = logging.getLogger(__name__)


def _json_error(message: str, status: int = 400) -> JsonResponse:
    """Return error JSON response"""
    return JsonResponse({"detail": message}, status=status)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Complete Dashboard ─────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class GamificationDashboardView(View):
    """
    GET /api/v1/admin/monitoring/gamification/dashboard

    Get complete gamification monitoring dashboard.
    Returns all metrics: cache, performance, WebSocket, trends, health.
    """

    def get(self, request):
        try:
            # Require authentication
            _require_auth(request)

            # Get all metrics
            dashboard_data = MetricsService.get_dashboard_data()

            return JsonResponse(dashboard_data)

        except Exception as e:
            log.error(f"GamificationDashboardView error: {e}", exc_info=True)
            return _json_error("Internal server error", status=500)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Cache Statistics ───────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class CacheStatisticsView(View):
    """
    GET /api/v1/admin/monitoring/gamification/cache

    Get Redis cache statistics.
    Shows hit rate, memory usage, key counts by layer.
    """

    def get(self, request):
        try:
            _require_auth(request)

            cache_stats = MetricsService.get_cache_statistics()

            return JsonResponse({
                "cache_statistics": cache_stats,
                "timestamp": cache_stats.get("timestamp"),
            })

        except Exception as e:
            log.error(f"CacheStatisticsView error: {e}", exc_info=True)
            return _json_error("Internal server error", status=500)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Leaderboard Performance ────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class LeaderboardPerformanceView(View):
    """
    GET /api/v1/admin/monitoring/gamification/performance

    Get leaderboard query performance metrics.
    Shows average query time, percentiles, breakdown by leaderboard type.
    """

    def get(self, request):
        try:
            _require_auth(request)

            performance = MetricsService.get_leaderboard_performance()

            return JsonResponse({
                "leaderboard_performance": performance,
                "timestamp": performance.get("timestamp"),
            })

        except Exception as e:
            log.error(f"LeaderboardPerformanceView error: {e}", exc_info=True)
            return _json_error("Internal server error", status=500)


# ═══════════════════════════════════════════════════════════════════════════════
# ── WebSocket Metrics ──────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class WebSocketMetricsView(View):
    """
    GET /api/v1/admin/monitoring/gamification/websocket

    Get WebSocket connection metrics.
    Shows current connections, connection rate, peak connections.
    """

    def get(self, request):
        try:
            _require_auth(request)

            websocket_metrics = MetricsService.get_websocket_metrics()

            return JsonResponse({
                "websocket_metrics": websocket_metrics,
                "timestamp": websocket_metrics.get("timestamp"),
            })

        except Exception as e:
            log.error(f"WebSocketMetricsView error: {e}", exc_info=True)
            return _json_error("Internal server error", status=500)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Trend Analysis Metrics ─────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class TrendMetricsView(View):
    """
    GET /api/v1/admin/monitoring/gamification/trends

    Get leaderboard trend analysis metrics.
    Shows snapshot count, snapshot age, breakdown by leaderboard type.
    """

    def get(self, request):
        try:
            _require_auth(request)

            trend_metrics = MetricsService.get_trend_metrics()

            return JsonResponse({
                "trend_metrics": trend_metrics,
                "timestamp": trend_metrics.get("timestamp"),
            })

        except Exception as e:
            log.error(f"TrendMetricsView error: {e}", exc_info=True)
            return _json_error("Internal server error", status=500)


# ═══════════════════════════════════════════════════════════════════════════════
# ── System Health ──────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class SystemHealthView(View):
    """
    GET /api/v1/admin/monitoring/gamification/health

    Get system health status.
    Checks Redis, MongoDB, Scheduler, recent errors.
    """

    def get(self, request):
        try:
            _require_auth(request)

            health = MetricsService.get_system_health()

            # Determine HTTP status based on health
            status_code = 200 if health["status"] == "healthy" else 503

            return JsonResponse(health, status=status_code)

        except Exception as e:
            log.error(f"SystemHealthView error: {e}", exc_info=True)
            return JsonResponse({
                "status": "error",
                "error": str(e),
            }, status=500)
