"""
URLs para o app de produtos.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from tcc_django.core.permissions import IsOwnerOrAdmin

router = DefaultRouter()
router.register(r'', views.ProductViewSet, basename='product')

urlpatterns = [
    path('', include(router.urls)),
    path('categories/', views.CategoryListView.as_view(), name='categories'),
    path('search/', views.ProductSearchView.as_view(), name='search'),
]