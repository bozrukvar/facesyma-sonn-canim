"""analysis_api/urls.py"""
from django.urls import path
from .views import (
    AnalyzeView, AnalyzeModulesView, AnalyzeGoldenView,
    AnalyzeFaceTypeView, AnalyzeArtView, AnalyzeAstrologyView,
    AnalyzeEnhancedView, AnalyzeGoldenTransformView,
    TwinsView, HistoryView, DailyView,
)
from .assessment_views import (
    AssessmentQuestionsView, AssessmentSubmitView,
    SaveAssessmentResultView, GetAssessmentHistoryView
)
from .similarity_views import SimilarityAnalyzeView
from .compatibility_views import (
    CheckCompatibilityView, FindCompatibleUsersView, CompatibilityStatsView,
    ListCommunitiesView, JoinCommunityView, ListCommunityMembersView,
    ApproveCommunityInvitationView, ListPendingInvitationsView,
    SubscriptionStatusView, SubscriptionUpgradeView, SubscriptionCancelView,
)

urlpatterns = [
    path('analyze/',             AnalyzeView.as_view(),                   name='analyze'),
    path('analyze/enhanced/',    AnalyzeEnhancedView.as_view(),           name='analyze-enhanced'),
    path('analyze/modules/',     AnalyzeModulesView.as_view(),            name='analyze-modules'),
    path('analyze/golden/',      AnalyzeGoldenView.as_view(),             name='analyze-golden'),
    path('analyze/golden/transform/', AnalyzeGoldenTransformView.as_view(), name='analyze-golden-transform'),
    path('analyze/face_type/',   AnalyzeFaceTypeView.as_view(),           name='analyze-face-type'),
    path('analyze/art/',         AnalyzeArtView.as_view(),                name='analyze-art'),
    path('analyze/astrology/',   AnalyzeAstrologyView.as_view(),          name='analyze-astrology'),
    path('analyze/similarity/',  SimilarityAnalyzeView.as_view(),         name='analyze-similarity'),
    path('twins/',               TwinsView.as_view(),                     name='twins'),
    path('history/',             HistoryView.as_view(),                   name='history'),
    path('daily/',               DailyView.as_view(),                     name='daily'),

    # ── Compatibility & Communities (Phase 1) ──────────────────────────────────
    path('compatibility/check/',      CheckCompatibilityView.as_view(),       name='compatibility-check'),
    path('compatibility/find/',       FindCompatibleUsersView.as_view(),      name='compatibility-find'),
    path('compatibility/stats/',      CompatibilityStatsView.as_view(),       name='compatibility-stats'),
    path('communities/',              ListCommunitiesView.as_view(),          name='communities-list'),
    path('communities/invitations/pending/', ListPendingInvitationsView.as_view(), name='invitations-pending'),
    path('communities/<str:community_id>/join/',     JoinCommunityView.as_view(),            name='community-join'),
    path('communities/<str:community_id>/approve/',  ApproveCommunityInvitationView.as_view(), name='community-approve'),
    path('communities/<str:community_id>/members/',  ListCommunityMembersView.as_view(),     name='community-members'),

    # ── Subscription & Freemium (Phase 1.1+) ────────────────────────────────────
    path('subscription/status/',   SubscriptionStatusView.as_view(),   name='subscription-status'),
    path('subscription/upgrade/',  SubscriptionUpgradeView.as_view(),  name='subscription-upgrade'),
    path('subscription/cancel/',   SubscriptionCancelView.as_view(),   name='subscription-cancel'),

    # ── Assessment & Questionnaires (Phase 5) ──────────────────────────────────
    path('assessment/questions/<str:test_type>/', AssessmentQuestionsView.as_view(), name='assessment-questions'),
    path('assessment/submit/<str:test_type>/',    AssessmentSubmitView.as_view(),    name='assessment-submit'),
    path('assessment/results/<str:test_type>/',   SaveAssessmentResultView.as_view(), name='assessment-save-result'),
    path('assessment/history/',                   GetAssessmentHistoryView.as_view(), name='assessment-history'),
]
