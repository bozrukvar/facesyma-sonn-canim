"""
admin_api/urls.py
=================
Admin API routing.
"""

from django.urls import path
from admin_api.views.auth_views import AdminLoginView, AdminMeView
from admin_api.views.user_views import (
    UserListView, UserStatsView, UserDetailView,
    UserUpdateView, UserDeleteView
)
from admin_api.views.database_views import (
    SifatListView, SifatDetailView, SifatCreateView,
    SifatUpdateView, SifatDeleteView, SifatAddCumleView,
    SifatAutoTranslateView
)
from admin_api.views.purchase_views import (
    PremiumListView, PurchaseStatsView, PlanChangeLogView
)
from admin_api.views.review_views import (
    ReviewListView, ReviewCreateView, ReviewStatsView,
    ReviewUpdateView, ReviewExportView
)
from admin_api.views.coach_views import (
    CoachOverallStatsView,
    CoachUserListView, CoachUserStatsView, CoachUserDetailView,
    CoachGoalListView, CoachGoalStatsView, CoachGoalDetailView,
    CoachAttributeListView, CoachAttributeLangView, CoachAttributeDetailView,
)

# Phase 1: Analytics, Payment, Monitoring
from admin_api.views.analytics_views import (
    AnalyticsDashboardView, UserGrowthMetricsView, RevenueMetricsView,
    CommunityMetricsView, CompatibilityMetricsView
)
from admin_api.views.payment_views import (
    PaymentTransactionsView, PaymentWebhookStripeView, PaymentWebhookIyzicoView,
    RefundView, PaymentStatsView, PaymentSettingsView
)
from admin_api.views.subscription_views import (
    VerifySubscriptionView, SubscriptionStatusView, FeatureAccessView,
    CancelSubscriptionView
)
from admin_api.views.monitoring_views import (
    HealthCheckView, UptimeMetricsView, ErrorRateView, ResponseTimeView,
    AlertManagementView, LogsView
)

# Phase 2: Moderation & Content Management
from admin_api.views.moderation_views import (
    UserReportsView, ReportReviewView, ContentModerationView,
    BanManagementView, ModerationStatsView
)
from admin_api.views.content_views import (
    CoachingContentView, ContentPublishView, ContentTranslationView,
    ABTestingView, ContentAnalyticsView, ContentTemplateView
)

# Phase 3: User Engagement & Retention
from admin_api.views.engagement_views import (
    PushNotificationCampaignView, NotificationTemplateView, EmailCampaignView,
    CampaignAnalyticsView, NotificationStatsView
)
from admin_api.views.retention_views import (
    CohortAnalysisView, RetentionCurveView, ChurnPredictionView,
    UserFunnelView, BehaviorSegmentationView
)

# Phase 4: Advanced Features
from admin_api.views.backup_views import (
    BackupManagementView, RestoreView, BackupScheduleView
)
from admin_api.views.logging_views import (
    LogAggregationView, LogAnalysisView, LogExportView
)
from admin_api.views.health_monitoring_views import (
    HealthMonitoringView, AlertConfigView, AlertHistoryView
)
from admin_api.views.reporting_views import (
    ReportGeneratorView, ReportScheduleView, ReportHistoryView
)

# Phase 6: Gamification (Coins & Achievements)
from admin_api.views.coin_views import (
    CoinBalanceView, CoinStatsView, CoinHistoryView,
    CoinAddView, CoinDeductView, DailyQuestCompleteView,
    CoinAdminAdjustView
)
from admin_api.views.meal_views import (
    MealDailyView, MealSelectView, MealSifatGuessView,
    MealLeaderboardView, MealHistoryView
)
from admin_api.views.challenge_views import (
    ChallengeTypesView, ChallengeCreateView, ChallengeJoinView,
    ChallengeUpdateScoreView, ChallengeLeaderboardView, ChallengeCancelView,
    ChallengeActiveView
)
from admin_api.views.badge_views import (
    BadgesListView, UserBadgesView, BadgeDetailView, BadgeLeaderboardView
)
from admin_api.views.discovery_game_views import (
    DiscoveryGameTypesView, DiscoveryGameStartView, DiscoveryGameAnswerView,
    DiscoveryGameSessionView, DiscoveryGameAbandonView
)
from admin_api.views.community_mission_views import (
    MissionTypesView, ActiveMissionsView, JoinMissionView,
    ContributeMissionView, MissionDetailsView, MissionLeaderboardView
)
from admin_api.views.hybrid_leaderboard_views import (
    HybridLeaderboardView, GlobalLeaderboardView, TraitLeaderboardView,
    CommunityLeaderboardView
)
from admin_api.views.leaderboard_trend_views import (
    UserTrendView, TrendingUsersView, LeaderboardStatsView,
    TakeSnapshotView, CleanupSnapshotsView
)
from admin_api.views.monitoring_gamification_views import (
    GamificationDashboardView, CacheStatisticsView, LeaderboardPerformanceView,
    WebSocketMetricsView, TrendMetricsView, SystemHealthView
)
from admin_api.views.dashboard_html_views import GamificationDashboardHTMLView

# API Endpoint'leri
api_patterns = [
    # Auth
    path('auth/login/', AdminLoginView.as_view(), name='admin-login'),
    path('auth/me/', AdminMeView.as_view(), name='admin-me'),

    # User Management (Aşama 2)
    path('users/', UserListView.as_view(), name='users-list'),
    path('users/stats/', UserStatsView.as_view(), name='users-stats'),
    path('users/<int:uid>/', UserDetailView.as_view(), name='user-detail'),
    path('users/<int:uid>/update/', UserUpdateView.as_view(), name='user-update'),
    path('users/<int:uid>/delete/', UserDeleteView.as_view(), name='user-delete'),

    # Database Management (Aşama 3)
    path('database/sifatlar/', SifatListView.as_view(), name='sifat-list'),
    path('database/sifatlar/<int:no>/', SifatDetailView.as_view(), name='sifat-detail'),
    path('database/sifatlar/create/', SifatCreateView.as_view(), name='sifat-create'),
    path('database/sifatlar/<int:no>/update/', SifatUpdateView.as_view(), name='sifat-update'),
    path('database/sifatlar/<int:no>/delete/', SifatDeleteView.as_view(), name='sifat-delete'),
    path('database/sifatlar/<int:no>/cumle/', SifatAddCumleView.as_view(), name='sifat-add-cumle'),
    path('database/sifatlar/<int:no>/translate/', SifatAutoTranslateView.as_view(), name='sifat-translate'),

    # Purchase Management (Aşama 4)
    path('purchases/premium/', PremiumListView.as_view(), name='premium-list'),
    path('purchases/stats/', PurchaseStatsView.as_view(), name='purchase-stats'),
    path('purchases/log/', PlanChangeLogView.as_view(), name='plan-change-log'),

    # Reviews Management (Aşama 5)
    path('reviews/', ReviewListView.as_view(), name='reviews-list'),
    path('reviews/create/', ReviewCreateView.as_view(), name='reviews-create'),
    path('reviews/stats/', ReviewStatsView.as_view(), name='reviews-stats'),
    path('reviews/<int:rid>/update/', ReviewUpdateView.as_view(), name='reviews-update'),
    path('reviews/export/', ReviewExportView.as_view(), name='reviews-export'),

    # Coach DB Management (Aşama 7)
    path('coach/stats/', CoachOverallStatsView.as_view(), name='coach-overall-stats'),
    path('coach/users/', CoachUserListView.as_view(), name='coach-user-list'),
    path('coach/users/stats/', CoachUserStatsView.as_view(), name='coach-user-stats'),
    path('coach/users/<int:user_id>/', CoachUserDetailView.as_view(), name='coach-user-detail'),
    path('coach/goals/', CoachGoalListView.as_view(), name='coach-goal-list'),
    path('coach/goals/stats/', CoachGoalStatsView.as_view(), name='coach-goal-stats'),
    path('coach/goals/<str:goal_id>/', CoachGoalDetailView.as_view(), name='coach-goal-detail'),
    path('coach/attributes/', CoachAttributeListView.as_view(), name='coach-attr-list'),
    path('coach/attributes/<str:lang>/', CoachAttributeLangView.as_view(), name='coach-attr-lang'),
    path('coach/attributes/<str:lang>/<path:sifat_name>/', CoachAttributeDetailView.as_view(), name='coach-attr-detail'),

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 1: ANALYTICS DASHBOARD, PAYMENT, MONITORING
    # ═══════════════════════════════════════════════════════════════════

    # Analytics & Metrics (PHASE 1)
    path('analytics/dashboard/', AnalyticsDashboardView.as_view(), name='analytics-dashboard'),
    path('analytics/users/growth/', UserGrowthMetricsView.as_view(), name='user-growth'),
    path('analytics/revenue/', RevenueMetricsView.as_view(), name='revenue-metrics'),
    path('analytics/communities/', CommunityMetricsView.as_view(), name='community-metrics'),
    path('analytics/compatibility/', CompatibilityMetricsView.as_view(), name='compatibility-metrics'),

    # Payment Integration (PHASE 1)
    path('payments/transactions/', PaymentTransactionsView.as_view(), name='payment-transactions'),
    path('payments/webhook/stripe/', PaymentWebhookStripeView.as_view(), name='webhook-stripe'),
    path('payments/webhook/iyzico/', PaymentWebhookIyzicoView.as_view(), name='webhook-iyzico'),
    path('payments/refund/', RefundView.as_view(), name='payment-refund'),
    path('payments/stats/', PaymentStatsView.as_view(), name='payment-stats'),
    path('payments/settings/', PaymentSettingsView.as_view(), name='payment-settings'),

    # Subscription Management (Mobile In-App Purchase / RevenueCat)
    path('subscription/verify/', VerifySubscriptionView.as_view(), name='subscription-verify'),
    path('subscription/status/<int:user_id>/', SubscriptionStatusView.as_view(), name='subscription-status'),
    path('subscription/feature/<int:user_id>/', FeatureAccessView.as_view(), name='feature-access'),
    path('subscription/cancel/<int:user_id>/', CancelSubscriptionView.as_view(), name='subscription-cancel'),

    # Monitoring & Health (PHASE 1)
    path('monitoring/health/', HealthCheckView.as_view(), name='health-check'),
    path('monitoring/uptime/', UptimeMetricsView.as_view(), name='uptime-metrics'),
    path('monitoring/errors/', ErrorRateView.as_view(), name='error-rate'),
    path('monitoring/response-time/', ResponseTimeView.as_view(), name='response-time'),
    path('monitoring/alerts/', AlertManagementView.as_view(), name='alert-management'),
    path('monitoring/logs/', LogsView.as_view(), name='logs'),

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 2: MODERATION & CONTENT MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════

    # Moderation & Safety (PHASE 2)
    path('moderation/reports/', UserReportsView.as_view(), name='user-reports'),
    path('moderation/reports/review/', ReportReviewView.as_view(), name='report-review'),
    path('moderation/content-check/', ContentModerationView.as_view(), name='content-moderation'),
    path('moderation/bans/', BanManagementView.as_view(), name='ban-management'),
    path('moderation/stats/', ModerationStatsView.as_view(), name='moderation-stats'),

    # Content Management (PHASE 2)
    path('content/coaching/', CoachingContentView.as_view(), name='coaching-content'),
    path('content/publish/', ContentPublishView.as_view(), name='content-publish'),
    path('content/translate/', ContentTranslationView.as_view(), name='content-translate'),
    path('content/ab-test/', ABTestingView.as_view(), name='ab-testing'),
    path('content/analytics/', ContentAnalyticsView.as_view(), name='content-analytics'),
    path('content/templates/', ContentTemplateView.as_view(), name='content-templates'),

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 3: USER ENGAGEMENT & RETENTION
    # ═══════════════════════════════════════════════════════════════════

    # Push Notifications (PHASE 3)
    path('engagement/push-campaigns/', PushNotificationCampaignView.as_view(), name='push-campaigns'),
    path('engagement/notification-templates/', NotificationTemplateView.as_view(), name='notification-templates'),
    path('engagement/email-campaigns/', EmailCampaignView.as_view(), name='email-campaigns'),
    path('engagement/campaign-analytics/', CampaignAnalyticsView.as_view(), name='campaign-analytics'),
    path('engagement/notification-stats/', NotificationStatsView.as_view(), name='notification-stats'),

    # Retention & Cohorts (PHASE 3)
    path('retention/cohort-analysis/', CohortAnalysisView.as_view(), name='cohort-analysis'),
    path('retention/curve/', RetentionCurveView.as_view(), name='retention-curve'),
    path('retention/churn-prediction/', ChurnPredictionView.as_view(), name='churn-prediction'),
    path('retention/funnel/', UserFunnelView.as_view(), name='user-funnel'),
    path('retention/segments/', BehaviorSegmentationView.as_view(), name='behavior-segments'),

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 4: ADVANCED FEATURES
    # ═══════════════════════════════════════════════════════════════════

    # Backup & Recovery (PHASE 4)
    path('backup/status/', BackupManagementView.as_view(), name='backup-status'),
    path('backup/create/', BackupManagementView.as_view(), name='backup-create'),
    path('backup/restore/', RestoreView.as_view(), name='backup-restore'),
    path('backup/schedule/', BackupScheduleView.as_view(), name='backup-schedule'),

    # Log Aggregation (PHASE 4)
    path('logs/aggregated/', LogAggregationView.as_view(), name='logs-aggregated'),
    path('logs/analysis/', LogAnalysisView.as_view(), name='logs-analysis'),
    path('logs/export/', LogExportView.as_view(), name='logs-export'),

    # Health Monitoring & Alerts (PHASE 4)
    path('health/services/', HealthMonitoringView.as_view(), name='health-services'),
    path('alerts/config/', AlertConfigView.as_view(), name='alerts-config'),
    path('alerts/history/', AlertHistoryView.as_view(), name='alerts-history'),

    # Report Generation (PHASE 4)
    path('reports/generate/', ReportGeneratorView.as_view(), name='reports-generate'),
    path('reports/schedule/', ReportScheduleView.as_view(), name='reports-schedule'),
    path('reports/history/', ReportHistoryView.as_view(), name='reports-history'),

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 6: GAMIFICATION (COINS & ACHIEVEMENTS)
    # ═══════════════════════════════════════════════════════════════════

    # Coin System (PHASE 6)
    path('coins/balance/', CoinBalanceView.as_view(), name='coin-balance'),
    path('coins/stats/', CoinStatsView.as_view(), name='coin-stats'),
    path('coins/history/', CoinHistoryView.as_view(), name='coin-history'),
    path('coins/add/', CoinAddView.as_view(), name='coin-add'),
    path('coins/deduct/', CoinDeductView.as_view(), name='coin-deduct'),
    path('coins/daily-quest/complete/', DailyQuestCompleteView.as_view(), name='daily-quest-complete'),
    path('coins/admin/adjust/', CoinAdminAdjustView.as_view(), name='coin-admin-adjust'),

    # Meal Game (PHASE 6)
    path('meals/daily/', MealDailyView.as_view(), name='meals-daily'),
    path('meals/select/', MealSelectView.as_view(), name='meals-select'),
    path('meals/guess-sifat/', MealSifatGuessView.as_view(), name='meals-guess-sifat'),
    path('meals/leaderboard/', MealLeaderboardView.as_view(), name='meals-leaderboard'),
    path('meals/history/', MealHistoryView.as_view(), name='meals-history'),

    # Social Challenges (PHASE 6)
    path('challenges/types/', ChallengeTypesView.as_view(), name='challenge-types'),
    path('challenges/create/', ChallengeCreateView.as_view(), name='challenge-create'),
    path('challenges/join/', ChallengeJoinView.as_view(), name='challenge-join'),
    path('challenges/update-score/', ChallengeUpdateScoreView.as_view(), name='challenge-update-score'),
    path('challenges/leaderboard/', ChallengeLeaderboardView.as_view(), name='challenge-leaderboard'),
    path('challenges/cancel/', ChallengeCancelView.as_view(), name='challenge-cancel'),
    path('challenges/active/', ChallengeActiveView.as_view(), name='challenge-active'),

    # Badges/Rozetler (PHASE 6)
    path('badges/', BadgesListView.as_view(), name='badges-list'),
    path('badges/user/', UserBadgesView.as_view(), name='user-badges'),
    path('badges/<str:badge_id>/', BadgeDetailView.as_view(), name='badge-detail'),
    path('badges/<str:badge_id>/leaderboard/', BadgeLeaderboardView.as_view(), name='badge-leaderboard'),

    # Discovery Games (PHASE 6)
    path('discovery-games/types/', DiscoveryGameTypesView.as_view(), name='discovery-game-types'),
    path('discovery-games/start/', DiscoveryGameStartView.as_view(), name='discovery-game-start'),
    path('discovery-games/answer/', DiscoveryGameAnswerView.as_view(), name='discovery-game-answer'),
    path('discovery-games/session/<str:session_id>/', DiscoveryGameSessionView.as_view(), name='discovery-game-session'),
    path('discovery-games/abandon/', DiscoveryGameAbandonView.as_view(), name='discovery-game-abandon'),

    # Community Missions (PHASE 6)
    path('missions/types/', MissionTypesView.as_view(), name='mission-types'),
    path('missions/active/', ActiveMissionsView.as_view(), name='missions-active'),
    path('missions/join/', JoinMissionView.as_view(), name='missions-join'),
    path('missions/contribute/', ContributeMissionView.as_view(), name='missions-contribute'),
    path('missions/<str:mission_id>/', MissionDetailsView.as_view(), name='mission-details'),
    path('missions/<str:mission_id>/leaderboard/', MissionLeaderboardView.as_view(), name='mission-leaderboard'),

    # Hybrid Leaderboards (PHASE 6)
    path('leaderboards/', HybridLeaderboardView.as_view(), name='leaderboards-hybrid'),
    path('leaderboards/global/', GlobalLeaderboardView.as_view(), name='leaderboards-global'),
    path('leaderboards/trait/', TraitLeaderboardView.as_view(), name='leaderboards-trait'),
    path('leaderboards/community/', CommunityLeaderboardView.as_view(), name='leaderboards-community'),

    # Leaderboard Trend Analysis (PHASE 6.2)
    path('leaderboards/trend/user/<int:user_id>/', UserTrendView.as_view(), name='leaderboards-user-trend'),
    path('leaderboards/trending/', TrendingUsersView.as_view(), name='leaderboards-trending'),
    path('leaderboards/stats/', LeaderboardStatsView.as_view(), name='leaderboards-stats'),
    path('leaderboards/snapshot/', TakeSnapshotView.as_view(), name='leaderboards-snapshot'),
    path('leaderboards/cleanup/', CleanupSnapshotsView.as_view(), name='leaderboards-cleanup'),

    # Gamification Monitoring Dashboard (PHASE 6.3)
    path('gamification-dashboard/', GamificationDashboardHTMLView.as_view(), name='gamification-dashboard-html'),
    path('monitoring/gamification/dashboard/', GamificationDashboardView.as_view(), name='gamification-dashboard'),
    path('monitoring/gamification/cache/', CacheStatisticsView.as_view(), name='gamification-cache-stats'),
    path('monitoring/gamification/performance/', LeaderboardPerformanceView.as_view(), name='gamification-performance'),
    path('monitoring/gamification/websocket/', WebSocketMetricsView.as_view(), name='gamification-websocket'),
    path('monitoring/gamification/trends/', TrendMetricsView.as_view(), name='gamification-trends'),
    path('monitoring/gamification/health/', SystemHealthView.as_view(), name='gamification-health'),
]

urlpatterns = api_patterns
