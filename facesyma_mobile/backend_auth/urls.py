# facesyma_mobile/backend_auth/urls.py
# Mevcut Django urls.py'ye şunu ekleyin:
# path('auth/', include('facesyma_auth.urls')),

from django.urls import path
from . import views

urlpatterns = [
    path('register/',       views.register,       name='register'),
    path('token/',          views.login,           name='login'),
    path('token/refresh/',  views.token_refresh,   name='token-refresh'),
    path('google/',         views.google_auth,     name='google-auth'),
    path('me/',             views.me,              name='me'),
]
