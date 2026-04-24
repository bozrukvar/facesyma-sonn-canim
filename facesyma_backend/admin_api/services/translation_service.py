"""
admin_api/services/translation_service.py
==========================================
Translation service for Gamification Phase 2 i18n.

Provides translation strings for all user-facing components.
Uses Django gettext for proper pluralization and context support.
"""

from django.utils.translation import gettext_lazy as _

# ═══════════════════════════════════════════════════════════════════════════════
# MONITORING DASHBOARD TRANSLATIONS
# ═══════════════════════════════════════════════════════════════════════════════

DASHBOARD_STRINGS = {
    # Header
    'title': _('🎮 Gamification Phase 2 — Monitoring Dashboard'),
    'status_loading': _('Loading...'),
    'status_healthy': _('Healthy'),
    'status_degraded': _('Degraded'),
    'status_error': _('Error'),
    'last_updated': _('Last updated: %s'),
    'refresh_now': _('↻ Refresh Now'),
    'auto_refresh': _('Auto-refresh (5s)'),

    # Cache Card
    'cache_title': _('📦 Cache Performance'),
    'cache_hit_rate': _('Hit Rate'),
    'cache_total_queries': _('Total Queries'),
    'cache_memory_used': _('Memory Used'),

    # Performance Card
    'performance_title': _('⚡ Leaderboard Performance'),
    'performance_avg_time': _('Average Query Time'),
    'performance_p95_time': _('P95 Latency'),
    'performance_total_queries': _('Total Queries'),

    # WebSocket Card
    'websocket_title': _('📡 WebSocket Connections'),
    'websocket_current': _('Current Connections'),
    'websocket_last_hour': _('Connections (Last Hour)'),
    'websocket_peak': _('Peak Today'),

    # Trends Card
    'trends_title': _('📊 Trend Analysis'),
    'trends_total': _('Total Snapshots'),
    'trends_age': _('Latest Snapshot Age'),
    'trends_retention': _('Retention Policy'),

    # Health Card
    'health_title': _('🏥 System Health'),
    'health_status': _('Status'),
    'health_components': _('Components'),

    # Chart
    'chart_title': _('📈 Query Performance Trend'),
    'chart_avg': _('Average'),
    'chart_min': _('Min'),
    'chart_max': _('Max'),

    # Table Headers
    'table_leaderboard_type': _('Leaderboard Type'),
    'table_snapshots': _('Snapshots'),
    'table_type': _('Type'),
    'table_queries': _('Queries'),
    'table_avg_time': _('Avg Time'),
    'table_min': _('Min'),
    'table_max': _('Max'),

    # Units
    'unit_percent': '%',
    'unit_ms': 'ms',
    'unit_mb': 'MB',
    'unit_hours': _('h'),
    'unit_days': _('days'),
}

# ═══════════════════════════════════════════════════════════════════════════════
# WEBSOCKET MESSAGE TRANSLATIONS
# ═══════════════════════════════════════════════════════════════════════════════

WEBSOCKET_STRINGS = {
    'connection_success': _('Connected to %s leaderboard'),
    'connection_failed': _('Failed to connect'),
    'disconnected': _('Disconnected from leaderboard'),
    'leaderboard_updated': _('Leaderboard updated, please refresh'),
    'rank_improved': _('%s moved from rank %d to rank %d'),
    'keep_alive': _('Keep-alive ping confirmed'),
    'subscribed': _('Subscribed to leaderboard updates'),
    'unsubscribed': _('Unsubscribed from leaderboard updates'),
    'error': _('Error: %s'),
}

# ═══════════════════════════════════════════════════════════════════════════════
# API ERROR MESSAGES
# ═══════════════════════════════════════════════════════════════════════════════

ERROR_STRINGS = {
    'internal_error': _('Internal server error'),
    'invalid_parameter': _('Invalid parameter: %s'),
    'not_found': _('Not found'),
    'unauthorized': _('Unauthorized'),
    'forbidden': _('Forbidden'),
    'trend_not_found': _('No trend data found for user %d'),
    'leaderboard_error': _('Leaderboard error: %s'),
    'cache_error': _('Cache error: %s'),
    'database_error': _('Database error: %s'),
    'websocket_error': _('WebSocket error: %s'),
    'invalid_json': _('Invalid JSON in request body'),
}

# ═══════════════════════════════════════════════════════════════════════════════
# LEADERBOARD STRINGS
# ═══════════════════════════════════════════════════════════════════════════════

LEADERBOARD_STRINGS = {
    'global_leaderboard': _('Global Leaderboard'),
    'trait_leaderboard': _('Trait-Based Leaderboard'),
    'community_leaderboard': _('Community Leaderboard'),
    'rank': _('Rank'),
    'username': _('Username'),
    'coins': _('Coins'),
    'badges': _('Badges'),
    'meals_completed': _('Meals Completed'),
    'challenges_won': _('Challenges Won'),
    'accuracy': _('Accuracy'),
    'user_rank': _('Your Rank'),
    'rank_change': _('Rank Change'),
    'coins_gained': _('Coins Gained'),
    'badges_unlocked': _('Badges Unlocked'),
}

# ═══════════════════════════════════════════════════════════════════════════════
# TREND ANALYSIS STRINGS
# ═══════════════════════════════════════════════════════════════════════════════

TREND_STRINGS = {
    'user_trend': _('User Trend'),
    'trending_users': _('Trending Users'),
    'leaderboard_stats': _('Leaderboard Statistics'),
    'most_improved': _('Most Improved'),
    'most_active': _('Most Active'),
    'momentum_ascending': _('Ascending'),
    'momentum_stable': _('Stable'),
    'momentum_descending': _('Descending'),
    'days_tracked': _('%d days tracked'),
    'snapshot_count': _('%d snapshots'),
}

# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM HEALTH STRINGS
# ═══════════════════════════════════════════════════════════════════════════════

HEALTH_STRINGS = {
    'redis': _('Redis'),
    'mongodb': _('MongoDB'),
    'scheduler': _('Scheduler'),
    'healthy': _('Healthy'),
    'degraded': _('Degraded'),
    'error': _('Error'),
    'unavailable': _('Unavailable'),
    'running': _('Running'),
    'stopped': _('Stopped'),
    'unknown': _('Unknown'),
}

# ═══════════════════════════════════════════════════════════════════════════════
# CACHE INVALIDATION STRINGS
# ═══════════════════════════════════════════════════════════════════════════════

CACHE_INVALIDATION_STRINGS = {
    'coins_awarded': _('Coins awarded'),
    'badge_unlocked': _('Badge unlocked'),
    'mission_completed': _('Mission completed'),
    'cache_cleared': _('Cache cleared'),
    'invalidation_failed': _('Cache invalidation failed (non-critical): %s'),
}

# Helper function to get all translations
def get_all_translations():
    """Get all translation strings for i18n setup"""
    return {
        'dashboard': DASHBOARD_STRINGS,
        'websocket': WEBSOCKET_STRINGS,
        'errors': ERROR_STRINGS,
        'leaderboard': LEADERBOARD_STRINGS,
        'trends': TREND_STRINGS,
        'health': HEALTH_STRINGS,
        'cache': CACHE_INVALIDATION_STRINGS,
    }
