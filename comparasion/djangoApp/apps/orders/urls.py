from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, OrderItemViewSet, OrderItemsByOrderAPIView

router = DefaultRouter()
router.register(r'', OrderViewSet, basename='orders')
router.register(r'items', OrderItemViewSet, basename='order-items')

urlpatterns = [
    path('', include(router.urls)),
    path('<int:order_id>/items/', OrderItemsByOrderAPIView.as_view(), name='order-items-by-order'),
]