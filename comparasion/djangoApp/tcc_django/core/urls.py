"""
Configuração de URLs principal do Django.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import APIRootView, HealthCheckView

# Router principal da API
router = DefaultRouter()

# URLs da API
api_patterns = [
    path('', APIRootView.as_view(), name='api-root'),
    path('health/', HealthCheckView.as_view(), name='health-check'),
    
    # Autenticação
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Apps
    path('users/', include('tcc_django.apps.users.urls')),
    path('products/', include('tcc_django.apps.products.urls')),
    path('orders/', include('tcc_django.apps.orders.urls')),
    path('payments/', include('tcc_django.apps.payments.urls')),
    
]

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API v1
    path('api/v1/', include(api_patterns)),
    
    # Router URLs
    path('api/v1/', include(router.urls)),
]

# Servir arquivos estáticos e de mídia em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Configuração do admin
admin.site.site_header = "TCC Django Admin"
admin.site.site_title = "TCC Django"
admin.site.index_title = "Painel de Administração"
