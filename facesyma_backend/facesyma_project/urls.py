"""facesyma_project/urls.py"""
from django.urls import path, include
from django.http import HttpResponse


def health(request):
    return HttpResponse("ok", content_type="text/plain")


urlpatterns = [
    path('health/', health),
    path('api/v1/analysis/', include('analysis_api.urls')),
    path('api/v1/auth/',     include('auth_api.urls')),
    path('api/v1/config/',   include('auth_api.config_urls')),

    # Admin API (Aşama 1'den itibaren)
    path('api/v1/admin/',    include('admin_api.urls')),

    # Admin HTML Panel
    path('admin/',           include('admin_api.html_urls')),

    # AI chat servisi (FastAPI, ai_chat:8002) — Django'ya BAĞLI DEĞİL.
    # Nginx doğrudan yönlendirir: /chat/* → ai_chat:8002, /languages → ai_chat:8002
    # Django'ya /api/v1/chat/ route'u EKLEME — gereksiz ve yanlış olur.
]
