from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, OrderItemViewSet, OrderItemsByOrderAPIView

router = DefaultRouter()
# /api/orders/  and /api/orders/{pk}/
router.register(r'', OrderViewSet, basename='orders')
# /api/orders/items/  and /api/orders/items/{pk}/
router.register(r'items', OrderItemViewSet, basename='order-items')

urlpatterns = [
    path('', include(router.urls)),
    # nested: /api/orders/{order_id}/items/
    path('<uuid:order_id>/items/', OrderItemsByOrderAPIView.as_view(), name='order-items-by-order'),
]
