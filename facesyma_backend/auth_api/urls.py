"""auth_api/urls.py"""
from django.urls import path
from django.http import JsonResponse
from django.views import View
from .views import (
    RegisterView, LoginView, GoogleAuthView, TokenRefreshView,
    MeView, ChangePasswordView, PasswordResetRequestView,
    DeleteAccountView, ExportDataView,
)

class AuthHealthView(View):
    def get(self, request):
        return JsonResponse({'status': 'ok'})

urlpatterns = [
    path('health/',            AuthHealthView.as_view(),             name='auth-health'),
    path('register/',          RegisterView.as_view(),              name='register'),
    path('token/',             LoginView.as_view(),                  name='login'),
    path('token/refresh/',     TokenRefreshView.as_view(),           name='token-refresh'),
    path('google/',            GoogleAuthView.as_view(),             name='google-auth'),
    path('me/',                MeView.as_view(),                     name='me'),
    path('me/delete/',         DeleteAccountView.as_view(),          name='me-delete'),
    path('me/export/',         ExportDataView.as_view(),             name='me-export'),
    path('password/change/',   ChangePasswordView.as_view(),         name='password-change'),
    path('password/reset/',    PasswordResetRequestView.as_view(),   name='password-reset'),
]
