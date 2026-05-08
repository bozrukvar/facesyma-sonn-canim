"""partnerships/urls.py"""
from django.urls import path
from .views import InviteView, JoinView, CompatibilityView, PartnerStatusView, DisconnectView

urlpatterns = [
    path('invite/',        InviteView.as_view(),        name='partner-invite'),
    path('join/',          JoinView.as_view(),           name='partner-join'),
    path('compatibility/', CompatibilityView.as_view(),  name='partner-compatibility'),
    path('status/',        PartnerStatusView.as_view(),  name='partner-status'),
    path('disconnect/',    DisconnectView.as_view(),     name='partner-disconnect'),
]
